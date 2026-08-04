// 정책 후보 3종
export type PolicyId = 'no_action' | 'fixed_metering' | 'corridor_gating';

// 화면 상태 7종
export type ScreenState =
  | 'normal'
  | 'rain_warning'
  | 'spillback'
  | 'policy_compare'
  | 'safety_review'
  | 'operator_approval'
  | 'recovery_compare';

// KPI 4종
export interface KPI {
  spillback_time_sec: number;
  recovery_time_sec: number;
  recovery_observed?: boolean;
  total_travel_time_sec: number;
  worst_approach_delay_sec: number;
}

// 가드 위반
export interface Violation {
  code: string;
  detail: string;
  threshold_pct?: number;
  observed_pct?: number;
}

// 정책 객체
export interface Policy {
  policy_id: PolicyId;
  label: string;
  kpi: KPI;
  delta_vs_no_action: {
    spillback_time_pct: number;
    total_travel_time_pct: number;
    worst_approach_delay_pct: number;
  };
  guard: {
    passed: boolean;
    violations: Violation[];
    note: string;
  };
  explanation: string;
}

// 타임라인 한 스텝
export interface TimelineStep {
  t_sec: number;
  screen_state: ScreenState;
  rain_level: string;
  links: Array<{
    link_id: string;
    occupancy_ratio: number;
    queue_veh: number;
    spillback: boolean;
  }>;
  note: string;
}

// 전체 DemoRun 타입
export interface DemoRun {
  run_id: string;
  result_source: 'fixture' | 'live_simulation' | 'cached_simulation';
  provisional: boolean;
  scenario: {
    scenario_id: string;
    seed: number;
    rain_level: string;
  };
  timeline: TimelineStep[];
  policies: Policy[];
  approval: {
    status: string;
    policy_id: PolicyId;
    operator: string;
    reason: string;
  };
  recovery_compare: {
    no_action: KPI;
    applied: KPI;
    improvement: {
      spillback_time_pct: number;
      recovery_time_pct: number;
      total_travel_time_pct: number;
      worst_approach_delay_pct: number;
    };
  };
}
