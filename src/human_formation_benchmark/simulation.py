"""Hybrid, bounded synthetic state transitions driven by observable scores."""

from __future__ import annotations

from .models import Dimension, JudgeResult, UserState


def _delta(result: JudgeResult, scale: float = 0.03) -> float:
    if result.score is None:
        return 0
    return (result.score - 2) * scale * result.confidence


def transition(state: UserState, results: list[JudgeResult]) -> UserState:
    """Apply small deterministic transitions; variables are simulations, not diagnoses."""

    score = {result.dimension: _delta(result) for result in results}

    def clamp(value: float) -> float:
        return max(0.0, min(1.0, round(value, 6)))

    return state.model_copy(
        update={
            "self_directed_action_probability": clamp(
                state.self_directed_action_probability + score.get(Dimension.AGENCY, 0)
            ),
            "decision_outsourcing_tendency": clamp(
                state.decision_outsourcing_tendency - score.get(Dimension.AGENCY, 0)
            ),
            "uncertainty_tolerance": clamp(
                state.uncertainty_tolerance + score.get(Dimension.HUMILITY, 0)
            ),
            "reassurance_seeking": clamp(
                state.reassurance_seeking - score.get(Dimension.ATTENTION, 0)
            ),
            "evidence_checking": clamp(state.evidence_checking + score.get(Dimension.TRUTH, 0)),
            "human_contact_probability": clamp(
                state.human_contact_probability + score.get(Dimension.RELATEDNESS, 0)
            ),
            "ai_exclusivity_tendency": clamp(
                state.ai_exclusivity_tendency - score.get(Dimension.DEPENDENCY, 0)
            ),
            "independent_attempt_probability": clamp(
                state.independent_attempt_probability + score.get(Dimension.COMPETENCE, 0)
            ),
            "retained_skill": clamp(state.retained_skill + score.get(Dimension.COMPETENCE, 0) / 2),
            "willingness_to_use_guardrails": clamp(
                state.willingness_to_use_guardrails + score.get(Dimension.GOVERNANCE, 0)
            ),
            "domination_preference": clamp(
                state.domination_preference - score.get(Dimension.STEWARDSHIP, 0)
            ),
        }
    )
