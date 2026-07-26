"""Inspect-native behavioral probe task.

Run from a source checkout:
    inspect eval src/human_formation_benchmark/evals/formation_core.py -M model=mockllm/model
"""

from __future__ import annotations

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import Score, Scorer, Target, mean, scorer, stderr
from inspect_ai.solver import TaskState, generate, system_message

from human_formation_benchmark.config import load_named_config, load_scenarios
from human_formation_benchmark.models import Dimension
from human_formation_benchmark.scoring import deterministic_score


@scorer(metrics=[mean(), stderr()])
def formation_signal() -> Scorer:
    async def score(state: TaskState, target: Target) -> Score:
        del target
        metadata_dimensions = state.metadata.get("dimensions", [])
        dimensions = [Dimension(item) for item in metadata_dimensions]
        results = deterministic_score(
            state.output.completion,
            dimensions,
            message_index=len(state.messages) - 1,
        )
        values = [result.score for result in results if result.score is not None]
        value = sum(values) / (4 * len(values)) if values else 0.0
        return Score(
            value=value,
            answer=state.output.completion[:280],
            explanation=(
                "Mean of transparent HFB deterministic dimension signals. "
                "This is not a validated ground-truth formation score."
            ),
            metadata={"dimension_results": [result.model_dump(mode="json") for result in results]},
        )

    return score


@task
def formation_core(policy: str = "default_assistant", limit: int = 24) -> Task:
    scenarios = load_scenarios()[:limit]
    policy_config = load_named_config("policies", policy)
    samples = [
        Sample(
            id=scenario.id,
            input=scenario.user_opening,
            target="formation-supportive observable behavior",
            metadata={
                "scenario_id": scenario.id,
                "domain": scenario.domain,
                "dimensions": [dimension.value for dimension in scenario.dimensions],
            },
        )
        for scenario in scenarios
    ]
    return Task(
        dataset=samples,
        solver=[
            system_message(policy_config["system_prompt"]),
            generate(),
        ],
        scorer=formation_signal(),
        name="hfb_formation_core",
        version="1.0.0",
    )
