"""결정론적 안전·공정성 가드. LLM은 판정에 관여하지 않는다."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .simulation import SimResult, approach_display_name

FAIRNESS_P95_LIMIT_PCT = 15.0  # provisional, 시우 검증 대상
DIVERSION_DELAY_LIMIT_SEC = 180.0
P95_NOISE_FLOOR_SEC = 30.0  # 기준 지체가 작을 때의 백분율 노이즈 차단
DATA_STALE_LIMIT_SEC = 120.0
RULE_VERSION = "rainflow-guard-v2"


def operational_violations(data_quality: dict[str, Any] | None) -> list[dict]:
    """Return approval-blocking data/device violations."""
    quality = data_quality or {}
    violations = []
    age = float(quality.get("data_age_sec", 0))
    sensor_available = bool(quality.get("sensor_available", True))
    device_status = str(quality.get("device_status", "ok"))

    if not sensor_available or age > DATA_STALE_LIMIT_SEC:
        detail = (
            "센서 입력을 사용할 수 없어 관찰 전용 모드로 전환"
            if not sensor_available
            else f"입력 데이터 경과 {age:.1f}초가 허용한도 {DATA_STALE_LIMIT_SEC:.0f}초 초과"
        )
        violations.append(
            {
                "code": "DATA_STALE",
                "detail": detail,
                "threshold_sec": DATA_STALE_LIMIT_SEC,
                "observed_sec": round(age, 1),
            }
        )
    if device_status == "fault":
        violations.append(
            {
                "code": "DEVICE_FAULT",
                "detail": "제어기 상태가 fault이므로 정책 적용을 차단하고 기본 양보운전을 유지",
            }
        )
    return violations


def evaluate_guard(
    candidate: SimResult,
    baseline: SimResult,
    data_quality: dict[str, Any] | None = None,
) -> dict:
    """무대응 기준선 대비 후보 정책의 가드 판정. 안정적 규칙 코드로 사유를 남긴다."""
    violations = operational_violations(data_quality)

    for approach, base_p95 in baseline.approach_p95_delay.items():
        label = approach_display_name(approach)
        if approach not in candidate.approach_p95_delay:
            violations.append(
                {
                    "code": "FAIRNESS_INPUT_INVALID",
                    "approach": approach,
                    "detail": f"{label} P95 대기 proxy가 누락되어 판정 불가",
                }
            )
            continue
        cand_p95 = candidate.approach_p95_delay[approach]
        ref = max(base_p95, P95_NOISE_FLOOR_SEC)
        worsen_pct = (cand_p95 - base_p95) / ref * 100
        if worsen_pct > FAIRNESS_P95_LIMIT_PCT:
            violations.append(
                {
                    "code": "FAIRNESS_P95_EXCEEDED",
                    "approach": approach,
                    "detail": f"{label} P95 지체가 기준 대비 {worsen_pct:.1f}% 악화. 허용한도 {FAIRNESS_P95_LIMIT_PCT}% 초과",
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
                "code": "HARD_BRAKE_PROXY_DEGRADED",
                "detail": f"차단 진입 proxy {baseline.hard_brakes}→{candidate.hard_brakes} 악화",
            }
        )

    return {
        "passed": not violations,
        "violations": violations,
        "rule_version": RULE_VERSION,
    }


def candidate_hash(policy: dict[str, Any]) -> str:
    """Hash only the immutable calculation and guard fields of one candidate."""
    payload = {
        key: policy.get(key)
        for key in (
            "policy_id",
            "kpi",
            "extra",
            "delta_vs_no_action",
            "guard",
        )
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
