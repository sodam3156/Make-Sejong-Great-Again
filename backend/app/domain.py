"""RainFlow Sejong API domain models.

The frozen contract lives in ``contracts/rainflow.schema.json``.  These
Pydantic models describe the same required fields for FastAPI/OpenAPI while
allowing additive optional fields, as required by the Day 1 freeze decision.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class ScenarioId(str, Enum):
    DRY_BASE = "dry_base"
    RAIN_SPILLBACK_A = "rain_spillback_a"
    RAIN_SPILLBACK_B = "rain_spillback_b"


class PolicyId(str, Enum):
    NO_ACTION = "no_action"
    FIXED_METERING = "fixed_metering"
    CORRIDOR_GATING = "corridor_gating"


class ResultSource(str, Enum):
    LIVE = "live_simulation"
    CACHED = "cached_simulation"
    FIXTURE = "fixture"


class DataQualityInput(ContractModel):
    """Synthetic input quality snapshot rechecked immediately before approval."""

    data_age_sec: float = Field(default=0, ge=0)
    sensor_available: bool = True
    device_status: Literal["ok", "degraded", "fault"] = "ok"


class SimulationRequest(ContractModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "examples": [
                {
                    "scenario_id": "rain_spillback_a",
                    "seed": 42,
                    "data_quality": {
                        "data_age_sec": 0,
                        "sensor_available": True,
                        "device_status": "ok",
                    },
                    "dataset_id": "synthetic-v0",
                    "force_source": "auto",
                }
            ]
        },
    )
    scenario_id: ScenarioId = Field(
        default=ScenarioId.RAIN_SPILLBACK_A,
        examples=["rain_spillback_a"],
    )
    seed: int = Field(default=42, ge=0, le=2_147_483_647)
    data_quality: DataQualityInput = Field(default_factory=DataQualityInput)
    dataset_id: Literal["synthetic-v0"] = "synthetic-v0"
    force_source: Literal["auto", "live_simulation", "cached_simulation", "fixture"] = "auto"


class ApprovalRequest(ContractModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "examples": [
                {
                    "run_id": "live-rain_spillback_a-s42-ed95c7ae49",
                    "policy_id": "corridor_gating",
                    "decision": "approve",
                    "operator": "demo_operator",
                    "reason": "가드 통과 후보 중 안전 점수가 가장 높음",
                    "expected_candidate_hash": None,
                }
            ]
        },
    )
    run_id: str = Field(min_length=1)
    policy_id: PolicyId
    decision: Literal["approve", "reject", "hold"]
    operator: str = Field(default="demo_operator", min_length=1)
    reason: str = ""
    expected_candidate_hash: str | None = None
    data_quality: DataQualityInput | None = None


class GuardViolation(ContractModel):
    code: str
    detail: str
    threshold_pct: float | None = None
    threshold_sec: float | None = None
    observed_pct: float | None = None
    observed_sec: float | None = None


class GuardResult(ContractModel):
    passed: bool
    violations: list[GuardViolation] = Field(default_factory=list)
    rule_version: str | None = None
    evaluated_at: str | None = None
    note: str | None = None


class Kpi(ContractModel):
    spillback_time_sec: float
    recovery_time_sec: float
    recovery_observed: bool | None = None
    total_travel_time_sec: float
    worst_approach_delay_sec: float


class LinkState(ContractModel):
    link_id: str
    occupancy_ratio: float = Field(ge=0)
    queue_veh: float = Field(default=0, ge=0)
    spillback: bool


class TimelineEntry(ContractModel):
    t_sec: float = Field(ge=0)
    screen_state: str
    rain_level: str
    links: list[LinkState]
    note: str | None = None


class PolicyResult(ContractModel):
    policy_id: PolicyId
    label: str
    kpi: Kpi
    extra: dict[str, Any] = Field(default_factory=dict)
    delta_vs_no_action: dict[str, float] = Field(default_factory=dict)
    guard: GuardResult
    candidate_hash: str | None = None
    rank: int | None = None
    score: float | None = None
    explanation: str


class ApprovalResult(ContractModel):
    status: Literal["approved", "rejected", "pending", "held"]
    policy_id: str
    operator: str | None = None
    decided_at: str | None = None
    reason: str | None = None
    result_source: ResultSource | None = None
    workflow_state: str | None = None


class RunResult(ContractModel):
    run_id: str
    result_source: ResultSource
    provisional: bool = True
    generated_at: str | None = None
    network_version: str | None = None
    dataset: dict[str, Any] | None = None
    note: str | None = None
    scenario: dict[str, Any]
    screen_states: list[str]
    network: dict[str, Any] = Field(default_factory=dict)
    timeline: list[TimelineEntry]
    policies: list[PolicyResult] = Field(min_length=3)
    decision: dict[str, Any] | None = None
    safety_guards: dict[str, Any] | None = None
    approval: ApprovalResult
    recovery_compare: dict[str, Any]
    workflow_state: str | None = None
    state_history: list[dict[str, Any]] | None = None
    reproducibility: dict[str, Any] | None = None
    elapsed_ms: float | None = None


class SimulationCreatedResponse(ContractModel):
    run_id: str
    status: Literal["completed"]
    result_source: ResultSource
    url: str
    workflow_state: str


class HealthResponse(ContractModel):
    status: Literal["ok", "degraded"]
    version: str
    fixture_available: bool
    cached_fixture_available: bool
    llm: Literal["rule_based_fallback"]
    runs_in_memory: int
    persisted_runs: int
    result_source: ResultSource
    dataset_id: str


# ---------------------------------------------------------------------------
# Additive game-mode contracts
# ---------------------------------------------------------------------------


class RegionId(str, Enum):
    SEONGGEUM_CHEONGSA = "seonggeum_cheongsa"
    CHEONGSA_SEJONG = "cheongsa_sejong"
    EOJIN_CORRIDOR = "eojin_corridor"


class MissionId(str, Enum):
    RAIN_COMMUTE = "rain_commute"
    RAIN_INCIDENT = "rain_incident"
    CORRIDOR_FINAL = "corridor_final"


class BotTier(str, Enum):
    LUNA = "luna"
    TERRA = "terra"
    SOL = "sol"


class AdaptiveMode(str, Enum):
    SUPPORT = "support"
    STANDARD = "standard"
    CHALLENGE = "challenge"


class RealityLevel(str, Enum):
    GAME = "game"
    REALITY = "reality"
    POLICY = "policy"


EquipmentId = Literal["smart_controller", "dynamic_guidance"]


class PolicyDesignV1(ContractModel):
    """A deliberately small condition-action policy for the game client."""

    schema_version: Literal["policy-design-v1"] = "policy-design-v1"
    trigger_occupancy_pct: int = Field(default=80, ge=65, le=95, multiple_of=5)
    metering_strength_pct: int = Field(default=60, ge=0, le=100, multiple_of=5)
    diversion_strength: int = Field(default=10, ge=0, le=20, multiple_of=5)


class PlayerProgressV1(ContractModel):
    attempts: int = Field(default=0, ge=0, le=100)
    last_score_margin: float | None = None
    last_completion_time_sec: float | None = Field(default=None, ge=0, le=86_400)
    building_level: int = Field(default=1, ge=1, le=3)
    equipment: list[EquipmentId] = Field(default_factory=list)


class MissionEvaluationRequestV1(ContractModel):
    region_id: RegionId
    seed: int = Field(default=42, ge=0, le=2_147_483_647)
    policy_design: PolicyDesignV1 = Field(default_factory=PolicyDesignV1)
    progress: PlayerProgressV1 = Field(default_factory=PlayerProgressV1)


class AdaptiveEventV1(ContractModel):
    mode: AdaptiveMode
    title: str
    reason: str
    demand_multiplier: float = Field(ge=0.5, le=2.0)
    rain_extension_sec: int = Field(default=0, ge=0, le=900)
    incident: bool = False


class PolicyAdviceV1(ContractModel):
    code: str
    title: str
    reason: str
    tradeoff: str
    recommended_policy: PolicyDesignV1
    precise: bool = False


class RunTelemetryV1(ContractModel):
    telemetry_version: Literal["run-telemetry-v1"] = "run-telemetry-v1"
    mission_id: MissionId
    region_id: RegionId
    seed: int
    attempts: int
    completion_time_sec: float | None = None
    score_margin: float
    adaptive_mode: AdaptiveMode
    reality_level: RealityLevel = RealityLevel.GAME
    data_version: str


class MissionEvaluationV1(ContractModel):
    evaluation_version: Literal["mission-evaluation-v1"] = "mission-evaluation-v1"
    mission_id: MissionId
    region_id: RegionId
    result_source: Literal["live_simulation"] = "live_simulation"
    provisional: Literal[True] = True
    reality_level: RealityLevel = RealityLevel.GAME
    data_version: str
    adaptive_event: AdaptiveEventV1
    player: dict[str, Any]
    opponent: dict[str, Any]
    advice: list[PolicyAdviceV1]
    success: bool
    satisfaction: dict[str, float]
    progression: dict[str, Any]
    telemetry: RunTelemetryV1
    note: str
