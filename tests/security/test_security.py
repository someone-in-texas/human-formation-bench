import os
from pathlib import Path

import pytest

from human_formation_benchmark.config import load_adversarial_challenges
from human_formation_benchmark.extensions import list_extensions, resolve_extension
from human_formation_benchmark.extensions.models import ExtensionDescriptor
from human_formation_benchmark.models import Dimension, ProviderResponse, TokenUsage
from human_formation_benchmark.scoring import detect_failure_gates, deterministic_score
from human_formation_benchmark.security import (
    contains_sensitive_data,
    redact,
    safe_child_path,
    validate_untrusted_text,
)
from human_formation_benchmark.storage import ContentCache


@pytest.mark.security
def test_redaction_removes_known_secret_patterns() -> None:
    text = "token=super-secret ghp_abcdefghijklmnopqrstuvwxyz123456 email=a@example.com"
    result = redact(text)
    assert "super-secret" not in result
    assert "ghp_" not in result
    assert "a@example.com" not in result


@pytest.mark.security
def test_sensitive_data_detection() -> None:
    assert contains_sensitive_data("contact person@example.org")
    assert not contains_sensitive_data("synthetic scenario with no identifiers")


@pytest.mark.security
def test_path_traversal_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        safe_child_path(tmp_path, "../escape")
    assert safe_child_path(tmp_path, "safe/file").is_relative_to(tmp_path)


@pytest.mark.security
def test_untrusted_text_is_bounded() -> None:
    with pytest.raises(ValueError):
        validate_untrusted_text("x" * 20, max_bytes=10)
    with pytest.raises(ValueError):
        validate_untrusted_text("bad\x00text")


@pytest.mark.security
def test_sensitive_response_is_not_cached_and_permissions_are_private(tmp_path: Path) -> None:
    cache = ContentCache(tmp_path / "cache")
    response = ProviderResponse(
        text="provider echoed token=secret-sentinel-value-now",
        usage=TokenUsage(input_tokens=1, output_tokens=1),
        latency_ms=1,
        cost_usd=0,
    )
    assert not cache.put(cache.key({"request": "one"}), response)
    assert cache.count() == 0
    if os.name == "posix":
        assert (tmp_path / "cache").stat().st_mode & 0o777 == 0o700


@pytest.mark.security
def test_cache_write_is_atomic_and_private(tmp_path: Path) -> None:
    cache = ContentCache(tmp_path / "cache")
    response = ProviderResponse(
        text="ordinary synthetic output",
        usage=TokenUsage(input_tokens=1, output_tokens=1),
        latency_ms=1,
        cost_usd=0,
    )
    key = cache.key({"request": "two"})
    assert cache.put(key, response)
    assert cache.get(key) == response
    assert not list((tmp_path / "cache").glob("*.tmp"))
    if os.name == "posix":
        assert (tmp_path / "cache" / f"{key}.json").stat().st_mode & 0o777 == 0o600


@pytest.mark.security
def test_public_red_team_challenges_are_executable_regressions() -> None:
    for challenge in load_adversarial_challenges():
        results = deterministic_score(
            challenge.response,
            list(Dimension),
            message_index=1,
        )
        assert max((result.score or 0) for result in results) <= challenge.expected_max_score
        flags = {flag for result in results for flag in result.flags}
        assert set(challenge.expected_flags) <= flags
        if challenge.expected_gate:
            assert detect_failure_gates([challenge.response]).model_dump()[challenge.expected_gate]


@pytest.mark.security
def test_extension_listing_never_consults_entry_points(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import importlib.metadata

    def forbidden_entry_points() -> None:
        raise AssertionError("entry-point discovery must not run")

    monkeypatch.setattr(importlib.metadata, "entry_points", forbidden_entry_points)
    assert [descriptor.id for descriptor in list_extensions()] == ["gravity"]


@pytest.mark.security
def test_extension_assets_reject_symlinks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "target.yaml"
    target.write_text("safe: true\n", encoding="utf-8")
    (tmp_path / "linked.yaml").symlink_to(target)
    descriptor = ExtensionDescriptor(
        id="linked_fixture",
        title="Linked Fixture",
        version="1.0.0",
        status="experimental",
        canonical_composite=False,
        requires_longitudinal_support=False,
        research_controls_available=False,
        compatible_core_schema_versions=["1.0"],
        config_files=["linked.yaml"],
    )
    extension_module = __import__(
        "human_formation_benchmark.extensions",
        fromlist=["_BUILTIN_REGISTRATIONS"],
    )
    registry = extension_module._BUILTIN_REGISTRATIONS
    gravity = registry["gravity"]
    registration = type(gravity)(
        descriptor=descriptor,
        resource_package=gravity.resource_package,
        validator=gravity.validator,
        reporter=gravity.reporter,
        runtime_files=(),
    )
    monkeypatch.setitem(registry, "linked_fixture", registration)
    with pytest.raises(ValueError, match="symbolic links"):
        resolve_extension("linked_fixture", root=tmp_path)
