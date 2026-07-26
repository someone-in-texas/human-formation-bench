from pathlib import Path

import pytest
from pydantic import ValidationError

from human_formation_benchmark.extensions import get_extension, list_extensions, resolve_extension
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
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    descriptor = ExtensionDescriptor(
        id="fixture",
        title="Fixture Extension",
        version="1.0.0",
        status="experimental",
        canonical_composite=False,
        requires_longitudinal_support=False,
        research_controls_available=False,
        config_files=["config.yaml"],
    )
    monkeypatch.setitem(
        __import__(
            "human_formation_benchmark.extensions",
            fromlist=["_BUILTIN_EXTENSIONS"],
        )._BUILTIN_EXTENSIONS,
        "fixture",
        descriptor,
    )
    asset = tmp_path / "config.yaml"
    asset.write_text("version: one\n", encoding="utf-8")
    first = resolve_extension("fixture", root=tmp_path)
    assert first is not None
    assert first.root == tmp_path.resolve()

    asset.write_text("version: two\n", encoding="utf-8")
    second = resolve_extension("fixture", root=tmp_path)
    assert second is not None
    assert first.fingerprint != second.fingerprint
