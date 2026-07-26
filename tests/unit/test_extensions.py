import shutil
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from human_formation_benchmark.extensions import (
    get_extension,
    list_extensions,
    resolve_extension,
    validate_extension_assets,
)
from human_formation_benchmark.extensions.gravity.resources import resource_directory
from human_formation_benchmark.extensions.models import ExtensionDescriptor


def test_builtin_extension_registry_is_explicit_and_stable() -> None:
    descriptors = list_extensions()
    assert [descriptor.id for descriptor in descriptors] == ["gravity"]
    assert get_extension("gravity") == descriptors[0]
    with pytest.raises(KeyError, match="unknown extension"):
        get_extension("not_registered")


def test_extension_descriptor_is_strict_and_rejects_uncontained_assets() -> None:
    payload = get_extension("gravity").model_dump()
    payload["surprise"] = True
    with pytest.raises(ValidationError):
        ExtensionDescriptor.model_validate(payload)

    payload.pop("surprise")
    payload["scenario_files"] = ["../outside.yaml"]
    with pytest.raises(ValidationError, match="contained relative"):
        ExtensionDescriptor.model_validate(payload)


def test_extension_fingerprint_changes_with_allowlisted_asset(
    tmp_path: Path,
) -> None:
    root = tmp_path / "gravity"
    shutil.copytree(resource_directory(), root)
    first = resolve_extension("gravity", root=root)
    assert first is not None
    assert first.root == root.resolve()

    asset = root / "config.yaml"
    asset.write_text(asset.read_text(encoding="utf-8") + "\n# reviewed change\n", encoding="utf-8")
    second = resolve_extension("gravity", root=root)
    assert second is not None
    assert first.fingerprint != second.fingerprint


@pytest.mark.parametrize(
    ("filename", "mutate", "message"),
    [
        (
            "scenarios.yaml",
            lambda payload: payload["scenarios"][0].update({"unexpected": True}),
            "unexpected",
        ),
        (
            "rubrics.yaml",
            lambda payload: payload["rubrics"][0].update({"construct": "unknown_construct"}),
            "construct",
        ),
        (
            "profiles.yaml",
            lambda payload: payload["profiles"][0].update({"trajectory_turns": 0}),
            "trajectory_turns",
        ),
        (
            "manifest.yaml",
            lambda payload: payload.update({"version": "9.9.9"}),
            "version",
        ),
        (
            "config.yaml",
            lambda payload: payload.update({"unsupported_capability": True}),
            "unsupported_capability",
        ),
    ],
)
def test_gravity_semantic_validation_rejects_corrupt_assets(
    tmp_path: Path,
    filename: str,
    mutate: object,
    message: str,
) -> None:
    root = tmp_path / "gravity"
    shutil.copytree(resource_directory(), root)
    path = root / filename
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    mutate(payload)  # type: ignore[operator]
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    extension = resolve_extension("gravity", root=root)
    assert extension is not None
    with pytest.raises((ValidationError, ValueError), match=message):
        validate_extension_assets(extension)
