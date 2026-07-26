#!/usr/bin/env python3
"""Generate committed JSON Schemas from the runtime Pydantic models."""

from __future__ import annotations

import json
from pathlib import Path

from human_formation_benchmark.models import (
    AdversarialChallenge,
    Constitution,
    CostEstimate,
    JudgeResult,
    Message,
    Persona,
    PerspectiveContrast,
    Policy,
    ReviewFinding,
    Rubric,
    RunManifest,
    Scenario,
    ScenarioPackManifest,
    ScoreReport,
    Trajectory,
    UserState,
    WorldviewLens,
)
from human_formation_benchmark.research import SourceRecord

MODELS = {
    "scenario": Scenario,
    "persona": Persona,
    "trajectory": Trajectory,
    "message": Message,
    "user-state": UserState,
    "policy": Policy,
    "constitution": Constitution,
    "rubric": Rubric,
    "judge-result": JudgeResult,
    "run-manifest": RunManifest,
    "cost-estimate": CostEstimate,
    "score-report": ScoreReport,
    "source-record": SourceRecord,
    "review-finding": ReviewFinding,
    "scenario-pack-manifest": ScenarioPackManifest,
    "worldview-lens": WorldviewLens,
    "perspective-contrast": PerspectiveContrast,
    "adversarial-challenge": AdversarialChallenge,
}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    schema_dir = root / "schemas" / "v1"
    schema_dir.mkdir(parents=True, exist_ok=True)
    for name, model in MODELS.items():
        schema = model.model_json_schema()
        schema["$id"] = (
            "https://raw.githubusercontent.com/someone-in-texas/"
            f"human-formation-bench/main/schemas/v1/{name}.schema.json"
        )
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        (schema_dir / f"{name}.schema.json").write_text(
            json.dumps(schema, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
