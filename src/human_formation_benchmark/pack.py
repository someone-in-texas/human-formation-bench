"""Scenario-pack validation and content hashing."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from .config import load_scenarios, load_yaml
from .hashing import content_hash
from .models import Scenario, ScenarioPackManifest
from .security import contains_sensitive_data


def validate_pack(
    path: Path | None = None, *, require_public_approval: bool | None = None
) -> list[Scenario]:
    public = path is None if require_public_approval is None else require_public_approval
    if path is None:
        scenarios = load_scenarios()
    else:
        payload = load_yaml(path)
        scenarios = [Scenario.model_validate(item) for item in payload["scenarios"]]
    ids = [scenario.id for scenario in scenarios]
    if len(ids) != len(set(ids)):
        raise ValueError("scenario IDs must be unique")
    for scenario in scenarios:
        serialized = scenario.model_dump_json()
        if contains_sensitive_data(serialized):
            raise ValueError(f"possible secret or PII in scenario {scenario.id}")
        if public and not scenario.approved_for_public_core:
            raise ValueError(f"public pack scenario lacks human approval: {scenario.id}")
    return scenarios


def pack_hash(path: Path | None = None) -> str:
    scenarios = validate_pack(path)
    return content_hash([scenario.model_dump(mode="json") for scenario in scenarios])


def build_manifest(
    path: Path | None = None,
    *,
    pack_id: str | None = None,
    version: str | None = None,
) -> ScenarioPackManifest:
    payload = load_yaml(path) if path is not None else {}
    canonical = path is None
    scenarios = validate_pack(path, require_public_approval=canonical)
    return ScenarioPackManifest(
        pack_id=pack_id or payload.get("pack_id", "hfb-private-extension"),
        version=version or payload.get("pack_version", "0.1.0"),
        canonical=canonical,
        human_approved=False,
        disclosure="public" if canonical else "private",
        scenario_ids=[scenario.id for scenario in scenarios],
        content_hash=content_hash([scenario.model_dump(mode="json") for scenario in scenarios]),
        generated_at=datetime.now(UTC),
    )
