"""Vector-first reports with an explicit interpretation boundary."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from jinja2 import Environment, StrictUndefined

from .models import RunManifest, ScoreReport, Trajectory

DISCLAIMER = """\
## What this result does not mean

This result evaluates observable assistant behaviors. Scorer-derived state annotations are diagnostic
only and are not outcome evidence. It does not
show that a real person became autonomous, dependent, lonely, virtuous, healed, delusional, or
spiritually mature. It is not a clinical certification, a universal moral ranking, or a substitute
for preregistered human-subjects research. Scores are scenario-, rubric-, policy-, and judge-dependent.
"""

HTML_TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>HFB report {{ manifest.run_id }}</title>
<style>
body{font:16px/1.5 system-ui;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#18212b}
table{border-collapse:collapse;width:100%}th,td{padding:.55rem;border-bottom:1px solid #ccd}
th{text-align:left;background:#f3f5f7}.warning{padding:1rem;background:#fff3cd;border-left:4px solid #b58105}
.gate{font-weight:700;color:#9b1c1c}.muted{color:#52606d}code{background:#eef;padding:.12rem .3rem}
</style></head><body>
<h1>Human Formation Benchmark</h1>
<p class="warning"><strong>{{ report.assurance|upper }} ASSURANCE.</strong>
Synthetic model-behavior evidence; not evidence of real-user psychological outcomes.</p>
{% if report.assurance_reasons %}<ul class="warning">{% for reason in report.assurance_reasons %}
<li>{{ reason }}</li>{% endfor %}</ul>{% endif %}
<p>Run <code>{{ manifest.run_id }}</code> · model <code>{{ manifest.model }}</code> ·
{{ report.sample_count }} trajectories · ${{ "%.6f"|format(manifest.spent_usd) }}</p>
{% if manifest.lens_versions %}<p>Versioned lenses:
{% for lens,version in manifest.lens_versions.items() %}<code>{{ lens }}@{{ version }}</code>{% if not loop.last %}, {% endif %}{% endfor %}</p>{% endif %}
<p class="{{ 'gate' if manifest.status != 'completed' else '' }}"><strong>Status:
{{ manifest.status }}</strong> · completed {{ manifest.completed_sample_ids|length }} /
{{ manifest.expected_sample_count }} · failed {{ manifest.failed_sample_ids|length }}.</p>
{% if manifest.status != "completed" %}<p class="warning">Partial or failed run. Estimates and
comparisons are incomplete and must not be interpreted as an assurance result.</p>{% endif %}
{% for policy_id, policy in report.policy_profiles.items() %}
<h2>Policy/lens: {{ policy_id }}{% if policy.research_control %} (research control){% endif %}</h2>
<table><thead><tr><th>Dimension</th><th>Score</th><th>95% scenario-cluster interval</th><th>Clusters</th><th>Missing</th></tr></thead><tbody>
{% for dimension, value in policy.formation_profile.items() %}<tr>
<td>{{ dimension.value }}</td><td>{{ "%.3f"|format(value) if value is not none else "N/A" }}</td>
<td>{% set ci=policy.cluster_bootstrap_95_pct[dimension] %}{{ "[%.3f, %.3f]"|format(ci[0],ci[1]) if ci else "N/A" }}</td>
<td>{{ policy.scenario_cluster_count[dimension] }}</td>
<td>{{ policy.missing_scores[dimension] }}</td></tr>{% endfor %}</tbody></table>
<h3>Failure gates</h3><ul>{% for key,value in report.failure_gates_by_policy[policy_id].model_dump().items() %}
<li class="{{ 'gate' if value else '' }}">{{ key }}: {{ value }}</li>{% endfor %}</ul>
<h3>Attributed gate hits</h3><ul>{% for hit in report.gate_hits if hit.policy_id == policy_id %}
<li class="gate">{{ hit.gate }} · {{ hit.scenario_id }} · message {{ hit.message_index }}:
<code>{{ hit.quote }}</code></li>{% else %}<li>None.</li>{% endfor %}</ul>
{% endfor %}
<h2>Paired policy contrasts</h2><ul>{% for delta in report.paired_policy_deltas %}
<li>{{ delta.policy_a }} vs {{ delta.policy_b }} · {{ delta.dimension.value }}:
{{ "%+.3f"|format(delta.mean_delta) }} (n={{ delta.pair_count }})</li>{% else %}
<li>No paired multi-policy contrasts.</li>{% endfor %}</ul>
<h2>Material normative disagreements</h2><ul>{% for item in report.normative_disagreements %}
<li>{{ item }}</li>{% else %}<li>None detected by the operational threshold.</li>{% endfor %}</ul>
<h2>Operational invariants</h2><ul>{% for item in report.invariants %}
<li>{{ item }}</li>{% else %}<li>No paired invariants met the operational threshold.</li>{% endfor %}</ul>
<h2>What this result does not mean</h2>
<p>This result evaluates observable assistant behaviors. Scorer-derived state annotations are
diagnostic only, not outcome evidence. It does not
show that a real person acquired an inner trait or clinical condition. It is not a universal moral
ranking or a substitute for preregistered human-subjects research.</p>
<h2>Reproducibility</h2><pre>{{ manifest.model_dump_json(indent=2) }}</pre>
</body></html>"""


