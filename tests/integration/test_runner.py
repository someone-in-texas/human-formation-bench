import json
from pathlib import Path

import pytest

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
