"""Declarative registry and safe resolution for built-in benchmark extensions."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING

from ..hashing import content_hash
from ..security import safe_child_path, validate_regular_file
from .models import ExtensionDescriptor, ResolvedExtension

if TYPE_CHECKING:
    from ..models import Trajectory

from .gravity.aggregation import render_run_artifacts as render_gravity_artifacts
from .gravity.validation import validate_assets as validate_gravity_assets


@dataclass(frozen=True)
class _BuiltinRegistration:
    descriptor: ExtensionDescriptor
    resource_package: str
    validator: Callable[[Path], dict[str, int]]
    reporter: Callable[[Path, Iterable[Trajectory]], list[Path]]
    runtime_files: tuple[str, ...]


_GRAVITY = _BuiltinRegistration(
    descriptor=ExtensionDescriptor(
        id="gravity",
        title="Chosen Gravity Experimental Extension",
        version="0.1.0",
        status="experimental",
        canonical_composite=False,
        requires_longitudinal_support=True,
        research_controls_available=True,
        compatible_core_schema_versions=["1.0", "1.1"],
        dependencies=[],
        scenario_files=["runner_scenarios.yaml"],
        rubric_files=[],
        policy_files=["runner_policies.yaml"],
        profile_files=["runner_profiles.yaml"],
        config_files=[
            "manifest.yaml",
            "config.yaml",
            "scenarios.yaml",
            "rubrics.yaml",
            "profiles.yaml",
        ],
        research_control_policy_ids=[
            "gravity_frictionless_concierge",
            "gravity_hardship_maximizer",
            "gravity_productivity_substitution_maximizer",
            "gravity_relationally_sticky_companion",
        ],
    ),
    resource_package="human_formation_benchmark.extensions.gravity",
    validator=validate_gravity_assets,
    reporter=render_gravity_artifacts,
    runtime_files=(
        "__init__.py",
        "aggregation.py",
        "controls.py",
        "models.py",
        "resources.py",
        "schemas/gravity-report.schema.json",
        "schemas/rubric.schema.json",
        "schemas/scenario.schema.json",
        "schemas/signal-report.schema.json",
        "schemas/transfer-result.schema.json",
        "schemas/user-state.schema.json",
        "signals.py",
        "transfer.py",
        "transitions.py",
        "validation.py",
    ),
)
_BUILTIN_REGISTRATIONS = {"gravity": _GRAVITY}


def list_extensions() -> list[ExtensionDescriptor]:
    """Return built-in extension descriptors in stable ID order."""

    return [
        _BUILTIN_REGISTRATIONS[key].descriptor.model_copy(deep=True)
        for key in sorted(_BUILTIN_REGISTRATIONS)
    ]


def get_extension(extension_id: str) -> ExtensionDescriptor:
    """Return one known descriptor without consulting executable plugin metadata."""

    try:
        return _BUILTIN_REGISTRATIONS[extension_id].descriptor.model_copy(deep=True)
    except KeyError as error:
        raise KeyError(f"unknown extension: {extension_id}") from error


def _resolve_files(root: Path, paths: list[str]) -> list[Path]:
    resolved = []
    for relative in paths:
        unresolved = root / relative
        path = safe_child_path(root, relative)
        validate_regular_file(unresolved)
        resolved.append(path)
    return resolved


def resolve_extension(
    extension_id: str | None,
    *,
    root: Path | None = None,
) -> ResolvedExtension | None:
    """Resolve and fingerprint a built-in descriptor's explicitly named assets."""

    if extension_id is None:
        return None
    registration = _BUILTIN_REGISTRATIONS.get(extension_id)
    if registration is None:
        raise KeyError(f"unknown extension: {extension_id}")
    descriptor = registration.descriptor.model_copy(deep=True)
    if root is None:
        base = Path(str(files(registration.resource_package).joinpath("resources"))).resolve()
    else:
        base = root.resolve()
    scenario_files = _resolve_files(base, descriptor.scenario_files)
    rubric_files = _resolve_files(base, descriptor.rubric_files)
    policy_files = _resolve_files(base, descriptor.policy_files)
    profile_files = _resolve_files(base, descriptor.profile_files)
    config_files = _resolve_files(base, descriptor.config_files)
    paths = [
        *scenario_files,
        *rubric_files,
        *policy_files,
        *profile_files,
        *config_files,
    ]
    asset_hashes = {
        str(path.relative_to(base)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths
    }
    runtime_root = files(registration.resource_package)
    runtime_hashes = {
        filename: hashlib.sha256(runtime_root.joinpath(filename).read_bytes()).hexdigest()
        for filename in registration.runtime_files
    }
    binding_path = files("human_formation_benchmark.extensions").joinpath("__init__.py")
    runtime_hashes["registry-binding.py"] = hashlib.sha256(binding_path.read_bytes()).hexdigest()
    fingerprint = content_hash(
        {
            "descriptor": descriptor.model_dump(mode="json"),
            "assets": asset_hashes,
            "runtime": runtime_hashes,
        }
    )
    return ResolvedExtension(
        descriptor=descriptor,
        root=base,
        scenario_files=scenario_files,
        rubric_files=rubric_files,
        policy_files=policy_files,
        profile_files=profile_files,
        config_files=config_files,
        fingerprint=fingerprint,
    )


def render_extension_artifacts(
    extension_id: str | None,
    run_dir: Path,
    trajectories: Iterable[Trajectory],
) -> list[Path]:
    """Dispatch report generation only to reviewed, built-in extension code."""

    if extension_id is None:
        return []
    try:
        reporter = _BUILTIN_REGISTRATIONS[extension_id].reporter
    except KeyError as error:
        raise KeyError(f"unknown extension reporter: {extension_id}") from error
    return reporter(run_dir, trajectories)


def validate_extension_assets(extension: ResolvedExtension) -> dict[str, int]:
    """Run the reviewed semantic validator registered for a built-in extension."""

    try:
        validator = _BUILTIN_REGISTRATIONS[extension.descriptor.id].validator
    except KeyError as error:
        raise KeyError(f"unknown extension validator: {extension.descriptor.id}") from error
    return validator(extension.root)


__all__ = [
    "ExtensionDescriptor",
    "ResolvedExtension",
    "get_extension",
    "list_extensions",
    "render_extension_artifacts",
    "resolve_extension",
    "validate_extension_assets",
]
