import importlib.util
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

PRE_RELEASE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "pre_release.py"
SPEC = importlib.util.spec_from_file_location("pre_release", PRE_RELEASE_PATH)
assert SPEC is not None and SPEC.loader is not None
PRE_RELEASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PRE_RELEASE)
verify_release_metadata = PRE_RELEASE.verify_release_metadata
verify_release_candidate_review = PRE_RELEASE.verify_release_candidate_review
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
                    "triggered": [],
                    "reenable_triggers": [
                        "beta_or_stable_release",
                        "calibrated_or_ordinal_scoring",
                        "comparative_or_construct_validity_claims",
                        "human_subject_research",
                        "large_public_pack_expansion",
                        "second_active_maintainer_and_review_panel",
                    ],
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
    verify_reviews(tmp_path, expected_content_hash="sha256:candidate")


def test_external_review_fails_closed_on_stale_or_unmarked_artifact(tmp_path: Path) -> None:
    _write_policy(tmp_path, external_required=True)
    _write_review(tmp_path)
    with pytest.raises(SystemExit, match="external verification marker missing"):
        verify_reviews(tmp_path, expected_content_hash="sha256:candidate")


def test_external_review_accepts_candidate_bound_artifact(tmp_path: Path) -> None:
    _write_policy(tmp_path, external_required=True)
    provenance = {
        "verification": "external",
        "reviewed_commit": "0123456789abcdef0123456789abcdef01234567",
        "reviewed_content_hash": "sha256:candidate",
        "reviewer_identity": "Reviewer One",
        "affiliation": "Independent",
        "expertise": ["technical"],
        "conflicts": ["none"],
        "independence_statement": "No project role.",
    }
    _write_review(tmp_path, **provenance)
    accessibility = tmp_path / "reviews" / "accessibility"
    accessibility.mkdir()
    (accessibility / "final.yaml").write_text(
        yaml.safe_dump(
            {
                "reviewer_role": "accessibility",
                "verdict": "approve",
                "reviewed_commit": "0123456789abcdef0123456789abcdef01234567",
                "reviewed_content_hash": "sha256:candidate",
                "verification": "external",
                "reviewer_identity": "Reviewer Two",
                "affiliation": "Independent",
                "expertise": ["accessibility"],
                "conflicts": ["none"],
                "independence_statement": "No project role.",
                "findings": [],
            }
        ),
        encoding="utf-8",
    )
    verify_reviews(tmp_path, expected_content_hash="sha256:candidate")


def test_external_review_requires_all_specialist_roles(tmp_path: Path) -> None:
    _write_policy(tmp_path, external_required=True)
    _write_review(
        tmp_path,
        verification="external",
        reviewed_commit="candidate",
        reviewed_content_hash="sha256:candidate",
    )
    with pytest.raises(SystemExit, match=r"missing final reviewer roles.*accessibility"):
        verify_reviews(tmp_path, expected_content_hash="sha256:candidate")


