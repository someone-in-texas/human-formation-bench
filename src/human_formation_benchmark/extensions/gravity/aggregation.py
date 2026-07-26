"""Vector-only aggregation and report artifact helpers."""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterable
from html import escape
from pathlib import Path

from human_formation_benchmark.models import Trajectory

from .models import (
    GravityConstruct,
    GravityGates,
    GravityReportArtifact,
    GravityScoreObservation,
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
HTML_START_MARKER = "<!-- hfb:gravity:start -->"
HTML_END_MARKER = "<!-- hfb:gravity:end -->"


def _missing_artifact(
    observations: list[GravityScoreObservation],
    detector_hits_by_policy: dict[str, GravityGates],
) -> GravityReportArtifact:
    """Build the staged report; executable ordinal judgment is intentionally absent."""

    union: dict[str, bool] = {}
    for hits in detector_hits_by_policy.values():
        for name, value in hits.model_dump().items():
            union[name] = union.get(name, False) or bool(value)
    return GravityReportArtifact(
        construct_profile={construct: None for construct in GravityConstruct},
        raw_observations=observations,
        detector_hits_by_policy=detector_hits_by_policy,
        run_detector_hit_union=GravityGates.model_validate(union),
        transfer=None,
        limitations=LIMITATIONS,
    )


def render_run_artifacts(run_dir: Path, trajectories: Iterable[Trajectory]) -> list[Path]:
    """Write contextual Gravity signals and an explicitly non-composite report.

    No ordinal result is inferred from detector matches. Missing rubric
    observations remain visible until a configured judge or human reviewer
    supplies evidence-backed judgments.
    """

    scenario_context = {item.id: item.gravity for item in load_scenarios()}
    signals_path = run_dir / "gravity-signals.jsonl"
    signal_count = 0
    detector_hits_by_policy: dict[str, dict[str, bool]] = defaultdict(dict)
    with signals_path.open("w", encoding="utf-8") as signals_file:
        for trajectory in trajectories:
            context = scenario_context.get(trajectory.scenario_id)
            if context is None:
                continue
            for message_index, message in enumerate(trajectory.messages):
                if message.role != "assistant":
                    continue
                report = analyze_response(message.content, context)
                policy_hits = detector_hits_by_policy[trajectory.policy_id]
                for field_name, value in report.detector_hits.model_dump().items():
                    policy_hits[field_name] = policy_hits.get(field_name, False) or bool(value)
                payload = {
                    "trajectory_id": trajectory.id,
                    "scenario_id": trajectory.scenario_id,
                    "policy_id": trajectory.policy_id,
                    "message_index": message_index,
                    "report": report.model_dump(mode="json"),
                }
                signals_file.write(json.dumps(payload, sort_keys=True) + "\n")
                signal_count += 1

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
    typed_hits = {
        policy_id: GravityGates.model_validate(values)
        for policy_id, values in detector_hits_by_policy.items()
    }
    artifact = _missing_artifact(missing, typed_hits)
    report_path = run_dir / "gravity-report.json"
    report_path.write_text(
        artifact.model_dump_json(indent=2, by_alias=True) + "\n",
        encoding="utf-8",
    )
    markdown_path = run_dir / "report.md"
    existing = markdown_path.read_text(encoding="utf-8") if markdown_path.exists() else ""
    if SECTION_MARKER in existing:
        existing = existing.split(SECTION_MARKER, 1)[0].rstrip()
    policy_lines = []
    for policy_id, hits in sorted(typed_hits.items()):
        hit_names = [name for name, value in hits.model_dump().items() if value]
        policy_lines.append(
            f"- `{policy_id}` detector hits requiring adjudication: "
            f"{', '.join(hit_names) if hit_names else 'none'}"
        )
    if not policy_lines:
        policy_lines.append("- No assistant messages were available for detector analysis.")
    section = (
        f"\n\n{SECTION_MARKER}\n\n"
        "This section evaluates assistant behavior and synthetic outcomes. It is not a "
        "validated psychometric or clinical measure. Deterministic matches are triage "
        "signals requiring adjudication, not failure determinations or ordinal judgments, "
        "and no canonical composite is produced.\n\n"
        f"- Contextual assistant messages analyzed: {signal_count}\n"
        + "\n".join(policy_lines)
        + "\n"
        "- Rubric profile: insufficient evidence pending configured judgment\n"
    )
    markdown_path.write_text(existing.rstrip() + section, encoding="utf-8")
    html_path = run_dir / "report.html"
    if html_path.exists():
        html = html_path.read_text(encoding="utf-8")
        if HTML_START_MARKER in html and HTML_END_MARKER in html:
            before, remainder = html.split(HTML_START_MARKER, 1)
            _, after = remainder.split(HTML_END_MARKER, 1)
            html = before.rstrip() + "\n" + after.lstrip()
        rows = "".join(
            "<li><code>"
            + escape(policy_id)
            + "</code>: "
            + escape(
                ", ".join(name for name, value in hits.model_dump().items() if value) or "none"
            )
            + "</li>"
            for policy_id, hits in sorted(typed_hits.items())
        )
        if not rows:
            rows = "<li>No assistant messages were available for detector analysis.</li>"
        html_section = (
            f"{HTML_START_MARKER}\n"
            '<section id="gravity-experimental"><h2>Gravity experimental extension</h2>'
            '<p class="warning">Synthetic behavioral detector scaffold; not a validated '
            "psychometric or clinical measure. Hits require adjudication and no canonical "
            "composite or ordinal profile is produced.</p>"
            f"<p>Contextual assistant messages analyzed: {signal_count}</p>"
            f"<ul>{rows}</ul>"
            "<p>Rubric profile: insufficient evidence pending calibrated judgment.</p>"
            "</section>\n"
            f"{HTML_END_MARKER}\n"
        )
        html = html.replace("</body>", html_section + "</body>")
        html_path.write_text(html, encoding="utf-8")
    benchmark_card_path = run_dir / "benchmark-card.json"
    if benchmark_card_path.exists():
        benchmark_card = json.loads(benchmark_card_path.read_text(encoding="utf-8"))
        benchmark_card["extensions"] = {
            "gravity": {
                "version": "0.1.0",
                "status": "experimental",
                "canonical_composite": False,
                "ordinal_profile_available": False,
                "adjudicated_failure_gates_available": False,
                "detector_hits_by_policy": {
                    policy_id: hits.model_dump(mode="json")
                    for policy_id, hits in typed_hits.items()
                },
                "run_detector_hit_union": artifact.run_detector_hit_union.model_dump(mode="json"),
            }
        }
        benchmark_card_path.write_text(
            json.dumps(benchmark_card, indent=2) + "\n",
            encoding="utf-8",
        )
    return [report_path, signals_path, markdown_path]
