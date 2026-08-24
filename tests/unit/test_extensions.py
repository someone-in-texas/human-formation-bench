import shutil
from importlib.resources import files
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


def test_extension_fingerprint_covers_runtime_schema_and_registry_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asset_root = tmp_path / "assets"
    runtime_root = tmp_path / "runtime"
    binding_root = tmp_path / "binding"
    shutil.copytree(resource_directory(), asset_root)
    shutil.copytree(
        Path(str(files("human_formation_benchmark.extensions.gravity"))),
        runtime_root,
    )
    binding_root.mkdir()
    shutil.copy2(
        Path(str(files("human_formation_benchmark.extensions").joinpath("__init__.py"))),
        binding_root / "__init__.py",
    )
    extension_module = __import__(
        "human_formation_benchmark.extensions",
        fromlist=["files"],
    )

    def fixture_files(package: str) -> Path:
        return runtime_root if package.endswith(".gravity") else binding_root

    monkeypatch.setattr(extension_module, "files", fixture_files)
    baseline = resolve_extension("gravity", root=asset_root)
    assert baseline is not None

    resources_path = runtime_root / "resources.py"
    resources_path.write_text(
        resources_path.read_text(encoding="utf-8") + "\n# behavior change\n",
        encoding="utf-8",
    )
    runtime_changed = resolve_extension("gravity", root=asset_root)
    assert runtime_changed is not None
    assert runtime_changed.fingerprint != baseline.fingerprint

    schema_path = runtime_root / "schemas" / "scenario.schema.json"
    schema_path.write_text(
        schema_path.read_text(encoding="utf-8") + " ",
        encoding="utf-8",
    )
    schema_changed = resolve_extension("gravity", root=asset_root)
    assert schema_changed is not None
    assert schema_changed.fingerprint != runtime_changed.fingerprint

    binding_path = binding_root / "__init__.py"
    binding_path.write_text(
        binding_path.read_text(encoding="utf-8") + "\n# binding change\n",
        encoding="utf-8",
    )
    binding_changed = resolve_extension("gravity", root=asset_root)
    assert binding_changed is not None
    assert binding_changed.fingerprint != schema_changed.fingerprint


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
        (
            "runner_scenarios.yaml",
            lambda payload: payload["scenarios"][0].update({"dimensions": ["human_relatedness"]}),
            "projection drift",
        ),
        (
            "runner_policies.yaml",
            lambda payload: payload["policies"][0].update(
                {"system_prompt": "Only I can understand you; do not leave."}
            ),
            "policy projection drift",
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


@pytest.mark.parametrize(
    ("filename", "key"),
    [
        ("scenarios.yaml", "scenarios"),
        ("rubrics.yaml", "rubrics"),
        ("profiles.yaml", "profiles"),
        ("runner_scenarios.yaml", "scenarios"),
        ("runner_profiles.yaml", "profiles"),
        ("runner_policies.yaml", "policies"),
    ],
)
def test_gravity_semantic_validation_rejects_duplicate_ids(
    tmp_path: Path,
    filename: str,
    key: str,
) -> None:
    root = tmp_path / "gravity"
    shutil.copytree(resource_directory(), root)
    path = root / filename
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload[key].append(payload[key][0].copy())
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    extension = resolve_extension("gravity", root=root)
    assert extension is not None
    with pytest.raises(ValueError, match="duplicate Gravity"):
        validate_extension_assets(extension)
