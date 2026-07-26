"""Vector-only aggregation and report artifact helpers."""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path
from statistics import mean

from human_formation_benchmark.models import Trajectory

from .models import (
    GravityConstruct,
    GravityGates,
    GravityReportArtifact,
    GravityScoreObservation,
    GravityTransferResult,
)
from .resources import load_scenarios
from .signals import analyze_response

LIMITATIONS = [
    "Experimental behavioral benchmark; not a validated psychometric instrument.",
    (
        "Evaluates assistant behavior and synthetic outcomes, not a real person's "
        "flourishing or health."
    ),
    "Constructs are contestable and normatively loaded; causal effects require human validation.",
    "The default artifact has no canonical composite score.",
]
SECTION_MARKER = "## Gravity experimental extension"


def build_artifact(
    observations: list[GravityScoreObservation],
    *,
    gates: GravityGates | None = None,
    transfer: GravityTransferResult | None = None,
) -> GravityReportArtifact:
    """Normalize reviewed 0-4 judgments per construct while preserving raw data."""

    values: dict[GravityConstruct, list[int]] = defaultdict(list)
    for observation in observations:
        if observation.raw_score is not None:
            values[observation.gravity_construct].append(observation.raw_score)
    profile = {
        construct: mean(values[construct]) / 4 if values[construct] else None
        for construct in GravityConstruct
    }
    return GravityReportArtifact(
        construct_profile=profile,
        raw_observations=observations,
        failure_gates=gates or GravityGates(),
        transfer=transfer,
        limitations=LIMITATIONS,
    )


def render_run_artifacts(run_dir: Path, trajectories: Sequence[Trajectory]) -> list[Path]:
    """Write contextual Gravity signals and an explicitly non-composite report.

    No ordinal result is inferred from detector matches. Missing rubric
    observations remain visible until a configured judge or human reviewer
    supplies evidence-backed judgments.
    """

    scenario_context = {item.id: item.gravity for item in load_scenarios()}
    signal_lines: list[str] = []
    gate_values: dict[str, bool] = {}
    for trajectory in trajectories:
        context = scenario_context.get(trajectory.scenario_id)
        if context is None:
            continue
        for message_index, message in enumerate(trajectory.messages):
            if message.role != "assistant":
                continue
            report = analyze_response(message.content, context)
            for field_name, value in report.gates.model_dump().items():
                gate_values[field_name] = gate_values.get(field_name, False) or bool(value)
            payload = {
                "trajectory_id": trajectory.id,
                "scenario_id": trajectory.scenario_id,
                "message_index": message_index,
                "report": report.model_dump(mode="json"),
            }
            signal_lines.append(json.dumps(payload, sort_keys=True))

    missing = [
        GravityScoreObservation(
            construct=construct,
            raw_score=None,
            confidence=0.0,
            insufficient_evidence=True,
            evidence=[],
        )
        for construct in GravityConstruct
    ]
    artifact = build_artifact(missing, gates=GravityGates.model_validate(gate_values))
    report_path = run_dir / "gravity-report.json"
    signals_path = run_dir / "gravity-signals.jsonl"
    report_path.write_text(
        artifact.model_dump_json(indent=2, by_alias=True) + "\n",
        encoding="utf-8",
    )
    signals_path.write_text(
        "\n".join(signal_lines) + ("\n" if signal_lines else ""),
        encoding="utf-8",
    )
    markdown_path = run_dir / "report.md"
    existing = markdown_path.read_text(encoding="utf-8") if markdown_path.exists() else ""
    if SECTION_MARKER in existing:
        existing = existing.split(SECTION_MARKER, 1)[0].rstrip()
    hit_names = [name for name, value in gate_values.items() if value]
    section = (
        f"\n\n{SECTION_MARKER}\n\n"
        "This section evaluates assistant behavior and synthetic outcomes. It is not a "
        "validated psychometric or clinical measure. Deterministic matches are triage "
        "signals, not ordinal judgments, and no canonical composite is produced.\n\n"
        f"- Contextual assistant messages analyzed: {len(signal_lines)}\n"
        f"- Visible failure gates: {', '.join(hit_names) if hit_names else 'none detected'}\n"
        "- Rubric profile: insufficient evidence pending configured judgment\n"
    )
    markdown_path.write_text(existing.rstrip() + section, encoding="utf-8")
    benchmark_card_path = run_dir / "benchmark-card.json"
    if benchmark_card_path.exists():
        benchmark_card = json.loads(benchmark_card_path.read_text(encoding="utf-8"))
        benchmark_card["extensions"] = {
            "gravity": {
                "version": "0.1.0",
                "status": "experimental",
                "canonical_composite": False,
                "ordinal_profile_available": False,
                "failure_gates": artifact.failure_gates.model_dump(mode="json"),
            }
        }
        benchmark_card_path.write_text(
            json.dumps(benchmark_card, indent=2) + "\n",
            encoding="utf-8",
        )
    return [report_path, signals_path, markdown_path]
