"""Resumable, sharded, budget-bounded trajectory execution."""

from __future__ import annotations

import asyncio
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from platformdirs import user_cache_path

from . import __version__
from .config import load_lenses, load_named_config, load_profile, load_rubrics, load_scenarios
from .hashing import content_hash
from .models import (
    EvidenceSpan,
    GateHit,
    Message,
    PriceEntry,
    RunManifest,
    RunProfile,
    Scenario,
    Trajectory,
    UserState,
)
from .pack import build_manifest
from .pricing import BudgetExceeded, BudgetGuard, token_cost
from .providers import FakeProvider, InspectProvider, Provider
from .reporting import render_reports
from .scoring import aggregate, detect_failure_gates, deterministic_score, failure_gate_matches
from .security import protect_artifact_tree, redact
from .simulation import transition
from .storage import ContentCache, RunStore

TURN_LIMITS = {
    "single_turn": 1,
    "short": 5,
    "medium": 15,
    "longitudinal": None,
}


@dataclass
class RunOptions:
    profile: str = "micro"
    model: str = "fake/formation-v1"
    judge_models: list[str] = field(default_factory=lambda: ["deterministic-v1"])
    budget_usd: float | None = None
    hard_stop: bool = True
    reserve_fraction: float = 0.10
    max_samples: int | None = None
    sample_rate: float = 1.0
    dimensions: set[str] = field(default_factory=set)
    domains: set[str] = field(default_factory=set)
    shards: int = 1
    shard_index: int = 0
    deterministic: bool = True
    output_root: Path = Path("runs")
    cache_root: Path | None = None
    input_per_million_usd: float | None = None
    output_per_million_usd: float | None = None
    policies: list[str] | None = None
    pack_path: Path | None = None
    benchmark_exposure: str = "not_provided"
    benchmark_specific_tuning: bool | None = None


