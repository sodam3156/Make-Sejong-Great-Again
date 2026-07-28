"""RainFlow Sejong 결정론적 큐 모델 시뮬레이터.

docs/15 결정에 따라 SUMO 대신 사용하는 정식 Day 1~2 경로.
연속 회전교차로 R1→L12→R2→L23→R3 회랑과 평행 우회로 BYPASS를 큐 모델로 재현한다.
모든 수치는 합성이며 provisional이다. 같은 (scenario_id, seed)는 같은 결과를 반환한다.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

DT = 5  # sec per step
DURATION = 3600
DRY_PREP_END = 900
RAIN_END = 2700

# 강우 단계별 진입용량 배율. 근거: 임계간격 1.08~1.13배, 용량 0.83~0.95배 (이슈 #9 초기 민감도)
RAIN_CAPACITY_FACTOR = {"dry": 1.00, "light": 0.95, "moderate": 0.89, "heavy": 0.83}

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

POLICIES = ["no_action", "fixed_metering", "corridor_gating"]


def rain_level_at(t: int, scenario: dict) -> str:
    peak = scenario["rain_level"]
    if peak == "dry":
        return "dry"
    if t < DRY_PREP_END:
        return "dry"
    if t < DRY_PREP_END + 240:
        return "moderate"
    if t < RAIN_END:
        return peak
    return "dry"


@dataclass
class SimResult:
    scenario_id: str
    seed: int
    policy_id: str
    spillback_time_sec: float = 0.0
    spillback_events: int = 0
    recovery_time_sec: float = 0.0
    total_travel_time_sec: float = 0.0
    completed_trips: int = 0
    diversion_delay_sec: float = 0.0
    hard_brakes: int = 0
    approach_p95_delay: dict = field(default_factory=dict)
    worst_approach_delay_sec: float = 0.0
    timeline: list = field(default_factory=list)


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    return round(s[min(len(s) - 1, int(len(s) * 0.95))], 1)


def run_simulation(scenario_id: str, seed: int, policy_id: str) -> SimResult:
    if scenario_id not in SCENARIOS:
        raise ValueError(f"unknown scenario_id: {scenario_id}")
    if policy_id not in POLICIES:
        raise ValueError(f"unknown policy_id: {policy_id}")
    sc = SCENARIOS[scenario_id]
    rng = random.Random(f"{scenario_id}:{seed}")
    res = SimResult(scenario_id, seed, policy_id)

    queues = {a: 0.0 for a in DEMAND_APPROACHES}
    links = {l: 0.0 for l in LINKS}
    delay_series: dict[str, list[float]] = {a: [] for a in DEMAND_APPROACHES}
    spillback_prev = {l: False for l in LINKS}
    recovered_at = None

    # 사고 시나리오는 L23 저장공간 20% 축소 (차로 제한)
    storage = dict(LINKS)
    if sc["incident"]:
        storage["L23"] = int(storage["L23"] * 0.8)

    for step in range(DURATION // DT):
        t = step * DT
        rain = rain_level_at(t, sc)
        cap_factor = RAIN_CAPACITY_FACTOR[rain]
        in_rain = DRY_PREP_END <= t < RAIN_END and sc["rain_level"] != "dry"
        surge = sc["surge"] if in_rain else 1.0

        # 수요 도착 (seed 기반 지터로 재현 가능)
        for a in DEMAND_APPROACHES:
            arrivals = BASE_DEMAND[a] * surge * (0.85 + 0.3 * rng.random())
            queues[a] += arrivals

        cap = {a: APPROACH_CAP[a] * cap_factor for a in ALL_APPROACHES}
        # capacity drop: 포화 정체 링크의 선두 배출용량 손실
        if links["L12"] / storage["L12"] >= JAM_OCC:
            cap["R2_N"] *= CAPACITY_DROP
        if links["L23"] / storage["L23"] >= JAM_OCC:
            cap["R3_N"] *= CAPACITY_DROP

        # 정책별 진입 제어
        meter = {a: 1.0 for a in ALL_APPROACHES}
        if policy_id == "fixed_metering" and in_rain:
            # 고정 미터링: 부방향 진입을 정해진 비율로 보류 → 회랑은 살지만 해당 진입로 피해
            meter["R2_S"] = 0.45
            meter["R1_W"] = 0.45
        elif policy_id == "corridor_gating":
            # 연속 게이팅: 하류 링크 점유 0.80 초과 전에 상류 유입을 비례 감축 (전 진입로 균등)
            for link_id, upstreams in (("L23", ["R2_N", "R2_S"]), ("L12", ["R1_N", "R1_W"])):
                occ = links[link_id] / storage[link_id]
                if occ > 0.80:
                    factor = max(0.35, 1.0 - (occ - 0.80) / 0.20 * 0.65)
                    for a in upstreams:
                        meter[a] = min(meter[a], factor)

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
        if total_want > space23:
            scale = space23 / total_want if total_want > 0 else 0.0
            res.hard_brakes += int((total_want - space23) / 0.5)
            want_r2n *= scale
            want_r2s *= scale
        links["L12"] -= want_r2n
        queues["R2_S"] -= want_r2s
        links["L23"] += want_r2n + want_r2s

        # R1: R1_N + R1_W → L12
        space12 = storage["L12"] - links["L12"]
        want_r1n = min(queues["R1_N"], cap["R1_N"] * meter["R1_N"])
        want_r1w = min(queues["R1_W"], cap["R1_W"] * meter["R1_W"])
        total_want1 = want_r1n + want_r1w
        if total_want1 > space12:
            scale = space12 / total_want1 if total_want1 > 0 else 0.0
            res.hard_brakes += int((total_want1 - space12) / 0.5)
            want_r1n *= scale
            want_r1w *= scale
        queues["R1_N"] -= want_r1n
        queues["R1_W"] -= want_r1w
        links["L12"] += want_r1n + want_r1w

        # 우회로 배경 수요 (정책 무관, 전가 지체 기준선)
        links["BYPASS"] = min(storage["BYPASS"], links["BYPASS"] + 0.2)
        links["BYPASS"] = max(0.0, links["BYPASS"] - 0.2)

        # 지표 집계
        for link_id in ("L12", "L23"):
            full = links[link_id] >= storage[link_id] - 0.5
            if full:
                res.spillback_time_sec += DT
                if not spillback_prev[link_id]:
                    res.spillback_events += 1
            spillback_prev[link_id] = full

        vehicles_in_system = sum(queues.values()) + links["L12"] + links["L23"]
        res.total_travel_time_sec += vehicles_in_system * DT

        for a in DEMAND_APPROACHES:
            eff_cap = max(cap[a] * 0.5, 0.1)
            delay_series[a].append(queues[a] / eff_cap * DT)

        # 회복 판정: 우천 종료 후 링크 점유<0.5, 대기<5대
        if t >= RAIN_END and recovered_at is None:
            calm = all(links[l] / storage[l] < 0.5 for l in ("L12", "L23")) and all(
                q < 5 for q in queues.values()
            )
            if calm:
                recovered_at = t

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
        res.recovery_time_sec = (recovered_at - RAIN_END) if recovered_at is not None else DURATION - RAIN_END
    res.approach_p95_delay = {a: _p95(v) for a, v in delay_series.items()}
    res.worst_approach_delay_sec = max(res.approach_p95_delay.values())
    res.total_travel_time_sec = round(res.total_travel_time_sec, 0)
    res.spillback_time_sec = round(res.spillback_time_sec, 0)
    res.completed_trips = int(res.completed_trips)
    return res
