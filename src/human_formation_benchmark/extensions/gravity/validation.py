"""Cross-file validation for the built-in Gravity extension."""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from human_formation_benchmark.models import Policy, RunProfile, Scenario
from human_formation_benchmark.security import validate_untrusted_text

from .controls import GRAVITY_POLICIES
from .models import (
    GravityReportArtifact,
    GravityRubric,
    GravityScenario,
    GravityTransferResult,
    GravityUserState,
    SignalReport,
)
from .resources import load_config, load_manifest, load_profiles, load_rubrics, load_scenarios

_SCHEMA_MODELS: dict[str, type[BaseModel]] = {
    "gravity-report": GravityReportArtifact,
    "rubric": GravityRubric,
    "scenario": GravityScenario,
    "signal-report": SignalReport,
    "transfer-result": GravityTransferResult,
    "user-state": GravityUserState,
}


def _validate_schema_parity() -> int:
    schema_root = files("human_formation_benchmark.extensions.gravity.schemas")
    for name, model in _SCHEMA_MODELS.items():
        path = schema_root.joinpath(f"{name}.schema.json")
        actual = json.loads(path.read_text(encoding="utf-8"))
        expected = model.model_json_schema()
        expected["$id"] = (
            "https://raw.githubusercontent.com/someone-in-texas/"
            f"human-formation-bench/main/schemas/v1.1/extensions/gravity/{name}.schema.json"
        )
        expected["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        if actual != expected:
            raise ValueError(f"packaged Gravity JSON Schema drift: {name}")
    return len(_SCHEMA_MODELS)


def _runner_models(
    root: Path,
    filename: str,
    key: str,
    model: type[Policy] | type[RunProfile] | type[Scenario],
) -> list[Any]:
    path = root / filename
    text = path.read_text(encoding="utf-8")
    validate_untrusted_text(text)
    payload = yaml.safe_load(text)
    if not isinstance(payload, dict) or not isinstance(payload.get(key), list):
        raise ValueError(f"invalid Gravity asset {filename}: expected {key} list")
    return [model.model_validate(item) for item in payload[key]]


def validate_assets(root: Path) -> dict[str, int]:
    """Parse every semantic asset and enforce rich/runner adapter equivalence."""

    manifest = load_manifest(root=root)
    config = load_config(root=root)
    scenarios = load_scenarios(root=root)
    rubrics = load_rubrics(root=root)
    profiles = load_profiles(root=root)
    runner_scenarios = _runner_models(root, "runner_scenarios.yaml", "scenarios", Scenario)
    runner_profiles = _runner_models(root, "runner_profiles.yaml", "profiles", RunProfile)
    runner_policies = _runner_models(root, "runner_policies.yaml", "policies", Policy)

    if manifest.version != config.module_version:
        raise ValueError("Gravity manifest and configuration module versions differ")

    rich_scenarios = {item.id: item for item in scenarios}
    adapted_scenarios = {item.id: item for item in runner_scenarios}
    if set(rich_scenarios) != set(adapted_scenarios):
        raise ValueError("Gravity rich and runner scenario IDs differ")
    for scenario_id, rich in rich_scenarios.items():
        adapted = adapted_scenarios[scenario_id]
        comparable = ("title", "domain", "stakes", "user_opening")
        if any(getattr(rich, field) != getattr(adapted, field) for field in comparable):
            raise ValueError(f"Gravity runner scenario projection drift: {scenario_id}")

    rich_profiles = {item.id: item for item in profiles}
    adapted_profiles = {item.id: item for item in runner_profiles}
    if set(rich_profiles) != set(adapted_profiles):
        raise ValueError("Gravity rich and runner profile IDs differ")
    for profile_id, rich_profile in rich_profiles.items():
        adapted = adapted_profiles[profile_id]
        if (
            rich_profile.scenario_limit != adapted.scenario_limit
            or rich_profile.seeds != adapted.seeds
            or rich_profile.trajectory_turns != adapted.trajectory_turns
            or rich_profile.requires_explicit_budget != adapted.requires_explicit_budget
        ):
            raise ValueError(f"Gravity runner profile projection drift: {profile_id}")

    typed_policies = {item.id: item for item in GRAVITY_POLICIES}
    adapted_policies = {item.id: item for item in runner_policies}
    if set(typed_policies) != set(adapted_policies):
        raise ValueError("Gravity typed and runner policy IDs differ")
    for policy_id, typed in typed_policies.items():
        adapted = adapted_policies[policy_id]
        if (
            typed.production_safe != adapted.production_safe
            or typed.research_control != adapted.research_control
        ):
            raise ValueError(f"Gravity runner policy projection drift: {policy_id}")

    constructs = {rubric.gravity_construct for rubric in rubrics}
    targeted = {
        construct for scenario in scenarios for construct in scenario.gravity.target_constructs
    }
    if constructs != targeted:
        raise ValueError("Gravity rubric and scenario construct coverage differ")

    controls = sum(item.research_control for item in runner_policies)
    return {
        "scenarios": len(scenarios),
        "rubrics": len(rubrics),
        "profiles": len(profiles),
        "policies": len(runner_policies),
        "controls": controls,
        "schemas": _validate_schema_parity(),
    }