def render_reports(
    run_dir: Path,
    manifest: RunManifest,
    report: ScoreReport,
    trajectories: list[Trajectory],
) -> None:
    (run_dir / "score-report.json").write_text(
        report.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# Human Formation Benchmark report",
        "",
        f"- Run: `{manifest.run_id}`",
        f"- Model: `{manifest.model}`",
        f"- Profile: `{manifest.profile}`",
        f"- Trajectories: {report.sample_count}",
        f"- Actual cost: `${manifest.spent_usd:.6f}`",
        f"- Assurance: **{report.assurance.upper()}**",
        (
            "- Versioned lenses: "
            + (
                ", ".join(f"`{lens}@{version}`" for lens, version in manifest.lens_versions.items())
                or "none"
            )
        ),
        f"- Status: **{manifest.status.upper()}**",
        (
            f"- Completion: {len(manifest.completed_sample_ids)} / "
            f"{manifest.expected_sample_count}; failed: {len(manifest.failed_sample_ids)}"
        ),
        "",
        "## Assurance basis",
        "",
        f"- Configured judges: {', '.join(report.configured_judges) or 'none'}",
        f"- Observed judges: {', '.join(report.observed_judges) or 'none'}",
    ]
    lines.extend(f"- Downgrade reason: {reason}" for reason in report.assurance_reasons)
    for policy_id, policy in report.policy_profiles.items():
        control = " — **RESEARCH CONTROL**" if policy.research_control else ""
        lines.extend(
            [
                "",
                f"## Policy/lens: `{policy_id}`{control}",
                "",
                "| Dimension | Score | Scenario-cluster 95% interval | Clusters | Missing |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for dimension, value in policy.formation_profile.items():
            ci = policy.cluster_bootstrap_95_pct[dimension]
            score = "N/A" if value is None else f"{value:.3f}"
            interval = "N/A" if ci is None else f"[{ci[0]:.3f}, {ci[1]:.3f}]"
            lines.append(
                f"| {dimension.value} | {score} | {interval} | "
                f"{policy.scenario_cluster_count[dimension]} | "
                f"{policy.missing_scores[dimension]} |"
            )
        lines.extend(["", "### Failure gates", ""])
        lines.extend(
            f"- {name}: **{value}**" if value else f"- {name}: {value}"
            for name, value in report.failure_gates_by_policy[policy_id].model_dump().items()
        )
        lines.extend(["", "### Attributed gate hits", ""])
        policy_hits = [hit for hit in report.gate_hits if hit.policy_id == policy_id]
        lines.extend(
            (f"- **{hit.gate}** · `{hit.scenario_id}` · message {hit.message_index}: `{hit.quote}`")
            for hit in policy_hits
        )
        if not policy_hits:
            lines.append("- None.")
    lines.extend(["", "## Paired policy contrasts", ""])
    lines.extend(
        (
            f"- `{delta.policy_a}` vs `{delta.policy_b}` · {delta.dimension.value}: "
            f"{delta.mean_delta:+.3f} (n={delta.pair_count})"
        )
        for delta in report.paired_policy_deltas
    )
    if not report.paired_policy_deltas:
        lines.append("- No paired multi-policy contrasts.")
    lines.extend(["", "## Material normative disagreements", ""])
    lines.extend(f"- {item}" for item in report.normative_disagreements)
    if not report.normative_disagreements:
        lines.append("- None detected by the operational threshold.")
    lines.extend(["", "## Operational invariants", ""])
    lines.extend(f"- {item}" for item in report.invariants)
    if not report.invariants:
        lines.append("- No paired invariants met the operational threshold.")
    lines.extend(["", DISCLAIMER, "", "## Reproducibility manifest", "", "```json"])
    lines.append(manifest.model_dump_json(indent=2))
    lines.extend(["```", ""])
    (run_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")
    environment = Environment(undefined=StrictUndefined, autoescape=True)
    html = environment.from_string(HTML_TEMPLATE).render(manifest=manifest, report=report)
    (run_dir / "report.html").write_text(html, encoding="utf-8")
    with (run_dir / "scores.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "trajectory_id",
                "scenario_id",
                "policy_id",
                "dimension",
                "score",
                "confidence",
            ],
        )
        writer.writeheader()
        for trajectory in trajectories:
            for result in trajectory.judge_results:
                writer.writerow(
                    {
                        "trajectory_id": trajectory.id,
                        "scenario_id": trajectory.scenario_id,
                        "policy_id": trajectory.policy_id,
                        "dimension": result.dimension.value,
                        "score": result.score,
                        "confidence": result.confidence,
                    }
                )
    benchmark_card = {
        "schema_version": "1.0",
        "maturity": "alpha",
        "run_id": manifest.run_id,
        "model": manifest.model,
        "profile": manifest.profile,
        "scenario_count": len({item.scenario_id for item in trajectories}),
        "trajectory_count": report.sample_count,
        "unique_scenario_count": len({item.scenario_id for item in trajectories}),
        "run_status": manifest.status,
        "expected_trajectory_count": manifest.expected_sample_count,
        "completed_trajectory_count": len(manifest.completed_sample_ids),
        "failed_trajectory_count": len(manifest.failed_sample_ids),
        "configured_judges": report.configured_judges,
        "observed_judges": report.observed_judges,
        "lens_versions": manifest.lens_versions,
        "benchmark_exposure": manifest.benchmark_exposure,
        "benchmark_specific_tuning": manifest.benchmark_specific_tuning,
        "limitations": [
            "synthetic trajectories do not establish effects on real users",
            "deterministic scoring is a transparent signal, not ground truth",
            "public scenarios can be contaminated or directly optimized against",
        ],
    }
    (run_dir / "benchmark-card.json").write_text(
        json.dumps(benchmark_card, indent=2) + "\n", encoding="utf-8"
    )
