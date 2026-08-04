"""Deterministic game-mode mission evaluation built on the frozen simulator.

This module is intentionally additive.  It never changes the legacy policy
catalogue or approval workflow, and every result is labelled as a synthetic
game estimate rather than a real property or policy forecast.
"""
from __future__ import annotations

import copy
import hashlib
import json
from functools import lru_cache
from typing import Any

from .decision import score_policy_delta
from .domain import (
    AdaptiveMode,
    BotTier,
    MissionEvaluationRequestV1,
    MissionId,
    PlayerProgressV1,
    PolicyDesignV1,
    RegionId,
)
from .safety import evaluate_guard
from .simulation import SimResult, run_game_simulation, run_simulation

GAME_DATA_VERSION = "rainflow-game-synthetic-v1"
GAME_RULE_VERSION = "rainflow-game-rules-v1"
BOT_SEARCH_SALT = "rainflow-game-rules-v1-31"
REALITY_NOTE = (
    "게임 시뮬레이션·합성 추정치입니다. 실제 부동산 가격이나 정책 효과를 "
    "예측하지 않습니다."
)

REGIONS: dict[str, dict[str, Any]] = {
    RegionId.SEONGGEUM_CHEONGSA.value: {
        "region_id": RegionId.SEONGGEUM_CHEONGSA.value,
        "label": "성금–청사 생활권",
        "focus_link": "L12",
        "center": {"longitude": 127.2638, "latitude": 36.5019},
        "adjacent_region_id": RegionId.CHEONGSA_SEJONG.value,
        "starting_region": True,
    },
    RegionId.CHEONGSA_SEJONG.value: {
        "region_id": RegionId.CHEONGSA_SEJONG.value,
        "label": "청사–세종 생활권",
        "focus_link": "L23",
        "center": {"longitude": 127.2826, "latitude": 36.5048},
        "adjacent_region_id": RegionId.SEONGGEUM_CHEONGSA.value,
        "starting_region": True,
    },
    RegionId.EOJIN_CORRIDOR.value: {
        "region_id": RegionId.EOJIN_CORRIDOR.value,
        "label": "어진동 통합 회랑",
        "focus_link": "corridor",
        "center": {"longitude": 127.2734, "latitude": 36.5035},
        "adjacent_region_id": None,
        "starting_region": False,
    },
}

MISSIONS: dict[str, dict[str, Any]] = {
    MissionId.RAIN_COMMUTE.value: {
        "mission_id": MissionId.RAIN_COMMUTE.value,
        "title": "출퇴근 집중호우",
        "description": "첫 생활권의 역류를 줄이고 Luna보다 안전한 정책을 설계하세요.",
        "scenario_id": "rain_spillback_a",
        "bot_tier": BotTier.LUNA.value,
        "base_demand_multiplier": 1.0,
        "base_incident": False,
        "reward_bonus": 20,
        "allowed_regions": [
            RegionId.SEONGGEUM_CHEONGSA.value,
            RegionId.CHEONGSA_SEJONG.value,
        ],
        "stage": 1,
    },
    MissionId.RAIN_INCIDENT.value: {
        "mission_id": MissionId.RAIN_INCIDENT.value,
        "title": "강우·사고 복구",
        "description": "인접 생활권의 사고 병목을 복구하고 Terra를 이기세요.",
        "scenario_id": "rain_spillback_b",
        "bot_tier": BotTier.TERRA.value,
        "base_demand_multiplier": 1.03,
        "base_incident": True,
        "reward_bonus": 40,
        "allowed_regions": [
            RegionId.SEONGGEUM_CHEONGSA.value,
            RegionId.CHEONGSA_SEJONG.value,
        ],
        "stage": 2,
    },
    MissionId.CORRIDOR_FINAL.value: {
        "mission_id": MissionId.CORRIDOR_FINAL.value,
        "title": "어진동 AI 회랑전",
        "description": "성장한 두 생활권의 추가 수요를 견디고 Sol을 이기세요.",
        "scenario_id": "rain_spillback_b",
        "bot_tier": BotTier.SOL.value,
        "base_demand_multiplier": 1.08,
        "base_incident": True,
        "reward_bonus": 100,
        "allowed_regions": [RegionId.EOJIN_CORRIDOR.value],
        "stage": 3,
    },
}

BOT_BUDGETS = {
    BotTier.LUNA.value: 9,
    BotTier.TERRA.value: 36,
    BotTier.SOL.value: 128,
}


