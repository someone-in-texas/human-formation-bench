"""Command-line interface for planning, running, validating, and reporting HFB."""

from __future__ import annotations

import asyncio
import json
import shutil
import sys
from pathlib import Path
from typing import Annotated, Any, Literal, NoReturn

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .config import (
    list_profiles,
    load_named_config,
    load_prices,
    load_profile,
    load_rubrics,
    load_scenarios,
    validate_challenge_coverage,
    validate_foundations,
)
from .extensions import list_extensions, render_extension_artifacts, resolve_extension
from .hashing import content_hash
from .models import Dimension
from .pack import build_manifest, pack_hash, validate_pack
from .pricing import estimate_run
from .providers import FakeProvider
from .reporting import render_reports
from .research import check_registry
from .runner import RunOptions, merge_shards, run_benchmark
from .scoring import aggregate
from .security import protect_artifact_tree
from .storage import ContentCache, RunStore

app = typer.Typer(
    name="hfb",
    help="Human Formation Benchmark: vector-first evaluation of longitudinal interaction behavior.",
    no_args_is_help=True,
)
list_app = typer.Typer(help="List canonical benchmark assets.")
pack_app = typer.Typer(help="Build, validate, and hash scenario packs.")
cache_app = typer.Typer(help="Inspect or prune the content-addressed response cache.")
prices_app = typer.Typer(help="Inspect and validate versioned price data.")
research_app = typer.Typer(help="Validate research provenance.")
app.add_typer(list_app, name="list")
app.add_typer(pack_app, name="pack")
app.add_typer(cache_app, name="cache")
app.add_typer(prices_app, name="prices")
app.add_typer(research_app, name="research")
console = Console()


def _emit(payload: Any, *, json_output: bool = False) -> None:
    if json_output:
        if hasattr(payload, "model_dump"):
            payload = payload.model_dump(mode="json")
        console.print_json(json.dumps(payload, default=str))
    else:
        console.print(payload)


def _fail(message: str, code: int = 2) -> NoReturn:
    console.print(f"[red]Error:[/red] {message}", highlight=False)
    raise typer.Exit(code)


def _resolve_cli_extension(extension: str | None) -> Any:
    try:
        return resolve_extension(extension)
    except (KeyError, OSError, ValueError) as error:
        _fail(f"{type(error).__name__}: {error}")


@app.command()
def init(
    destination: Annotated[Path, typer.Argument(help="Directory to initialize.")] = Path("."),
    force: Annotated[bool, typer.Option(help="Overwrite an existing hfb.yaml.")] = False,
) -> None:
    """Create a minimal local configuration; never writes API keys."""

    destination.mkdir(parents=True, exist_ok=True)
    path = destination / "hfb.yaml"
    if path.exists() and not force:
        _fail(f"{path} already exists (use --force to replace)")
    path.write_text(
        "schema_version: '1.0'\nprofile: micro\nmodel: fake/formation-v1\nbudget_usd: 5.0\n",
        encoding="utf-8",
    )
    console.print(f"Created {path}")


