"""Strict declarative models for benchmark extensions."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator

from ..models import StrictModel


class ExtensionDescriptor(StrictModel):
    """Built-in extension metadata with an explicit asset allowlist."""

    schema_version: Literal["1.0"] = "1.0"
    id: str = Field(pattern=r"^[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*$")
    title: str = Field(min_length=3, max_length=200)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
    status: Literal["experimental", "stable", "deprecated"]
    canonical_composite: bool
    requires_longitudinal_support: bool
    research_controls_available: bool
    compatible_core_schema_versions: list[str] = Field(min_length=1)
    dependencies: list[str] = Field(default_factory=list)
    scenario_files: list[str] = Field(default_factory=list)
    rubric_files: list[str] = Field(default_factory=list)
    policy_files: list[str] = Field(default_factory=list)
    profile_files: list[str] = Field(default_factory=list)
    config_files: list[str] = Field(default_factory=list)
    research_control_policy_ids: list[str] = Field(default_factory=list)

    @field_validator(
        "scenario_files",
        "rubric_files",
        "policy_files",
        "profile_files",
        "config_files",
    )
    @classmethod
    def asset_paths_are_contained_and_unique(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("extension asset paths must be unique")
        for raw in value:
            path = Path(raw)
            if path.is_absolute() or not path.parts or ".." in path.parts:
                raise ValueError("extension asset paths must be contained relative paths")
            if path.suffix not in {".yaml", ".yml", ".json"}:
                raise ValueError("extension assets must be declarative YAML or JSON files")
        return value

    @field_validator("research_control_policy_ids")
    @classmethod
    def research_control_ids_are_unique(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("research-control policy IDs must be unique")
        return value

    @field_validator("compatible_core_schema_versions", "dependencies")
    @classmethod
    def string_lists_are_unique(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("extension compatibility and dependency entries must be unique")
        return value


class ResolvedExtension(StrictModel):
    """A descriptor resolved to contained, verified local asset paths."""

    descriptor: ExtensionDescriptor
    root: Path
    scenario_files: list[Path]
    rubric_files: list[Path]
    policy_files: list[Path]
    profile_files: list[Path]
    config_files: list[Path]
    fingerprint: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
