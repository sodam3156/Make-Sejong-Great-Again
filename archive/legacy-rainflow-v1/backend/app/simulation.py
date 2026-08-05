"""RainFlow Sejong 결정론적 큐 모델 시뮬레이터.

docs/15 결정에 따라 SUMO 대신 사용하는 정식 Day 1~2 경로.
연속 회전교차로 R1→L12→R2→L23→R3 회랑과 평행 우회로 BYPASS를 큐 모델로 재현한다.
모든 수치는 합성이며 provisional이다. 같은 (scenario_id, seed)는 같은 결과를 반환한다.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from .policies import POLICIES, metering_factors

DT = 5  # sec per step
DURATION = 3600
DRY_PREP_END = 900
RAIN_END = 2700
RECOVERY_HOLD_SEC = 60
RECOVERY_OCCUPANCY_LIMIT = 0.50
RECOVERY_QUEUE_LIMIT = 5.0
SIMULATOR_VERSION = "rainflow-queue-v2"
PARAMETER_SET_VERSION = "rainflow-provisional-v2"
KPI_DEFINITION_VERSION = "rainflow-kpi-v2"

# 강우 단계별 진입용량 배율. 근거: 임계간격 1.08~1.13배, 용량 0.83~0.95배 (이슈 #9 초기 민감도)
RAIN_CAPACITY_FACTOR = {"dry": 1.00, "light": 0.95, "moderate": 0.89, "heavy": 0.84}

LINKS = {"L12": 22, "L23": 18, "BYPASS": 60}  # storage_veh
DEMAND_APPROACHES = ["R1_N", "R1_W", "R2_S", "R3_E"]
ALL_APPROACHES = ["R1_N", "R1_W", "R2_N", "R2_S", "R3_N", "R3_E"]

# 기본 수요 (veh per DT). provisional 합성값
BASE_DEMAND = {"R1_N": 0.90, "R1_W": 0.35, "R2_S": 0.40, "R3_E": 0.35}
# 진입로별 기본 용량 (veh per DT). 회랑 선두(R2_N, R3_N)는 2차로 우선권으로 상향
APPROACH_CAP = {"R1_N": 1.3, "R1_W": 0.8, "R2_N": 2.0, "R2_S": 0.8, "R3_N": 2.0, "R3_E": 0.8}
# 링크가 포화 정체(occ>=0.95)에 빠지면 stop-and-go 방출 손실로 하류 배출용량이 깎인다 (capacity drop)
JAM_OCC = 0.95
CAPACITY_DROP = 0.70

SCENARIOS = {
    "dry_base": {"rain_level": "dry", "surge": 1.0, "incident": False},
    "rain_spillback_a": {"rain_level": "heavy", "surge": 1.10, "incident": False},
    "rain_spillback_b": {"rain_level": "heavy", "surge": 1.18, "incident": True},
}

def rain_level_at(t: int, scenario: dict, *, rain_end: int = RAIN_END) -> str:
    peak = scenario["rain_level"]
    if peak == "dry":
        return "dry"
    if t < DRY_PREP_END:
        return "dry"
    if t < DRY_PREP_END + 240:
        return "moderate"
    if t < rain_end:
        return peak
    return "dry"


def _game_metering_factors(
    design: dict,
    *,
    in_rain: bool,
    link_occupancy: dict[str, float],
    approaches: tuple[str, ...] | list[str],
    focus_link: str,
) -> dict[str, float]:
    """Translate the game policy's three controls into meter multipliers."""

    meter = {approach: 1.0 for approach in approaches}
    if not in_rain:
        return meter

    trigger = float(design["trigger_occupancy_pct"]) / 100.0
    strength = float(design["metering_strength_pct"]) / 100.0
    factor = max(0.35, 1.0 - 0.65 * strength)
    targets = (
        (("L12", ("R1_N", "R1_W")),)
        if focus_link == "L12"
        else (("L23", ("R2_N", "R2_S")),)
        if focus_link == "L23"
        else (
            ("L12", ("R1_N", "R1_W")),
            ("L23", ("R2_N", "R2_S")),
        )
    )
    for link_id, upstreams in targets:
        if link_occupancy[link_id] >= trigger:
            for approach in upstreams:
                meter[approach] = min(meter[approach], factor)
    return meter


