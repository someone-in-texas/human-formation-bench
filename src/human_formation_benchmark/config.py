"""Configuration and public benchmark asset loading."""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel

from .models import PriceEntry, Rubric, RunProfile, Scenario
from .security import safe_child_path, validate_untrusted_text

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


def load_scenarios(*, root: Path | None = None) -> list[Scenario]:
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
