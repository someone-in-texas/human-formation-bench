#!/usr/bin/env python3
"""Generate committed JSON Schemas from the runtime Pydantic models."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from human_formation_benchmark.extensions.gravity.models import (
    GravityReportArtifact,
    GravityRubric,
    GravityScenario,
    GravityTransferResult,
    GravityUserState,
    SignalReport,
)
from human_formation_benchmark.models import (
    AdversarialChallenge,
    Constitution,
    CostEstimate,
    ExtensionRunManifest,
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
GRAVITY_MODELS = {
    "gravity-report": GravityReportArtifact,
    "rubric": GravityRubric,
    "scenario": GravityScenario,
    "signal-report": SignalReport,
    "transfer-result": GravityTransferResult,
    "user-state": GravityUserState,
}


def _write_schema(path: Path, schema_id: str, model: type[BaseModel]) -> None:
    schema = model.model_json_schema()
    schema["$id"] = schema_id
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(schema, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    schema_dir = root / "schemas" / "v1"
    schema_dir.mkdir(parents=True, exist_ok=True)
    for name, model in MODELS.items():
        schema_id = (
            "https://raw.githubusercontent.com/someone-in-texas/"
            f"human-formation-bench/main/schemas/v1/{name}.schema.json"
        )
        _write_schema(schema_dir / f"{name}.schema.json", schema_id, model)

    v11 = root / "schemas" / "v1.1"
    _write_schema(
        v11 / "run-manifest.schema.json",
        (
            "https://raw.githubusercontent.com/someone-in-texas/"
            "human-formation-bench/main/schemas/v1.1/run-manifest.schema.json"
        ),
        ExtensionRunManifest,
    )
    package_schema_dir = (
        root / "src" / "human_formation_benchmark" / "extensions" / "gravity" / "schemas"
    )
    for name, model in GRAVITY_MODELS.items():
        schema_id = (
            "https://raw.githubusercontent.com/someone-in-texas/"
            f"human-formation-bench/main/schemas/v1.1/extensions/gravity/{name}.schema.json"
        )
        _write_schema(v11 / "extensions" / "gravity" / f"{name}.schema.json", schema_id, model)
        _write_schema(package_schema_dir / f"{name}.schema.json", schema_id, model)


if __name__ == "__main__":
    main()
