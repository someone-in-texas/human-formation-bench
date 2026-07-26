"""Declarative registry and safe resolution for built-in benchmark extensions."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING

from ..hashing import content_hash
from ..security import safe_child_path, validate_regular_file
from .models import ExtensionDescriptor, ResolvedExtension

if TYPE_CHECKING:
    from ..models import Trajectory

_BUILTIN_EXTENSIONS: dict[str, ExtensionDescriptor] = {
    "gravity": ExtensionDescriptor(
        id="gravity",
        title="Chosen Gravity Experimental Extension",
        version="0.1.0",
        status="experimental",
        canonical_composite=False,
        requires_longitudinal_support=True,
        research_controls_available=True,
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
    )
}
_BUILTIN_RESOURCE_PACKAGES = {
    "gravity": "human_formation_benchmark.extensions.gravity",
}


def list_extensions() -> list[ExtensionDescriptor]:
    """Return built-in extension descriptors in stable ID order."""

    return [_BUILTIN_EXTENSIONS[key].model_copy(deep=True) for key in sorted(_BUILTIN_EXTENSIONS)]


def get_extension(extension_id: str) -> ExtensionDescriptor:
    """Return one known descriptor without consulting executable plugin metadata."""

    try:
        return _BUILTIN_EXTENSIONS[extension_id].model_copy(deep=True)
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
    descriptor = get_extension(extension_id)
    if root is None:
        base = Path(
            str(files(_BUILTIN_RESOURCE_PACKAGES[extension_id]).joinpath("resources"))
        ).resolve()
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
    fingerprint = content_hash(
        {
            "descriptor": descriptor.model_dump(mode="json"),
            "assets": asset_hashes,
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
    trajectories: Sequence[Trajectory],
) -> list[Path]:
    """Dispatch report generation only to reviewed, built-in extension code."""

    if extension_id is None:
        return []
    if extension_id == "gravity":
        from .gravity.aggregation import render_run_artifacts

        return render_run_artifacts(run_dir, trajectories)
    raise KeyError(f"unknown extension reporter: {extension_id}")


__all__ = [
    "ExtensionDescriptor",
    "ResolvedExtension",
    "get_extension",
    "list_extensions",
    "render_extension_artifacts",
    "resolve_extension",
]
