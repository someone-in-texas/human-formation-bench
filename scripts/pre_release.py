#!/usr/bin/env python3
"""Fail-closed prerelease gate for the HFB alpha."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

import yaml

REQUIRED_ROLES = {
    "technical_reproducibility",
    "psychometrics_methodology",
    "philosophy_pluralism",
    "alignment_adversarial",
    "security_privacy_open_source",
}
APPROVED = {"approve", "approve_with_non_blocking_reservations"}


def run(command: list[str], *, cwd: Path) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def verify_reviews(root: Path) -> None:
    roles = set()
    blockers = []
    for path in sorted((root / "reviews").glob("*/final.yaml")):
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        roles.add(payload["reviewer_role"])
        if payload["verdict"] not in APPROVED:
            blockers.append(f"{path}: verdict {payload['verdict']}")
        for finding in payload.get("findings", []):
            if finding["severity"] in {"Critical", "High"}:
                blockers.append(f"{path}: unresolved {finding['id']} {finding['severity']}")
    missing = REQUIRED_ROLES - roles
    if missing:
        blockers.append(f"missing final reviewer roles: {sorted(missing)}")
    if blockers:
        raise SystemExit("review gate failed:\n- " + "\n- ".join(blockers))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="v0.1.0-alpha.1")
    parser.add_argument("--skip-checks", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    git = shutil.which("git")
    uv = shutil.which("uv")
    if not git or not uv:
        raise SystemExit("git and uv are required")
    status = subprocess.run(
        [git, "status", "--porcelain"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    if status:
        raise SystemExit("working tree must be clean")
    changelog_version = args.tag.removeprefix("v")
    if changelog_version not in (root / "CHANGELOG.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CHANGELOG.md does not mention {args.tag}")
    if args.tag != "v0.1.0-alpha.1":
        raise SystemExit("update the explicit alpha version gates before releasing another tag")
    verify_reviews(root)
    if not (root / "reviews/REVIEW_SUMMARY.md").is_file():
        raise SystemExit("reviews/REVIEW_SUMMARY.md is required")
    if not args.skip_checks:
        for command in [
            [uv, "sync", "--all-groups", "--extra", "release", "--frozen"],
            [uv, "run", "ruff", "format", "--check", "."],
            [uv, "run", "ruff", "check", "."],
            [uv, "run", "mypy"],
            [uv, "run", "pytest", "--cov"],
            [uv, "run", "mkdocs", "build", "--strict"],
            [uv, "run", "hfb", "validate"],
            [uv, "run", "python", "scripts/check_dependency_exceptions.py"],
            [
                uv,
                "run",
                "pip-audit",
                "--skip-editable",
                "--ignore-vuln",
                "PYSEC-2026-2132",
            ],
        ]:
            run(command, cwd=root)
        run([uv, "build"], cwd=root)
        wheels = sorted((root / "dist").glob("*.whl"))
        if len(wheels) != 1:
            raise SystemExit(f"expected one wheel, found {len(wheels)}")
        run([uv, "run", "python", "scripts/wheel_smoke.py", str(wheels[0])], cwd=root)
    expected_hash = yaml.safe_load((root / "data/public_core/manifest.yaml").read_text())[
        "content_hash"
    ]
    actual_hash = subprocess.run(
        [uv, "run", "hfb", "pack", "hash"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if actual_hash != expected_hash:
        raise SystemExit(f"scenario hash mismatch: {actual_hash} != {expected_hash}")
    for schema in (root / "schemas/v1").glob("*.json"):
        json.loads(schema.read_text(encoding="utf-8"))
    print(f"Prerelease gates passed for {args.tag}")


if __name__ == "__main__":
    main()
