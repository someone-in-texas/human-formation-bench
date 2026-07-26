"""Portable JSONL plus scalable DuckDB/Parquet result storage."""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from .hashing import content_hash
from .models import ProviderResponse, RunManifest, Trajectory, dump_json
from .security import contains_sensitive_data, safe_child_path, validate_regular_file

PRIVATE_DIR_MODE = 0o700
PRIVATE_FILE_MODE = 0o600


def _protect_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=PRIVATE_DIR_MODE)
    if os.name == "posix":
        path.chmod(PRIVATE_DIR_MODE)


def _protect_file(path: Path) -> None:
    if os.name == "posix" and path.exists():
        path.chmod(PRIVATE_FILE_MODE)


class ContentCache:
    """Content-addressed cache that never includes credentials in keys or values."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        _protect_directory(self.root)

    def key(self, payload: dict[str, Any]) -> str:
        return content_hash(payload).removeprefix("sha256:")

    def get(self, key: str) -> ProviderResponse | None:
        path = safe_child_path(self.root, f"{key}.json")
        if not path.is_file():
            return None
        validate_regular_file(path, max_bytes=1_000_000)
        return ProviderResponse.model_validate_json(path.read_text(encoding="utf-8"))

    def put(self, key: str, response: ProviderResponse) -> bool:
        if contains_sensitive_data(response.text):
            return False
        path = safe_child_path(self.root, f"{key}.json")
        payload = response.model_dump_json(indent=2) + "\n"
        descriptor, temporary_name = tempfile.mkstemp(
            dir=self.root, prefix=f".{key}.", suffix=".tmp"
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            temporary.replace(path)
            _protect_file(path)
        finally:
            temporary.unlink(missing_ok=True)
        return True

    def count(self) -> int:
        return sum(1 for _ in self.root.glob("*.json"))

    def prune(self) -> int:
        count = 0
        for path in self.root.glob("*.json"):
            path.unlink()
            count += 1
        return count


class RunStore:
    def __init__(self, run_dir: Path) -> None:
        self.run_dir = run_dir.resolve()
        _protect_directory(self.run_dir)
        self.results_path = self.run_dir / "results.jsonl"
        self._lock = asyncio.Lock()

    def create(self, manifest: RunManifest, resolved_config: dict[str, Any]) -> None:
        dump_json(manifest, self.run_dir / "manifest.initial.json")
        dump_json(manifest, self.run_dir / "manifest.json")
        (self.run_dir / "resolved-config.json").write_text(
            json.dumps(resolved_config, indent=2, sort_keys=True, default=str) + "\n",
            encoding="utf-8",
        )
        for name in ("manifest.initial.json", "manifest.json", "resolved-config.json"):
            _protect_file(self.run_dir / name)

    def load_manifest(self) -> RunManifest:
        return RunManifest.model_validate_json(
            (self.run_dir / "manifest.json").read_text(encoding="utf-8")
        )

    def update_manifest(self, manifest: RunManifest) -> None:
        temporary = self.run_dir / "manifest.json.tmp"
        dump_json(manifest, temporary)
        temporary.replace(self.run_dir / "manifest.json")
        _protect_file(self.run_dir / "manifest.json")

    async def append(self, trajectory: Trajectory) -> None:
        line = trajectory.model_dump_json() + "\n"
        async with self._lock:
            with self.results_path.open("a", encoding="utf-8") as handle:
                handle.write(line)
                handle.flush()
            _protect_file(self.results_path)

    def trajectories(self) -> list[Trajectory]:
        if not self.results_path.is_file():
            return []
        validate_regular_file(self.results_path, max_bytes=1_000_000_000)
        results: list[Trajectory] = []
        with self.results_path.open(encoding="utf-8") as handle:
            for index, line in enumerate(handle, start=1):
                if index > 2_000_000:
                    raise ValueError("result record count exceeds safety limit")
                if len(line.encode("utf-8")) > 2_000_000:
                    raise ValueError("result record exceeds safety limit")
                if line.strip():
                    results.append(Trajectory.model_validate_json(line))
        return results

    def export_columnar(self, trajectories: list[Trajectory]) -> None:
        rows = []
        scores = []
        for trajectory in trajectories:
            rows.append(
                {
                    "trajectory_id": trajectory.id,
                    "scenario_id": trajectory.scenario_id,
                    "policy_id": trajectory.policy_id,
                    "model_id": trajectory.model_id,
                    "seed": trajectory.seed,
                    "cost_usd": trajectory.cost_usd,
                    "latency_ms": trajectory.latency_ms,
                    "errors_json": json.dumps(trajectory.errors),
                }
            )
            for result in trajectory.judge_results:
                scores.append(
                    {
                        "trajectory_id": trajectory.id,
                        "dimension": result.dimension.value,
                        "score": result.score,
                        "confidence": result.confidence,
                        "judge_id": result.judge_id,
                        "flags_json": json.dumps(result.flags),
                    }
                )
        trajectory_table = pa.Table.from_pylist(rows)
        score_table = pa.Table.from_pylist(scores)
        pq.write_table(trajectory_table, self.run_dir / "trajectories.parquet")
        pq.write_table(score_table, self.run_dir / "scores.parquet")
        with duckdb.connect(str(self.run_dir / "results.duckdb")) as connection:
            connection.execute("DROP TABLE IF EXISTS trajectories")
            connection.execute("DROP TABLE IF EXISTS scores")
            connection.register("trajectory_input", trajectory_table)
            connection.register("score_input", score_table)
            connection.execute("CREATE TABLE trajectories AS SELECT * FROM trajectory_input")
            connection.execute("CREATE TABLE scores AS SELECT * FROM score_input")
        for name in ("trajectories.parquet", "scores.parquet", "results.duckdb"):
            _protect_file(self.run_dir / name)
