"""Contained loaders for declarative Gravity extension assets."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel

from human_formation_benchmark.security import validate_untrusted_text

from .models import GravityProfile, GravityRubric, GravityScenario

ModelT = TypeVar("ModelT", bound=BaseModel)


def resource_directory() -> Path:
    """Return the installed package resource directory."""

    return Path(str(files(__package__).joinpath("resources")))


def _load_yaml(name: str) -> Any:
    allowed = {"scenarios.yaml", "rubrics.yaml", "profiles.yaml"}
    if name not in allowed:
        raise ValueError(f"unknown Gravity resource: {name}")
    path = resource_directory() / name
    text = path.read_text(encoding="utf-8")
    validate_untrusted_text(text)
    return yaml.safe_load(text)


def _models(name: str, key: str, model: type[ModelT]) -> list[ModelT]:
    payload = _load_yaml(name)
    if not isinstance(payload, dict) or not isinstance(payload.get(key), list):
        raise ValueError(f"invalid Gravity {key} resource")
    return [model.model_validate(item) for item in payload[key]]


def load_scenarios() -> list[GravityScenario]:
    return _models("scenarios.yaml", "scenarios", GravityScenario)


def load_rubrics() -> list[GravityRubric]:
    return _models("rubrics.yaml", "rubrics", GravityRubric)


def load_profiles() -> list[GravityProfile]:
    return _models("profiles.yaml", "profiles", GravityProfile)
