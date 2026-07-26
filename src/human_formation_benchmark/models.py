"""Versioned, validation-first data models used throughout HFB."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SCHEMA_VERSION = "1.0"


class StrictModel(BaseModel):
    """Base model that rejects accidental schema drift."""

    model_config = ConfigDict(extra="forbid")


class Dimension(StrEnum):
    TRUTH = "truth_epistemic_integrity"
    HUMILITY = "intellectual_humility"
    AGENCY = "agency_support"
    COMPETENCE = "competence_retention"
    RELATEDNESS = "human_relatedness"
    DEPENDENCY = "dependency_boundary_quality"
    REALITY = "reality_contact"
    MORAL = "moral_responsibility"
    EMPATHY = "empathy_perspective_taking"
    CONSENT = "consent_non_coercion"
    STEWARDSHIP = "stewardship_non_domination"
    OPTIONS = "option_stewardship"
    GOVERNANCE = "human_standing_governance"
    PLURALISM = "pluralism_worldview_integrity"
    ATTENTION = "attention_wireheading_resistance"
    CONSISTENCY = "long_horizon_consistency"


class TrajectoryLength(StrEnum):
    SINGLE_TURN = "single_turn"
    SHORT = "short"
    MEDIUM = "medium"
    LONGITUDINAL = "longitudinal"


class EvidenceSpan(StrictModel):
    message_index: int = Field(ge=0)
    quote: str = Field(min_length=1, max_length=280)


class Message(StrictModel):
    schema_version: str = SCHEMA_VERSION
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=100_000)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Scenario(StrictModel):
    schema_version: str = SCHEMA_VERSION
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]+$")
    title: str = Field(min_length=3, max_length=200)
    domain: str
    stakes: Literal["low", "medium", "high", "critical"]
    reversibility: Literal["high", "medium", "low", "irreversible"]
    vulnerability: Literal["low", "medium", "high"]
    required_expertise: list[str] = Field(default_factory=list)
    affected_parties: list[str] = Field(default_factory=list)
    consent_structure: str
    uncertainty: Literal["low", "medium", "high"]
    social_context: str
    worldview_salience: Literal["low", "medium", "high"]
    dependency_risk: Literal["low", "medium", "high"]
    persuasion_risk: Literal["low", "medium", "high"]
    trajectory_length: TrajectoryLength
    prohibited_shortcuts: list[str] = Field(default_factory=list)
    dimensions: list[Dimension] = Field(min_length=1)
    source_provenance: list[str] = Field(default_factory=list)
    scenario_version: str = "1.0.0"
    user_opening: str = Field(min_length=10, max_length=10_000)
    follow_ups: list[str] = Field(default_factory=list)
    positive_indicators: list[str] = Field(default_factory=list)
    failure_modes: list[str] = Field(default_factory=list)
    control_label: Literal["positive", "negative", "ambiguous", "adversarial"] | None = None
    approved_for_public_core: bool = False

    @field_validator("dimensions")
    @classmethod
    def dimensions_are_unique(cls, value: list[Dimension]) -> list[Dimension]:
        if len(value) != len(set(value)):
            raise ValueError("scenario dimensions must be unique")
        return value


class Persona(StrictModel):
    schema_version: str = SCHEMA_VERSION
    id: str
    confidence: float = Field(ge=0, le=1)
    uncertainty_tolerance: float = Field(ge=0, le=1)
    social_support: float = Field(ge=0, le=1)
    directiveness_preference: float = Field(ge=0, le=1)
    prior_ai_trust: float = Field(ge=0, le=1)
    attachment_tendency: float = Field(ge=0, le=1)
    expertise: float = Field(ge=0, le=1)
    digital_literacy: float = Field(ge=0, le=1)
    conflict_style: str
    worldview: str
    institutional_trust: float = Field(ge=0, le=1)
    urgency: float = Field(ge=0, le=1)
    counsel_willingness: float = Field(ge=0, le=1)


class UserState(StrictModel):
    schema_version: str = SCHEMA_VERSION
    self_directed_action_probability: float = Field(0.55, ge=0, le=1)
    decision_outsourcing_tendency: float = Field(0.30, ge=0, le=1)
    uncertainty_tolerance: float = Field(0.40, ge=0, le=1)
    reassurance_seeking: float = Field(0.60, ge=0, le=1)
    evidence_checking: float = Field(0.45, ge=0, le=1)
    human_contact_probability: float = Field(0.50, ge=0, le=1)
    ai_exclusivity_tendency: float = Field(0.10, ge=0, le=1)
    independent_attempt_probability: float = Field(0.60, ge=0, le=1)
    retained_skill: float = Field(0.52, ge=0, le=1)
    willingness_to_use_guardrails: float = Field(0.50, ge=0, le=1)
    domination_preference: float = Field(0.15, ge=0, le=1)


class Rubric(StrictModel):
    schema_version: str = SCHEMA_VERSION
    id: str
    dimension: Dimension
    version: str
    construct_claim: str
    positive_indicators: list[str] = Field(min_length=2)
    failure_modes: list[str] = Field(min_length=2)
    edge_cases: list[str] = Field(min_length=1)
    examples: list[str] = Field(min_length=1)
    sources: list[str] = Field(min_length=1)


class Policy(StrictModel):
    schema_version: str = SCHEMA_VERSION
    id: str
    description: str
    system_prompt: str
    production_safe: bool
    research_control: bool = False


class Constitution(StrictModel):
    schema_version: str = SCHEMA_VERSION
    id: str
    thin_floor: list[str]
    commitments: list[str]
    research_control: bool = False


class JudgeResult(StrictModel):
    schema_version: str = SCHEMA_VERSION
    dimension: Dimension
    score: int | None = Field(default=None, ge=0, le=4)
    confidence: float = Field(ge=0, le=1)
    evidence: list[EvidenceSpan] = Field(default_factory=list)
    flags: list[str] = Field(default_factory=list)
    rationale: str = Field(max_length=2_000)
    insufficient_evidence: bool = False
    not_applicable: bool = False
    judge_id: str = "deterministic-v1"

    @model_validator(mode="after")
    def missing_score_must_be_explained(self) -> JudgeResult:
        if self.score is None and not (self.insufficient_evidence or self.not_applicable):
            raise ValueError("missing score requires insufficient_evidence or not_applicable")
        return self


class TokenUsage(StrictModel):
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)


class ProviderResponse(StrictModel):
    text: str
    usage: TokenUsage
    latency_ms: float = Field(ge=0)
    cost_usd: float = Field(ge=0)
    provider_request_id: str | None = None


class Trajectory(StrictModel):
    schema_version: str = SCHEMA_VERSION
    id: str
    scenario_id: str
    policy_id: str
    model_id: str
    seed: int
    messages: list[Message]
    initial_state: UserState
    final_state: UserState
    judge_results: list[JudgeResult]
    cost_usd: float = Field(ge=0)
    latency_ms: float = Field(ge=0)
    errors: list[str] = Field(default_factory=list)


class PriceEntry(StrictModel):
    provider: str
    model_pattern: str
    input_per_million_usd: float = Field(ge=0)
    cached_input_per_million_usd: float | None = Field(default=None, ge=0)
    output_per_million_usd: float = Field(ge=0)
    currency: str = "USD"
    effective_date: str
    source_url: str
    last_verified_date: str


class RunProfile(StrictModel):
    schema_version: str = SCHEMA_VERSION
    id: str
    scenario_limit: int = Field(gt=0)
    policies: list[str] = Field(min_length=1)
    seeds: list[int] = Field(min_length=1)
    judges: list[str] = Field(min_length=1)
    trajectory_turns: int = Field(gt=0)
    max_input_tokens: int = Field(gt=0)
    max_output_tokens: int = Field(gt=0)
    concurrency: int = Field(gt=0)
    rpm: int = Field(gt=0)
    tpm: int = Field(gt=0)
    default_budget_usd: float | None = Field(default=None, gt=0)
    requires_explicit_budget: bool = False
    assurance: Literal["low", "moderate", "research"]


class CostEstimate(StrictModel):
    schema_version: str = SCHEMA_VERSION
    profile: str
    samples: int = Field(ge=0)
    calls: int = Field(ge=0)
    estimated_input_tokens: int = Field(ge=0)
    estimated_output_tokens: int = Field(ge=0)
    low_usd: float = Field(ge=0)
    base_usd: float = Field(ge=0)
    high_usd: float = Field(ge=0)
    budget_usd: float = Field(gt=0)
    price_data_stale: bool
    assumptions: list[str]


class FailureGates(StrictModel):
    exclusivity_language: bool = False
    covert_persuasion: bool = False
    severe_reality_distortion: bool = False
    human_veto_bypass: bool = False


class ScoreReport(StrictModel):
    schema_version: str = SCHEMA_VERSION
    formation_profile: dict[Dimension, float | None]
    bootstrap_95_pct: dict[Dimension, tuple[float, float] | None]
    failure_gates: FailureGates
    judge_agreement: dict[str, float | None]
    sample_count: int
    missing_scores: dict[Dimension, int]
    assurance: str


class RunManifest(StrictModel):
    schema_version: str = SCHEMA_VERSION
    run_id: str
    status: Literal["planned", "running", "interrupted", "completed", "failed", "budget_exhausted"]
    created_at: datetime
    updated_at: datetime
    profile: str
    model: str
    judge_models: list[str]
    policies: list[str]
    seeds: list[int]
    scenario_pack_hash: str
    config_hash: str
    git_commit: str
    package_version: str
    python_version: str
    operating_system: str
    budget_usd: float
    hard_stop: bool
    reserve_fraction: float
    spent_usd: float = 0
    completed_sample_ids: list[str] = Field(default_factory=list)
    failed_sample_ids: list[str] = Field(default_factory=list)
    shard_index: int = 0
    shards: int = 1
    redacted_environment: dict[str, str] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


class ScenarioPackManifest(StrictModel):
    schema_version: str = SCHEMA_VERSION
    pack_id: str
    version: str
    license: str = "CC-BY-4.0"
    canonical: bool
    human_approved: bool
    scenario_ids: list[str]
    content_hash: str
    generated_at: datetime


class ReviewFinding(StrictModel):
    id: str
    severity: Literal["Critical", "High", "Medium", "Low", "Note"]
    title: str
    evidence: list[dict[str, Any]]
    why_it_matters: str
    required_change: str
    acceptance_test: str


def dump_json(model: BaseModel, path: Path) -> None:
    """Write a Pydantic model as deterministic, human-readable JSON."""

    path.write_text(model.model_dump_json(indent=2, exclude_none=False) + "\n", encoding="utf-8")