def mission_catalog() -> dict[str, Any]:
    return {
        "catalog_version": "mission-catalog-v1",
        "result_source": "live_simulation",
        "provisional": True,
        "reality_level": "game",
        "data_version": GAME_DATA_VERSION,
        "reality_note": REALITY_NOTE,
        "regions": list(REGIONS.values()),
        "missions": [
            {
                **mission,
                "bot_candidate_budget": BOT_BUDGETS[mission["bot_tier"]],
            }
            for mission in MISSIONS.values()
        ],
        "policy_controls": {
            "trigger_occupancy_pct": {"minimum": 65, "maximum": 95, "step": 5},
            "metering_strength_pct": {
                "minimum": 0,
                "maximum": 100,
                "base_step": 10,
                "smart_controller_step": 5,
            },
            "diversion_strength": {
                "minimum": 0,
                "base_maximum": 10,
                "dynamic_guidance_maximum": 20,
                "step": 5,
            },
        },
        "equipment": [
            {
                "equipment_id": "smart_controller",
                "label": "스마트 신호제어기",
                "cost_credits": 50,
                "effect": "유입 제한 강도를 5% 단위로 조정",
            },
            {
                "equipment_id": "dynamic_guidance",
                "label": "동적 우회 안내판",
                "cost_credits": 50,
                "effect": "우회 유도 강도 상한을 20으로 확장",
            },
        ],
        "out_of_scope": [
            "실제 부동산 가격 예측",
            "정부 정책 성과 주장",
            "사용자 기록 서버 업로드",
            "건물·공장 직접 건설",
        ],
    }


def _adaptive_event(mission: dict[str, Any], progress: PlayerProgressV1) -> dict[str, Any]:
    struggling = progress.attempts >= 3 or (
        progress.last_score_margin is not None and progress.last_score_margin <= -5.0
    )
    excelling = (
        progress.last_score_margin is not None
        and progress.last_score_margin >= 5.0
        and progress.last_completion_time_sec is not None
        and progress.last_completion_time_sec <= 90.0
    )

    if struggling:
        return {
            "mode": AdaptiveMode.SUPPORT.value,
            "title": "AI 지원 이벤트",
            "reason": "최근 시도 기록을 바탕으로 수요를 5% 낮추고 정밀 조언을 제공합니다.",
            "demand_multiplier": 0.95,
            "rain_extension_sec": 0,
            "incident": bool(mission["base_incident"]),
        }
    if excelling:
        commute = mission["mission_id"] == MissionId.RAIN_COMMUTE.value
        return {
            "mode": AdaptiveMode.CHALLENGE.value,
            "title": "AI 도전 이벤트",
            "reason": "빠른 승리 기록을 반영해 다음 스트레스 테스트를 강화합니다.",
            "demand_multiplier": 1.05,
            "rain_extension_sec": 300 if commute else 0,
            "incident": bool(mission["base_incident"] or not commute),
        }
    return {
        "mode": AdaptiveMode.STANDARD.value,
        "title": "표준 이벤트",
        "reason": "현재 진행 기록에 맞는 표준 수요를 적용합니다.",
        "demand_multiplier": 1.0,
        "rain_extension_sec": 0,
        "incident": bool(mission["base_incident"]),
    }


def _validate_equipment(design: PolicyDesignV1, progress: PlayerProgressV1) -> None:
    equipment = set(progress.equipment)
    if (
        "smart_controller" not in equipment
        and design.metering_strength_pct % 10 != 0
    ):
        raise ValueError(
            "metering_strength_pct requires 10% steps until smart_controller is unlocked"
        )
    if (
        "dynamic_guidance" not in equipment
        and design.diversion_strength > 10
    ):
        raise ValueError(
            "diversion_strength above 10 requires dynamic_guidance"
        )


def _pct(candidate: float, baseline: float) -> float:
    if baseline == 0:
        return 0.0 if candidate == 0 else 100.0
    return round((candidate - baseline) / baseline * 100.0, 3)


def _kpi(result: SimResult) -> dict[str, Any]:
    return {
        "spillback_time_sec": result.spillback_time_sec,
        "recovery_time_sec": result.recovery_time_sec,
        "recovery_observed": result.recovery_observed,
        "total_travel_time_sec": result.total_travel_time_sec,
        "worst_approach_delay_sec": result.worst_approach_delay_sec,
        "completed_trips": result.completed_trips,
        "diverted_vehicles": result.diverted_vehicles,
        "approach_p95_delay": result.approach_p95_delay,
    }


