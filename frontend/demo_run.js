window.DEMO_RUN = {
  "approval": {
    "decided_at": "2026-07-29T20:25:09+09:00",
    "operator": "demo_operator",
    "policy_id": "corridor_gating",
    "reason": "QA v2 가드 통과 후보 중 규칙 기반 안전 점수가 가장 높음",
    "requested_at": "2026-07-29T20:25:09+09:00",
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
            "detail": "성금교차로 서측 진입로 진입로 P95 지체가 기준 대비 55.4% 악화. 허용한도 15.0% 초과"
          },
          {
            "code": "FAIRNESS_P95_EXCEEDED",
            "detail": "청사교차로 남측 진입로 진입로 P95 지체가 기준 대비 938.5% 악화. 허용한도 15.0% 초과"
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
  "generated_at": "2026-07-29T20:25:09+09:00",
  "network": {
    "approaches": [
      "성금교차로 북측 진입로",
      "성금교차로 서측 진입로",
      "청사교차로 남측 진입로",
      "세종교차로 동측 진입로"
    ],
    "junctions": [
      {
        "display_name": "성금교차로",
        "node_ids": [
          "4130092501",
          "4130092502",
          "4130092503",
          "4130092504"
        ]
      },
      {
        "display_name": "청사교차로",
        "node_ids": [
          "4130102901",
          "4130102902",
          "4130102903",
          "4130102904"
        ]
      },
      {
        "display_name": "세종교차로",
        "node_ids": [
          "4130138001",
          "4130138002",
          "4130138003",
          "4130138004"
        ]
      }
    ],
    "links": [
      {
        "display_name": "성금교차로 → 청사교차로 · 절재로",
        "from": "성금교차로",
        "link_id": "seonggeum-cheongsa-jeoljae",
        "source_from_node_id": "4130092502",
        "source_length_m": 553.7,
        "source_link_ids": [
          "4130260500",
          "4130260501",
          "4130261100",
          "4130261101",
          "4130260400",
          "4130258200"
        ],
        "source_to_node_id": "4130102903",
        "synthetic_storage_veh": 22,
        "to": "청사교차로"
      },
      {
        "display_name": "청사교차로 → 세종교차로 · 절재로",
        "from": "청사교차로",
        "link_id": "cheongsa-sejong-jeoljae",
        "source_from_node_id": "4130102902",
        "source_length_m": 2669.9,
        "source_link_ids": [
          "4130254200",
          "4130251800",
          "4130251802",
          "4130245001",
          "4130242000",
          "4130242002",
          "4130242001",
          "4130225400",
          "4130225403",
          "4130225402"
        ],
        "source_to_node_id": "4130138003",
        "synthetic_storage_veh": 18,
        "to": "세종교차로"
      },
      {
        "display_name": "성금교차로 → 세종교차로 · 절재로 대체 경로",
        "from": "성금교차로",
        "link_id": "seonggeum-sejong-alternative",
        "source_from_node_id": "4130092502",
        "source_length_m": 3234.3,
        "source_link_ids": [
          "4130260500",
          "4130260501",
          "4130261100",
          "4130261101",
          "4130260400",
          "4130254400",
          "4130254401",
          "4130251800",
          "4130251802",
          "4130245001",
          "4130242000",
          "4130242002",
          "4130242001",
          "4130225400",
          "4130225403",
          "4130225402"
        ],
        "source_to_node_id": "4130138003",
        "synthetic_storage_veh": 60,
        "to": "세종교차로"
      }
    ],
    "model_limitations": "대기열·저장공간·수요·강우 용량·정책 효과는 실제 세종 측정값이 아닌 provisional 합성 입력이다. 실제 도로 제어나 성과를 뜻하지 않는다.",
    "reference": {
      "derived_files": [
        "data/public/2026-07-29/sejong_nodelink_node.geojson",
        "data/public/2026-07-29/sejong_nodelink_link.geojson"
      ],
      "limitations": "공간망 참조일 뿐, 실시간 교통량·신호현시·차로 운영·정책 효과를 보정하지 않는다.",
      "link_count": 11893,
      "node_count": 8768,
      "source": "국가교통정보센터 전국표준노드링크 2026-07-16, 세종 지역코드 413",
      "usage": "화면의 교차로 표시명과 링크 연결 관계"
    }
  },
  "network_version": "sejong-nodelink-20260716-v1",
  "note": "rainflow-kpi-v2로 재동결한 provisional 합성 데모 결과. 실제 세종시 실측 성과나 실제 도로 제어 결과가 아니다.",
  "policies": [
    {
      "candidate_hash": "60ed4286b4ee6490c1b08032ee944fd9e77ed07ccf0ff672b92b24b210b89d06",
      "delta_vs_no_action": {
        "spillback_time_pct": 0.0,
        "total_travel_time_pct": 0.0,
        "worst_approach_delay_pct": 0.0
      },
      "explanation": "기존 양보운전 유지. spillback 누적 1980초, 총 통행시간 265228초가 비교 기준선이 된다.",
      "extra": {
        "approach_p95_delay": {
          "성금교차로 북측 진입로": 1099.4,
          "성금교차로 서측 진입로": 278.3,
          "세종교차로 동측 진입로": 0.0,
          "청사교차로 남측 진입로": 70.1
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
          "cheongsa-sejong-jeoljae": 1980.0,
          "seonggeum-cheongsa-jeoljae": 1785.0
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
      "candidate_hash": "42cc78249382a68b179f825a3db7880ce7da2a31513a9eed515a705c27f55cbb",
      "delta_vs_no_action": {
        "spillback_time_pct": -62.4,
        "total_travel_time_pct": -41.6,
        "worst_approach_delay_pct": -33.8
      },
      "explanation": "고정 미터링 적용 시 무대응 대비 spillback 누적 -62.4%, 총 통행시간 -41.6%. 가드 위반(FAIRNESS_P95_EXCEEDED, FAIRNESS_P95_EXCEEDED)으로 적용 불가.",
      "extra": {
        "approach_p95_delay": {
          "성금교차로 북측 진입로": 259.9,
          "성금교차로 서측 진입로": 432.5,
          "세종교차로 동측 진입로": 0.0,
          "청사교차로 남측 진입로": 728.0
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
          "cheongsa-sejong-jeoljae": 745.0,
          "seonggeum-cheongsa-jeoljae": 600.0
        }
      },
      "guard": {
        "passed": false,
        "rule_version": "rainflow-guard-v2",
        "violations": [
          {
            "code": "FAIRNESS_P95_EXCEEDED",
            "detail": "성금교차로 서측 진입로 진입로 P95 지체가 기준 대비 55.4% 악화. 허용한도 15.0% 초과",
            "observed_pct": 55.4,
            "threshold_pct": 15.0
          },
          {
            "code": "FAIRNESS_P95_EXCEEDED",
            "detail": "청사교차로 남측 진입로 진입로 P95 지체가 기준 대비 938.5% 악화. 허용한도 15.0% 초과",
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
      "candidate_hash": "dad35cd61630783f4ea256d31759ea58a0207cf981e10bacaab9c82b75a98ad3",
      "delta_vs_no_action": {
        "spillback_time_pct": -100.0,
        "total_travel_time_pct": -77.3,
        "worst_approach_delay_pct": -96.7
      },
      "explanation": "연속 게이팅 적용 시 무대응 대비 spillback 누적 -100.0%, 총 통행시간 -77.3%. 모든 안전·공정성 가드를 통과했다.",
      "extra": {
        "approach_p95_delay": {
          "성금교차로 북측 진입로": 36.1,
          "성금교차로 서측 진입로": 0.0,
          "세종교차로 동측 진입로": 0.0,
          "청사교차로 남측 진입로": 0.0
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
      "corridor_gating": "dad35cd61630783f4ea256d31759ea58a0207cf981e10bacaab9c82b75a98ad3",
      "fixed_metering": "42cc78249382a68b179f825a3db7880ce7da2a31513a9eed515a705c27f55cbb",
      "no_action": "60ed4286b4ee6490c1b08032ee944fd9e77ed07ccf0ff672b92b24b210b89d06"
    },
    "freeze_id": "freeze-20260729-202509-kst",
    "git_commit_sha": "20ce47135281f1c93ebf84555ba94dae113c0418",
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
    "network_version": "sejong-nodelink-20260716-v1",
    "parameter_set_version": "rainflow-provisional-v2",
    "policy_version": "rainflow-policy-v1",
    "result_checksum": "c9088907640696c315685619ce18ae1529ceb8bc1e993bb36c0f080b7ce4ed89",
    "rule_version": "rainflow-guard-v2",
    "scoring_version": "rainflow-rule-v1",
    "simulator_version": "rainflow-queue-v2",
    "source_live_run_id": "live-rain_spillback_a-s42-f3727bcd00",
    "source_tree_checksum": "94d556a6de2f09c3d432465edd63be156df494a1548a6ef69516591ab0e55efd"
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
          "display_name": "성금교차로 → 청사교차로 · 절재로",
          "link_id": "seonggeum-cheongsa-jeoljae",
          "occupancy_ratio": 0.06,
          "queue_veh": 1.2,
          "spillback": false
        },
        {
          "display_name": "청사교차로 → 세종교차로 · 절재로",
          "link_id": "cheongsa-sejong-jeoljae",
          "occupancy_ratio": 0.02,
          "queue_veh": 0.4,
          "spillback": false
        },
        {
          "display_name": "성금교차로 → 세종교차로 · 절재로 대체 경로",
          "link_id": "seonggeum-sejong-alternative",
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
          "display_name": "성금교차로 → 청사교차로 · 절재로",
          "link_id": "seonggeum-cheongsa-jeoljae",
          "occupancy_ratio": 0.05,
          "queue_veh": 1.2,
          "spillback": false
        },
        {
          "display_name": "청사교차로 → 세종교차로 · 절재로",
          "link_id": "cheongsa-sejong-jeoljae",
          "occupancy_ratio": 0.08,
          "queue_veh": 1.5,
          "spillback": false
        },
        {
          "display_name": "성금교차로 → 세종교차로 · 절재로 대체 경로",
          "link_id": "seonggeum-sejong-alternative",
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
          "display_name": "성금교차로 → 청사교차로 · 절재로",
          "link_id": "seonggeum-cheongsa-jeoljae",
          "occupancy_ratio": 0.06,
          "queue_veh": 1.3,
          "spillback": false
        },
        {
          "display_name": "청사교차로 → 세종교차로 · 절재로",
          "link_id": "cheongsa-sejong-jeoljae",
          "occupancy_ratio": 0.1,
          "queue_veh": 1.8,
          "spillback": false
        },
        {
          "display_name": "성금교차로 → 세종교차로 · 절재로 대체 경로",
          "link_id": "seonggeum-sejong-alternative",
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
          "display_name": "성금교차로 → 청사교차로 · 절재로",
          "link_id": "seonggeum-cheongsa-jeoljae",
          "occupancy_ratio": 0.06,
          "queue_veh": 1.4,
          "spillback": false
        },
        {
          "display_name": "청사교차로 → 세종교차로 · 절재로",
          "link_id": "cheongsa-sejong-jeoljae",
          "occupancy_ratio": 0.1,
          "queue_veh": 1.7,
          "spillback": false
        },
        {
          "display_name": "성금교차로 → 세종교차로 · 절재로 대체 경로",
          "link_id": "seonggeum-sejong-alternative",
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
          "display_name": "성금교차로 → 청사교차로 · 절재로",
          "link_id": "seonggeum-cheongsa-jeoljae",
          "occupancy_ratio": 0.06,
          "queue_veh": 1.3,
          "spillback": false
        },
        {
          "display_name": "청사교차로 → 세종교차로 · 절재로",
          "link_id": "cheongsa-sejong-jeoljae",
          "occupancy_ratio": 0.1,
          "queue_veh": 1.7,
          "spillback": false
        },
        {
          "display_name": "성금교차로 → 세종교차로 · 절재로 대체 경로",
          "link_id": "seonggeum-sejong-alternative",
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
          "display_name": "성금교차로 → 청사교차로 · 절재로",
          "link_id": "seonggeum-cheongsa-jeoljae",
          "occupancy_ratio": 0.06,
          "queue_veh": 1.4,
          "spillback": false
        },
        {
          "display_name": "청사교차로 → 세종교차로 · 절재로",
          "link_id": "cheongsa-sejong-jeoljae",
          "occupancy_ratio": 0.1,
          "queue_veh": 1.7,
          "spillback": false
        },
        {
          "display_name": "성금교차로 → 세종교차로 · 절재로 대체 경로",
          "link_id": "seonggeum-sejong-alternative",
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
          "display_name": "성금교차로 → 청사교차로 · 절재로",
          "link_id": "seonggeum-cheongsa-jeoljae",
          "occupancy_ratio": 0.06,
          "queue_veh": 1.3,
          "spillback": false
        },
        {
          "display_name": "청사교차로 → 세종교차로 · 절재로",
          "link_id": "cheongsa-sejong-jeoljae",
          "occupancy_ratio": 0.21,
          "queue_veh": 3.8,
          "spillback": false
        },
        {
          "display_name": "성금교차로 → 세종교차로 · 절재로 대체 경로",
          "link_id": "seonggeum-sejong-alternative",
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
          "display_name": "성금교차로 → 청사교차로 · 절재로",
          "link_id": "seonggeum-cheongsa-jeoljae",
          "occupancy_ratio": 0.07,
          "queue_veh": 1.5,
          "spillback": false
        },
        {
          "display_name": "청사교차로 → 세종교차로 · 절재로",
          "link_id": "cheongsa-sejong-jeoljae",
          "occupancy_ratio": 0.45,
          "queue_veh": 8.0,
          "spillback": false
        },
        {
          "display_name": "성금교차로 → 세종교차로 · 절재로 대체 경로",
          "link_id": "seonggeum-sejong-alternative",
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
          "display_name": "성금교차로 → 청사교차로 · 절재로",
          "link_id": "seonggeum-cheongsa-jeoljae",
          "occupancy_ratio": 0.07,
          "queue_veh": 1.5,
          "spillback": false
        },
        {
          "display_name": "청사교차로 → 세종교차로 · 절재로",
          "link_id": "cheongsa-sejong-jeoljae",
          "occupancy_ratio": 0.69,
          "queue_veh": 12.5,
          "spillback": false
        },
        {
          "display_name": "성금교차로 → 세종교차로 · 절재로 대체 경로",
          "link_id": "seonggeum-sejong-alternative",
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
          "display_name": "성금교차로 → 청사교차로 · 절재로",
          "link_id": "seonggeum-cheongsa-jeoljae",
          "occupancy_ratio": 0.07,
          "queue_veh": 1.5,
          "spillback": false
        },
        {
          "display_name": "청사교차로 → 세종교차로 · 절재로",
          "link_id": "cheongsa-sejong-jeoljae",
          "occupancy_ratio": 0.99,
          "queue_veh": 17.9,
          "spillback": true
        },
        {
          "display_name": "성금교차로 → 세종교차로 · 절재로 대체 경로",
          "link_id": "seonggeum-sejong-alternative",
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
          "display_name": "성금교차로 → 청사교차로 · 절재로",
          "link_id": "seonggeum-cheongsa-jeoljae",
          "occupancy_ratio": 0.92,
          "queue_veh": 20.2,
          "spillback": false
        },
        {
          "display_name": "청사교차로 → 세종교차로 · 절재로",
          "link_id": "cheongsa-sejong-jeoljae",
          "occupancy_ratio": 1.0,
          "queue_veh": 18.0,
          "spillback": true
        },
        {
          "display_name": "성금교차로 → 세종교차로 · 절재로 대체 경로",
          "link_id": "seonggeum-sejong-alternative",
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
          "display_name": "성금교차로 → 청사교차로 · 절재로",
          "link_id": "seonggeum-cheongsa-jeoljae",
          "occupancy_ratio": 1.0,
          "queue_veh": 22.0,
          "spillback": true
        },
        {
          "display_name": "청사교차로 → 세종교차로 · 절재로",
          "link_id": "cheongsa-sejong-jeoljae",
          "occupancy_ratio": 1.0,
          "queue_veh": 18.0,
          "spillback": true
        },
        {
          "display_name": "성금교차로 → 세종교차로 · 절재로 대체 경로",
          "link_id": "seonggeum-sejong-alternative",
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
          "display_name": "성금교차로 → 청사교차로 · 절재로",
          "link_id": "seonggeum-cheongsa-jeoljae",
          "occupancy_ratio": 1.0,
          "queue_veh": 22.0,
          "spillback": true
        },
        {
          "display_name": "청사교차로 → 세종교차로 · 절재로",
          "link_id": "cheongsa-sejong-jeoljae",
          "occupancy_ratio": 1.0,
          "queue_veh": 18.0,
          "spillback": true
        },
        {
          "display_name": "성금교차로 → 세종교차로 · 절재로 대체 경로",
          "link_id": "seonggeum-sejong-alternative",
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
          "display_name": "성금교차로 → 청사교차로 · 절재로",
          "link_id": "seonggeum-cheongsa-jeoljae",
          "occupancy_ratio": 1.0,
          "queue_veh": 22.0,
          "spillback": true
        },
        {
          "display_name": "청사교차로 → 세종교차로 · 절재로",
          "link_id": "cheongsa-sejong-jeoljae",
          "occupancy_ratio": 1.0,
          "queue_veh": 18.0,
          "spillback": true
        },
        {
          "display_name": "성금교차로 → 세종교차로 · 절재로 대체 경로",
          "link_id": "seonggeum-sejong-alternative",
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
          "display_name": "성금교차로 → 청사교차로 · 절재로",
          "link_id": "seonggeum-cheongsa-jeoljae",
          "occupancy_ratio": 1.0,
          "queue_veh": 22.0,
          "spillback": true
        },
        {
          "display_name": "청사교차로 → 세종교차로 · 절재로",
          "link_id": "cheongsa-sejong-jeoljae",
          "occupancy_ratio": 1.0,
          "queue_veh": 18.0,
          "spillback": true
        },
        {
          "display_name": "성금교차로 → 세종교차로 · 절재로 대체 경로",
          "link_id": "seonggeum-sejong-alternative",
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
          "display_name": "성금교차로 → 청사교차로 · 절재로",
          "link_id": "seonggeum-cheongsa-jeoljae",
          "occupancy_ratio": 1.0,
          "queue_veh": 22.0,
          "spillback": true
        },
        {
          "display_name": "청사교차로 → 세종교차로 · 절재로",
          "link_id": "cheongsa-sejong-jeoljae",
          "occupancy_ratio": 1.0,
          "queue_veh": 18.0,
          "spillback": true
        },
        {
          "display_name": "성금교차로 → 세종교차로 · 절재로 대체 경로",
          "link_id": "seonggeum-sejong-alternative",
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
          "display_name": "성금교차로 → 청사교차로 · 절재로",
          "link_id": "seonggeum-cheongsa-jeoljae",
          "occupancy_ratio": 1.0,
          "queue_veh": 22.0,
          "spillback": true
        },
        {
          "display_name": "청사교차로 → 세종교차로 · 절재로",
          "link_id": "cheongsa-sejong-jeoljae",
          "occupancy_ratio": 1.0,
          "queue_veh": 18.0,
          "spillback": true
        },
        {
          "display_name": "성금교차로 → 세종교차로 · 절재로 대체 경로",
          "link_id": "seonggeum-sejong-alternative",
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
          "display_name": "성금교차로 → 청사교차로 · 절재로",
          "link_id": "seonggeum-cheongsa-jeoljae",
          "occupancy_ratio": 1.0,
          "queue_veh": 22.0,
          "spillback": true
        },
        {
          "display_name": "청사교차로 → 세종교차로 · 절재로",
          "link_id": "cheongsa-sejong-jeoljae",
          "occupancy_ratio": 1.0,
          "queue_veh": 18.0,
          "spillback": true
        },
        {
          "display_name": "성금교차로 → 세종교차로 · 절재로 대체 경로",
          "link_id": "seonggeum-sejong-alternative",
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
          "display_name": "성금교차로 → 청사교차로 · 절재로",
          "link_id": "seonggeum-cheongsa-jeoljae",
          "occupancy_ratio": 1.0,
          "queue_veh": 22.0,
          "spillback": true
        },
        {
          "display_name": "청사교차로 → 세종교차로 · 절재로",
          "link_id": "cheongsa-sejong-jeoljae",
          "occupancy_ratio": 1.0,
          "queue_veh": 18.0,
          "spillback": true
        },
        {
          "display_name": "성금교차로 → 세종교차로 · 절재로 대체 경로",
          "link_id": "seonggeum-sejong-alternative",
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
          "display_name": "성금교차로 → 청사교차로 · 절재로",
          "link_id": "seonggeum-cheongsa-jeoljae",
          "occupancy_ratio": 1.0,
          "queue_veh": 22.0,
          "spillback": true
        },
        {
          "display_name": "청사교차로 → 세종교차로 · 절재로",
          "link_id": "cheongsa-sejong-jeoljae",
          "occupancy_ratio": 1.0,
          "queue_veh": 18.0,
          "spillback": true
        },
        {
          "display_name": "성금교차로 → 세종교차로 · 절재로 대체 경로",
          "link_id": "seonggeum-sejong-alternative",
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
