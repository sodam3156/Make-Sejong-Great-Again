window.DEMO_RUN = {
  "run_id": "fixture-day1-001",
  "result_source": "fixture",
  "provisional": true,
  "generated_at": "2026-07-28T22:30:00+09:00",
  "network_version": "sejong-corridor-v0",
  "note": "합성 데이터 기반 fixture. 모든 수치는 provisional이며 시우 검증 후 교체한다. 실제 세종시 실측 성과가 아니다.",
  "scenario": {
    "scenario_id": "rain_spillback_a",
    "seed": 42,
    "rain_level": "heavy",
    "duration_sec": 3600,
    "phases": { "dry_prep_sec": 900, "rain_peak_sec": 1800, "recovery_sec": 900 },
    "incident": false
  },
  "screen_states": [
    "normal",
    "rain_warning",
    "spillback",
    "policy_compare",
    "safety_review",
    "operator_approval",
    "recovery_compare"
  ],
  "network": {
    "roundabouts": ["R1", "R2", "R3"],
    "links": [
      { "link_id": "L12", "from": "R1", "to": "R2", "storage_veh": 22 },
      { "link_id": "L23", "from": "R2", "to": "R3", "storage_veh": 18 },
      { "link_id": "BYPASS", "from": "R1", "to": "R3", "storage_veh": 60 }
    ],
    "approaches": ["R1_N", "R1_W", "R2_N", "R2_S", "R3_N", "R3_E"]
  },
  "timeline": [
    { "t_sec": 0, "screen_state": "normal", "rain_level": "dry", "links": [ { "link_id": "L12", "occupancy_ratio": 0.28, "queue_veh": 3, "spillback": false }, { "link_id": "L23", "occupancy_ratio": 0.31, "queue_veh": 3, "spillback": false }, { "link_id": "BYPASS", "occupancy_ratio": 0.12, "queue_veh": 2, "spillback": false } ], "note": "건조 상태. 세 회전교차로 정상 처리" },
    { "t_sec": 900, "screen_state": "rain_warning", "rain_level": "moderate", "links": [ { "link_id": "L12", "occupancy_ratio": 0.55, "queue_veh": 9, "spillback": false }, { "link_id": "L23", "occupancy_ratio": 0.68, "queue_veh": 11, "spillback": false }, { "link_id": "BYPASS", "occupancy_ratio": 0.15, "queue_veh": 3, "spillback": false } ], "note": "강우 시작. 하류 R3 진입용량 감소" },
    { "t_sec": 1380, "screen_state": "spillback", "rain_level": "heavy", "links": [ { "link_id": "L12", "occupancy_ratio": 0.82, "queue_veh": 17, "spillback": false }, { "link_id": "L23", "occupancy_ratio": 1.0, "queue_veh": 18, "spillback": true }, { "link_id": "BYPASS", "occupancy_ratio": 0.18, "queue_veh": 4, "spillback": false } ], "note": "L23 저장한계 도달. R2 회전부 역류 시작" },
    { "t_sec": 1560, "screen_state": "policy_compare", "rain_level": "heavy", "links": [ { "link_id": "L12", "occupancy_ratio": 0.97, "queue_veh": 21, "spillback": false }, { "link_id": "L23", "occupancy_ratio": 1.0, "queue_veh": 18, "spillback": true }, { "link_id": "BYPASS", "occupancy_ratio": 0.2, "queue_veh": 5, "spillback": false } ], "note": "15분 내 R1 도달 확률 0.87 예측. 대응안 3종 비교 제시" },
    { "t_sec": 1740, "screen_state": "safety_review", "rain_level": "heavy", "links": [ { "link_id": "L12", "occupancy_ratio": 1.0, "queue_veh": 22, "spillback": true }, { "link_id": "L23", "occupancy_ratio": 1.0, "queue_veh": 18, "spillback": true }, { "link_id": "BYPASS", "occupancy_ratio": 0.22, "queue_veh": 6, "spillback": false } ], "note": "fixed_metering이 공정성 가드 위반으로 탈락" },
    { "t_sec": 1920, "screen_state": "operator_approval", "rain_level": "heavy", "links": [ { "link_id": "L12", "occupancy_ratio": 1.0, "queue_veh": 22, "spillback": true }, { "link_id": "L23", "occupancy_ratio": 0.94, "queue_veh": 17, "spillback": false }, { "link_id": "BYPASS", "occupancy_ratio": 0.25, "queue_veh": 7, "spillback": false } ], "note": "운영자가 corridor_gating 승인" },
    { "t_sec": 3600, "screen_state": "recovery_compare", "rain_level": "dry", "links": [ { "link_id": "L12", "occupancy_ratio": 0.33, "queue_veh": 4, "spillback": false }, { "link_id": "L23", "occupancy_ratio": 0.36, "queue_veh": 4, "spillback": false }, { "link_id": "BYPASS", "occupancy_ratio": 0.13, "queue_veh": 2, "spillback": false } ], "note": "우천 종료. 무대응 대비 회복시간 단축 비교 표시" }
  ],
  "policies": [
    {
      "policy_id": "no_action",
      "label": "무대응",
      "kpi": { "spillback_time_sec": 1240, "recovery_time_sec": 780, "total_travel_time_sec": 51840, "worst_approach_delay_sec": 310 },
      "extra": { "spillback_events": 3, "completed_trips": 1685, "diversion_delay_sec": 0, "safety_proxy_hard_brakes": 41 },
      "delta_vs_no_action": { "spillback_time_pct": 0.0, "total_travel_time_pct": 0.0, "worst_approach_delay_pct": 0.0 },
      "guard": { "passed": true, "violations": [], "note": "기준선. 가드 판정 대상 아님" },
      "explanation": "기존 양보운전 유지. L23 포화 후 R2와 R1까지 역류가 이어져 spillback 누적 1240초 발생."
    },
    {
      "policy_id": "fixed_metering",
      "label": "고정 미터링",
      "kpi": { "spillback_time_sec": 620, "recovery_time_sec": 600, "total_travel_time_sec": 47400, "worst_approach_delay_sec": 364 },
      "extra": { "spillback_events": 1, "completed_trips": 1760, "diversion_delay_sec": 0, "safety_proxy_hard_brakes": 38 },
      "delta_vs_no_action": { "spillback_time_pct": -50.0, "total_travel_time_pct": -8.6, "worst_approach_delay_pct": 17.4 },
      "guard": {
        "passed": false,
        "violations": [
          { "code": "FAIRNESS_P95_EXCEEDED", "detail": "R2_S 진입로 P95 지체가 무대응 대비 17.4% 악화. 허용한도 15% 초과", "threshold_pct": 15.0, "observed_pct": 17.4 }
        ],
        "note": "spillback은 줄지만 특정 진입로에 피해를 전가하여 탈락"
      },
      "explanation": "우세 방향 유입을 고정 시간 보류. 회랑 spillback은 절반으로 줄지만 R2_S 진입로 대기가 한도를 넘어 공정성 가드에서 탈락."
    },
    {
      "policy_id": "corridor_gating",
      "label": "연속 게이팅",
      "kpi": { "spillback_time_sec": 360, "recovery_time_sec": 420, "total_travel_time_sec": 44900, "worst_approach_delay_sec": 296 },
      "extra": { "spillback_events": 1, "completed_trips": 1815, "diversion_delay_sec": 95, "safety_proxy_hard_brakes": 29 },
      "delta_vs_no_action": { "spillback_time_pct": -71.0, "total_travel_time_pct": -13.4, "worst_approach_delay_pct": -4.5 },
      "guard": { "passed": true, "violations": [], "note": "전 진입로 P95 악화 없음. 안전 대리지표 개선" },
      "explanation": "하류 점유율 임계 도달 전에 상류 유입을 단계적으로 조절. spillback 누적 71% 감소, 총 통행시간 13.4% 감소, 어느 진입로도 15% 이상 악화 없음."
    }
  ],
  "safety_guards": {
    "provisional": true,
    "rules": [
      { "code": "STORAGE_OVERFLOW_PREDICTED", "description": "하류 링크 저장공간 초과 예측 시 정책 재탐색" },
      { "code": "FAIRNESS_P95_EXCEEDED", "description": "진입로 P95 지체 15% 초과 악화 시 후보 거절", "threshold_pct": 15.0 },
      { "code": "DIVERSION_DELAY_EXCEEDED", "description": "우회도로 전가 지체 허용한도 초과 시 거절", "threshold_sec": 180 },
      { "code": "SAFETY_TTC_DEGRADED", "description": "급제동·TTC 대리지표 악화 시 거절" },
      { "code": "DATA_STALE", "description": "센서 지연·결측 임계 초과 시 관찰 전용 모드" },
      { "code": "OPERATOR_NOT_APPROVED", "description": "운영자 미승인 시 정책 미적용" }
    ]
  },
  "approval": {
    "status": "approved",
    "policy_id": "corridor_gating",
    "operator": "demo_operator",
    "requested_at": "2026-07-28T22:32:00+09:00",
    "decided_at": "2026-07-28T22:32:40+09:00",
    "reason": "가드 통과 후보 중 spillback 감소 최대. 우회 전가 95초는 한도 내"
  },
  "recovery_compare": {
    "no_action": { "spillback_time_sec": 1240, "recovery_time_sec": 780, "total_travel_time_sec": 51840, "worst_approach_delay_sec": 310 },
    "applied": { "spillback_time_sec": 360, "recovery_time_sec": 420, "total_travel_time_sec": 44900, "worst_approach_delay_sec": 296 },
    "improvement": { "spillback_time_pct": -71.0, "recovery_time_pct": -46.2, "total_travel_time_pct": -13.4, "worst_approach_delay_pct": -4.5 }
  }
}
;
