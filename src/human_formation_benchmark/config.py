"""Configuration and public benchmark asset loading."""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel

from .models import (
    AdversarialChallenge,
    Constitution,
    PerspectiveContrast,
    PriceEntry,
    Rubric,
    RunProfile,
    Scenario,
    WorldviewLens,
)
from .security import safe_child_path, validate_regular_file, validate_untrusted_text

ModelT = TypeVar("ModelT", bound=BaseModel)


def project_root(start: Path | None = None) -> Path | None:
    """Find a source checkout without assuming the current directory."""

    current = (start or Path.cwd()).resolve()
    for parent in (current, *current.parents):
        if (parent / "pyproject.toml").is_file() and (parent / "configs").is_dir():
            return parent
    return None


def resource_root() -> Path:
    """Resolve assets from an override, source checkout, or installed data files."""

    override = os.environ.get("HFB_HOME")
    if override:
        root = Path(override).expanduser().resolve()
        if not root.is_dir():
            raise ValueError("HFB_HOME does not point to a directory")
        return root
    checkout = project_root()
    if checkout:
        return checkout
    installed = Path(sys.prefix) / "share" / "human-formation-benchmark"
    if installed.is_dir():
        return installed
    raise FileNotFoundError("HFB benchmark assets not found; set HFB_HOME")


def load_yaml(path: Path) -> Any:
    """Safely load bounded YAML."""

    validate_regular_file(path)
    text = path.read_text(encoding="utf-8")
    validate_untrusted_text(text)
    return yaml.safe_load(text)


def deep_merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    """Merge nested mappings while replacing lists and scalar values."""

    merged: dict[str, Any] = dict(base)
    for key, value in override.items():
        existing = merged.get(key)
        if isinstance(existing, Mapping) and isinstance(value, Mapping):
            merged[key] = deep_merge(existing, value)
        else:
            merged[key] = value
    return merged


def _load_models(items: list[dict[str, Any]], model: type[ModelT]) -> list[ModelT]:
    return [model.model_validate(item) for item in items]


def load_profile(name: str, *, root: Path | None = None) -> RunProfile:
    base = root or resource_root()
    path = safe_child_path(base, Path("configs/profiles") / f"{name}.yaml")
    return RunProfile.model_validate(load_yaml(path))


def list_profiles(*, root: Path | None = None) -> list[RunProfile]:
    base = root or resource_root()
    profile_dir = safe_child_path(base, "configs/profiles")
    return [
        RunProfile.model_validate(load_yaml(path)) for path in sorted(profile_dir.glob("*.yaml"))
    ]


def load_scenarios(*, root: Path | None = None, pack_path: Path | None = None) -> list[Scenario]:
    if pack_path is not None:
        payload = load_yaml(pack_path.resolve())
        return _load_models(payload["scenarios"], Scenario)
    base = root or resource_root()
    payload = load_yaml(safe_child_path(base, "data/public_core/scenarios.yaml"))
    return _load_models(payload["scenarios"], Scenario)


def load_rubrics(*, root: Path | None = None) -> list[Rubric]:
    base = root or resource_root()
    payload = load_yaml(safe_child_path(base, "rubrics/core.yaml"))
    return _load_models(payload["rubrics"], Rubric)


def load_prices(*, root: Path | None = None) -> list[PriceEntry]:
    base = root or resource_root()
    payload = load_yaml(safe_child_path(base, "configs/prices.yaml"))
    return _load_models(payload["prices"], PriceEntry)


def load_named_config(kind: str, name: str, *, root: Path | None = None) -> dict[str, Any]:
    """Load a named policy, constitution, or judge configuration."""

    allowed = {
        "policies": "configs/policies/policies.yaml",
        "constitutions": "configs/constitutions/constitutions.yaml",
        "judges": "configs/judges/deterministic.yaml",
    }
    if kind not in allowed:
        raise ValueError(f"unsupported config kind: {kind}")
    base = root or resource_root()
    payload = load_yaml(safe_child_path(base, allowed[kind]))
    for item in payload[kind]:
        if item["id"] == name:
            return dict(item)
    raise KeyError(f"unknown {kind[:-1]}: {name}")


def load_constitutions(*, root: Path | None = None) -> list[Constitution]:
    base = root or resource_root()
    payload = load_yaml(safe_child_path(base, "configs/constitutions/constitutions.yaml"))
    return _load_models(payload["constitutions"], Constitution)


def load_lenses(*, root: Path | None = None) -> list[WorldviewLens]:
    base = root or resource_root()
    payload = load_yaml(safe_child_path(base, "configs/lenses/lenses.yaml"))
    return _load_models(payload["lenses"], WorldviewLens)


def validate_foundations(*, root: Path | None = None) -> tuple[int, int]:
    base = root or resource_root()
    shared = load_yaml(safe_child_path(base, "configs/foundations/thin_floor.yaml"))
    floor = set(shared["commitments"])
    constitutions = load_constitutions(root=base)
    for constitution in constitutions:
        if constitution.research_control:
            if constitution.thin_floor:
                raise ValueError("research control must remain outside the production thin floor")
            continue
        if constitution.thin_floor_version != shared["version"]:
            raise ValueError(f"{constitution.id} does not inherit the current thin-floor version")
        if set(constitution.thin_floor) != floor:
            raise ValueError(f"{constitution.id} has an unexplained thin-floor omission")
    lenses = load_lenses(root=base)
    required = {
        "christian",
        "secular_pluralist",
        "virtue_ethical",
        "care_ethical",
        "communal_duty",
        "individual_self_direction",
    }
    if {lens.perspective for lens in lenses} != required:
        raise ValueError("lens registry does not cover every required perspective")
    return len(constitutions), len(lenses)


def load_perspective_contrasts(*, root: Path | None = None) -> list[PerspectiveContrast]:
    base = root or resource_root()
    payload = load_yaml(safe_child_path(base, "data/public_core/perspective_contrasts.yaml"))
    return _load_models(payload["contrasts"], PerspectiveContrast)


def load_adversarial_challenges(*, root: Path | None = None) -> list[AdversarialChallenge]:
    base = root or resource_root()
    payload = load_yaml(safe_child_path(base, "data/challenges/public_red_team.yaml"))
    return _load_models(payload["challenges"], AdversarialChallenge)


def validate_challenge_coverage(*, root: Path | None = None) -> tuple[int, int]:
    contrasts = load_perspective_contrasts(root=root)
    required = {
        "christian",
        "secular_pluralist",
        "virtue_ethical",
        "care_ethical",
        "communal_duty",
        "individual_self_direction",
    }
    observed = {(item.perspective, item.role) for item in contrasts}
    missing = {
        (perspective, role)
        for perspective in required
        for role in ("positive", "adversarial")
        if (perspective, role) not in observed
    }
    if missing:
        raise ValueError(f"perspective contrast coverage missing: {sorted(missing)}")
    challenges = load_adversarial_challenges(root=root)
    attack_families = {item.attack_family for item in challenges}
    required_attacks = {
        "lexical_goodhart",
        "negation",
        "false_deference",
        "evaluator_prompt_injection",
        "evaluation_awareness",
        "prompt_injection_and_exfiltration",
    }
    if not required_attacks <= attack_families:
        raise ValueError("public red-team smoke set lacks required attack families")
    return len(contrasts), len(challenges)
