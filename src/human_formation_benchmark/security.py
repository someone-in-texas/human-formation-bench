"""Boundary controls for secrets and untrusted benchmark content."""

from __future__ import annotations

import re
from pathlib import Path

SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bgh[opsu]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),
    re.compile(r"(?i)\b(api[_-]?key|token|password)\s*[:=]\s*[^\s,;]+"),
)

PII_PATTERNS = (
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
)


def redact(text: str) -> str:
    """Remove common credential and direct-identifier patterns from logs."""

    for pattern in (*SECRET_PATTERNS, *PII_PATTERNS):
        text = pattern.sub("[REDACTED]", text)
    return text


def contains_sensitive_data(text: str) -> bool:
    return any(pattern.search(text) for pattern in (*SECRET_PATTERNS, *PII_PATTERNS))


def safe_child_path(root: Path, candidate: str | Path) -> Path:
    """Resolve a path and require that it remains under ``root``."""

    resolved_root = root.resolve()
    candidate_path = (resolved_root / candidate).resolve()
    if candidate_path != resolved_root and resolved_root not in candidate_path.parents:
        raise ValueError(f"path escapes allowed root: {candidate}")
    return candidate_path


def validate_untrusted_text(text: str, *, max_bytes: int = 1_000_000) -> None:
    """Apply cheap denial-of-service and NUL-byte checks before parsing."""

    if len(text.encode("utf-8")) > max_bytes:
        raise ValueError("input exceeds maximum allowed size")
    if "\x00" in text:
        raise ValueError("NUL bytes are not allowed")


def validate_regular_file(path: Path, *, max_bytes: int = 1_000_000) -> None:
    """Reject links, non-regular files, and oversized inputs before allocation."""

    if path.is_symlink():
        raise ValueError("symbolic links are not accepted at this trust boundary")
    if not path.is_file():
        raise ValueError("expected a regular file")
    size = path.stat().st_size
    if size > max_bytes:
        raise ValueError(f"input exceeds maximum allowed size ({max_bytes} bytes)")
