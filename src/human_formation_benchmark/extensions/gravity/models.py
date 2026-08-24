"""Strict, versioned models for the Gravity extension."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from human_formation_benchmark.models import Dimension

GRAVITY_SCHEMA_VERSION = "1.1"
GRAVITY_MODULE_VERSION = "0.1.0"
Probability = Annotated[float, Field(ge=0.0, le=1.0)]


class GravityModel(BaseModel):
    """Reject unknown data so extension assets cannot silently drift."""

    model_config = ConfigDict(extra="forbid")


class GravityConstruct(StrEnum):
    FRICTION = "formative_friction_calibration"
    COMPETENCE = "competence_transfer"
    COMMITMENT = "commitment_sovereignty"
    REALITY = "reality_contact_and_causal_stakes"
    SOCIAL = "human_social_complementarity"
    IDENTITY = "identity_resilience"
    STEWARDSHIP = "stewardship_and_shared_goods"
    DEPENDENCY = "dependency_and_exclusivity_resistance"
    APPRECIATION = "attentive_appreciation"
    TRANSFER = "formation_transfer"


class FrictionClass(StrEnum):
    FORMATIVE = "formative"
    NEUTRAL = "instrumental_but_neutral"
    ARBITRARY = "arbitrary"
    HARMFUL = "harmful_or_coercive"
    AMBIGUOUS = "ambiguous"


class GoalMode(StrEnum):
    COMPLETION = "completion"
    LEARNING = "learning"
    EXPRESSION = "expression"
    RECOVERY = "recovery"
    RELATIONSHIP = "relationship"
    GOVERNANCE = "governance"
    DECISION_SUPPORT = "decision_support"
    EMOTIONAL_PROCESSING = "emotional_processing"
    APPRECIATION = "appreciation"


class AssistanceMode(StrEnum):
    DIRECT_EXECUTOR = "direct_executor"
    TEACHER = "teacher"
    COACH = "coach"
    CRITIC = "critic"
    FACILITATOR = "facilitator"
    COMPANION = "companion"
    GOVERNOR = "governor"


class Urgency(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"


class TransferTest(StrEnum):
    AI_WITHDRAWAL = "ai_withdrawal"
    NOVEL_TASK = "novel_task"
    HUMAN_HANDOFF = "human_handoff"
    MODEL_SWITCH = "model_switch"
    ADVERSARIAL_ATTACHMENT = "adversarial_attachment"


class GravityUserState(GravityModel):
    schema_version: Literal["1.1"] = "1.1"
    skill_ownership: Probability = 0.55
    independent_action_probability: Probability = 0.60
    external_verification_probability: Probability = 0.45
    human_contact_probability: Probability = 0.50
    ai_reliance_tendency: Probability = 0.25
    ai_exclusivity_tendency: Probability = 0.05
    commitment_authorship: Probability = 0.80
    commitment_reversibility: Probability = 0.75
    identity_role_concentration: Probability = 0.70
    shared_stewardship_engagement: Probability = 0.30
    attentional_presence: Probability = 0.45
    simulation_substitution_tendency: Probability = 0.20
    challenge_capacity_match: Probability = 0.50
    material_stress: Probability = 0.40
    available_time_minutes: int = Field(default=90, ge=0, le=10_080)
    support_network_availability: Probability = 0.60
    accessibility_support_need: Probability = 0.00


class Opportunity(GravityModel):
    available: bool = True
    type: str = Field(min_length=2, max_length=80)
    session: int = Field(ge=1, le=100)


class ObservableEvent(GravityModel):
    session: int = Field(ge=1, le=100)
    event_type: Literal[
        "assistant_behavior",
        "user_action",
        "external_feedback",
        "model_outage",
        "human_opportunity",
        "transfer_task",
    ]
    description: str = Field(min_length=5, max_length=1000)
    observed: bool = True
    provenance: Literal["fixture", "deterministic_rule", "simulator", "human_review"]


class GravityScenarioPayload(GravityModel):
    module_version: Literal["0.1.0"] = "0.1.0"
    user_goal_mode: GoalMode
    requested_assistance_mode: AssistanceMode
    appropriate_assistance_modes: list[AssistanceMode] = Field(min_length=1)
    friction_classification: FrictionClass
    urgency: Urgency
    accessibility_factors: list[str] = Field(default_factory=list, max_length=8)
    external_action_opportunity: Opportunity | None = None
    human_handoff_opportunity: Opportunity | None = None
    transfer_tests: list[TransferTest] = Field(default_factory=list)
    prohibited_shortcuts: list[str] = Field(default_factory=list)
    target_constructs: list[GravityConstruct] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_values(self) -> GravityScenarioPayload:
        for field_name in (
            "appropriate_assistance_modes",
            "transfer_tests",
            "target_constructs",
        ):
            values = getattr(self, field_name)
            if len(values) != len(set(values)):
                raise ValueError(f"{field_name} must be unique")
        if self.urgency == Urgency.EMERGENCY and AssistanceMode.DIRECT_EXECUTOR not in (
            self.appropriate_assistance_modes
        ):
            raise ValueError("emergency scenarios must permit direct execution")
        return self


class GravityScenario(GravityModel):
    schema_version: Literal["1.1"] = "1.1"
    id: str = Field(pattern=r"^gravity\.[a-z0-9][a-z0-9.-]+$")
    title: str = Field(min_length=3, max_length=200)
    review_status: Literal[
        "author_draft",
        "internal_multi_agent_reviewed",
        "independent_reviewed",
        "community_reviewed",
    ]
    review_scope: list[str] = Field(min_length=1)
    reviewer_type: Literal["author", "internal_agent", "external_expert", "affected_community"]
    reviewer_provenance: list[str] = Field(min_length=1)
    domain: str = Field(min_length=2, max_length=80)
    stakes: Literal["low", "medium", "high", "critical"]
    synthetic: Literal[True] = True
    sensitive_domain: bool = False
    user_opening: str = Field(min_length=10, max_length=10_000)
    initial_state: GravityUserState
    gravity: GravityScenarioPayload
    core_dimensions: list[Dimension] = Field(min_length=1)
    external_events: list[ObservableEvent] = Field(default_factory=list)
    positive_indicators: list[str] = Field(min_length=2)
    failure_modes: list[str] = Field(min_length=2)
    source_provenance: list[str] = Field(min_length=1)
    license_review: str = Field(min_length=5)

    @model_validator(mode="after")
    def consistent_schedule(self) -> GravityScenario:
        sessions = {event.session for event in self.external_events}
        for opportunity in (
            self.gravity.external_action_opportunity,
            self.gravity.human_handoff_opportunity,
        ):
            if opportunity and opportunity.available and opportunity.session not in sessions:
                raise ValueError("available opportunities require a scheduled event")
        if (
            self.gravity.accessibility_factors
            and self.initial_state.accessibility_support_need == 0
        ):
            raise ValueError(
                "declared accessibility factors require a nonzero accessibility support need"
            )
        if self.review_status == "independent_reviewed" and self.reviewer_type != "external_expert":
            raise ValueError("independent review requires external-expert provenance")
        if (
            self.review_status == "community_reviewed"
            and self.reviewer_type != "affected_community"
        ):
            raise ValueError("community review requires affected-community provenance")
        return self


class GravityRubric(GravityModel):
    schema_version: Literal["1.1"] = "1.1"
    id: str = Field(pattern=r"^gravity\.[a-z0-9_]+$")
    gravity_construct: GravityConstruct = Field(alias="construct", serialization_alias="construct")
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    operational_definition: str
    positive_indicators: list[str] = Field(min_length=2)
    negative_indicators: list[str] = Field(min_length=2)
    subtle_failures: list[str] = Field(min_length=1)
    contraindications: list[str] = Field(min_length=1)
    cultural_accessibility_caveats: list[str] = Field(min_length=1)
    minimal_pairs: list[str] = Field(min_length=1)
    evidence_requirements: list[str] = Field(min_length=1)
    not_applicable_rule: str
    insufficient_evidence_rule: str
    source_mapping: list[str] = Field(min_length=1)
    score_anchors: dict[Literal["0", "1", "2", "3", "4"], str]
    changelog: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_anchors(self) -> GravityRubric:
        if set(self.score_anchors) != {"0", "1", "2", "3", "4"}:
            raise ValueError("rubric requires observable anchors 0 through 4")
        return self


class EvidenceSpan(GravityModel):
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    quote: str = Field(min_length=1, max_length=280)

    @model_validator(mode="after")
    def valid_span(self) -> EvidenceSpan:
        if self.end <= self.start:
            raise ValueError("evidence end must follow start")
        return self


class GravitySignal(GravityModel):
    signal_id: str = Field(pattern=r"^gravity\.[a-z0-9_]+$")
    polarity: Literal["supportive", "risk", "adjudication_required", "context"]
    precision: Literal["exact_pattern"]
    evidence: EvidenceSpan
    rule_version: str
    note: str


class GravityGates(GravityModel):
    coercive_self_binding: bool = False
    assistant_as_unreviewable_governor: bool = False
    consent_bypass: bool = False
    unsafe_commitment: bool = False
    exclusivity_language: bool = False
    exit_guilt: bool = False
    human_support_displacement: bool = False
    dependency_for_retention: bool = False
    emergency_delay_for_formation: bool = False
    accessibility_need_ignored: bool = False
    formation_paternalism: bool = False


class SignalReport(GravityModel):
    schema_version: Literal["1.1"] = "1.1"
    detector_version: str
    signals: list[GravitySignal]
    detector_hits: GravityGates
    ordinal_score: Literal[None] = None
    interpretation: Literal["triage_only_not_a_semantic_or_psychometric_judgment"] = (
        "triage_only_not_a_semantic_or_psychometric_judgment"
    )


class TransferObservation(GravityModel):
    test: TransferTest
    event_id: str
    occurred: bool
    success: bool | None = None
    evidence: str | None = Field(default=None, max_length=1000)
    signal_provenance: list[str] = Field(default_factory=list)
    contraindications_reviewed: bool = False

    @model_validator(mode="after")
    def success_requires_event(self) -> TransferObservation:
        if self.success is not None and not self.occurred:
            raise ValueError("transfer success cannot be reported without an event")
        if self.success is not None and (
            self.evidence is None
            or not self.signal_provenance
            or not self.contraindications_reviewed
        ):
            raise ValueError(
                "transfer outcomes require evidence, signal provenance, and contraindication review"
            )
        return self


class GravityTransferResult(GravityModel):
    schema_version: Literal["1.1"] = "1.1"
    scenario_id: str
    transition_version_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    transfer_version_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    observations: list[TransferObservation] = Field(min_length=1)
    unaided_task_success: Probability | None = None
    external_verification_use: Probability | None = None
    human_handoff_success: Probability | None = None
    workflow_portability: Probability | None = None
    commitment_self_authorship_retained: Probability | None = None
    reassurance_independence: Probability | None = None
    evidence_count: int = Field(ge=0)
    synthetic_outcome: Literal[True] = True


class GravityProfile(GravityModel):
    schema_version: Literal["1.1"] = "1.1"
    id: Literal["gravity_micro", "gravity_small", "gravity_standard", "gravity_research"]
    scenario_limit: int = Field(gt=0)
    seeds: list[int] = Field(min_length=1)
    trajectory_turns: int = Field(gt=0)
    transfer_evaluations: int = Field(ge=0)
    judges: list[str] = Field(min_length=1)
    include_research_controls: bool = False
    requires_explicit_budget: bool
    default_budget_usd: float | None = Field(default=None, gt=0)
    assurance: Literal["smoke", "illustrative", "moderate", "research_candidate"]
    limitations: list[str] = Field(min_length=1)


class GravityScoreObservation(GravityModel):
    gravity_construct: GravityConstruct = Field(alias="construct", serialization_alias="construct")
    raw_score: int | None = Field(default=None, ge=0, le=4)
    confidence: Probability
    evidence: list[str] = Field(default_factory=list)
    scenario_id: str | None = None
    rubric_id: str | None = None
    rubric_version_hash: str | None = Field(default=None, pattern=r"^sha256:[0-9a-f]{64}$")
    judge_id: str | None = None
    judgment_status: Literal["uncalibrated_experimental_judgment"] | None = None
    insufficient_evidence: bool = False
    not_applicable: bool = False

    @model_validator(mode="after")
    def missing_is_explicit(self) -> GravityScoreObservation:
        if self.raw_score is None and not (self.insufficient_evidence or self.not_applicable):
            raise ValueError("missing rubric judgment requires an explicit reason")
        if self.raw_score is not None and (
            not self.evidence
            or self.scenario_id is None
            or self.rubric_id is None
            or self.rubric_version_hash is None
            or self.judge_id is None
            or self.judgment_status is None
        ):
            raise ValueError(
                "ordinal judgments require evidence, scenario, rubric hash, judge, and status"
            )
        return self


class GravityReportArtifact(GravityModel):
    schema_version: Literal["1.1"] = "1.1"
    module_version: Literal["0.1.0"] = "0.1.0"
    experimental_status: Literal[
        "synthetic_behavioral_benchmark_not_clinical_or_psychometric_measure"
    ] = "synthetic_behavioral_benchmark_not_clinical_or_psychometric_measure"
    construct_profile: dict[GravityConstruct, float | None]
    raw_observations: list[GravityScoreObservation]
    detector_hits_by_policy: dict[str, GravityGates]
    run_detector_hit_union: GravityGates
    transfer: GravityTransferResult | None = None
    canonical_composite: Literal[False] = False
    ordinal_profile_status: Literal["unavailable_pending_calibrated_judgment"] = (
        "unavailable_pending_calibrated_judgment"
    )
    limitations: list[str] = Field(min_length=1)


class GravityManifest(GravityModel):
    schema_version: Literal["1.1"] = "1.1"
    id: Literal["gravity"]
    title: str
    version: Literal["0.1.0"]
    status: Literal["experimental"]
    canonical_composite: Literal[False]
    requires_longitudinal_support: Literal[True]
    research_controls_available: Literal[True]
    experimental_notice: str
    license: Literal["Apache-2.0"]
    synthetic_data_only: Literal[True]
    copyrighted_scale_items: Literal[False]


class VersionedMethod(GravityModel):
    version: str


class TransitionParameters(VersionedMethod):
    bounded: Literal[True]
    interpretation: Literal["experimental_simulation_parameters_not_human_causal_effects"]


class TransferProtocolConfig(VersionedMethod):
    success_requires_observed_event: Literal[True]


class SignalConfig(VersionedMethod):
    output: Literal["attributable_triage_signals_not_ordinal_scores"]


class ControlConfig(GravityModel):
    explicit_opt_in_required: Literal[True]
    production_adapters_must_refuse: Literal[True]


class GravityConfig(GravityModel):
    schema_version: Literal["1.1"] = "1.1"
    module_version: Literal["0.1.0"]
    transition_parameters: TransitionParameters
    transfer_protocol: TransferProtocolConfig
    deterministic_signals: SignalConfig
    controls: ControlConfig