def test_release_metadata_requires_matching_prerelease_and_citation(tmp_path: Path) -> None:
    _write_policy(tmp_path, external_required=False)
    (tmp_path / "CHANGELOG.md").write_text("## [0.2.0-alpha.1]\n", encoding="utf-8")
    (tmp_path / "CITATION.cff").write_text("version: 0.2.0-alpha.1\n", encoding="utf-8")
    verify_release_metadata(tmp_path, "v0.2.0-alpha.1")
    with pytest.raises(SystemExit, match="semantic prerelease"):
        verify_release_metadata(tmp_path, "v0.2.0")
    (tmp_path / "CHANGELOG.md").write_text("## [0.2.0-beta.1]\n", encoding="utf-8")
    (tmp_path / "CITATION.cff").write_text("version: 0.2.0-beta.1\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="beta and rc tags require external"):
        verify_release_metadata(tmp_path, "v0.2.0-beta.1")


def test_review_policy_stage_and_review_date_fail_closed(tmp_path: Path) -> None:
    _write_policy(tmp_path, external_required=False)
    policy_path = tmp_path / "reviews" / "review-policy.yaml"
    policy = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    policy["stage"] = "external_review"
    policy_path.write_text(yaml.safe_dump(policy), encoding="utf-8")
    with pytest.raises(SystemExit, match="stage must be internal_alpha"):
        verify_reviews(tmp_path, expected_content_hash="sha256:candidate")

    policy["stage"] = "internal_alpha"
    policy["review_by"] = "2000-01-01"
    policy_path.write_text(yaml.safe_dump(policy), encoding="utf-8")
    with pytest.raises(SystemExit, match="requires reconsideration"):
        verify_reviews(tmp_path, expected_content_hash="sha256:candidate")


def test_release_candidate_review_is_tag_and_commit_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_policy(tmp_path, external_required=False)
    candidate = {
        "schema_version": 1,
        "release_tag": "v0.2.0-alpha.1",
        "stage": "internal_alpha",
        "reviewed_commit": "0123456789abcdef0123456789abcdef01234567",
        "reviewed_content_hash": "sha256:candidate",
        "verdict": "approve",
        "scopes": ["technical", "governance", "release"],
        "findings": [],
    }
    (tmp_path / "reviews" / "release-candidate.yaml").write_text(
        yaml.safe_dump(candidate), encoding="utf-8"
    )
    (tmp_path / "reviews" / "REVIEW_SUMMARY.md").write_text(
        "# v0.2.0-alpha.1\n\n0123456789abcdef0123456789abcdef01234567\nsha256:candidate\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(PRE_RELEASE, "release_content_hash", lambda root: "sha256:candidate")
    verify_release_candidate_review(tmp_path, "v0.2.0-alpha.1")
    candidate["reviewed_content_hash"] = "sha256:stale"
    (tmp_path / "reviews" / "release-candidate.yaml").write_text(
        yaml.safe_dump(candidate), encoding="utf-8"
    )
    with pytest.raises(SystemExit, match="not bound to the release content"):
        verify_release_candidate_review(tmp_path, "v0.2.0-alpha.1")


def test_repository_policy_preserves_all_seven_external_roles() -> None:
    root = Path(__file__).resolve().parents[2]
    policy = PRE_RELEASE.load_review_policy(root)
    assert set(policy["external_required_roles"]) == {
        "technical_reproducibility",
        "psychometrics_methodology",
        "philosophy_pluralism",
        "alignment_adversarial",
        "disability_accessibility_care",
        "security_privacy_open_source",
        "benchmark_red_team_goodhart",
    }


def test_release_content_hash_excludes_evidence_but_includes_policy(tmp_path: Path) -> None:
    (tmp_path / "reviews").mkdir()
    summary = tmp_path / "reviews" / "REVIEW_SUMMARY.md"
    policy = tmp_path / "reviews" / "review-policy.yaml"
    summary.write_text("first review\n", encoding="utf-8")
    policy.write_text("stage: internal_alpha\n", encoding="utf-8")
    (tmp_path / "code.py").write_text("value = 1\n", encoding="utf-8")
    git = shutil.which("git")
    assert git is not None
    subprocess.run([git, "init", "-q"], cwd=tmp_path, check=True)  # noqa: S603
    subprocess.run([git, "add", "."], cwd=tmp_path, check=True)  # noqa: S603
    original = PRE_RELEASE.release_content_hash(tmp_path)

    summary.write_text("second review\n", encoding="utf-8")
    subprocess.run(  # noqa: S603
        [git, "add", "reviews/REVIEW_SUMMARY.md"], cwd=tmp_path, check=True
    )
    assert PRE_RELEASE.release_content_hash(tmp_path) == original

    policy.write_text("stage: external_review\n", encoding="utf-8")
    subprocess.run(  # noqa: S603
        [git, "add", "reviews/review-policy.yaml"], cwd=tmp_path, check=True
    )
    assert PRE_RELEASE.release_content_hash(tmp_path) != original