@dataclass
class SimResult:
    scenario_id: str
    seed: int
    policy_id: str
    spillback_time_sec: float = 0.0
    spillback_link_seconds: dict[str, float] = field(default_factory=dict)
    spillback_events: int = 0
    recovery_time_sec: float = 0.0
    recovery_observed: bool = False
    total_travel_time_sec: float = 0.0
    modeled_vehicle_seconds: float = 0.0
    completed_trips: int = 0
    diversion_delay_sec: float = 0.0
    diverted_vehicles: float = 0.0
    diversion_vehicle_seconds: float = 0.0
    diversion_freeflow_seconds: float = 0.0
    hard_brakes: int = 0
    approach_p95_delay: dict = field(default_factory=dict)
    worst_approach_delay_sec: float = 0.0
    timeline: list = field(default_factory=list)


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    return round(s[min(len(s) - 1, int(len(s) * 0.95))], 1)


def _accumulate_spillback(
    result: SimResult,
    full_by_link: dict[str, bool],
) -> None:
    """Accumulate one wall-clock step and optional link-level diagnostics."""
    for link_id, full in full_by_link.items():
        if full:
            result.spillback_link_seconds[link_id] = (
                result.spillback_link_seconds.get(link_id, 0.0) + DT
            )
    if any(full_by_link.values()):
        result.spillback_time_sec += DT


def _advance_recovery_window(
    calm_started_at: int | None,
    *,
    t: int,
    calm: bool,
) -> tuple[int | None, int | None]:
    """Return updated calm start and confirmed recovery start, if any."""
    if not calm:
        return None, None
    started_at = t if calm_started_at is None else calm_started_at
    recovered_at = (
        started_at
        if t - started_at + DT >= RECOVERY_HOLD_SEC
        else None
    )
    return started_at, recovered_at


def _clearance_proxy(queue_veh: float, effective_service: float) -> float:
    """Queue-clearance proxy in seconds using the constrained service rate."""
    return queue_veh / max(effective_service, 0.1) * DT