def _delta(candidate: SimResult, baseline: SimResult) -> dict[str, float]:
    return {
        "spillback_time_pct": _pct(
            candidate.spillback_time_sec, baseline.spillback_time_sec
        ),
        "recovery_time_pct": _pct(
            candidate.recovery_time_sec, baseline.recovery_time_sec
        ),
        "total_travel_time_pct": _pct(
            candidate.total_travel_time_sec, baseline.total_travel_time_sec
        ),
        "worst_approach_delay_pct": _pct(
            candidate.worst_approach_delay_sec,
            baseline.worst_approach_delay_sec,
        ),
    }


def _evaluate_design(
    mission: dict[str, Any],
    region: dict[str, Any],
    seed: int,
    design: dict[str, Any],
    *,
    demand_multiplier: float,
    incident: bool,
    rain_extension_sec: int,
    include_timeline: bool,
) -> tuple[dict[str, Any], SimResult, SimResult]:
    incident_link = None
    if incident:
        # The frozen queue model is asymmetric and has its physical bottleneck
        # on L23. Keeping the incident there makes either starting-region choice
        # mechanically equivalent while the client changes the spatial focus.
        incident_link = "L23"
    baseline = run_simulation(
        mission["scenario_id"],
        seed,
        "no_action",
        demand_multiplier=demand_multiplier,
        incident_link=incident_link,
        rain_extension_sec=rain_extension_sec,
    )
    candidate = run_game_simulation(
        mission["scenario_id"],
        seed,
        design,
        # The vertical slice controls the connected corridor; region selection
        # determines presentation/progression, not a hidden difficulty change.
        focus_link="corridor",
        demand_multiplier=demand_multiplier,
        incident_link=incident_link,
        rain_extension_sec=rain_extension_sec,
    )
    delta = _delta(candidate, baseline)
    guard = evaluate_guard(candidate, baseline)
    result = {
        "policy_design": design,
        "score": score_policy_delta(delta),
        "kpi": _kpi(candidate),
        "delta_vs_no_action": delta,
        "guard": guard,
    }
    if include_timeline:
        result["timeline"] = candidate.timeline
    return result, candidate, baseline


def _candidate_pool(equipment: tuple[str, ...]) -> list[dict[str, Any]]:
    strength_step = 5 if "smart_controller" in equipment else 10
    diversion_max = 20 if "dynamic_guidance" in equipment else 10
    return [
        {
            "schema_version": "policy-design-v1",
            "trigger_occupancy_pct": trigger,
            "metering_strength_pct": strength,
            "diversion_strength": diversion,
        }
        for trigger in range(65, 96, 5)
        for strength in range(0, 101, strength_step)
        for diversion in range(0, diversion_max + 1, 5)
    ]


@lru_cache(maxsize=128)
def _run_bot_cached(
    mission_id: str,
    region_id: str,
    seed: int,
    tier: str,
    equipment: tuple[str, ...],
    demand_multiplier: float,
    incident: bool,
    rain_extension_sec: int,
) -> dict[str, Any]:
    mission = MISSIONS[mission_id]
    region = REGIONS[region_id]
    pool = _candidate_pool(equipment)
    ranked = sorted(
        pool,
        key=lambda design: hashlib.sha256(
            (
                f"{BOT_SEARCH_SALT}:{mission_id}:{seed}:"
                + json.dumps(design, sort_keys=True, separators=(",", ":"))
            ).encode("utf-8")
        ).hexdigest(),
    )
    candidates = ranked[: BOT_BUDGETS[tier]]
    evaluated = []
    for design in candidates:
        result, _, _ = _evaluate_design(
            mission,
            region,
            seed,
            design,
            demand_multiplier=demand_multiplier,
            incident=incident,
            rain_extension_sec=rain_extension_sec,
            include_timeline=False,
        )
        evaluated.append(result)
    winner = min(
        evaluated,
        key=lambda item: (
            item["guard"]["passed"] is not True,
            -item["score"],
            json.dumps(item["policy_design"], sort_keys=True),
        ),
    )
    return {
        "tier": tier,
        "candidate_budget": BOT_BUDGETS[tier],
        **winner,
    }


def _clamp_step(value: int, *, low: int, high: int, step: int) -> int:
    clamped = max(low, min(high, value))
    return int(round(clamped / step) * step)


