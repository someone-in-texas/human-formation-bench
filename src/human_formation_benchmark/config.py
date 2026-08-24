"""Configuration and public benchmark asset loading."""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel

from .extensions.models import ResolvedExtension
from .models import (
    AdversarialChallenge,
    Constitution,
    PerspectiveContrast,
    Policy,
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


def _extension_items(
    extension: ResolvedExtension | None,
    attribute: str,
    payload_key: str,
) -> list[dict[str, Any]]:
    if extension is None:
        return []
    items: list[dict[str, Any]] = []
    for path in getattr(extension, attribute):
        payload = load_yaml(path)
        if not isinstance(payload, Mapping) or not isinstance(payload.get(payload_key), list):
            raise ValueError(f"{path} must contain a {payload_key!r} list")
        items.extend(payload[payload_key])
    return items


def load_profile(
    name: str,
    *,
    root: Path | None = None,
    extension: ResolvedExtension | None = None,
) -> RunProfile:
    base = root or resource_root()
    matches: list[RunProfile] = []
    for path in extension.profile_files if extension else []:
        payload = load_yaml(path)
        if isinstance(payload, Mapping) and isinstance(payload.get("profiles"), list):
            matches.extend(
                RunProfile.model_validate(item)
                for item in payload["profiles"]
                if item.get("id") == name
            )
        elif isinstance(payload, Mapping) and payload.get("id") == name:
            matches.append(RunProfile.model_validate(payload))
    core_path = safe_child_path(base, Path("configs/profiles") / f"{name}.yaml")
    if core_path.is_file():
        matches.append(RunProfile.model_validate(load_yaml(core_path)))
    if not matches:
        raise KeyError(f"unknown profile: {name}")
    if len(matches) > 1:
        raise ValueError(f"duplicate profile ID across core and extension assets: {name}")
    return matches[0]


def list_profiles(
    *,
    root: Path | None = None,
    extension: ResolvedExtension | None = None,
) -> list[RunProfile]:
    base = root or resource_root()
    profile_dir = safe_child_path(base, "configs/profiles")
    profiles = [
        RunProfile.model_validate(load_yaml(path)) for path in sorted(profile_dir.glob("*.yaml"))
    ]
    for path in extension.profile_files if extension else []:
        payload = load_yaml(path)
        if isinstance(payload, Mapping) and isinstance(payload.get("profiles"), list):
            profiles.extend(_load_models(payload["profiles"], RunProfile))
        else:
            profiles.append(RunProfile.model_validate(payload))
    ids = [profile.id for profile in profiles]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate profile ID across core and extension assets")
    return profiles


def load_scenarios(
    *,
    root: Path | None = None,
    pack_path: Path | None = None,
    extension: ResolvedExtension | None = None,
) -> list[Scenario]:
    if pack_path is not None:
        payload = load_yaml(pack_path.resolve())
        return _load_models(payload["scenarios"], Scenario)
    if extension is not None and extension.scenario_files:
        return _load_models(
            _extension_items(extension, "scenario_files", "scenarios"),
            Scenario,
        )
    base = root or resource_root()
    payload = load_yaml(safe_child_path(base, "data/public_core/scenarios.yaml"))
    return _load_models(payload["scenarios"], Scenario)


def load_rubrics(
    *,
    root: Path | None = None,
    extension: ResolvedExtension | None = None,
) -> list[Rubric]:
    base = root or resource_root()
    payload = load_yaml(safe_child_path(base, "rubrics/core.yaml"))
    rubrics = _load_models(payload["rubrics"], Rubric)
    rubrics.extend(_load_models(_extension_items(extension, "rubric_files", "rubrics"), Rubric))
    ids = [rubric.id for rubric in rubrics]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate rubric ID across core and extension assets")
    return rubrics


def load_prices(*, root: Path | None = None) -> list[PriceEntry]:
    base = root or resource_root()
    payload = load_yaml(safe_child_path(base, "configs/prices.yaml"))
    return _load_models(payload["prices"], PriceEntry)


def load_named_config(
    kind: str,
    name: str,
    *,
    root: Path | None = None,
    extension: ResolvedExtension | None = None,
) -> dict[str, Any]:
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
    matches = [dict(item) for item in payload[kind] if item["id"] == name]
    if extension is not None and kind == "policies":
        matches.extend(
            dict(item)
            for item in _extension_items(extension, "policy_files", "policies")
            if item.get("id") == name
        )
    if len(matches) > 1:
        raise ValueError(f"duplicate {kind[:-1]} ID across core and extension assets: {name}")
    if matches:
        if kind == "policies":
            Policy.model_validate(matches[0])
        return matches[0]
    raise KeyError(f"unknown {kind[:-1]}: {name}")


def load_constitutions(*, root: Path | None = None) -> list[Constitution]:
    base = root or resource_root()
    payload = load_yaml(safe_child_path(base, "configs/constitutions/constitutions.yaml"))
    return _load_models(payload["constitutions"], Constitution)


def load_policies(*, root: Path | None = None) -> list[Policy]:
    base = root or resource_root()
    payload = load_yaml(safe_child_path(base, "configs/policies/policies.yaml"))
    return _load_models(payload["policies"], Policy)


def load_lenses(*, root: Path | None = None) -> list[WorldviewLens]:
    base = root or resource_root()
    payload = load_yaml(safe_child_path(base, "configs/lenses/lenses.yaml"))
    return _load_models(payload["lenses"], WorldviewLens)


def required_perspectives(*, root: Path | None = None) -> set[str]:
    """Load the data-declared baseline perspectives for core validity fixtures."""

    base = root or resource_root()
    payload = load_yaml(safe_child_path(base, "configs/lenses/lenses.yaml"))
    values = payload.get("required_perspectives")
    if (
        not isinstance(values, list)
        or not values
        or any(not isinstance(item, str) for item in values)
    ):
        raise ValueError("lens registry must declare required_perspectives")
    if len(values) != len(set(values)):
        raise ValueError("required_perspectives must be unique")
    return set(values)


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
    required = required_perspectives(root=base)
    if {lens.perspective for lens in lenses} != required:
        raise ValueError("lens registry does not cover every required perspective")
    for lens in lenses:
        if lens.validation_status == "author_draft":
            raise ValueError(f"production lens remains an author draft: {lens.id}")
        if any("required" in reviewer for reviewer in lens.reviewer_provenance):
            raise ValueError(f"production lens has placeholder reviewer provenance: {lens.id}")
    linked_lenses = {
        policy.lens_id for policy in load_policies(root=base) if policy.production_safe
    }
    missing_links = {lens.id for lens in lenses} - linked_lenses
    if missing_links:
        raise ValueError(f"lenses lack executable production policies: {sorted(missing_links)}")
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
    from .scoring import detect_failure_gates, deterministic_score

    contrasts = load_perspective_contrasts(root=root)
    required = required_perspectives(root=root)
    observed = {(item.perspective, item.role) for item in contrasts}
    missing = {
        (perspective, role)
        for perspective in required
        for role in ("positive", "adversarial")
        if (perspective, role) not in observed
    }
    if missing:
        raise ValueError(f"perspective contrast coverage missing: {sorted(missing)}")
    for contrast in contrasts:
        if contrast.reviewer_status != "independent_reviewed":
            raise ValueError(f"perspective contrast remains an author draft: {contrast.id}")
        results = deterministic_score(
            contrast.exemplar_response, contrast.dimensions, message_index=0
        )
        gates = detect_failure_gates([contrast.exemplar_response])
        if contrast.role == "positive" and any(gates.model_dump().values()):
            raise ValueError(f"positive perspective fixture triggers a hard gate: {contrast.id}")
        if set(contrast.reviewed_scores) != set(contrast.dimensions):
            raise ValueError(f"reviewed scores do not cover fixture dimensions: {contrast.id}")
        if contrast.role == "positive" and min(contrast.reviewed_scores.values()) < 3:
            raise ValueError(f"positive reviewed contrast falls below supportive: {contrast.id}")
        if contrast.role == "adversarial" and max(contrast.reviewed_scores.values()) > 1:
            raise ValueError(
                f"adversarial reviewed contrast exceeds substantial-failure: {contrast.id}"
            )
        if not results or any(result.score is not None for result in results):
            raise ValueError("public lexical detector must not replace reviewed contrast judgments")
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
