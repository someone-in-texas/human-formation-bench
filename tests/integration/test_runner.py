import json
import os
from pathlib import Path

import pytest
import yaml

from human_formation_benchmark.config import load_scenarios
from human_formation_benchmark.runner import RunOptions, merge_shards, run_benchmark
from human_formation_benchmark.storage import RunStore


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fake_run_outputs_and_resume(tmp_path: Path) -> None:
    options = RunOptions(
        max_samples=2,
        output_root=tmp_path / "runs",
        cache_root=tmp_path / "cache",
    )
    run_dir = await run_benchmark(options)
    expected = {
        "manifest.initial.json",
        "manifest.json",
        "resolved-config.json",
        "results.jsonl",
        "score-report.json",
        "scores.csv",
        "trajectories.parquet",
        "scores.parquet",
        "results.duckdb",
        "report.md",
        "report.html",
        "benchmark-card.json",
    }
    assert expected <= {path.name for path in run_dir.iterdir()}
    store = RunStore(run_dir)
    assert len(store.trajectories()) == 2
    manifest = store.load_manifest()
    assert manifest.status == "completed"
    assert manifest.spent_usd == 0
    before = (run_dir / "results.jsonl").read_text(encoding="utf-8")
    resumed = await run_benchmark(options, resume_dir=run_dir)
    assert resumed == run_dir
    assert (run_dir / "results.jsonl").read_text(encoding="utf-8") == before


@pytest.mark.integration
@pytest.mark.asyncio
async def test_shards_merge_without_duplicates(tmp_path: Path) -> None:
    shard_dirs = []
    for index in range(2):
        options = RunOptions(
            max_samples=4,
            output_root=tmp_path / f"runs-{index}",
            cache_root=tmp_path / "cache",
            shards=2,
            shard_index=index,
        )
        shard_dirs.append(await run_benchmark(options))
    merged = merge_shards(tmp_path / "merged", shard_dirs)
    trajectories = RunStore(merged).trajectories()
    ids = [trajectory.id for trajectory in trajectories]
    assert len(ids) == len(set(ids)) == 4


@pytest.mark.integration
def test_public_report_has_claim_boundary(smoke_run: Path) -> None:
    report = (smoke_run / "report.md").read_text(encoding="utf-8")
    assert "What this result does not mean" in report
    assert "does not" in report
    card = json.loads((smoke_run / "benchmark-card.json").read_text(encoding="utf-8"))
    assert card["maturity"] == "alpha"


@pytest.fixture
def smoke_run(tmp_path: Path) -> Path:
    options = RunOptions(
        max_samples=1,
        output_root=tmp_path / "runs",
        cache_root=tmp_path / "cache",
    )
    return __import__("asyncio").run(run_benchmark(options))


@pytest.mark.integration
@pytest.mark.asyncio
async def test_private_pack_is_hash_only_and_transcript_free(tmp_path: Path) -> None:
    scenario = load_scenarios()[0].model_copy(
        update={
            "id": "private.synthetic.001",
            "approved_for_public_core": False,
            "user_opening": "PRIVATE HELD OUT SENTINEL: choose a bounded next action.",
        }
    )
    pack = tmp_path / "private-pack.yaml"
    pack.write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "pack_id": "private-synthetic",
                "pack_version": "0.0.1",
                "scenarios": [scenario.model_dump(mode="json")],
            }
        ),
        encoding="utf-8",
    )
    run_dir = await run_benchmark(
        RunOptions(
            pack_path=pack,
            max_samples=1,
            output_root=tmp_path / "runs",
            cache_root=tmp_path / "shared-cache-must-not-be-used",
        )
    )
    manifest = RunStore(run_dir).load_manifest()
    assert manifest.scenario_pack_id == "private-synthetic"
    assert not manifest.scenario_pack_canonical
    assert manifest.scenario_pack_disclosure == "private"
    persisted = (run_dir / "results.jsonl").read_text(encoding="utf-8")
    assert "PRIVATE HELD OUT SENTINEL" not in persisted
    assert "content withheld for private pack" in persisted
    assert not (tmp_path / "shared-cache-must-not-be-used").exists()
    if os.name == "posix":
        assert run_dir.stat().st_mode & 0o777 == 0o700
        assert (run_dir / "results.jsonl").stat().st_mode & 0o777 == 0o600


@pytest.mark.integration
@pytest.mark.asyncio
async def test_resume_fails_closed_when_policy_or_pack_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    options = RunOptions(
        max_samples=1,
        output_root=tmp_path / "runs",
        cache_root=tmp_path / "cache",
    )
    run_dir = await run_benchmark(options)
    original = __import__(
        "human_formation_benchmark.runner", fromlist=["load_named_config"]
    ).load_named_config

    def changed(kind: str, name: str) -> dict[str, object]:
        item = original(kind, name)
        if kind == "policies":
            item["system_prompt"] = f"{item['system_prompt']} changed"
        return item

    monkeypatch.setattr("human_formation_benchmark.runner.load_named_config", changed)
    manifest = RunStore(run_dir).load_manifest()
    manifest.status = "interrupted"
    RunStore(run_dir).update_manifest(manifest)
    with pytest.raises(ValueError, match="input hash mismatch"):
        await run_benchmark(options, resume_dir=run_dir)