def _advice(
    player: dict[str, Any],
    design: PolicyDesignV1,
    progress: PlayerProgressV1,
    adaptive_mode: str,
) -> list[dict[str, Any]]:
    equipment = set(progress.equipment)
    strength_step = 5 if "smart_controller" in equipment else 10
    diversion_max = 20 if "dynamic_guidance" in equipment else 10
    current = design.model_dump(mode="json")
    precise = adaptive_mode == AdaptiveMode.SUPPORT.value
    violations = {item["code"] for item in player["guard"]["violations"]}

    if "FAIRNESS_P95_EXCEEDED" in violations:
        recommended = {
            **current,
            "metering_strength_pct": _clamp_step(
                design.metering_strength_pct - 20,
                low=0,
                high=100,
                step=strength_step,
            ),
            "diversion_strength": _clamp_step(
                design.diversion_strength + 5,
                low=0,
                high=diversion_max,
                step=5,
            ),
        }
        return [
            {
                "code": "BALANCE_SIDE_APPROACHES",
                "title": "진입로 부담을 나눠보세요",
                "reason": "한 접근로의 P95 지연이 안전 한계를 넘었습니다.",
                "tradeoff": "제한을 완화하면 역류 시간이 조금 늘 수 있습니다.",
                "recommended_policy": recommended,
                "precise": precise,
            }
        ]

    if player["delta_vs_no_action"]["spillback_time_pct"] > -10.0:
        recommended = {
            **current,
            "trigger_occupancy_pct": _clamp_step(
                design.trigger_occupancy_pct - 5, low=65, high=95, step=5
            ),
            "metering_strength_pct": _clamp_step(
                design.metering_strength_pct + strength_step,
                low=0,
                high=100,
                step=strength_step,
            ),
        }
        return [
            {
                "code": "ACT_BEFORE_SPILLBACK",
                "title": "조금 더 일찍 개입하세요",
                "reason": "현재 정책은 역류가 시작된 뒤에야 충분히 작동합니다.",
                "tradeoff": "너무 이른 제한은 접근로 대기시간을 늘릴 수 있습니다.",
                "recommended_policy": recommended,
                "precise": precise,
            }
        ]

    if player["delta_vs_no_action"]["total_travel_time_pct"] > 0.0:
        recommended = {
            **current,
            "trigger_occupancy_pct": _clamp_step(
                design.trigger_occupancy_pct + 5, low=65, high=95, step=5
            ),
            "metering_strength_pct": _clamp_step(
                design.metering_strength_pct - strength_step,
                low=0,
                high=100,
                step=strength_step,
            ),
        }
        return [
            {
                "code": "RELAX_OVER_CONTROL",
                "title": "과도한 제한을 완화하세요",
                "reason": "역류는 줄었지만 전체 통행시간이 늘었습니다.",
                "tradeoff": "제한을 줄이면 병목 점유율이 다시 높아질 수 있습니다.",
                "recommended_policy": recommended,
                "precise": precise,
            }
        ]

    recommended = {
        **current,
        "diversion_strength": _clamp_step(
            design.diversion_strength + 5,
            low=0,
            high=diversion_max,
            step=5,
        ),
    }
    return [
        {
            "code": "FINE_TUNE_DIVERSION",
            "title": "우회 여력을 미세 조정하세요",
            "reason": "안전 기준을 지켰습니다. 남은 정체를 우회로 분산할 수 있습니다.",
            "tradeoff": "우회를 늘리면 우회 차량의 자유주행 시간이 추가됩니다.",
            "recommended_policy": recommended,
            "precise": precise,
        }
    ]


def _pedestrian_satisfaction(candidate: SimResult, baseline: SimResult) -> float:
    worsens = []
    for approach, base in baseline.approach_p95_delay.items():
        ref = max(float(base), 30.0)
        candidate_value = float(candidate.approach_p95_delay.get(approach, base))
        worsens.append(max(0.0, (candidate_value - float(base)) / ref * 100.0))
    worst = max(worsens, default=0.0)
    return float(max(0, min(100, round(100.0 - 4.0 * worst))))


