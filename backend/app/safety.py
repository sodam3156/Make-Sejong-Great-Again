"""결정론적 안전·공정성 가드. LLM은 판정에 관여하지 않는다."""
from __future__ import annotations

from .simulation import SimResult

FAIRNESS_P95_LIMIT_PCT = 15.0  # provisional, 시우 검증 대상
DIVERSION_DELAY_LIMIT_SEC = 180.0
P95_NOISE_FLOOR_SEC = 30.0  # 기준 지체가 작을 때의 백분율 노이즈 차단


def evaluate_guard(candidate: SimResult, baseline: SimResult) -> dict:
    """무대응 기준선 대비 후보 정책의 가드 판정. 안정적 규칙 코드로 사유를 남긴다."""
    violations = []

    for approach, base_p95 in baseline.approach_p95_delay.items():
        cand_p95 = candidate.approach_p95_delay.get(approach, 0.0)
        ref = max(base_p95, P95_NOISE_FLOOR_SEC)
        worsen_pct = (cand_p95 - ref) / ref * 100
        if worsen_pct > FAIRNESS_P95_LIMIT_PCT:
            violations.append(
                {
                    "code": "FAIRNESS_P95_EXCEEDED",
                    "detail": f"{approach} 진입로 P95 지체가 기준 대비 {worsen_pct:.1f}% 악화. 허용한도 {FAIRNESS_P95_LIMIT_PCT}% 초과",
                    "threshold_pct": FAIRNESS_P95_LIMIT_PCT,
                    "observed_pct": round(worsen_pct, 1),
                }
            )

    diversion_delta = candidate.diversion_delay_sec - baseline.diversion_delay_sec
    if diversion_delta > DIVERSION_DELAY_LIMIT_SEC:
        violations.append(
            {
                "code": "DIVERSION_DELAY_EXCEEDED",
                "detail": f"우회도로 전가 지체 {diversion_delta:.0f}초가 허용한도 {DIVERSION_DELAY_LIMIT_SEC:.0f}초 초과",
            }
        )

    if candidate.hard_brakes > baseline.hard_brakes:
        violations.append(
            {
                "code": "SAFETY_TTC_DEGRADED",
                "detail": f"급제동 대리지표 {baseline.hard_brakes}→{candidate.hard_brakes} 악화",
            }
        )

    return {"passed": not violations, "violations": violations}
