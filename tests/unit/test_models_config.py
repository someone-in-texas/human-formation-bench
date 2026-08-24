from pathlib import Path

import pytest
from pydantic import ValidationError

from human_formation_benchmark.config import (
    deep_merge,
    list_profiles,
    load_lenses,
    load_rubrics,
    load_scenarios,
    required_perspectives,
)
from human_formation_benchmark.hashing import content_hash
from human_formation_benchmark.models import Dimension, JudgeResult, Scenario


def test_public_assets_cover_core_contract() -> None:
    scenarios = load_scenarios()
    rubrics = load_rubrics()
    assert len(scenarios) == 24
    assert len(rubrics) == 16
    assert {rubric.dimension for rubric in rubrics} == set(Dimension)
    assert all(scenario.approved_for_public_core for scenario in scenarios)
    assert len(list_profiles()) == 5
    assert {lens.perspective for lens in load_lenses()} == required_perspectives()


def test_scenario_rejects_unknown_field() -> None:
    payload = load_scenarios()[0].model_dump(mode="json")
    payload["surprise"] = "schema drift"
    with pytest.raises(ValidationError):
        Scenario.model_validate(payload)


def test_missing_score_cannot_be_silent_zero() -> None:
    with pytest.raises(ValidationError):
        JudgeResult(
            dimension=Dimension.AGENCY,
            score=None,
            confidence=0.5,
            rationale="Missing without an explanation.",
        )


def test_deep_merge_replaces_lists_and_merges_mappings() -> None:
    merged = deep_merge(
        {"runner": {"concurrency": 2, "seeds": [1]}, "budget": 5},
        {"runner": {"seeds": [9]}, "budget": 3},
    )
    assert merged == {"runner": {"concurrency": 2, "seeds": [9]}, "budget": 3}


def test_content_hash_is_stable_across_mapping_order() -> None:
    assert content_hash({"a": 1, "b": 2}) == content_hash({"b": 2, "a": 1})


def test_schema_files_are_committed() -> None:
    root = Path(__file__).resolve().parents[2]
    schemas = list((root / "schemas/v1").glob("*.schema.json"))
    assert len(schemas) == 18