def run_simulation(
    scenario_id: str,
    seed: int,
    policy_id: str,
    *,
    policy_design: dict | None = None,
    focus_link: str = "corridor",
    demand_multiplier: float = 1.0,
    incident_link: str | None = None,
    rain_extension_sec: int = 0,
) -> SimResult:
    if scenario_id not in SCENARIOS:
        raise ValueError(f"unknown scenario_id: {scenario_id}")
    if policy_design is None and policy_id not in POLICIES:
        raise ValueError(f"unknown policy_id: {policy_id}")
    if policy_design is not None and policy_id != "game_policy":
        raise ValueError("custom policy_design requires policy_id='game_policy'")
    if focus_link not in {"L12", "L23", "corridor"}:
        raise ValueError(f"unknown focus_link: {focus_link}")
    if not 0.5 <= demand_multiplier <= 2.0:
        raise ValueError("demand_multiplier must be between 0.5 and 2.0")
    if incident_link not in {None, "L12", "L23"}:
        raise ValueError("incident_link must be L12, L23, or None")
    if not 0 <= rain_extension_sec <= 900:
        raise ValueError("rain_extension_sec must be between 0 and 900")
    sc = SCENARIOS[scenario_id]
    rng = random.Random(f"{scenario_id}:{seed}")
    res = SimResult(scenario_id, seed, policy_id)

    queues = {a: 0.0 for a in DEMAND_APPROACHES}
    links = {l: 0.0 for l in LINKS}
    delay_series: dict[str, list[float]] = {a: [] for a in DEMAND_APPROACHES}
    spillback_prev = {l: False for l in LINKS}
    recovery_calm_started_at = None
    recovered_at = None
    diverted_vehicles = 0.0
    diversion_vehicle_seconds = 0.0

    # 사고 시나리오는 L23 저장공간 20% 축소 (차로 제한)
    storage = dict(LINKS)
    effective_incident_link = incident_link or ("L23" if sc["incident"] else None)
    if effective_incident_link:
        storage[effective_incident_link] = storage[effective_incident_link] * 0.8
    effective_rain_end = min(DURATION - RECOVERY_HOLD_SEC, RAIN_END + rain_extension_sec)

    for step in range(DURATION // DT):
        t = step * DT
        rain = rain_level_at(t, sc, rain_end=effective_rain_end)
        cap_factor = RAIN_CAPACITY_FACTOR[rain]
        in_rain = DRY_PREP_END <= t < effective_rain_end and sc["rain_level"] != "dry"
        surge = sc["surge"] if in_rain else 1.0

        # 수요 도착 (seed 기반 지터로 재현 가능)
        for a in DEMAND_APPROACHES:
            arrivals = (
                BASE_DEMAND[a]
                * surge
                * demand_multiplier
                * (0.85 + 0.3 * rng.random())
            )
            queues[a] += arrivals

        cap = {a: APPROACH_CAP[a] * cap_factor for a in ALL_APPROACHES}
        # capacity drop: 포화 정체 링크의 선두 배출용량 손실
        if links["L12"] / storage["L12"] >= JAM_OCC:
            cap["R2_N"] *= CAPACITY_DROP
        if links["L23"] / storage["L23"] >= JAM_OCC:
            cap["R3_N"] *= CAPACITY_DROP

        # 정책별 진입 제어
        occupancy = {
            "L12": links["L12"] / storage["L12"],
            "L23": links["L23"] / storage["L23"],
        }
        if policy_design is None:
            meter = metering_factors(
                policy_id,
                in_rain=in_rain,
                link_occupancy=occupancy,
                approaches=ALL_APPROACHES,
            )
        else:
            meter = _game_metering_factors(
                policy_design,
                in_rain=in_rain,
                link_occupancy=occupancy,
                approaches=ALL_APPROACHES,
                focus_link=focus_link,
            )

        # 연속 게이팅이 강하게 작동할 때 일부 운전자가 BYPASS를 선택한다.
        # 우회량과 추가 지체를 별도로 기록해 전가 피해 가드가 실제 값을 검사하게 한다.
        if (policy_id == "corridor_gating" or policy_design is not None) and in_rain:
            gate_strength = max(
                0.0,
                1.0
                - (
                    min(meter.values())
                    if policy_design is not None
                    else meter["R1_N"]
                ),
            )
            diversion_strength = (
                10.0
                if policy_design is None
                else float(policy_design["diversion_strength"])
            )
            diverted = min(
                queues["R1_N"],
                diversion_strength / 100.0 * gate_strength,
            )
            queues["R1_N"] -= diverted
            links["BYPASS"] = min(storage["BYPASS"], links["BYPASS"] + diverted)
            diverted_vehicles += diverted

        # R3: L23 선두(R3_N) + R3_E → 무한 출구
        out_r3n = min(links["L23"], cap["R3_N"] * meter["R3_N"])
        links["L23"] -= out_r3n
        out_r3e = min(queues["R3_E"], cap["R3_E"] * meter["R3_E"])
        queues["R3_E"] -= out_r3e
        res.completed_trips += out_r3n + out_r3e

        # R2: L12 선두(R2_N) + R2_S → L23 (저장공간 제한 = spillback)
        space23 = storage["L23"] - links["L23"]
        want_r2n = min(links["L12"], cap["R2_N"] * meter["R2_N"])
        want_r2s = min(queues["R2_S"], cap["R2_S"] * meter["R2_S"])
        total_want = want_r2n + want_r2s
        scale23 = 1.0
        if total_want > space23:
            scale23 = space23 / total_want if total_want > 0 else 0.0
            res.hard_brakes += int((total_want - space23) / 0.5)
            want_r2n *= scale23
            want_r2s *= scale23
        links["L12"] -= want_r2n
        queues["R2_S"] -= want_r2s
        links["L23"] += want_r2n + want_r2s

        # R1: R1_N + R1_W → L12
        space12 = storage["L12"] - links["L12"]
        want_r1n = min(queues["R1_N"], cap["R1_N"] * meter["R1_N"])
        want_r1w = min(queues["R1_W"], cap["R1_W"] * meter["R1_W"])
        total_want1 = want_r1n + want_r1w
        scale12 = 1.0
        if total_want1 > space12:
            scale12 = space12 / total_want1 if total_want1 > 0 else 0.0
            res.hard_brakes += int((total_want1 - space12) / 0.5)
            want_r1n *= scale12
            want_r1w *= scale12
        queues["R1_N"] -= want_r1n
        queues["R1_W"] -= want_r1w
        links["L12"] += want_r1n + want_r1w

        # 우회로는 본선보다 긴 자유주행 60초에 더해 대기시간이 든다.
        bypass_out = min(links["BYPASS"], 0.30 * cap_factor)
        links["BYPASS"] -= bypass_out
        res.completed_trips += bypass_out
        diversion_vehicle_seconds += links["BYPASS"] * DT

        # 지표 집계: headline spillback은 링크별 합이 아니라 회랑 wall-clock이다.
        full_by_link = {
            link_id: links[link_id] >= storage[link_id] - 0.5
            for link_id in ("L12", "L23")
        }
        for link_id in ("L12", "L23"):
            full = full_by_link[link_id]
            if full:
                if not spillback_prev[link_id]:
                    res.spillback_events += 1
            spillback_prev[link_id] = full
        _accumulate_spillback(res, full_by_link)

        vehicles_in_system = sum(queues.values()) + sum(links.values())
        res.total_travel_time_sec += vehicles_in_system * DT

        effective_service = {
            "R1_N": cap["R1_N"] * meter["R1_N"] * scale12,
            "R1_W": cap["R1_W"] * meter["R1_W"] * scale12,
            "R2_S": cap["R2_S"] * meter["R2_S"] * scale23,
            "R3_E": cap["R3_E"] * meter["R3_E"],
        }
        for a in DEMAND_APPROACHES:
            delay_series[a].append(
                _clearance_proxy(queues[a], effective_service[a])
            )

        # 회복 판정: 우천 종료 후 calm이 연속 60초 유지된 구간의 시작 시각.
        if t >= effective_rain_end and recovered_at is None:
            calm = all(
                links[l] / storage[l] < RECOVERY_OCCUPANCY_LIMIT
                for l in ("L12", "L23")
            ) and all(q < RECOVERY_QUEUE_LIMIT for q in queues.values())
            recovery_calm_started_at, confirmed_at = _advance_recovery_window(
                recovery_calm_started_at,
                t=t,
                calm=calm,
            )
            if confirmed_at is not None:
                recovered_at = confirmed_at

        if step % 36 == 0:  # 180초마다 타임라인 샘플
            res.timeline.append(
                {
                    "t_sec": t,
                    "rain_level": rain,
                    "links": [
                        {
                            "link_id": l,
                            "occupancy_ratio": round(links[l] / storage[l], 2),
                            "queue_veh": round(links[l], 1),
                            "spillback": links[l] >= storage[l] - 0.5,
                        }
                        for l in LINKS
                    ],
                }
            )

    if sc["rain_level"] != "dry":
        res.recovery_observed = recovered_at is not None
        res.recovery_time_sec = (
            recovered_at - effective_rain_end
            if recovered_at is not None
            else DURATION - effective_rain_end
        )
    res.approach_p95_delay = {a: _p95(v) for a, v in delay_series.items()}
    res.worst_approach_delay_sec = max(res.approach_p95_delay.values())
    if diverted_vehicles:
        res.diversion_delay_sec = round(60.0 + diversion_vehicle_seconds / diverted_vehicles, 1)
    res.diverted_vehicles = round(diverted_vehicles, 1)
    res.diversion_vehicle_seconds = round(diversion_vehicle_seconds, 1)
    res.diversion_freeflow_seconds = round(diverted_vehicles * 60.0, 1)
    res.modeled_vehicle_seconds = round(res.total_travel_time_sec, 1)
    res.total_travel_time_sec += res.diversion_freeflow_seconds
    res.total_travel_time_sec = round(res.total_travel_time_sec, 0)
    res.spillback_time_sec = round(res.spillback_time_sec, 0)
    res.completed_trips = int(res.completed_trips)
    return res


def run_game_simulation(
    scenario_id: str,
    seed: int,
    design: dict,
    *,
    focus_link: str,
    demand_multiplier: float,
    incident_link: str | None = None,
    rain_extension_sec: int = 0,
) -> SimResult:
    """Run one user-authored condition-action policy without changing legacy IDs."""

    return run_simulation(
        scenario_id,
        seed,
        "game_policy",
        policy_design=design,
        focus_link=focus_link,
        demand_multiplier=demand_multiplier,
        incident_link=incident_link,
        rain_extension_sec=rain_extension_sec,
    )
