#!/usr/bin/env python3
"""Fail-closed prerelease gate for the HFB alpha."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path
from typing import Any

import yaml

PRERELEASE_TAG = re.compile(r"^v\d+\.\d+\.\d+-(?:alpha|beta|rc)\.\d+$")


def run(command: list[str], *, cwd: Path) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def _string_set(payload: dict[str, Any], key: str) -> set[str]:
    value = payload.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) for item in value):
        raise SystemExit(f"review policy {key} must be a non-empty string list")
    return set(value)


def load_review_policy(root: Path) -> dict[str, Any]:
    path = root / "reviews" / "review-policy.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise SystemExit("reviews/review-policy.yaml must use schema_version 1")
    if payload.get("stage") not in {"internal_alpha", "external_review"}:
        raise SystemExit("review policy stage must be internal_alpha or external_review")
    _string_set(payload, "required_roles")
    _string_set(payload, "external_required_roles")
    _string_set(payload, "approved_verdicts")
    _string_set(payload, "blocking_severities")
    external = payload.get("external_verification")
    if not isinstance(external, dict) or not isinstance(external.get("required"), bool):
        raise SystemExit("review policy external_verification.required must be boolean")
    expected_stage = "external_review" if external["required"] else "internal_alpha"
    if payload["stage"] != expected_stage:
        raise SystemExit(
            f"review policy stage must be {expected_stage} when external verification "
            f"required is {external['required']}"
        )
    review_by = payload.get("review_by")
    if isinstance(review_by, date):
        review_date = review_by
    elif isinstance(review_by, str):
        try:
            review_date = date.fromisoformat(review_by)
        except ValueError as error:
            raise SystemExit("review policy review_by must be an ISO date") from error
    else:
        raise SystemExit("review policy review_by must be an ISO date")
    if date.today() >= review_date:
        raise SystemExit(f"review policy requires reconsideration by {review_date.isoformat()}")
    return payload


def permitted_review_commits(root: Path) -> set[str]:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()
    permitted = {head}
    parent = subprocess.run(
        ["git", "rev-parse", "HEAD^"], cwd=root, check=False, capture_output=True, text=True
    ).stdout.strip()
    if parent:
        changed = subprocess.run(
            ["git", "diff", "--name-only", parent, head],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        if changed and all(path.startswith("reviews/") for path in changed):
            permitted.add(parent)
    return permitted


def verify_reviews(root: Path, *, allowed_commits: set[str] | None = None) -> None:
    policy = load_review_policy(root)
    approved = _string_set(policy, "approved_verdicts")
    blocking_severities = _string_set(policy, "blocking_severities")
    external = policy["external_verification"]
    external_required = external["required"]
    required_roles = _string_set(
        policy, "external_required_roles" if external_required else "required_roles"
    )
    required_marker = external.get("required_marker", "external")
    if external_required and not isinstance(required_marker, str):
        raise SystemExit("review policy external required_marker must be a string")
    if external_required and allowed_commits is None:
        allowed_commits = permitted_review_commits(root)
    roles = set()
    blockers = []
    for path in sorted((root / "reviews").glob("*/final.yaml")):
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            blockers.append(f"{path}: review must be a mapping")
            continue
        role = payload.get("reviewer_role")
        if isinstance(role, str):
            roles.add(role)
        else:
            blockers.append(f"{path}: missing reviewer_role")
        verdict = payload.get("verdict")
        if verdict not in approved:
            blockers.append(f"{path}: verdict {verdict}")
        findings = payload.get("findings", [])
        if not isinstance(findings, list):
            blockers.append(f"{path}: findings must be a list")
            findings = []
        for finding in findings:
            if not isinstance(finding, dict):
                blockers.append(f"{path}: finding must be a mapping")
                continue
            severity = finding.get("severity")
            if severity in blocking_severities:
                blockers.append(f"{path}: unresolved {finding.get('id', 'unknown')} {severity}")
        if external_required:
            if payload.get("verification") != required_marker:
                blockers.append(f"{path}: external verification marker missing")
            if payload.get("reviewed_commit") not in allowed_commits:
                blockers.append(f"{path}: review is not bound to the release candidate")
    missing = required_roles - roles
    if missing:
        blockers.append(f"missing final reviewer roles: {sorted(missing)}")
    if blockers:
        raise SystemExit("review gate failed:\n- " + "\n- ".join(blockers))


def verify_release_metadata(root: Path, tag: str) -> None:
    if not PRERELEASE_TAG.fullmatch(tag):
        raise SystemExit("tag must be a semantic prerelease such as v0.2.0-alpha.1")
    version = tag.removeprefix("v")
    if f"## [{version}]" not in (root / "CHANGELOG.md").read_text(encoding="utf-8"):
        raise SystemExit(f"CHANGELOG.md does not contain a {version} release heading")
    citation = yaml.safe_load((root / "CITATION.cff").read_text(encoding="utf-8"))
    if not isinstance(citation, dict) or citation.get("version") != version:
        raise SystemExit(f"CITATION.cff version must equal {version}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="v0.2.0-alpha.1")
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
    verify_release_metadata(root, args.tag)
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
            [uv, "run", "pip-audit", "--skip-editable"],
        ]:
            run(command, cwd=root)
        run([uv, "build", "--clear"], cwd=root)
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
    subprocess.run([uv, "run", "python", "scripts/generate_schemas.py"], cwd=root, check=True)
    subprocess.run(
        [
            "git",
            "diff",
            "--exit-code",
            "--",
            "schemas",
            "src/human_formation_benchmark/extensions/gravity/schemas",
        ],
        cwd=root,
        check=True,
    )
    for schema in (root / "schemas").rglob("*.json"):
        json.loads(schema.read_text(encoding="utf-8"))
    print(f"Prerelease gates passed for {args.tag}")


if __name__ == "__main__":
    main()
