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
from .config import load_named_config, load_profile, load_scenarios
from .hashing import content_hash
from .models import Message, PriceEntry, RunManifest, Scenario, Trajectory, UserState
from .pricing import BudgetExceeded, BudgetGuard, token_cost
from .providers import FakeProvider, InspectProvider, Provider
from .reporting import render_reports
from .scoring import aggregate, deterministic_score
from .simulation import transition
from .storage import ContentCache, RunStore


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


def _select_scenarios(options: RunOptions, profile_limit: int) -> list[Scenario]:
    scenarios = load_scenarios()
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


def _manifest(
    run_id: str,
    options: RunOptions,
    scenarios: list[Scenario],
    policies: list[str],
    seeds: list[int],
    budget_usd: float,
) -> RunManifest:
    now = datetime.now(UTC)
    hash_options = {
        key: value
        for key, value in options.__dict__.items()
        if key not in {"shard_index", "output_root", "cache_root"}
    }
    config_payload = {
        "options": {
            **hash_options,
            "dimensions": sorted(options.dimensions),
            "domains": sorted(options.domains),
        },
        "policies": policies,
        "seeds": seeds,
    }
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
        scenario_pack_hash=content_hash(
            [scenario.model_dump(mode="json") for scenario in scenarios]
        ),
        config_hash=content_hash(config_payload),
        git_commit=_git_commit(),
        package_version=__version__,
        python_version=sys.version.split()[0],
        operating_system=f"{platform.system()} {platform.release()}",
        budget_usd=budget_usd,
        hard_stop=options.hard_stop,
        reserve_fraction=options.reserve_fraction,
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


class _Pacer:
    def __init__(self, rpm: int) -> None:
        self.interval = 60 / rpm
        self.last = 0.0
        self.lock = asyncio.Lock()

    async def wait(self) -> None:
        async with self.lock:
            loop = asyncio.get_running_loop()
            delay = self.last + self.interval - loop.time()
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
        high_estimate = (
            token_cost(
                sum(len(message.content) for message in messages) // 3,
                max_output_tokens,
                input_per_million_usd=price.input_per_million_usd,
                output_per_million_usd=price.output_per_million_usd,
            )
            * 1.5
        )
        if response is None:
            await budget.reserve(high_estimate)
            try:
                await pacer.wait()
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
    trajectory_id = f"{scenario.id}--{policy_id}--{seed}"
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
        cost_usd=total_cost,
        latency_ms=total_latency,
    )


async def run_benchmark(options: RunOptions, *, resume_dir: Path | None = None) -> Path:
    profile = load_profile(options.profile)
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
        )
        store.create(
            manifest,
            {
                "profile": profile.model_dump(mode="json"),
                "options": {
                    **options.__dict__,
                    "output_root": str(options.output_root),
                    "cache_root": str(options.cache_root) if options.cache_root else None,
                    "dimensions": sorted(options.dimensions),
                    "domains": sorted(options.domains),
                },
                "scenarios": [scenario.id for scenario in scenarios],
                "price": price.model_dump(mode="json"),
            },
        )
    completed = set(manifest.completed_sample_ids)
    existing = {trajectory.id: trajectory for trajectory in store.trajectories()}
    completed.update(existing)
    cache_root = options.cache_root or user_cache_path("hfb") / "responses"
    cache = ContentCache(cache_root)
    guard = BudgetGuard(budget_usd, options.reserve_fraction)
    guard.spent = manifest.spent_usd
    pacer = _Pacer(profile.rpm if not options.model.startswith("fake/") else 1_000_000)
    semaphore = asyncio.Semaphore(profile.concurrency)
    work = [
        (scenario, policy_id, seed)
        for scenario in scenarios
        for policy_id in policies
        for seed in profile.seeds
        if f"{scenario.id}--{policy_id}--{seed}" not in completed
    ]

    async def execute(scenario: Scenario, policy_id: str, seed: int) -> None:
        nonlocal manifest
        async with semaphore:
            trajectory_id = f"{scenario.id}--{policy_id}--{seed}"
            try:
                trajectory = await _trajectory(
                    scenario,
                    policy_id,
                    seed,
                    provider=provider,
                    price=price,
                    turns=min(
                        profile.trajectory_turns,
                        1 if scenario.trajectory_length.value == "single_turn" else 3,
                    ),
                    max_output_tokens=profile.max_output_tokens,
                    budget=guard,
                    cache=cache,
                    pacer=pacer,
                )
                await store.append(trajectory)
                existing[trajectory.id] = trajectory
                manifest.completed_sample_ids.append(trajectory_id)
            except BudgetExceeded as error:
                manifest.status = "budget_exhausted"
                manifest.errors.append(str(error))
            except Exception as error:
                manifest.failed_sample_ids.append(trajectory_id)
                manifest.errors.append(f"{trajectory_id}: {type(error).__name__}: {error}")
            manifest.spent_usd = guard.spent
            manifest.updated_at = datetime.now(UTC)
            store.update_manifest(manifest)

    try:
        await asyncio.gather(*(execute(*item) for item in work))
    except (KeyboardInterrupt, asyncio.CancelledError):
        manifest.status = "interrupted"
        manifest.updated_at = datetime.now(UTC)
        store.update_manifest(manifest)
        raise
    trajectories = list(existing.values())
    if manifest.status != "budget_exhausted":
        manifest.status = "completed" if not manifest.failed_sample_ids else "failed"
    manifest.spent_usd = guard.spent
    manifest.updated_at = datetime.now(UTC)
    store.update_manifest(manifest)
    report = aggregate(trajectories, assurance=profile.assurance)
    render_reports(run_dir, manifest, report, trajectories)
    store.export_columnar(trajectories)
    return run_dir


def merge_shards(output_dir: Path, shard_dirs: list[Path]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=False)
    trajectories: dict[str, Trajectory] = {}
    manifests = []
    for shard_dir in shard_dirs:
        shard_store = RunStore(shard_dir)
        manifests.append(shard_store.load_manifest())
        for trajectory in shard_store.trajectories():
            if trajectory.id in trajectories:
                raise ValueError(f"duplicate trajectory across shards: {trajectory.id}")
            trajectories[trajectory.id] = trajectory
    base = manifests[0]
    if any(manifest.config_hash != base.config_hash for manifest in manifests[1:]):
        raise ValueError("shards have different resolved configurations")
    merged = base.model_copy(
        update={
            "run_id": output_dir.name,
            "status": "completed",
            "shard_index": 0,
            "shards": len(shard_dirs),
            "spent_usd": sum(manifest.spent_usd for manifest in manifests),
            "completed_sample_ids": sorted(trajectories),
            "updated_at": datetime.now(UTC),
        }
    )
    store = RunStore(output_dir)
    store.create(merged, {"merged_from": [str(path) for path in shard_dirs]})
    output_lines = "\n".join(item.model_dump_json() for item in trajectories.values())
    (output_dir / "results.jsonl").write_text(output_lines + "\n", encoding="utf-8")
    values = list(trajectories.values())
    report = aggregate(values, assurance="research")
    render_reports(output_dir, merged, report, values)
    store.export_columnar(values)
    return output_dir
