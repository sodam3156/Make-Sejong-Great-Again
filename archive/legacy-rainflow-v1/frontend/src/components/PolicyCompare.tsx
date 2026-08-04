import type { Policy, PolicyId } from '../types/demo';

interface Props {
  policies: Policy[];
  approvedPolicyId: PolicyId;
}

function PctCell({ v }: { v: number }) {
  const color = v < 0 ? '#34d399' : v > 0 ? '#f87171' : '#8a93a8';
  const sign  = v > 0 ? '+' : '';
  return (
    <td style={{ padding: '6px 8px', borderBottom: '1px solid #22293a', color, fontWeight: 600 }}>
      {v === 0 ? '-' : `${sign}${v}%`}
    </td>
  );
}

const HEADERS = [
  '정책', 'Spillback wall-clock(초)', '누적 체류시간(vehicle-seconds)', 'P95 대기 proxy(초)',
  'Δ Spillback', 'Δ 통행시간', 'Δ 최악지체',
];

export function PolicyCompare({ policies, approvedPolicyId }: Props) {
  return (
    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
      <thead>
        <tr>
          {HEADERS.map((h) => (
            <th key={h} style={{
              textAlign: 'left', padding: '6px 8px',
              color: '#8a93a8', fontSize: 12,
              borderBottom: '1px solid #22293a',
            }}>
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {policies.map((p) => {
          const isRejected = !p.guard.passed;
          const isChosen   = p.policy_id === approvedPolicyId;
          const d = p.delta_vs_no_action;

          return (
            <tr
              key={p.policy_id}
              style={{ background: isRejected ? 'rgba(248,113,113,0.08)' : 'transparent' }}
            >
              {/* 정책 이름 */}
              <td style={{
                padding: '6px 8px',
                borderBottom: '1px solid #22293a',
                borderLeft: isRejected
                  ? '3px solid #f87171'
                  : isChosen
                  ? '3px solid #34d399'
                  : '3px solid transparent',
              }}>
                {p.label}
                {isRejected && <span style={{ color: '#f87171' }}> (탈락)</span>}
                {isChosen   && <span style={{ color: '#34d399' }}> (선택)</span>}
              </td>

              {/* KPI 수치 */}
              <td style={{ padding: '6px 8px', borderBottom: '1px solid #22293a' }}>
                {p.kpi.spillback_time_sec}
              </td>
              <td style={{ padding: '6px 8px', borderBottom: '1px solid #22293a' }}>
                {p.kpi.total_travel_time_sec}
              </td>
              <td style={{ padding: '6px 8px', borderBottom: '1px solid #22293a' }}>
                {p.kpi.worst_approach_delay_sec}
              </td>

              {/* 변화율 */}
              <PctCell v={d.spillback_time_pct} />
              <PctCell v={d.total_travel_time_pct} />
              <PctCell v={d.worst_approach_delay_pct} />
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
