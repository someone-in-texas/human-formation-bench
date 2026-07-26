from pathlib import Path

import pytest

from human_formation_benchmark.security import (
    contains_sensitive_data,
    redact,
    safe_child_path,
    validate_untrusted_text,
)


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