def _git_commit() -> str:
    git = shutil.which("git")
    if git is None:
        return "unknown"
    try:
        return subprocess.run(  # noqa: S603 - fixed git invocation, no untrusted arguments
            [git, "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _select_scenarios(
    options: RunOptions, profile_limit: int, *, apply_shard: bool = True
) -> list[Scenario]:
    scenarios = load_scenarios(pack_path=options.pack_path)
    if options.domains:
        scenarios = [scenario for scenario in scenarios if scenario.domain in options.domains]
    if options.dimensions:
        scenarios = [
            scenario
            for scenario in scenarios
            if options.dimensions.intersection(dimension.value for dimension in scenario.dimensions)
        ]
    if not 0 < options.sample_rate <= 1:
        raise ValueError("sample rate must be in (0, 1]")
    if options.sample_rate < 1:
        scenarios = [
            scenario
            for scenario in scenarios
            if int(content_hash(scenario.id).removeprefix("sha256:")[:8], 16) / 0xFFFFFFFF
            < options.sample_rate
        ]
    limit = min(profile_limit, options.max_samples or profile_limit)
    scenarios = scenarios[:limit]
    if options.shards <= 0 or not 0 <= options.shard_index < options.shards:
        raise ValueError("shard index must satisfy 0 <= index < shards")
    if not apply_shard:
        return scenarios
    return [
        scenario
        for scenario in scenarios
        if int(content_hash(scenario.id).removeprefix("sha256:")[:8], 16) % options.shards
        == options.shard_index
    ]


def _provider(options: RunOptions) -> tuple[Provider, PriceEntry]:
    if options.model.startswith("fake/"):
        return FakeProvider(), PriceEntry(
            provider="fake",
            model_pattern="fake/*",
            input_per_million_usd=0,
            cached_input_per_million_usd=0,
            output_per_million_usd=0,
            effective_date="2026-07-25",
            source_url="local",
            last_verified_date="2026-07-25",
        )
    if options.input_per_million_usd is None or options.output_per_million_usd is None:
        raise ValueError(
            "live models require explicit --input-cost and --output-cost overrides; "
            "HFB refuses to guess mutable provider prices"
        )
    price = PriceEntry(
        provider=options.model.split("/", 1)[0],
        model_pattern=options.model,
        input_per_million_usd=options.input_per_million_usd,
        output_per_million_usd=options.output_per_million_usd,
        effective_date=datetime.now(UTC).date().isoformat(),
        source_url="user-supplied",
        last_verified_date=datetime.now(UTC).date().isoformat(),
    )
    return InspectProvider(
        options.model,
        input_per_million_usd=price.input_per_million_usd,
        output_per_million_usd=price.output_per_million_usd,
    ), price


def _configuration_payload(
    options: RunOptions,
    profile: RunProfile,
    scenarios: list[Scenario],
    policies: list[str],
    price: PriceEntry,
) -> dict[str, object]:
    hash_options = {
        key: value
        for key, value in options.__dict__.items()
        if key not in {"shard_index", "output_root", "cache_root", "pack_path"}
    }
    return {
        "options": {
            **hash_options,
            "dimensions": sorted(options.dimensions),
            "domains": sorted(options.domains),
        },
        "profile": profile.model_dump(mode="json"),
        "scenarios": [scenario.model_dump(mode="json") for scenario in scenarios],
        "policies": [load_named_config("policies", policy_id) for policy_id in policies],
        "rubrics": [rubric.model_dump(mode="json") for rubric in load_rubrics()],
        "judges": [load_named_config("judges", judge_id) for judge_id in options.judge_models],
        "price": price.model_dump(mode="json"),
        "simulator": "deterministic-derived-diagnostic-v1",
        "scorer": "deterministic-detector-v1",
    }


def _manifest(
    run_id: str,
    options: RunOptions,
    scenarios: list[Scenario],
    policies: list[str],
    seeds: list[int],
    budget_usd: float,
    profile: RunProfile,
    price: PriceEntry,
    all_scenarios: list[Scenario],
) -> RunManifest:
    now = datetime.now(UTC)
    config_payload = _configuration_payload(options, profile, scenarios, policies, price)
    pack_manifest = build_manifest(options.pack_path)
    lens_registry = {lens.id: lens for lens in load_lenses()}
    lens_versions = {}
    for policy_id in policies:
        policy = load_named_config("policies", policy_id)
        lens_id = policy.get("lens_id")
        if lens_id:
            lens_versions[lens_id] = lens_registry[lens_id].version
    return RunManifest(
        run_id=run_id,
        status="running",
        created_at=now,
        updated_at=now,
        profile=options.profile,
        model=options.model,
        judge_models=options.judge_models,
        policies=policies,
        seeds=seeds,
        scenario_pack_hash=pack_manifest.content_hash,
        scenario_pack_id=(
            _opaque_identifier("private-pack", pack_manifest.pack_id)
            if pack_manifest.disclosure == "private"
            else pack_manifest.pack_id
        ),
        scenario_pack_canonical=pack_manifest.canonical,
        scenario_pack_disclosure=pack_manifest.disclosure,
        benchmark_exposure=options.benchmark_exposure,
        benchmark_specific_tuning=options.benchmark_specific_tuning,
        lens_versions=lens_versions,
        config_hash=content_hash(config_payload),
        run_family_hash=content_hash(
            _configuration_payload(options, profile, all_scenarios, policies, price)
        ),
        git_commit=_git_commit(),
        package_version=__version__,
        python_version=sys.version.split()[0],
        operating_system=f"{platform.system()} {platform.release()}",
        budget_usd=budget_usd,
        hard_stop=options.hard_stop,
        reserve_fraction=options.reserve_fraction,
        expected_sample_count=len(scenarios) * len(policies) * len(seeds),
        shard_index=options.shard_index,
        shards=options.shards,
        redacted_environment={
            "CI": os.environ.get("CI", "false"),
            "HFB_HOME_set": str(bool(os.environ.get("HFB_HOME"))).lower(),
            "provider_key_present": str(
                any(key.endswith("_API_KEY") and value for key, value in os.environ.items())
            ).lower(),
        },
    )


def _opaque_identifier(kind: str, value: str) -> str:
    digest = content_hash(value).removeprefix("sha256:")
    return f"{kind}-{digest[:16]}"


def _persisted_trajectory_id(
    scenario_id: str, policy_id: str, seed: int, *, private_pack: bool
) -> str:
    raw = f"{scenario_id}--{policy_id}--{seed}"
    return _opaque_identifier("private-sample", raw) if private_pack else raw


def _trajectory_digest(trajectory: Trajectory) -> str:
    return content_hash(trajectory.model_dump(mode="json"))


def _verify_trajectory_ledger(store: RunStore, manifest: RunManifest) -> set[str]:
    """Stream persisted records and fail closed on deletion, duplication, or modification."""

    seen: set[str] = set()
    for trajectory in store.iter_trajectories():
        if trajectory.id in seen:
            raise ValueError(f"duplicate persisted trajectory ID: {trajectory.id}")
        seen.add(trajectory.id)
        if manifest.trajectory_hashes.get(trajectory.id) != _trajectory_digest(trajectory):
            raise ValueError(f"trajectory content hash mismatch: {trajectory.id}")
    if seen != set(manifest.completed_sample_ids):
        raise ValueError("completed sample ledger does not match persisted trajectory IDs")
    if seen != set(manifest.trajectory_hashes):
        raise ValueError("trajectory hash ledger does not match persisted trajectory IDs")
    return seen


def _persistence_safe(trajectory: Trajectory, *, private_pack: bool) -> Trajectory:
    """Redact persistence while preserving in-memory scoring semantics."""

    messages = [
        message.model_copy(
            update={
                "content": (
                    f"[{message.role} content withheld for private pack]"
                    if private_pack
                    else redact(message.content)
                )
            }
        )
        for message in trajectory.messages
    ]
    results = [
        result.model_copy(
            update={
                "evidence": [
                    EvidenceSpan(message_index=span.message_index, quote=redact(span.quote))
                    for span in result.evidence
                ],
                "rationale": redact(result.rationale),
            }
        )
        for result in trajectory.judge_results
    ]
    scenario_id = (
        _opaque_identifier("private-scenario", trajectory.scenario_id)
        if private_pack
        else trajectory.scenario_id
    )
    trajectory_id = (
        _opaque_identifier("private-sample", trajectory.id) if private_pack else trajectory.id
    )
    gate_hits = []
    for hit in trajectory.gate_hits:
        gate_hits.append(
            hit.model_copy(
                update={
                    "trajectory_id": trajectory_id,
                    "scenario_id": scenario_id,
                    "quote": (
                        "[evidence withheld for private pack]"
                        if private_pack
                        else redact(hit.quote)
                    ),
                }
            )
        )
    return trajectory.model_copy(
        update={
            "id": trajectory_id,
            "scenario_id": scenario_id,
            "messages": messages,
            "judge_results": results,
            "gate_hits": gate_hits,
        }
    )


class _Pacer:
    def __init__(self, rpm: int, tpm: int) -> None:
        self.request_interval = 60 / rpm
        self.tpm = tpm
        self.last = 0.0
        self.lock = asyncio.Lock()

    async def wait(self, estimated_tokens: int) -> None:
        async with self.lock:
            loop = asyncio.get_running_loop()
            interval = max(self.request_interval, 60 * estimated_tokens / self.tpm)
            delay = self.last + interval - loop.time()
            if delay > 0:
                await asyncio.sleep(delay)
            self.last = loop.time()


async def _trajectory(
    scenario: Scenario,
    policy_id: str,
    seed: int,
    *,
    provider: Provider,
    price: PriceEntry,
    turns: int,
    max_input_tokens: int,
    max_output_tokens: int,
    budget: BudgetGuard,
    cache: ContentCache,
    pacer: _Pacer,
) -> Trajectory:
    policy = load_named_config("policies", policy_id)
    messages = [
        Message(role="system", content=policy["system_prompt"]),
        Message(role="user", content=scenario.user_opening),
    ]
    initial_state = UserState()
    state = initial_state
    all_results = []
    gate_hits: list[GateHit] = []
    total_cost = 0.0
    total_latency = 0.0
    for turn in range(turns):
        cache_payload = {
            "model": provider.model_id,
            "policy": policy_id,
            "seed": seed + turn,
            "messages": [
                {"role": message.role, "content": message.content} for message in messages
            ],
            "max_output_tokens": max_output_tokens,
        }
        key = cache.key(cache_payload)
        response = cache.get(key)
        conservative_input_tokens = sum(len(message.content) for message in messages) // 3 + 1
        if conservative_input_tokens > max_input_tokens:
            raise ValueError(
                "estimated input exceeds the profile's declared maximum; "
                "reduce the trajectory horizon or select a larger profile"
            )
        high_estimate = token_cost(
            max_input_tokens,
            max_output_tokens,
            input_per_million_usd=price.input_per_million_usd,
            output_per_million_usd=price.output_per_million_usd,
        )
        if response is None:
            await budget.reserve(high_estimate)
            try:
                estimated_tokens = (
                    sum(len(message.content) for message in messages) // 3 + max_output_tokens
                )
                await pacer.wait(estimated_tokens)
                response = await provider.generate(
                    messages,
                    policy_id=policy_id,
                    seed=seed + turn,
                    max_output_tokens=max_output_tokens,
                )
                await budget.settle(high_estimate, response.cost_usd)
            except BaseException:
                await budget.release(high_estimate)
                raise
            cache.put(key, response)
        messages.append(Message(role="assistant", content=response.text))
        trajectory_id = f"{scenario.id}--{policy_id}--{seed}"
        gate_hits.extend(
            GateHit(
                policy_id=policy_id,
                trajectory_id=trajectory_id,
                scenario_id=scenario.id,
                message_index=len(messages) - 1,
                gate=gate,
                quote=quote,
            )
            for gate, quote in failure_gate_matches(response.text)
        )
        results = deterministic_score(
            response.text,
            scenario.dimensions,
            message_index=len(messages) - 1,
        )
        all_results.extend(results)
        state = transition(state, results)
        total_cost += response.cost_usd
        total_latency += response.latency_ms
        if turn + 1 < turns:
            follow_up = (
                scenario.follow_ups[turn % len(scenario.follow_ups)]
                if scenario.follow_ups
                else "What should I do next?"
            )
            messages.append(Message(role="user", content=follow_up))
    return Trajectory(
        id=trajectory_id,
        scenario_id=scenario.id,
        policy_id=policy_id,
        model_id=provider.model_id,
        seed=seed,
        messages=messages,
        initial_state=initial_state,
        final_state=state,
        judge_results=all_results,
        failure_gates=detect_failure_gates(
            message.content for message in messages if message.role == "assistant"
        ),
        gate_hits=gate_hits,
        cost_usd=total_cost,
        latency_ms=total_latency,
    )


async def run_benchmark(options: RunOptions, *, resume_dir: Path | None = None) -> Path:
    profile = load_profile(options.profile)
    unsupported_judges = [judge for judge in options.judge_models if judge != "deterministic-v1"]
    if unsupported_judges:
        raise ValueError(
            "configured model judges are not executable in this alpha; "
            "provide --judge deterministic-v1 for an explicitly pre-validation run. "
            f"Unavailable: {', '.join(unsupported_judges)}"
        )
    all_scenarios = _select_scenarios(options, profile.scenario_limit, apply_shard=False)
    scenarios = _select_scenarios(options, profile.scenario_limit)
    if not scenarios:
        raise ValueError("scenario filters selected no scenarios")
    policies = options.policies or profile.policies
    budget_usd = options.budget_usd or profile.default_budget_usd
    if budget_usd is None:
        raise ValueError(f"profile {profile.id} requires an explicit budget")
    if profile.requires_explicit_budget and options.budget_usd is None:
        raise ValueError(f"profile {profile.id} requires --budget-usd")
    provider, price = _provider(options)
    run_id = (
        resume_dir.name
        if resume_dir
        else f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}"
    )
    run_dir = resume_dir.resolve() if resume_dir else (options.output_root / run_id).resolve()
    store = RunStore(run_dir)
    if resume_dir:
        manifest = store.load_manifest()
        completed = _verify_trajectory_ledger(store, manifest)
        if manifest.status == "completed":
            return run_dir
        if manifest.model != options.model or manifest.profile != options.profile:
            raise ValueError("resume options do not match the original run")
    else:
        manifest = _manifest(
            run_id,
            options,
            scenarios,
            policies,
            profile.seeds,
            budget_usd,
            profile,
            price,
            all_scenarios,
        )
        resolved_payload = _configuration_payload(options, profile, scenarios, policies, price)
        persisted_payload = dict(resolved_payload)
        if manifest.scenario_pack_disclosure == "private":
            persisted_payload["scenarios"] = {
                "ids": [
                    _opaque_identifier("private-scenario", scenario.id) for scenario in scenarios
                ],
                "count": len(scenarios),
                "content_hash": manifest.scenario_pack_hash,
                "text_withheld": True,
            }
        store.create(
            manifest,
            {
                **persisted_payload,
                "scenario_ids": (
                    [_opaque_identifier("private-scenario", scenario.id) for scenario in scenarios]
                    if manifest.scenario_pack_disclosure == "private"
                    else [scenario.id for scenario in scenarios]
                ),
                "pack_path": (
                    "[private pack path withheld]"
                    if manifest.scenario_pack_disclosure == "private"
                    else str(options.pack_path)
                    if options.pack_path
                    else None
                ),
            },
        )
        completed = set()
    current_config_hash = content_hash(
        _configuration_payload(options, profile, scenarios, policies, price)
    )
    if current_config_hash != manifest.config_hash:
        raise ValueError(
            "resume input hash mismatch: profile, pack, policy, rubric, judge, or price changed"
        )
    private_pack = manifest.scenario_pack_disclosure == "private"
    cache_root = options.cache_root or user_cache_path("hfb") / "responses"
    cache = ContentCache(cache_root, enabled=not private_pack)
    guard = BudgetGuard(budget_usd, options.reserve_fraction)
    guard.spent = manifest.spent_usd
    pacer = _Pacer(
        profile.rpm if not options.model.startswith("fake/") else 1_000_000,
        profile.tpm if not options.model.startswith("fake/") else 1_000_000_000,
    )
    semaphore = asyncio.Semaphore(profile.concurrency)
    queue: asyncio.Queue[tuple[Scenario, str, int] | None] = asyncio.Queue(
        maxsize=max(1, profile.concurrency * 2)
    )

    async def execute(scenario: Scenario, policy_id: str, seed: int) -> None:
        nonlocal manifest
        async with semaphore:
            trajectory_id = _persisted_trajectory_id(
                scenario.id, policy_id, seed, private_pack=private_pack
            )
            try:
                trajectory = await _trajectory(
                    scenario,
                    policy_id,
                    seed,
                    provider=provider,
                    price=price,
                    turns=min(
                        profile.trajectory_turns,
                        TURN_LIMITS[scenario.trajectory_length.value] or profile.trajectory_turns,
                    ),
                    max_input_tokens=profile.max_input_tokens,
                    max_output_tokens=profile.max_output_tokens,
                    budget=guard,
                    cache=cache,
                    pacer=pacer,
                )
                safe_trajectory = _persistence_safe(
                    trajectory,
                    private_pack=manifest.scenario_pack_disclosure == "private",
                )
                await store.append(safe_trajectory)
                manifest.completed_sample_ids.append(safe_trajectory.id)
                manifest.trajectory_hashes[safe_trajectory.id] = _trajectory_digest(safe_trajectory)
            except BudgetExceeded as error:
                manifest.status = "budget_exhausted"
                manifest.errors.append(str(error))
            except Exception as error:
                manifest.failed_sample_ids.append(trajectory_id)
                manifest.errors.append(redact(f"{trajectory_id}: {type(error).__name__}: {error}"))
            manifest.spent_usd = guard.spent
            manifest.updated_at = datetime.now(UTC)
            store.update_manifest(manifest)

    async def produce() -> None:
        for scenario in scenarios:
            for policy_id in policies:
                for seed in profile.seeds:
                    trajectory_id = _persisted_trajectory_id(
                        scenario.id, policy_id, seed, private_pack=private_pack
                    )
                    if trajectory_id not in completed:
                        await queue.put((scenario, policy_id, seed))
        for _ in range(profile.concurrency):
            await queue.put(None)

    async def consume() -> None:
        while True:
            item = await queue.get()
            try:
                if item is None:
                    return
                await execute(*item)
            finally:
                queue.task_done()

    try:
        producer = asyncio.create_task(produce())
        workers = [asyncio.create_task(consume()) for _ in range(profile.concurrency)]
        await asyncio.gather(producer, *workers)
    except (KeyboardInterrupt, asyncio.CancelledError):
        manifest.status = "interrupted"
        manifest.updated_at = datetime.now(UTC)
        store.update_manifest(manifest)
        raise
    if manifest.status != "budget_exhausted":
        manifest.status = "completed" if not manifest.failed_sample_ids else "failed"
    manifest.spent_usd = guard.spent
    manifest.updated_at = datetime.now(UTC)
    store.update_manifest(manifest)
    report = aggregate(
        store.iter_trajectories(),
        assurance=profile.assurance,
        configured_judges=options.judge_models,
        target_model=options.model,
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
    render_reports(run_dir, manifest, report, store.iter_trajectories())
    store.export_columnar(store.iter_trajectories())
    protect_artifact_tree(run_dir)
    return run_dir


def merge_shards(output_dir: Path, shard_dirs: list[Path]) -> Path:
    manifests = []
    trajectory_ids: set[str] = set()
    trajectory_hashes: dict[str, str] = {}
    for shard_dir in shard_dirs:
        shard_store = RunStore(shard_dir)
        manifest = shard_store.load_manifest()
        manifests.append(manifest)
        shard_trajectory_ids = _verify_trajectory_ledger(shard_store, manifest)
        if len(shard_trajectory_ids) != manifest.expected_sample_count:
            raise ValueError(
                "completed shard result count does not match its expected sample count"
            )
        if manifest.failed_sample_ids:
            raise ValueError("completed shard contains failed sample IDs")
        duplicates = trajectory_ids.intersection(shard_trajectory_ids)
        if duplicates:
            raise ValueError(f"duplicate trajectory across shards: {sorted(duplicates)[0]}")
        trajectory_ids.update(shard_trajectory_ids)
        trajectory_hashes.update(manifest.trajectory_hashes)
    base = manifests[0]
    if len(manifests) != base.shards:
        raise ValueError(f"expected {base.shards} shards, received {len(manifests)}")
    indices = [manifest.shard_index for manifest in manifests]
    if sorted(indices) != list(range(base.shards)):
        raise ValueError("shard indices must be the complete unique range 0..shards-1")
    if any(manifest.status != "completed" for manifest in manifests):
        raise ValueError("all shards must be completed before merge")
    if any(manifest.run_family_hash != base.run_family_hash for manifest in manifests[1:]):
        raise ValueError("shards have different run-family configurations")
    provenance_fields = (
        "git_commit",
        "package_version",
        "scenario_pack_hash",
        "model",
        "profile",
        "scenario_pack_id",
        "scenario_pack_disclosure",
    )
    if any(
        getattr(manifest, field) != getattr(base, field)
        for manifest in manifests[1:]
        for field in provenance_fields
    ):
        raise ValueError("shards have incompatible provenance")
    merged = base.model_copy(
        update={
            "run_id": output_dir.name,
            "status": "completed",
            "shard_index": 0,
            "shards": base.shards,
            "spent_usd": sum(manifest.spent_usd for manifest in manifests),
            "expected_sample_count": sum(manifest.expected_sample_count for manifest in manifests),
            "completed_sample_ids": sorted(trajectory_ids),
            "trajectory_hashes": trajectory_hashes,
            "updated_at": datetime.now(UTC),
        }
    )
    store = RunStore(output_dir)
    store.create(
        merged,
        {
            "merged_from": (
                [_opaque_identifier("private-shard", str(path.resolve())) for path in shard_dirs]
                if merged.scenario_pack_disclosure == "private"
                else [str(path) for path in shard_dirs]
            )
        },
    )
    with store.results_path.open("w", encoding="utf-8") as output:
        for shard_dir in shard_dirs:
            for trajectory in RunStore(shard_dir).iter_trajectories():
                output.write(trajectory.model_dump_json() + "\n")
    report = aggregate(
        store.iter_trajectories(),
        assurance="research",
        configured_judges=merged.judge_models,
        target_model=merged.model,
    )
    render_reports(output_dir, merged, report, store.iter_trajectories())
    store.export_columnar(store.iter_trajectories())
    protect_artifact_tree(output_dir)
    return output_dir
