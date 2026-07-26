import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from human_formation_benchmark.cli import app
from human_formation_benchmark.evals.formation_core import formation_core

runner = CliRunner()
ROOT = Path(__file__).resolve().parents[2]
ENV = {"HFB_HOME": str(ROOT)}


def test_cli_help_and_doctor() -> None:
    assert runner.invoke(app, ["--help"]).exit_code == 0
    doctor = runner.invoke(app, ["doctor", "--json"], env=ENV)
    assert doctor.exit_code == 0
    assert '"ok": true' in doctor.stdout


def test_cli_plan_and_validation() -> None:
    assert runner.invoke(app, ["validate", "--json"], env=ENV).exit_code == 0
    plan = runner.invoke(app, ["plan", "--max-samples", "1", "--json"], env=ENV)
    assert plan.exit_code == 0
    assert '"budget_usd": 5.0' in plan.stdout


def test_inspect_native_task_constructs() -> None:
    task = formation_core(limit=2)
    assert task.name == "hfb_formation_core"
    assert len(task.dataset) == 2


@pytest.mark.parametrize(
    "command",
    [
        ["list", "scenarios", "--json"],
        ["list", "rubrics", "--json"],
        ["list", "profiles", "--json"],
        ["prices", "show", "--json"],
        ["prices", "validate"],
        ["research", "check"],
        ["pack", "validate"],
        ["pack", "hash"],
        ["version"],
    ],
)
def test_read_only_commands(command: list[str]) -> None:
    result = runner.invoke(app, command, env=ENV)
    assert result.exit_code == 0, result.stdout


def test_init_and_pack_build(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    first = runner.invoke(app, ["init", str(config_dir)], env=ENV)
    assert first.exit_code == 0
    assert (config_dir / "hfb.yaml").is_file()
    assert runner.invoke(app, ["init", str(config_dir)], env=ENV).exit_code == 2
    assert runner.invoke(app, ["init", str(config_dir), "--force"], env=ENV).exit_code == 0
    manifest = tmp_path / "pack.json"
    build = runner.invoke(
        app,
        ["pack", "build", "--output", str(manifest)],
        env=ENV,
    )
    assert build.exit_code == 0
    assert json.loads(manifest.read_text())["scenario_ids"]


def test_run_postprocessing_and_cache_commands(tmp_path: Path) -> None:
    output = tmp_path / "runs"
    run_result = runner.invoke(
        app,
        [
            "run",
            "--max-samples",
            "1",
            "--output-root",
            str(output),
            "--benchmark-exposure",
            "public_seen",
            "--json",
        ],
        env=ENV,
    )
    assert run_result.exit_code == 0, run_result.stdout
    run_dir = next(output.iterdir())
    for command in [
        ["resume", str(run_dir), "--json"],
        ["score", str(run_dir)],
        ["adjudicate", str(run_dir)],
        ["compare", str(run_dir)],
        ["report", str(run_dir)],
        ["export", str(run_dir), "--destination", str(tmp_path / "export")],
    ]:
        result = runner.invoke(app, command, env=ENV)
        assert result.exit_code == 0, f"{command}: {result.stdout}"
    cache_dir = tmp_path / "cache"
    assert (
        runner.invoke(app, ["cache", "inspect", "--path", str(cache_dir)], env=ENV).exit_code == 0
    )
    assert runner.invoke(app, ["cache", "prune", "--path", str(cache_dir)], env=ENV).exit_code == 2
    assert (
        runner.invoke(
            app,
            ["cache", "prune", "--path", str(cache_dir), "--yes"],
            env=ENV,
        ).exit_code
        == 0
    )


def test_live_plan_requires_explicit_prices() -> None:
    result = runner.invoke(
        app,
        ["plan", "--model", "openai/example", "--budget-usd", "5"],
        env=ENV,
    )
    assert result.exit_code == 2
    assert "require --input-cost" in result.stdout
