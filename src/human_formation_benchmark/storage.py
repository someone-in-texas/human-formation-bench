"""Portable JSONL plus scalable DuckDB/Parquet result storage."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from .hashing import content_hash
from .models import ProviderResponse, RunManifest, Trajectory, dump_json
from .security import safe_child_path


class ContentCache:
    """Content-addressed cache that never includes credentials in keys or values."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def key(self, payload: dict[str, Any]) -> str:
        return content_hash(payload).removeprefix("sha256:")

    def get(self, key: str) -> ProviderResponse | None:
        path = safe_child_path(self.root, f"{key}.json")
        if not path.is_file():
            return None
        return ProviderResponse.model_validate_json(path.read_text(encoding="utf-8"))

    def put(self, key: str, response: ProviderResponse) -> None:
        path = safe_child_path(self.root, f"{key}.json")
        path.write_text(response.model_dump_json(indent=2) + "\n", encoding="utf-8")

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
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.results_path = self.run_dir / "results.jsonl"
        self._lock = asyncio.Lock()

    def create(self, manifest: RunManifest, resolved_config: dict[str, Any]) -> None:
        dump_json(manifest, self.run_dir / "manifest.initial.json")
        dump_json(manifest, self.run_dir / "manifest.json")
        (self.run_dir / "resolved-config.json").write_text(
            json.dumps(resolved_config, indent=2, sort_keys=True, default=str) + "\n",
            encoding="utf-8",
        )

    def load_manifest(self) -> RunManifest:
        return RunManifest.model_validate_json(
            (self.run_dir / "manifest.json").read_text(encoding="utf-8")
        )

    def update_manifest(self, manifest: RunManifest) -> None:
        temporary = self.run_dir / "manifest.json.tmp"
        dump_json(manifest, temporary)
        temporary.replace(self.run_dir / "manifest.json")

    async def append(self, trajectory: Trajectory) -> None:
        line = trajectory.model_dump_json() + "\n"
        async with self._lock:
            with self.results_path.open("a", encoding="utf-8") as handle:
                handle.write(line)
                handle.flush()

    def trajectories(self) -> list[Trajectory]:
        if not self.results_path.is_file():
            return []
        return [
            Trajectory.model_validate_json(line)
            for line in self.results_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

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
