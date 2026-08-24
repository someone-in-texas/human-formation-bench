import importlib.util
from pathlib import Path

import pytest
import yaml

PRE_RELEASE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "pre_release.py"
SPEC = importlib.util.spec_from_file_location("pre_release", PRE_RELEASE_PATH)
assert SPEC is not None and SPEC.loader is not None
PRE_RELEASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PRE_RELEASE)
verify_release_metadata = PRE_RELEASE.verify_release_metadata
verify_reviews = PRE_RELEASE.verify_reviews


def _write_policy(root: Path, *, external_required: bool) -> None:
    reviews = root / "reviews"
    reviews.mkdir()
    (reviews / "review-policy.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "stage": "external_review" if external_required else "internal_alpha",
                "review_by": "2099-12-31",
                "required_roles": ["technical"],
                "external_required_roles": ["technical", "accessibility"],
                "approved_verdicts": ["approve"],
                "blocking_severities": ["Critical", "High"],
                "external_verification": {
                    "required": external_required,
                    "required_marker": "external",
                },
            }
        ),
        encoding="utf-8",
    )


def _write_review(root: Path, **updates: object) -> None:
    review_dir = root / "reviews" / "technical"
    review_dir.mkdir()
    payload = {
        "reviewer_role": "technical",
        "verdict": "approve",
        "reviewed_commit": "old",
        "findings": [],
    }
    payload.update(updates)
    (review_dir / "final.yaml").write_text(yaml.safe_dump(payload), encoding="utf-8")


def test_internal_alpha_accepts_review_continuity_without_external_marker(tmp_path: Path) -> None:
    _write_policy(tmp_path, external_required=False)
    _write_review(tmp_path)
    verify_reviews(tmp_path, allowed_commits={"candidate"})


def test_external_review_fails_closed_on_stale_or_unmarked_artifact(tmp_path: Path) -> None:
    _write_policy(tmp_path, external_required=True)
    _write_review(tmp_path)
    with pytest.raises(SystemExit, match="external verification marker missing"):
        verify_reviews(tmp_path, allowed_commits={"candidate"})


def test_external_review_accepts_candidate_bound_artifact(tmp_path: Path) -> None:
    _write_policy(tmp_path, external_required=True)
    _write_review(tmp_path, verification="external", reviewed_commit="candidate")
    accessibility = tmp_path / "reviews" / "accessibility"
    accessibility.mkdir()
    (accessibility / "final.yaml").write_text(
        yaml.safe_dump(
            {
                "reviewer_role": "accessibility",
                "verdict": "approve",
                "reviewed_commit": "candidate",
                "verification": "external",
                "findings": [],
            }
        ),
        encoding="utf-8",
    )
    verify_reviews(tmp_path, allowed_commits={"candidate"})


def test_external_review_requires_all_specialist_roles(tmp_path: Path) -> None:
    _write_policy(tmp_path, external_required=True)
    _write_review(tmp_path, verification="external", reviewed_commit="candidate")
    with pytest.raises(SystemExit, match=r"missing final reviewer roles.*accessibility"):
        verify_reviews(tmp_path, allowed_commits={"candidate"})


def test_release_metadata_requires_matching_prerelease_and_citation(tmp_path: Path) -> None:
    (tmp_path / "CHANGELOG.md").write_text("## [0.2.0-alpha.1]\n", encoding="utf-8")
    (tmp_path / "CITATION.cff").write_text("version: 0.2.0-alpha.1\n", encoding="utf-8")
    verify_release_metadata(tmp_path, "v0.2.0-alpha.1")
    with pytest.raises(SystemExit, match="semantic prerelease"):
        verify_release_metadata(tmp_path, "v0.2.0")


def test_review_policy_stage_and_review_date_fail_closed(tmp_path: Path) -> None:
    _write_policy(tmp_path, external_required=False)
    policy_path = tmp_path / "reviews" / "review-policy.yaml"
    policy = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    policy["stage"] = "external_review"
    policy_path.write_text(yaml.safe_dump(policy), encoding="utf-8")
    with pytest.raises(SystemExit, match="stage must be internal_alpha"):
        verify_reviews(tmp_path, allowed_commits={"candidate"})

    policy["stage"] = "internal_alpha"
    policy["review_by"] = "2000-01-01"
    policy_path.write_text(yaml.safe_dump(policy), encoding="utf-8")
    with pytest.raises(SystemExit, match="requires reconsideration"):
        verify_reviews(tmp_path, allowed_commits={"candidate"})
