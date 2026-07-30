window.DEMO_RUN = {
  "approval": {
    "decided_at": "2026-07-30T15:38:57+09:00",
    "operator": "demo_operator",
    "policy_id": "corridor_gating",
    "reason": "QA v2 가드 통과 후보 중 규칙 기반 안전 점수가 가장 높음",
    "requested_at": "2026-07-30T15:38:57+09:00",
    "result_source": "fixture",
    "status": "approved",
    "workflow_state": "EVALUATED"
  },
  "dataset": {
    "adapter_version": "builtin-synthetic-v1",
    "data_class": "synthetic",
    "dataset_id": "synthetic-v0",
    "default": true,
    "schema_version": "rainflow-dataset-v1"
  },
  "decision": {
    "explanation_mode": "rule_based",
    "policy_assessments": [
      {
        "evidence": [
          {
            "code": "GUARD_PASSED",
            "value": true
          },
          {
            "assessment": "improved",
            "available": true,
            "delta_pct": -100.0,
            "metric": "spillback_time_pct",
            "weight": 0.5
          },
          {
            "assessment": "improved",
            "available": true,
            "delta_pct": -77.3,
            "metric": "total_travel_time_pct",
            "weight": 0.35
          },
          {
            "assessment": "improved",
            "available": true,
            "delta_pct": -96.7,
            "metric": "worst_approach_delay_pct",
            "weight": 0.15
          }
        ],
        "guard_passed": true,
        "policy_id": "corridor_gating",
        "rank": 1,
        "reasons": [
          {
            "code": "BEST_SAFE_SCORE",
            "detail": "Highest score among guard-passing policies."
          }
        ],
        "risks": [],
        "score": 91.56
      },
      {
        "evidence": [
          {
            "code": "GUARD_PASSED",
            "value": true
          },
          {
            "assessment": "unchanged",
            "available": true,
            "delta_pct": 0.0,
            "metric": "spillback_time_pct",
            "weight": 0.5
          },
          {
            "assessment": "unchanged",
            "available": true,
            "delta_pct": 0.0,
            "metric": "total_travel_time_pct",
            "weight": 0.35
          },
          {
            "assessment": "unchanged",
            "available": true,
            "delta_pct": 0.0,
            "metric": "worst_approach_delay_pct",
            "weight": 0.15
          }
        ],
        "guard_passed": true,
        "policy_id": "no_action",
        "rank": 2,
        "reasons": [
          {
            "code": "SAFE_BASELINE",
            "detail": "Retained as the fallback if the recommended policy cannot be applied."
          }
        ],
        "risks": [],
        "score": 0.0
      },
      {
        "evidence": [
          {
            "code": "GUARD_FAILED",
            "value": false
          },
          {
            "assessment": "improved",
            "available": true,
            "delta_pct": -62.4,
            "metric": "spillback_time_pct",
            "weight": 0.5
          },
          {
            "assessment": "improved",
            "available": true,
            "delta_pct": -41.6,
            "metric": "total_travel_time_pct",
            "weight": 0.35
          },
          {
            "assessment": "improved",
            "available": true,
            "delta_pct": -33.8,
            "metric": "worst_approach_delay_pct",
            "weight": 0.15
          }
        ],
        "guard_passed": false,
        "policy_id": "fixed_metering",
        "rank": 3,
        "reasons": [
          {
            "code": "EXCLUDED_BY_GUARD",
            "detail": "A guard-failing policy cannot be recommended."
          }
        ],
        "risks": [
          {
            "code": "FAIRNESS_P95_EXCEEDED",
            "detail": "성금교차로 서측 진입로 P95 지체가 기준 대비 55.4% 악화. 허용한도 15.0% 초과"
          },
          {
            "code": "FAIRNESS_P95_EXCEEDED",
            "detail": "청사교차로 남측 진입로 P95 지체가 기준 대비 938.5% 악화. 허용한도 15.0% 초과"
          }
        ],
        "score": 50.83
      }
    ],
    "ranked_policy_ids": [
      "corridor_gating",
      "no_action",
      "fixed_metering"
    ],
    "recommended_policy_id": "corridor_gating",
    "scoring_version": "rainflow-rule-v1"
  },
  "elapsed_ms": 0.0,
  "generated_at": "2026-07-30T15:38:57+09:00",
  "network": {
    "approaches": [
      "R1_N",
      "R1_W",
      "R2_S",
      "R3_E"
    ],
    "corridor_label": "절재로 회랑",
    "intersections": [
      {
        "display_name": "성금교차로",
        "engine_id": "R1",
        "order": 1,
        "representative_lonlat": [
          127.2616548,
          36.5086037
        ],
        "standard_node_ids": [
          "4130092501",
          "4130092502",
          "4130092503",
          "4130092504"
        ]
      },
      {
        "display_name": "청사교차로",
        "engine_id": "R2",
        "order": 2,
        "representative_lonlat": [
          127.2678512,
          36.5079813
        ],
        "standard_node_ids": [
          "4130102901",
          "4130102902",
          "4130102903",
          "4130102904"
        ]
      },
      {
        "display_name": "세종교차로",
        "engine_id": "R3",
        "order": 3,
        "representative_lonlat": [
          127.2961782,
          36.5005138
        ],
        "standard_node_ids": [
          "4130138001",
          "4130138002",
          "4130138003",
          "4130138004"
        ]
      }
    ],
    "links": [
      {
        "display_name": "성금교차로 → 청사교차로",
        "from": "R1",
        "from_display_name": "성금교차로",
        "link_id": "L12",
        "real_road": true,
        "storage_veh": 22,
        "to": "R2",
        "to_display_name": "청사교차로"
      },
      {
        "display_name": "청사교차로 → 세종교차로",
        "from": "R2",
        "from_display_name": "청사교차로",
        "link_id": "L23",
        "real_road": true,
        "storage_veh": 18,
        "to": "R3",
        "to_display_name": "세종교차로"
      },
      {
        "display_name": "모형 가정 우회경로 (실제 도로 아님)",
        "from": "R1",
        "from_display_name": "성금교차로",
        "link_id": "BYPASS",
        "real_road": false,
        "storage_veh": 60,
        "to": "R3",
        "to_display_name": "세종교차로"
      }
    ],
    "road_name": "절재로",
    "verification": {
      "demand": "synthetic",
      "intersection_form": "unverified",
      "intersection_identity": "verified",
      "intersection_position": "verified",
      "link_capacity": "synthetic",
      "link_geometry": "unmodeled",
      "note": "교차로 이름과 위치는 공식 표준노드링크로 확인했다. 교차로 형식(회전 또는 신호), 링크 길이·차로수·용량, 수요는 아직 확인하지 않았고 이 실행의 값은 모형 가정값이다. 확인 전 값을 실측값처럼 표시하지 않는다.",
      "source": "국토교통부 표준노드링크 [2026-07-16] 전국 원본에서 세종 지역코드 413 추출"
    }
  },
  "network_version": "sejong-jeoljaero-v1",
  "note": "rainflow-kpi-v2로 재동결한 provisional 합성 데모 결과. 실제 세종시 실측 성과나 실제 도로 제어 결과가 아니다.",
  "policies": [
    {
      "candidate_hash": "1b8abf877414569c4d34b295385ba5ce79c7a7ed614c5d0e8dba4243e268af3e",
      "delta_vs_no_action": {
        "spillback_time_pct": 0.0,
        "total_travel_time_pct": 0.0,
        "worst_approach_delay_pct": 0.0
      },
      "explanation": "기존 양보운전 유지. spillback 누적 1980초, 총 통행시간 265228초가 비교 기준선이 된다.",
      "extra": {
        "approach_p95_delay": {
          "R1_N": 1099.4,
          "R1_W": 278.3,
          "R2_S": 70.1,
          "R3_E": 0.0
        },
        "completed_trips": 1310,
        "diversion_delay_sec": 0.0,
        "diversion_freeflow_seconds": 0.0,
        "diversion_vehicle_seconds": 0.0,
        "diverted_vehicles": 0.0,
        "modeled_vehicle_seconds": 265227.8,
        "safety_proxy_hard_brakes": 1131,
        "spillback_events": 2,
        "spillback_link_seconds": {
          "L12": 1785.0,
          "L23": 1980.0
        }
      },
      "guard": {
        "note": "기준선. 가드 판정 대상 아님",
        "passed": true,
        "rule_version": "rainflow-guard-v2",
        "violations": []
      },
      "kpi": {
        "recovery_observed": false,
        "recovery_time_sec": 900,
        "spillback_time_sec": 1980.0,
        "total_travel_time_sec": 265228.0,
        "worst_approach_delay_sec": 1099.4
      },
      "label": "무대응",
      "policy_id": "no_action",
      "rank": 2,
      "score": 0.0
    },
    {
      "candidate_hash": "55304be81fe0117c93c98029a53023d1e2c49d6f3debe1506def365fbc47c0dc",
      "delta_vs_no_action": {
        "spillback_time_pct": -62.4,
        "total_travel_time_pct": -41.6,
        "worst_approach_delay_pct": -33.8
      },
      "explanation": "고정 미터링 적용 시 무대응 대비 spillback 누적 -62.4%, 총 통행시간 -41.6%. 가드 위반(FAIRNESS_P95_EXCEEDED, FAIRNESS_P95_EXCEEDED)으로 적용 불가.",
      "extra": {
        "approach_p95_delay": {
          "R1_N": 259.9,
          "R1_W": 432.5,
          "R2_S": 728.0,
          "R3_E": 0.0
        },
        "completed_trips": 1404,
        "diversion_delay_sec": 0.0,
        "diversion_freeflow_seconds": 0.0,
        "diversion_vehicle_seconds": 0.0,
        "diverted_vehicles": 0.0,
        "modeled_vehicle_seconds": 154800.3,
        "safety_proxy_hard_brakes": 414,
        "spillback_events": 2,
        "spillback_link_seconds": {
          "L12": 600.0,
          "L23": 745.0
        }
      },
      "guard": {
        "passed": false,
        "rule_version": "rainflow-guard-v2",
        "violations": [
          {
            "approach": "R1_W",
            "code": "FAIRNESS_P95_EXCEEDED",
            "detail": "성금교차로 서측 진입로 P95 지체가 기준 대비 55.4% 악화. 허용한도 15.0% 초과",
            "observed_pct": 55.4,
            "threshold_pct": 15.0
          },
          {
            "approach": "R2_S",
            "code": "FAIRNESS_P95_EXCEEDED",
            "detail": "청사교차로 남측 진입로 P95 지체가 기준 대비 938.5% 악화. 허용한도 15.0% 초과",
            "observed_pct": 938.5,
            "threshold_pct": 15.0
          }
        ]
      },
      "kpi": {
        "recovery_observed": false,
        "recovery_time_sec": 900,
        "spillback_time_sec": 745.0,
        "total_travel_time_sec": 154800.0,
        "worst_approach_delay_sec": 728.0
      },
      "label": "고정 미터링",
      "policy_id": "fixed_metering",
      "rank": 3,
      "score": 50.83
    },
    {
      "candidate_hash": "cddb4712471e0e2efd4672b5b62cdc0fdf0e617d8f9b77eef95dbef2a57050dc",
      "delta_vs_no_action": {
        "spillback_time_pct": -100.0,
        "total_travel_time_pct": -77.3,
        "worst_approach_delay_pct": -96.7
      },
      "explanation": "연속 게이팅 적용 시 무대응 대비 spillback 누적 -100.0%, 총 통행시간 -77.3%. 모든 안전·공정성 가드를 통과했다.",
      "extra": {
        "approach_p95_delay": {
          "R1_N": 36.1,
          "R1_W": 0.0,
          "R2_S": 0.0,
          "R3_E": 0.0
        },
        "completed_trips": 1509,
        "diversion_delay_sec": 60.0,
        "diversion_freeflow_seconds": 130.1,
        "diversion_vehicle_seconds": 0.0,
        "diverted_vehicles": 2.2,
        "modeled_vehicle_seconds": 59951.0,
        "safety_proxy_hard_brakes": 0,
        "spillback_events": 0,
        "spillback_link_seconds": {}
      },
      "guard": {
        "passed": true,
        "rule_version": "rainflow-guard-v2",
        "violations": []
      },
      "kpi": {
        "recovery_observed": true,
        "recovery_time_sec": 495,
        "spillback_time_sec": 0.0,
        "total_travel_time_sec": 60081.0,
        "worst_approach_delay_sec": 36.1
      },
      "label": "연속 게이팅",
      "policy_id": "corridor_gating",
      "rank": 1,
      "score": 91.56
    }
  ],
  "provisional": true,
  "recovery_compare": {
    "applied": {
      "recovery_observed": true,
      "recovery_time_sec": 495,
      "spillback_time_sec": 0.0,
      "total_travel_time_sec": 60081.0,
      "worst_approach_delay_sec": 36.1
    },
    "applied_policy_id": "corridor_gating",
    "improvement": {
      "recovery_time_pct": -45.0,
      "spillback_time_pct": -100.0,
      "total_travel_time_pct": -77.3,
      "worst_approach_delay_pct": -96.7
    },
    "no_action": {
      "recovery_observed": false,
      "recovery_time_sec": 900,
      "spillback_time_sec": 1980.0,
      "total_travel_time_sec": 265228.0,
      "worst_approach_delay_sec": 1099.4
    },
    "predicted_if_approved": {
      "improvement": {
        "recovery_time_pct": -45.0,
        "spillback_time_pct": -100.0,
        "total_travel_time_pct": -77.3,
        "worst_approach_delay_pct": -96.7
      },
      "kpi": {
        "recovery_observed": true,
        "recovery_time_sec": 495,
        "spillback_time_sec": 0.0,
        "total_travel_time_sec": 60081.0,
        "worst_approach_delay_sec": 36.1
      },
      "policy_id": "corridor_gating"
    }
  },
  "reproducibility": {
    "candidate_hashes": {
      "corridor_gating": "cddb4712471e0e2efd4672b5b62cdc0fdf0e617d8f9b77eef95dbef2a57050dc",
      "fixed_metering": "55304be81fe0117c93c98029a53023d1e2c49d6f3debe1506def365fbc47c0dc",
      "no_action": "1b8abf877414569c4d34b295385ba5ce79c7a7ed614c5d0e8dba4243e268af3e"
    },
    "freeze_id": "freeze-20260730-153857-kst",
    "git_commit_sha": "b9324ecfde1d74de154a21888e59632e1f50c329",
    "guard_version": "rainflow-guard-v2",
    "input": {
      "data_quality": {
        "data_age_sec": 0.0,
        "device_status": "ok",
        "sensor_available": true
      },
      "dataset_id": "synthetic-v0",
      "scenario_id": "rain_spillback_a",
      "seed": 42
    },
    "kpi_definition_version": "rainflow-kpi-v2",
    "network_version": "sejong-jeoljaero-v1",
    "parameter_set_version": "rainflow-provisional-v2",
    "policy_version": "rainflow-policy-v1",
    "result_checksum": "d5e70cb728442cec8000e9790ea51b5d90b6dd6899737dc6f5d9ea1370995127",
    "rule_version": "rainflow-guard-v2",
    "scoring_version": "rainflow-rule-v1",
    "simulator_version": "rainflow-queue-v2",
    "source_live_run_id": "live-rain_spillback_a-s42-218c686818",
    "source_tree_checksum": "800f2e29c53525b3322d789d26d1c6b0af9d327028baf9912b7d95b88ad77b04"
  },
  "result_source": "fixture",
  "run_id": "fixture-qa-v2-001",
  "safety_guards": {
    "provisional": true,
    "rule_version": "rainflow-guard-v2",
    "rules": [
      {
        "code": "FAIRNESS_P95_EXCEEDED",
        "threshold_pct": 15.0
      },
      {
        "code": "DIVERSION_DELAY_EXCEEDED",
        "threshold_sec": 180.0
      },
      {
        "code": "HARD_BRAKE_PROXY_DEGRADED"
      },
      {
        "code": "DATA_STALE",
        "threshold_sec": 120.0
      },
      {
        "code": "DEVICE_FAULT"
      },
      {
        "code": "CANDIDATE_HASH_MISMATCH"
      },
      {
        "code": "OPERATOR_NOT_APPROVED"
      }
    ]
  },
  "scenario": {
    "data_quality": {
      "data_age_sec": 0.0,
      "device_status": "ok",
      "sensor_available": true
    },
    "duration_sec": 3600,
    "incident": false,
    "phases": {
      "dry_prep_sec": 900,
      "rain_peak_sec": 1800,
      "recovery_sec": 900
    },
    "rain_level": "heavy",
    "scenario_id": "rain_spillback_a",
    "seed": 42
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
  "state_history": [
    {
      "sequence": 1,
      "state": "CREATED"
    },
    {
      "sequence": 2,
      "state": "PREDICTED"
    },
    {
      "sequence": 3,
      "state": "AI_REVIEWED"
    },
    {
      "sequence": 4,
      "state": "SAFETY_PASSED"
    },
    {
      "sequence": 5,
      "state": "HUMAN_APPROVED"
    },
    {
      "sequence": 6,
      "state": "TWIN_APPLIED"
    },
    {
      "sequence": 7,
      "state": "EVALUATED"
    }
  ],
  "timeline": [
    {
      "links": [
        {
          "link_id": "L12",
          "occupancy_ratio": 0.06,
          "queue_veh": 1.2,
          "spillback": false
        },
        {
          "link_id": "L23",
          "occupancy_ratio": 0.02,
          "queue_veh": 0.4,
          "spillback": false
        },
        {
          "link_id": "BYPASS",
          "occupancy_ratio": 0.0,
          "queue_veh": 0.0,
          "spillback": false
        }
      ],
      "note": "건조 기준 상태",
      "rain_level": "dry",
      "screen_state": "normal",
      "t_sec": 0
    },
    {
      "links": [
        {
          "link_id": "L12",
          "occupancy_ratio": 0.05,
          "queue_veh": 1.2,
          "spillback": false
        },
        {
          "link_id": "L23",
          "occupancy_ratio": 0.08,
          "queue_veh": 1.5,
          "spillback": false
        },
        {
          "link_id": "BYPASS",
          "occupancy_ratio": 0.0,
          "queue_veh": 0.0,
          "spillback": false
        }
      ],
      "note": "건조 기준 상태",
      "rain_level": "dry",
      "screen_state": "normal",
      "t_sec": 180
    },
    {
      "links": [
        {
          "link_id": "L12",
          "occupancy_ratio": 0.06,
          "queue_veh": 1.3,
          "spillback": false
        },
        {
          "link_id": "L23",
          "occupancy_ratio": 0.1,
          "queue_veh": 1.8,
          "spillback": false
        },
        {
          "link_id": "BYPASS",
          "occupancy_ratio": 0.0,
          "queue_veh": 0.0,
          "spillback": false
        }
      ],
      "note": "건조 기준 상태",
      "rain_level": "dry",
      "screen_state": "normal",
      "t_sec": 360
    },
    {
      "links": [
        {
          "link_id": "L12",
          "occupancy_ratio": 0.06,
          "queue_veh": 1.4,
          "spillback": false
        },
        {
          "link_id": "L23",
          "occupancy_ratio": 0.1,
          "queue_veh": 1.7,
          "spillback": false
        },
        {
          "link_id": "BYPASS",
          "occupancy_ratio": 0.0,
          "queue_veh": 0.0,
          "spillback": false
        }
      ],
      "note": "건조 기준 상태",
      "rain_level": "dry",
      "screen_state": "normal",
      "t_sec": 540
    },
    {
      "links": [
        {
          "link_id": "L12",
          "occupancy_ratio": 0.06,
          "queue_veh": 1.3,
          "spillback": false
        },
        {
          "link_id": "L23",
          "occupancy_ratio": 0.1,
          "queue_veh": 1.7,
          "spillback": false
        },
        {
          "link_id": "BYPASS",
          "occupancy_ratio": 0.0,
          "queue_veh": 0.0,
          "spillback": false
        }
      ],
      "note": "건조 기준 상태",
      "rain_level": "dry",
      "screen_state": "normal",
      "t_sec": 720
    },
    {
      "links": [
        {
          "link_id": "L12",
          "occupancy_ratio": 0.06,
          "queue_veh": 1.4,
          "spillback": false
        },
        {
          "link_id": "L23",
          "occupancy_ratio": 0.1,
          "queue_veh": 1.7,
          "spillback": false
        },
        {
          "link_id": "BYPASS",
          "occupancy_ratio": 0.0,
          "queue_veh": 0.0,
          "spillback": false
        }
      ],
      "note": "강우 용량 저하 감지",
      "rain_level": "moderate",
      "screen_state": "rain_warning",
      "t_sec": 900
    },
    {
      "links": [
        {
          "link_id": "L12",
          "occupancy_ratio": 0.06,
          "queue_veh": 1.3,
          "spillback": false
        },
        {
          "link_id": "L23",
          "occupancy_ratio": 0.21,
          "queue_veh": 3.8,
          "spillback": false
        },
        {
          "link_id": "BYPASS",
          "occupancy_ratio": 0.0,
          "queue_veh": 0.0,
          "spillback": false
        }
      ],
      "note": "강우 용량 저하 감지",
      "rain_level": "moderate",
      "screen_state": "rain_warning",
      "t_sec": 1080
    },
    {
      "links": [
        {
          "link_id": "L12",
          "occupancy_ratio": 0.07,
          "queue_veh": 1.5,
          "spillback": false
        },
        {
          "link_id": "L23",
          "occupancy_ratio": 0.45,
          "queue_veh": 8.0,
          "spillback": false
        },
        {
          "link_id": "BYPASS",
          "occupancy_ratio": 0.0,
          "queue_veh": 0.0,
          "spillback": false
        }
      ],
      "note": "연결도로 저장한계와 상류 역류 확인",
      "rain_level": "heavy",
      "screen_state": "spillback",
      "t_sec": 1260
    },
    {
      "links": [
        {
          "link_id": "L12",
          "occupancy_ratio": 0.07,
          "queue_veh": 1.5,
          "spillback": false
        },
        {
          "link_id": "L23",
          "occupancy_ratio": 0.69,
          "queue_veh": 12.5,
          "spillback": false
        },
        {
          "link_id": "BYPASS",
          "occupancy_ratio": 0.0,
          "queue_veh": 0.0,
          "spillback": false
        }
      ],
      "note": "연결도로 저장한계와 상류 역류 확인",
      "rain_level": "heavy",
      "screen_state": "spillback",
      "t_sec": 1440
    },
    {
      "links": [
        {
          "link_id": "L12",
          "occupancy_ratio": 0.07,
          "queue_veh": 1.5,
          "spillback": false
        },
        {
          "link_id": "L23",
          "occupancy_ratio": 0.99,
          "queue_veh": 17.9,
          "spillback": true
        },
        {
          "link_id": "BYPASS",
          "occupancy_ratio": 0.0,
          "queue_veh": 0.0,
          "spillback": false
        }
      ],
      "note": "동일 수요·seed에서 세 정책 KPI 비교",
      "rain_level": "heavy",
      "screen_state": "policy_compare",
      "t_sec": 1620
    },
    {
      "links": [
        {
          "link_id": "L12",
          "occupancy_ratio": 0.92,
          "queue_veh": 20.2,
          "spillback": false
        },
        {
          "link_id": "L23",
          "occupancy_ratio": 1.0,
          "queue_veh": 18.0,
          "spillback": true
        },
        {
          "link_id": "BYPASS",
          "occupancy_ratio": 0.0,
          "queue_veh": 0.0,
          "spillback": false
        }
      ],
      "note": "결정론적 안전·공정성 규칙 검사",
      "rain_level": "heavy",
      "screen_state": "safety_review",
      "t_sec": 1800
    },
    {
      "links": [
        {
          "link_id": "L12",
          "occupancy_ratio": 1.0,
          "queue_veh": 22.0,
          "spillback": true
        },
        {
          "link_id": "L23",
          "occupancy_ratio": 1.0,
          "queue_veh": 18.0,
          "spillback": true
        },
        {
          "link_id": "BYPASS",
          "occupancy_ratio": 0.0,
          "queue_veh": 0.0,
          "spillback": false
        }
      ],
      "note": "가드 통과 후보의 운영자 결정 대기",
      "rain_level": "heavy",
      "screen_state": "operator_approval",
      "t_sec": 1980
    },
    {
      "links": [
        {
          "link_id": "L12",
          "occupancy_ratio": 1.0,
          "queue_veh": 22.0,
          "spillback": true
        },
        {
          "link_id": "L23",
          "occupancy_ratio": 1.0,
          "queue_veh": 18.0,
          "spillback": true
        },
        {
          "link_id": "BYPASS",
          "occupancy_ratio": 0.0,
          "queue_veh": 0.0,
          "spillback": false
        }
      ],
      "note": "가드 통과 후보의 운영자 결정 대기",
      "rain_level": "heavy",
      "screen_state": "operator_approval",
      "t_sec": 2160
    },
    {
      "links": [
        {
          "link_id": "L12",
          "occupancy_ratio": 1.0,
          "queue_veh": 22.0,
          "spillback": true
        },
        {
          "link_id": "L23",
          "occupancy_ratio": 1.0,
          "queue_veh": 18.0,
          "spillback": true
        },
        {
          "link_id": "BYPASS",
          "occupancy_ratio": 0.0,
          "queue_veh": 0.0,
          "spillback": false
        }
      ],
      "note": "가드 통과 후보의 운영자 결정 대기",
      "rain_level": "heavy",
      "screen_state": "operator_approval",
      "t_sec": 2340
    },
    {
      "links": [
        {
          "link_id": "L12",
          "occupancy_ratio": 1.0,
          "queue_veh": 22.0,
          "spillback": true
        },
        {
          "link_id": "L23",
          "occupancy_ratio": 1.0,
          "queue_veh": 18.0,
          "spillback": true
        },
        {
          "link_id": "BYPASS",
          "occupancy_ratio": 0.0,
          "queue_veh": 0.0,
          "spillback": false
        }
      ],
      "note": "가드 통과 후보의 운영자 결정 대기",
      "rain_level": "heavy",
      "screen_state": "operator_approval",
      "t_sec": 2520
    },
    {
      "links": [
        {
          "link_id": "L12",
          "occupancy_ratio": 1.0,
          "queue_veh": 22.0,
          "spillback": true
        },
        {
          "link_id": "L23",
          "occupancy_ratio": 1.0,
          "queue_veh": 18.0,
          "spillback": true
        },
        {
          "link_id": "BYPASS",
          "occupancy_ratio": 0.0,
          "queue_veh": 0.0,
          "spillback": false
        }
      ],
      "note": "무대응과 승인 정책의 회복 결과 비교",
      "rain_level": "dry",
      "screen_state": "recovery_compare",
      "t_sec": 2700
    },
    {
      "links": [
        {
          "link_id": "L12",
          "occupancy_ratio": 1.0,
          "queue_veh": 22.0,
          "spillback": true
        },
        {
          "link_id": "L23",
          "occupancy_ratio": 1.0,
          "queue_veh": 18.0,
          "spillback": true
        },
        {
          "link_id": "BYPASS",
          "occupancy_ratio": 0.0,
          "queue_veh": 0.0,
          "spillback": false
        }
      ],
      "note": "무대응과 승인 정책의 회복 결과 비교",
      "rain_level": "dry",
      "screen_state": "recovery_compare",
      "t_sec": 2880
    },
    {
      "links": [
        {
          "link_id": "L12",
          "occupancy_ratio": 1.0,
          "queue_veh": 22.0,
          "spillback": true
        },
        {
          "link_id": "L23",
          "occupancy_ratio": 1.0,
          "queue_veh": 18.0,
          "spillback": true
        },
        {
          "link_id": "BYPASS",
          "occupancy_ratio": 0.0,
          "queue_veh": 0.0,
          "spillback": false
        }
      ],
      "note": "무대응과 승인 정책의 회복 결과 비교",
      "rain_level": "dry",
      "screen_state": "recovery_compare",
      "t_sec": 3060
    },
    {
      "links": [
        {
          "link_id": "L12",
          "occupancy_ratio": 1.0,
          "queue_veh": 22.0,
          "spillback": true
        },
        {
          "link_id": "L23",
          "occupancy_ratio": 1.0,
          "queue_veh": 18.0,
          "spillback": true
        },
        {
          "link_id": "BYPASS",
          "occupancy_ratio": 0.0,
          "queue_veh": 0.0,
          "spillback": false
        }
      ],
      "note": "무대응과 승인 정책의 회복 결과 비교",
      "rain_level": "dry",
      "screen_state": "recovery_compare",
      "t_sec": 3240
    },
    {
      "links": [
        {
          "link_id": "L12",
          "occupancy_ratio": 1.0,
          "queue_veh": 22.0,
          "spillback": true
        },
        {
          "link_id": "L23",
          "occupancy_ratio": 1.0,
          "queue_veh": 18.0,
          "spillback": true
        },
        {
          "link_id": "BYPASS",
          "occupancy_ratio": 0.0,
          "queue_veh": 0.0,
          "spillback": false
        }
      ],
      "note": "무대응과 승인 정책의 회복 결과 비교",
      "rain_level": "dry",
      "screen_state": "recovery_compare",
      "t_sec": 3420
    }
  ],
  "workflow_state": "EVALUATED"
};