@app.command()
def doctor(json_output: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Check local runtime, assets, and no-network fake-provider readiness."""

    checks: dict[str, Any] = {
        "python": sys.version.split()[0],
        "python_supported": sys.version_info >= (3, 11),
        "package_version": __version__,
        "scenarios": len(load_scenarios()),
        "rubrics": len(load_rubrics()),
        "profiles": len(list_profiles()),
        "fake_provider": FakeProvider.model_id,
        "inspect_cli": shutil.which("inspect") is not None,
        "git": shutil.which("git") is not None,
    }
    checks["ok"] = bool(
        checks["python_supported"]
        and checks["scenarios"] >= 20
        and checks["rubrics"] == len(Dimension)
        and checks["inspect_cli"]
    )
    _emit(checks, json_output=json_output)
    if not checks["ok"]:
        raise typer.Exit(1)


@app.command("validate")
def validate_command(
    extension: Annotated[
        str | None,
        typer.Option("--extension", "--module", help="Built-in benchmark extension."),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Validate canonical scenarios, rubrics, profiles, and source records."""

    try:
        resolved_extension = resolve_extension(extension)
        scenarios = (
            load_scenarios(extension=resolved_extension)
            if resolved_extension is not None
            else validate_pack()
        )
        rubrics = load_rubrics(extension=resolved_extension)
        profiles = list_profiles(extension=resolved_extension)
        sources = check_registry()
        constitutions, lenses = validate_foundations()
        perspective_contrasts, adversarial_challenges = validate_challenge_coverage()
        covered = {rubric.dimension for rubric in rubrics}
        if covered != set(Dimension):
            raise ValueError("rubrics do not cover every core dimension exactly")
        result = {
            "ok": True,
            "scenarios": len(scenarios),
            "rubrics": len(rubrics),
            "profiles": len(profiles),
            "sources": len(sources),
            "constitutions": constitutions,
            "lenses": lenses,
            "perspective_contrasts": perspective_contrasts,
            "adversarial_challenges": adversarial_challenges,
            "pack_hash": (
                content_hash([scenario.model_dump(mode="json") for scenario in scenarios])
                if resolved_extension is not None
                else pack_hash()
            ),
        }
        if resolved_extension is not None:
            controls = resolved_extension.descriptor.research_control_policy_ids
            for policy_id in controls:
                policy = load_named_config(
                    "policies",
                    policy_id,
                    extension=resolved_extension,
                )
                if policy.get("research_control") is not True:
                    raise ValueError(
                        f"declared research control is not marked research_control: {policy_id}"
                    )
            result["extension"] = {
                "id": resolved_extension.descriptor.id,
                "version": resolved_extension.descriptor.version,
                "fingerprint": resolved_extension.fingerprint,
            }
    except Exception as error:
        _fail(f"{type(error).__name__}: {error}")
    _emit(result, json_output=json_output)


@list_app.command("scenarios")
def list_scenarios(json_output: Annotated[bool, typer.Option("--json")] = False) -> None:
    scenarios = load_scenarios()
    if json_output:
        _emit([item.model_dump(mode="json") for item in scenarios], json_output=True)
        return
    table = Table("ID", "Domain", "Stakes", "Length")
    for scenario in scenarios:
        table.add_row(
            scenario.id,
            scenario.domain,
            scenario.stakes,
            scenario.trajectory_length.value,
        )
    console.print(table)


@list_app.command("rubrics")
def list_rubrics(json_output: Annotated[bool, typer.Option("--json")] = False) -> None:
    rubrics = load_rubrics()
    if json_output:
        _emit([item.model_dump(mode="json") for item in rubrics], json_output=True)
        return
    table = Table("ID", "Dimension", "Version")
    for rubric in rubrics:
        table.add_row(rubric.id, rubric.dimension.value, rubric.version)
    console.print(table)


@list_app.command("profiles")
def list_run_profiles(json_output: Annotated[bool, typer.Option("--json")] = False) -> None:
    profiles = list_profiles()
    if json_output:
        _emit([item.model_dump(mode="json") for item in profiles], json_output=True)
        return
    table = Table("Profile", "Scenarios", "Policies", "Seeds", "Budget", "Assurance")
    for profile in profiles:
        budget = (
            "explicit"
            if profile.default_budget_usd is None
            else f"${profile.default_budget_usd:.0f}"
        )
        table.add_row(
            profile.id,
            str(profile.scenario_limit),
            str(len(profile.policies)),
            str(len(profile.seeds)),
            budget,
            profile.assurance,
        )
    console.print(table)


@list_app.command("extensions")
def list_benchmark_extensions(
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    extensions = list_extensions()
    if json_output:
        _emit([item.model_dump(mode="json") for item in extensions], json_output=True)
        return
    table = Table("Extension", "Title", "Version", "Status", "Research controls")
    for descriptor in extensions:
        table.add_row(
            descriptor.id,
            descriptor.title,
            descriptor.version,
            descriptor.status,
            "yes" if descriptor.research_controls_available else "no",
        )
    console.print(table)


def _price_for_plan(model: str, input_cost: float | None, output_cost: float | None) -> Any:
    from .models import PriceEntry

    if model.startswith("fake/"):
        return load_prices()[0]
    if input_cost is None or output_cost is None:
        _fail("live models require --input-cost and --output-cost (USD per million tokens)")
    return PriceEntry(
        provider=model.split("/", 1)[0],
        model_pattern=model,
        input_per_million_usd=input_cost,
        output_per_million_usd=output_cost,
        effective_date="2026-07-25",
        source_url="user-supplied",
        last_verified_date="2026-07-25",
    )


@app.command()
def plan(
    profile: Annotated[str, typer.Option()] = "micro",
    model: Annotated[str, typer.Option()] = "fake/formation-v1",
    judge: Annotated[list[str] | None, typer.Option()] = None,
    budget_usd: Annotated[float | None, typer.Option(min=0.01)] = None,
    input_cost: Annotated[float | None, typer.Option(help="USD per million input tokens.")] = None,
    output_cost: Annotated[
        float | None, typer.Option(help="USD per million output tokens.")
    ] = None,
    max_samples: Annotated[int | None, typer.Option(min=1)] = None,
    pack: Annotated[
        Path | None,
        typer.Option(exists=True, dir_okay=False, help="External private scenario-pack YAML."),
    ] = None,
    extension: Annotated[
        str | None,
        typer.Option("--extension", "--module", help="Built-in benchmark extension."),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Print a no-network call graph and low/base/high cost estimate."""

    resolved_extension = _resolve_cli_extension(extension)
    run_profile = load_profile(profile, extension=resolved_extension)
    if judge:
        run_profile = run_profile.model_copy(update={"judges": judge})
    budget = budget_usd or run_profile.default_budget_usd
    if budget is None:
        _fail(f"{profile} requires --budget-usd")
    price = _price_for_plan(model, input_cost, output_cost)
    estimate = estimate_run(
        run_profile,
        model,
        price,
        budget,
        sample_count=min(
            run_profile.scenario_limit,
            max_samples or run_profile.scenario_limit,
            len(
                load_scenarios(
                    pack_path=pack.resolve() if pack else None,
                    extension=resolved_extension,
                )
            ),
        ),
    )
    if resolved_extension is None:
        _emit(estimate, json_output=json_output)
    else:
        payload = estimate.model_dump(mode="json")
        payload["extension"] = {
            "id": resolved_extension.descriptor.id,
            "version": resolved_extension.descriptor.version,
            "fingerprint": resolved_extension.fingerprint,
        }
        _emit(payload, json_output=json_output)


def _options(
    profile: str,
    model: str,
    judge: list[str] | None,
    budget_usd: float | None,
    hard_stop: bool,
    max_samples: int | None,
    sample_rate: float,
    dimensions: list[str] | None,
    domains: list[str] | None,
    shards: int,
    shard_index: int,
    output_root: Path,
    input_cost: float | None,
    output_cost: float | None,
    policies: list[str] | None,
    pack: Path | None,
    benchmark_exposure: str,
    benchmark_specific_tuning: bool | None,
    extension: str | None,
    allow_research_controls: bool,
) -> RunOptions:
    resolved_extension = _resolve_cli_extension(extension)
    configured_judges = judge or load_profile(profile, extension=resolved_extension).judges
    return RunOptions(
        profile=profile,
        model=model,
        judge_models=configured_judges,
        budget_usd=budget_usd,
        hard_stop=hard_stop,
        max_samples=max_samples,
        sample_rate=sample_rate,
        dimensions=set(dimensions or []),
        domains=set(domains or []),
        shards=shards,
        shard_index=shard_index,
        output_root=output_root,
        input_per_million_usd=input_cost,
        output_per_million_usd=output_cost,
        policies=policies,
        pack_path=pack.resolve() if pack else None,
        benchmark_exposure=benchmark_exposure,
        benchmark_specific_tuning=benchmark_specific_tuning,
        extension=extension,
        allow_research_controls=allow_research_controls,
    )


@app.command()
def run(
    profile: Annotated[str, typer.Option()] = "micro",
    model: Annotated[str, typer.Option()] = "fake/formation-v1",
    judge: Annotated[list[str] | None, typer.Option()] = None,
    budget_usd: Annotated[float | None, typer.Option(min=0.01)] = None,
    hard_stop: Annotated[bool, typer.Option("--hard-stop/--no-hard-stop")] = True,
    max_samples: Annotated[int | None, typer.Option(min=1)] = None,
    sample_rate: Annotated[float, typer.Option(min=0.0001, max=1)] = 1.0,
    dimensions: Annotated[list[str] | None, typer.Option("--dimension")] = None,
    domains: Annotated[list[str] | None, typer.Option("--domain")] = None,
    shards: Annotated[int, typer.Option(min=1)] = 1,
    shard_index: Annotated[int, typer.Option(min=0)] = 0,
    output_root: Annotated[Path, typer.Option()] = Path("runs"),
    input_cost: Annotated[float | None, typer.Option()] = None,
    output_cost: Annotated[float | None, typer.Option()] = None,
    policy: Annotated[list[str] | None, typer.Option()] = None,
    pack: Annotated[
        Path | None,
        typer.Option(exists=True, dir_okay=False, help="External private scenario-pack YAML."),
    ] = None,
    benchmark_exposure: Annotated[
        Literal["not_provided", "public_seen", "public_tuned", "private_unseen", "mixed"],
        typer.Option(help="Required disclosure for comparative publication."),
    ] = "not_provided",
    benchmark_specific_tuning: Annotated[
        bool | None,
        typer.Option("--benchmark-specific-tuning/--no-benchmark-specific-tuning"),
    ] = None,
    extension: Annotated[
        str | None,
        typer.Option("--extension", "--module", help="Built-in benchmark extension."),
    ] = None,
    allow_research_controls: Annotated[
        bool,
        typer.Option(
            "--allow-research-controls",
            help="Explicitly allow non-production research-control policies.",
        ),
    ] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Run a resumable evaluation; fake provider is the no-cost default."""

    options = _options(
        profile,
        model,
        judge,
        budget_usd,
        hard_stop,
        max_samples,
        sample_rate,
        dimensions,
        domains,
        shards,
        shard_index,
        output_root,
        input_cost,
        output_cost,
        policy,
        pack,
        benchmark_exposure,
        benchmark_specific_tuning,
        extension,
        allow_research_controls,
    )
    try:
        path = asyncio.run(run_benchmark(options))
    except Exception as error:
        _fail(f"{type(error).__name__}: {error}", 1)
    manifest = RunStore(path).load_manifest()
    _emit(
        {
            "run_dir": str(path),
            "report": str(path / "report.html"),
            "status": manifest.status,
        },
        json_output=json_output,
    )
    if manifest.status != "completed":
        raise typer.Exit(1)


@app.command()
def resume(
    run_dir: Annotated[Path, typer.Argument(exists=True, file_okay=False)],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Resume an interrupted run from its resolved configuration."""

    store = RunStore(run_dir)
    manifest = store.load_manifest()
    config = json.loads((run_dir / "resolved-config.json").read_text(encoding="utf-8"))
    raw = config["options"]
    options = RunOptions(
        profile=manifest.profile,
        model=manifest.model,
        judge_models=manifest.judge_models,
        budget_usd=manifest.budget_usd,
        hard_stop=manifest.hard_stop,
        reserve_fraction=manifest.reserve_fraction,
        max_samples=raw.get("max_samples"),
        sample_rate=raw.get("sample_rate", 1.0),
        dimensions=set(raw.get("dimensions", [])),
        domains=set(raw.get("domains", [])),
        shards=manifest.shards,
        shard_index=manifest.shard_index,
        output_root=run_dir.parent,
        input_per_million_usd=raw.get("input_per_million_usd"),
        output_per_million_usd=raw.get("output_per_million_usd"),
        policies=raw.get("policies"),
        pack_path=Path(config["pack_path"]).resolve() if config.get("pack_path") else None,
        benchmark_exposure=manifest.benchmark_exposure,
        benchmark_specific_tuning=manifest.benchmark_specific_tuning,
        extension=raw.get("extension"),
        allow_research_controls=raw.get("allow_research_controls", False),
    )
    try:
        path = asyncio.run(run_benchmark(options, resume_dir=run_dir))
    except Exception as error:
        _fail(f"{type(error).__name__}: {error}", 1)
    resumed = RunStore(path).load_manifest()
    _emit({"run_dir": str(path), "status": resumed.status}, json_output=json_output)
    if resumed.status != "completed":
        raise typer.Exit(1)


@app.command()
def score(run_dir: Annotated[Path, typer.Argument(exists=True, file_okay=False)]) -> None:
    store = RunStore(run_dir)
    manifest = store.load_manifest()
    report = aggregate(
        store.iter_trajectories(),
        assurance=load_profile(
            manifest.profile,
            extension=resolve_extension(getattr(manifest, "extension_id", None)),
        ).assurance,
        configured_judges=manifest.judge_models,
        target_model=manifest.model,
    )
    if manifest.status != "completed":
        report = report.model_copy(
            update={
                "assurance": "unavailable-partial",
                "assurance_reasons": [
                    *report.assurance_reasons,
                    f"run status is {manifest.status}",
                ],
            }
        )
    (run_dir / "score-report.json").write_text(
        report.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )
    protect_artifact_tree(run_dir)
    console.print(run_dir / "score-report.json")


@app.command()
def adjudicate(run_dir: Annotated[Path, typer.Argument(exists=True, file_okay=False)]) -> None:
    """Create a human-adjudication queue for low-confidence or large-disagreement cases."""

    store = RunStore(run_dir)
    queue = [
        {
            "trajectory_id": trajectory.id,
            "results": [
                result.model_dump(mode="json")
                for result in trajectory.judge_results
                if result.confidence < 0.60 or result.score == 2
            ],
        }
        for trajectory in store.iter_trajectories()
    ]
    queue = [item for item in queue if item["results"]]
    path = run_dir / "adjudication-queue.json"
    path.write_text(json.dumps(queue, indent=2) + "\n", encoding="utf-8")
    protect_artifact_tree(run_dir)
    console.print(f"{len(queue)} cases written to {path}")


@app.command()
def compare(run_dir: Annotated[Path, typer.Argument(exists=True, file_okay=False)]) -> None:
    """Print paired policy means by dimension for one multi-policy run."""

    store = RunStore(run_dir)
    manifest = store.load_manifest()
    if manifest.benchmark_exposure == "not_provided":
        _fail("comparative output requires --benchmark-exposure on the original run")
    buckets: dict[tuple[str, str], list[int]] = {}
    for trajectory in store.iter_trajectories():
        for result in trajectory.judge_results:
            if result.score is not None:
                buckets.setdefault((trajectory.policy_id, result.dimension.value), []).append(
                    result.score
                )
    table = Table("Policy", "Dimension", "Mean (0-4)", "N")
    for (policy_id, dimension), values in sorted(buckets.items()):
        table.add_row(policy_id, dimension, f"{sum(values) / len(values):.3f}", str(len(values)))
    console.print(table)


@app.command()
def report(run_dir: Annotated[Path, typer.Argument(exists=True, file_okay=False)]) -> None:
    store = RunStore(run_dir)
    manifest = store.load_manifest()
    score_report = aggregate(
        store.iter_trajectories(),
        assurance=load_profile(
            manifest.profile,
            extension=resolve_extension(getattr(manifest, "extension_id", None)),
        ).assurance,
        configured_judges=manifest.judge_models,
        target_model=manifest.model,
    )
    if manifest.status != "completed":
        score_report = score_report.model_copy(
            update={
                "assurance": "unavailable-partial",
                "assurance_reasons": [
                    *score_report.assurance_reasons,
                    f"run status is {manifest.status}",
                ],
            }
        )
    trajectories = list(store.iter_trajectories())
    render_reports(run_dir, manifest, score_report, trajectories)
    render_extension_artifacts(
        getattr(manifest, "extension_id", None),
        run_dir,
        trajectories,
    )
    store.export_columnar(trajectories)
    protect_artifact_tree(run_dir)
    console.print(run_dir / "report.html")


@app.command()
def export(
    run_dir: Annotated[Path, typer.Argument(exists=True, file_okay=False)],
    destination: Annotated[Path, typer.Option()] = Path("hfb-export"),
) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    manifest = RunStore(run_dir).load_manifest()
    names = [
        "manifest.json",
        "score-report.json",
        "scores.csv",
        "scores.parquet",
        "report.md",
        "report.html",
        "benchmark-card.json",
    ]
    if getattr(manifest, "extension_id", None) == "gravity":
        names.extend(["gravity-report.json", "gravity-signals.jsonl"])
    if manifest.scenario_pack_disclosure != "private":
        names.extend(["results.jsonl", "trajectories.parquet"])
    for name in names:
        source = run_dir / name
        if source.exists():
            shutil.copy2(source, destination / name)
    if manifest.scenario_pack_disclosure == "private":
        protect_artifact_tree(destination)
    console.print(destination)


@app.command()
def merge(
    output_dir: Annotated[Path, typer.Option()],
    shard_dirs: Annotated[list[Path], typer.Argument()],
) -> None:
    try:
        path = merge_shards(output_dir, shard_dirs)
    except Exception as error:
        _fail(f"{type(error).__name__}: {error}", 1)
    console.print(path)


@pack_app.command("validate")
def pack_validate(path: Annotated[Path | None, typer.Argument()] = None) -> None:
    scenarios = validate_pack(path)
    console.print(f"Valid: {len(scenarios)} scenarios")


@pack_app.command("hash")
def pack_hash_command(path: Annotated[Path | None, typer.Argument()] = None) -> None:
    console.print(pack_hash(path))


@pack_app.command("build")
def pack_build(
    path: Annotated[Path | None, typer.Argument()] = None,
    output: Annotated[Path, typer.Option()] = Path("scenario-pack-manifest.json"),
) -> None:
    output.write_text(build_manifest(path).model_dump_json(indent=2) + "\n", encoding="utf-8")
    console.print(output)


def _cache(path: Path | None) -> ContentCache:
    from platformdirs import user_cache_path

    return ContentCache(path or user_cache_path("hfb") / "responses")


@cache_app.command("inspect")
def cache_inspect(path: Annotated[Path | None, typer.Option()] = None) -> None:
    console.print({"entries": _cache(path).count()})


@cache_app.command("prune")
def cache_prune(
    path: Annotated[Path | None, typer.Option()] = None,
    yes: Annotated[bool, typer.Option("--yes")] = False,
) -> None:
    if not yes:
        _fail("cache deletion requires --yes")
    console.print({"removed": _cache(path).prune()})


@prices_app.command("show")
def prices_show(json_output: Annotated[bool, typer.Option("--json")] = False) -> None:
    prices = load_prices()
    _emit([price.model_dump(mode="json") for price in prices], json_output=json_output)


@prices_app.command("validate")
def prices_validate() -> None:
    prices = load_prices()
    console.print(f"Valid: {len(prices)} registry entries")


@research_app.command("check")
def research_check() -> None:
    sources = check_registry()
    console.print(f"Valid: {len(sources)} source records")


@app.command()
def version() -> None:
    console.print(__version__)


def main() -> None:
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
