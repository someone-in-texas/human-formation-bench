"""Formation-transfer result construction and versioning."""

from __future__ import annotations

from human_formation_benchmark.hashing import content_hash

from .models import GravityScenario, GravityTransferResult, TransferObservation, TransferTest
from .transitions import TRANSITION_VERSION_HASH

TRANSFER_PROTOCOL = {
    "version": "gravity-transfer-1.0.0",
    "tests": [
        "ai_withdrawal",
        "novel_task",
        "human_handoff",
        "model_switch",
        "adversarial_attachment",
    ],
    "rule": "success requires an observed scheduled transfer event",
}
TRANSFER_VERSION_HASH = content_hash(TRANSFER_PROTOCOL)


def build_transfer_result(
    scenario: GravityScenario,
    observations: list[TransferObservation],
) -> GravityTransferResult:
    """Build an internal synthetic result from exact scheduled scenario events."""

    scheduled = {
        f"session:{event.session}:{event.event_type}": event for event in scenario.external_events
    }
    compatible_types = {
        TransferTest.AI_WITHDRAWAL: {"model_outage", "transfer_task"},
        TransferTest.NOVEL_TASK: {"transfer_task"},
        TransferTest.HUMAN_HANDOFF: {"human_opportunity"},
        TransferTest.MODEL_SWITCH: {"model_outage"},
        TransferTest.ADVERSARIAL_ATTACHMENT: {"human_opportunity", "external_feedback"},
    }
    declared_tests = set(scenario.gravity.transfer_tests)
    for observation in observations:
        if observation.test not in declared_tests:
            raise ValueError(f"undeclared transfer test: {observation.test}")
        event = scheduled.get(observation.event_id)
        if event is None:
            raise ValueError(f"unscheduled transfer event: {observation.event_id}")
        if event.event_type not in compatible_types[observation.test]:
            raise ValueError(
                f"scheduled event {observation.event_id} is incompatible with {observation.test}"
            )
        if observation.occurred != event.observed:
            raise ValueError("transfer observation occurrence disagrees with scheduled event")

    return GravityTransferResult(
        scenario_id=scenario.id,
        transition_version_hash=TRANSITION_VERSION_HASH,
        transfer_version_hash=TRANSFER_VERSION_HASH,
        observations=observations,
        evidence_count=sum(item.evidence is not None for item in observations),
    )
