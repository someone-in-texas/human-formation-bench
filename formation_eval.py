"""Compatibility entrypoint for Inspect AI.

Prefer ``src/human_formation_benchmark/evals/formation_core.py`` in new tooling.
"""

from inspect_ai import Task, task

from human_formation_benchmark.evals.formation_core import formation_core as _formation_core


@task
def formation_core(policy: str = "default_assistant", limit: int = 24) -> Task:
    """Load the packaged formation-core task from the repository root."""

    return _formation_core(policy=policy, limit=limit)


__all__ = ["formation_core"]
