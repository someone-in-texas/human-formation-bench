from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from human_formation_benchmark.extensions.gravity import (
    GravityConstruct,
    load_profiles,
    load_rubrics,
    load_scenarios,
)
from human_formation_benchmark.extensions.gravity.models import (
    GravityScenarioPayload,
    GravityScoreObservation,
    GravityUserState,
    TransferObservation,
)
from human_formation_benchmark.extensions.gravity.resources import resource_directory
from human_formation_benchmark.extensions.gravity.transfer import build_transfer_result


def test_rich_assets_cover_vertical_slice() -> None:
    scenarios = load_scenarios()
    rubrics = load_rubrics()
    profiles = load_profiles()
    assert len(scenarios) == 12
    assert {target for item in scenarios for target in item.gravity.target_constructs} == set(
        GravityConstruct
    )
    assert {item.gravity_construct for item in rubrics} == set(GravityConstruct)
    assert {item.id for item in profiles} == {
        "gravity_micro",
        "gravity_small",
        "gravity_standard",
        "gravity_research",
    }
    assert all(item.synthetic for item in scenarios)
    assert all(item.review_status == "internal_multi_agent_reviewed" for item in scenarios)
    assert all(item.reviewer_type == "internal_agent" for item in scenarios)


def test_runner_assets_are_core_compatible() -> None:
    from human_formation_benchmark.models import Policy, RunProfile, Scenario

    root = resource_directory()
    cases = [
        ("runner_scenarios.yaml", "scenarios", Scenario),
        ("runner_profiles.yaml", "profiles", RunProfile),
        ("runner_policies.yaml", "policies", Policy),
    ]
    for filename, key, model in cases:
        payload = yaml.safe_load((root / filename).read_text(encoding="utf-8"))
        assert [model.model_validate(item) for item in payload[key]]


def test_strict_state_bounds_and_transfer_event_invariant() -> None:
    with pytest.raises(ValidationError):
        GravityUserState(ai_reliance_tendency=1.01)
    with pytest.raises(ValidationError):
        TransferObservation(
            test="novel_task",
            event_id="not-observed",
            occurred=False,
            success=True,
        )
    scenario = next(item for item in load_scenarios() if item.id == "gravity.learning.shortcut.001")
    result = build_transfer_result(
        scenario,
        [
            TransferObservation(
                test="novel_task",
                event_id="session:4:transfer_task",
                occurred=True,
                success=True,
                evidence="Synthetic user completed the scheduled related task.",
                signal_provenance=["fixture:session:4:transfer_task"],
                contraindications_reviewed=True,
            )
        ],
    )
    assert result.evidence_count == 1
    assert result.transition_version_hash.startswith("sha256:")
    assert result.transfer_version_hash.startswith("sha256:")


def test_transfer_rejects_unscheduled_or_evidence_free_success() -> None:
    scenario = next(item for item in load_scenarios() if item.id == "gravity.learning.shortcut.001")
    with pytest.raises(ValidationError, match="evidence"):
        TransferObservation(
            test="novel_task",
            event_id="session:4:transfer_task",
            occurred=True,
            success=True,
        )
    with pytest.raises(ValueError, match="unscheduled"):
        build_transfer_result(
            scenario,
            [
                TransferObservation(
                    test="novel_task",
                    event_id="session:99:transfer_task",
                    occurred=True,
                    success=None,
                )
            ],
        )


def test_ordinal_judgment_requires_complete_experimental_provenance() -> None:
    with pytest.raises(ValidationError, match="ordinal judgments require"):
        GravityScoreObservation(
            construct="formation_transfer",
            raw_score=4,
            confidence=1.0,
        )


def test_emergency_payload_must_allow_direct_execution() -> None:
    source = load_scenarios()[0].gravity.model_dump()
    source["urgency"] = "emergency"
    source["appropriate_assistance_modes"] = ["coach"]
    with pytest.raises(ValidationError):
        GravityScenarioPayload.model_validate(source)


def test_v11_schemas_are_present() -> None:
    root = Path(__file__).resolve().parents[4]
    schema_root = root / "schemas/v1.1/extensions/gravity"
    assert {path.name for path in schema_root.glob("*.json")} == {
        "gravity-report.schema.json",
        "rubric.schema.json",
        "scenario.schema.json",
        "signal-report.schema.json",
        "transfer-result.schema.json",
        "user-state.schema.json",
    }
    from importlib.resources import files

    packaged = files("human_formation_benchmark.extensions.gravity.schemas")
    assert {item.name for item in packaged.iterdir() if item.name.endswith(".json")} == {
        path.name for path in schema_root.glob("*.json")
    }
