#!/usr/bin/env python3
"""Fail when a temporary dependency-audit exception reaches its review date."""

from __future__ import annotations

from datetime import date
from importlib import import_module
from importlib.metadata import version
from pathlib import Path

EXCEPTIONS = {
    "PYSEC-2026-2132": {
        "review_by": date(2026, 8, 15),
        "packages": {"click": "8.2.1", "inspect-ai": "0.3.249"},
        "aliases": {"GHSA-47fr-3ffg-hgmw", "CVE-2026-7246"},
        "owner": "security maintainers",
    },
}


def main() -> None:
    expired = [
        identifier
        for identifier, exception in EXCEPTIONS.items()
        if date.today() >= exception["review_by"]
    ]
    if expired:
        raise SystemExit(
            "dependency exceptions require review before release: " + ", ".join(expired)
        )
    for identifier, exception in EXCEPTIONS.items():
        for package, expected in exception["packages"].items():
            actual = version(package)
            if actual != expected:
                raise SystemExit(
                    f"{identifier}: reviewed {package}=={expected}, found {actual}; "
                    "remove or re-review the exception"
                )
        roots = [
            Path(__file__).resolve().parents[1] / "src",
            Path(import_module("inspect_ai").__file__).resolve().parent,
        ]
        offenders = [
            path
            for root in roots
            for path in root.rglob("*.py")
            if "click.edit(" in path.read_text(encoding="utf-8", errors="replace")
        ]
        if offenders:
            raise SystemExit(f"{identifier}: vulnerable click.edit call surface found: {offenders}")
        review_by = exception["review_by"]
        print(
            f"{identifier}: locked graph and call surface verified; "
            f"review by {review_by.isoformat()}"
        )


if __name__ == "__main__":
    main()
