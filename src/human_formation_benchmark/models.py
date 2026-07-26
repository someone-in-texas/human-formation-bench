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
    included_content: list[str] = Field(min_length=1)
    excluded_content: list[str] = Field(min_length=1)
    neighboring_constructs: list[Dimension] = Field(min_length=1)
    score_anchors: dict[str, str]
    missingness_rules: dict[str, str]
    cultural_risks: list[str] = Field(min_length=1)
    source_use: str
    license_review: str

    @field_validator("score_anchors")
    @classmethod
    def anchors_cover_ordinal_scale(cls, value: dict[str, str]) -> dict[str, str]:
        if set(value) != {"0", "1", "2", "3", "4"}:
            raise ValueError("rubric must define behavioral anchors for scores 0 through 4")
        return value

    @field_validator("missingness_rules")
    @classmethod
    def missingness_is_explicit(cls, value: dict[str, str]) -> dict[str, str]:
        if set(value) != {"insufficient_evidence", "not_applicable"}:
            raise ValueError("rubric must distinguish insufficient evidence from not applicable")
        return value


class Policy(StrictModel):
    schema_version: str = SCHEMA_VERSION
    id: str
    description: str
    system_prompt: str
    production_safe: bool
    research_control: bool = False
    lens_id: str | None = None


class Constitution(StrictModel):
    schema_version: str = SCHEMA_VERSION
    id: str
    thin_floor_version: str | None = None
    thin_floor: list[str] = Field(default_factory=list)
    commitments: list[str]
    research_control: bool = False
    contested_interpretations: list[str] = Field(default_factory=list)


class WorldviewLens(StrictModel):
    """Versioned self-description kept distinct from thin-floor evaluation."""

    schema_version: str = SCHEMA_VERSION
    id: str
    version: str
    perspective: str = Field(pattern=r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
    self_description: str
    commitments: list[str] = Field(min_length=2)
    characteristic_reasons: list[str] = Field(min_length=2)
    internal_disagreements: list[str] = Field(min_length=1)
    prohibited_caricatures: list[str] = Field(min_length=1)
    lens_specific_expectations: list[str] = Field(min_length=2)
    sources: list[str] = Field(min_length=1)
    source_license_review: str
    interpretive_authority: str
    reviewer_provenance: list[str] = Field(min_length=1)
    validation_status: Literal["author_draft", "independent_reviewed", "community_reviewed"]


class PerspectiveContrast(StrictModel):
    id: str
    perspective: str = Field(pattern=r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
    role: Literal["positive", "adversarial"]
    shared_choice: str
    mechanism: str
    user_opening: str
    exemplar_response: str
    dimensions: list[Dimension] = Field(min_length=1)
    reviewed_scores: dict[Dimension, int] = Field(min_length=1)
    reviewer_rationale: str
    acceptable_rationales: list[str] = Field(min_length=1)
    prohibited_caricatures: list[str] = Field(min_length=1)
    reviewer_status: Literal["author_draft", "independent_reviewed"]
    reviewer_provenance: list[str] = Field(min_length=1)


class AdversarialChallenge(StrictModel):
    id: str
    attack_family: str
    response: str
    expected_max_score: int = Field(ge=0, le=4)
    expected_gate: str | None = None
    expected_flags: list[str] = Field(default_factory=list)
    private_rotation_required: bool = True


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
    state_evidence_status: Literal["scorer_derived_diagnostic_not_outcome"] = (
        "scorer_derived_diagnostic_not_outcome"
    )
    judge_results: list[JudgeResult]
    failure_gates: FailureGates | None = None
    gate_hits: list[GateHit] = Field(default_factory=list)
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
    practical_domination: bool = False


class GateHit(StrictModel):
    policy_id: str
    trajectory_id: str
    scenario_id: str
    message_index: int = Field(ge=0)
    gate: Literal[
        "exclusivity_language",
        "covert_persuasion",
        "severe_reality_distortion",
        "human_veto_bypass",
        "practical_domination",
    ]
    quote: str = Field(min_length=1, max_length=280)


class ScoreReport(StrictModel):
    schema_version: str = SCHEMA_VERSION
    formation_profile: dict[Dimension, float | None] | None
    bootstrap_95_pct: dict[Dimension, tuple[float, float] | None] | None
    policy_profiles: dict[str, PolicyScoreProfile] = Field(default_factory=dict)
    paired_policy_deltas: list[PairedPolicyDelta] = Field(default_factory=list)
    normative_disagreements: list[str] = Field(default_factory=list)
    invariants: list[str] = Field(default_factory=list)
    failure_gates: FailureGates | None
    failure_gates_by_policy: dict[str, FailureGates] = Field(default_factory=dict)
    gate_hits: list[GateHit] = Field(default_factory=list)
    judge_agreement: dict[str, float | None]
    observed_judges: list[str] = Field(default_factory=list)
    configured_judges: list[str] = Field(default_factory=list)
    sample_count: int
    missing_scores: dict[Dimension, int]
    assurance: str
    assurance_reasons: list[str] = Field(default_factory=list)


class PolicyScoreProfile(StrictModel):
    """One policy/lens estimand, clustered at the scenario level."""

    formation_profile: dict[Dimension, float | None]
    cluster_bootstrap_95_pct: dict[Dimension, tuple[float, float] | None]
    scenario_cluster_count: dict[Dimension, int]
    observation_count: dict[Dimension, int]
    missing_scores: dict[Dimension, int]
    research_control: bool = False


class PairedPolicyDelta(StrictModel):
    """A within-scenario/seed contrast; positive means policy_a scored higher."""

    policy_a: str
    policy_b: str
    dimension: Dimension
    mean_delta: float
    pair_count: int


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
    scenario_pack_id: str = "hfb-public-core"
    scenario_pack_canonical: bool = True
    scenario_pack_disclosure: Literal["public", "private"] = "public"
    benchmark_exposure: Literal[
        "not_provided", "public_seen", "public_tuned", "private_unseen", "mixed"
    ] = "not_provided"
    benchmark_specific_tuning: bool | None = None
    lens_versions: dict[str, str] = Field(default_factory=dict)
    config_hash: str
    run_family_hash: str
    git_commit: str
    package_version: str
    python_version: str
    operating_system: str
    budget_usd: float
    hard_stop: bool
    reserve_fraction: float
    spent_usd: float = 0
    expected_sample_count: int = 0
    completed_sample_ids: list[str] = Field(default_factory=list)
    trajectory_hashes: dict[str, str] = Field(default_factory=dict)
    failed_sample_ids: list[str] = Field(default_factory=list)
    shard_index: int = 0
    shards: int = 1
    redacted_environment: dict[str, str] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


class ExtensionRunManifest(RunManifest):
    """Run manifest v1.1 with required extension provenance."""

    schema_version: Literal["1.1"] = "1.1"
    extension_id: str = Field(pattern=r"^[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*$")
    extension_version: str = Field(pattern=r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
    extension_fingerprint: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")


class ScenarioPackManifest(StrictModel):
    schema_version: str = SCHEMA_VERSION
    pack_id: str
    version: str
    license: str = "CC-BY-4.0"
    canonical: bool
    human_approved: bool
    disclosure: Literal["public", "private"] = "public"
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
