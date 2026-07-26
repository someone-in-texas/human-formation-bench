#!/usr/bin/env python3
"""Fail when a temporary dependency-audit exception reaches its review date."""

from __future__ import annotations

from datetime import date

EXCEPTIONS = {
    "PYSEC-2026-2132": date(2026, 8, 15),
}


def main() -> None:
    expired = [
        identifier
        for identifier, review_by in EXCEPTIONS.items()
        if date.today() >= review_by
    ]
    if expired:
        raise SystemExit(
            "dependency exceptions require review before release: " + ", ".join(expired)
        )
    for identifier, review_by in EXCEPTIONS.items():
        print(f"{identifier}: documented exception; review by {review_by.isoformat()}")


if __name__ == "__main__":
    main()
