"""Formation-transfer result construction and versioning."""

from __future__ import annotations

from human_formation_benchmark.hashing import content_hash

from .models import GravityTransferResult, TransferObservation
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
    scenario_id: str,
    observations: list[TransferObservation],
    **proxies: float | int | None,
) -> GravityTransferResult:
    """Build a synthetic transfer result with full protocol hashes."""

    return GravityTransferResult(
        scenario_id=scenario_id,
        transition_version_hash=TRANSITION_VERSION_HASH,
        transfer_version_hash=TRANSFER_VERSION_HASH,
        observations=observations,
        evidence_count=sum(item.evidence is not None for item in observations),
        **proxies,
    )