def evaluate_mission(
    mission_id: str,
    request: MissionEvaluationRequestV1,
) -> dict[str, Any]:
    if mission_id not in MISSIONS:
        raise KeyError(mission_id)
    mission = MISSIONS[mission_id]
    region_id = request.region_id.value
    if region_id not in mission["allowed_regions"]:
        raise ValueError(f"region_id {region_id} is not available for {mission_id}")
    _validate_equipment(request.policy_design, request.progress)

    region = REGIONS[region_id]
    adaptive = _adaptive_event(mission, request.progress)
    building_demand = 1.0 + 0.05 * (request.progress.building_level - 1)
    demand_multiplier = round(
        mission["base_demand_multiplier"]
        * adaptive["demand_multiplier"]
        * building_demand,
        6,
    )
    adaptive["effective_demand_multiplier"] = demand_multiplier

    player, candidate, baseline = _evaluate_design(
        mission,
        region,
        request.seed,
        request.policy_design.model_dump(mode="json"),
        demand_multiplier=demand_multiplier,
        incident=adaptive["incident"],
        rain_extension_sec=adaptive["rain_extension_sec"],
        include_timeline=True,
    )
    equipment = tuple(sorted(set(request.progress.equipment)))
    opponent = copy.deepcopy(
        _run_bot_cached(
            mission_id,
            region_id,
            request.seed,
            mission["bot_tier"],
            equipment,
            demand_multiplier,
            adaptive["incident"],
            adaptive["rain_extension_sec"],
        )
    )

    margin = round(float(player["score"]) - float(opponent["score"]), 3)
    traffic_satisfaction = float(max(0, min(100, round(50.0 + player["score"]))))
    pedestrian_satisfaction = _pedestrian_satisfaction(candidate, baseline)
    accessibility = round(
        traffic_satisfaction * 0.6 + pedestrian_satisfaction * 0.4,
        1,
    )
    # docs/17 정의대로 미션 성공은 안전과 접근성으로만 판정한다.  AI 승리는
    # 별도 도전 과제이고 Level 3 승급에만 관여한다.
    #
    #   성공 조건에 AI 승리를 넣으면 진행이 스스로를 잠근다.
    #
    #     잘한 플레이 → 건물 Lv↑ + 도전 모드 → 수요 ×1.25
    #                                            ↓
    #                        달성 가능한 margin 상한이 0으로 압축
    #                                            ↓
    #                     접근성 100점이어도 success=False, 보상 0
    #
    # 실측(2026-08-04): corridor_final / 도전 / Lv3 / 장비 2종에서 가능한
    # 정책 735개 중 margin >= 0.1을 넘는 것이 0개였다.
    defeated_opponent = margin >= 0.1
    success = bool(
        player["guard"]["passed"]
        and traffic_satisfaction >= 60
        and pedestrian_satisfaction >= 60
    )

    achieved_level = request.progress.building_level
    if success and accessibility >= 85 and margin >= 5:
        achieved_level = max(achieved_level, 3)
    elif success and accessibility >= 70:
        achieved_level = max(achieved_level, 2)
    property_value = round(
        100.0
        + max(0.0, accessibility - 50.0) * 0.3
        + (achieved_level - 1) * 5.0,
        1,
    )
    credits = (
        int(round(max(0.0, property_value - 100.0) * 10))
        + int(mission["reward_bonus"])
        if success
        else 0
    )

    advice = _advice(
        player,
        request.policy_design,
        request.progress,
        adaptive["mode"],
    )
    telemetry = {
        "telemetry_version": "run-telemetry-v1",
        "mission_id": mission_id,
        "region_id": region_id,
        "seed": request.seed,
        "attempts": request.progress.attempts,
        "completion_time_sec": request.progress.last_completion_time_sec,
        "score_margin": margin,
        "defeated_opponent": defeated_opponent,
        "adaptive_mode": adaptive["mode"],
        "reality_level": "game",
        "data_version": GAME_DATA_VERSION,
    }
    return {
        "evaluation_version": "mission-evaluation-v1",
        "mission_id": mission_id,
        "region_id": region_id,
        "result_source": "live_simulation",
        "provisional": True,
        "reality_level": "game",
        "data_version": GAME_DATA_VERSION,
        "rule_version": GAME_RULE_VERSION,
        "adaptive_event": adaptive,
        "player": player,
        "opponent": opponent,
        "advice": advice,
        "success": success,
        "defeated_opponent": defeated_opponent,
        "satisfaction": {
            "traffic": traffic_satisfaction,
            "pedestrian_proxy": pedestrian_satisfaction,
            "accessibility": accessibility,
        },
        "progression": {
            "building_level_before": request.progress.building_level,
            "building_level_after": achieved_level,
            "next_demand_bonus_pct": (achieved_level - 1) * 5,
            "virtual_property_value_index": property_value,
            "credits_earned": credits,
            "opponent_score_margin": margin,
        },
        "telemetry": telemetry,
        "note": REALITY_NOTE,
    }
