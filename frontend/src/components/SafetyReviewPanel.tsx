// 안전 검토 패널 — safety_review 상태일 때 각 정책의 통과·탈락 사유 표시
import type { Policy } from '../types/demo';

interface Props {
  policies: Policy[];
}

export function SafetyReviewPanel({ policies }: Props) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {policies.map((p) => {
        const passed = p.guard.passed;
        return (
          <div
            key={p.policy_id}
            style={{
              background: passed ? '#10151f' : 'rgba(248,113,113,0.06)',
              border: `1px solid ${passed ? '#22293a' : 'rgba(248,113,113,0.4)'}`,
              borderRadius: 8,
              padding: '10px 14px',
            }}
          >
            {/* 헤더 */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: passed && !p.guard.note ? 0 : 6 }}>
              <span style={{ fontWeight: 700, fontSize: 14, color: '#e6ebf5' }}>
                {p.label}
              </span>
              <span style={{
                fontSize: 12, fontWeight: 700,
                color: passed ? '#34d399' : '#f87171',
              }}>
                {passed ? 'PASS ✓' : 'FAIL ✗'}
              </span>
            </div>

            {/* 가드 노트 */}
            {p.guard.note && (
              <div style={{ fontSize: 12, color: '#8a93a8', marginBottom: p.guard.violations?.length ? 6 : 0 }}>
                {p.guard.note}
              </div>
            )}

            {/* 위반 목록 */}
            {p.guard.violations?.map((v, i) => (
              <div key={i} style={{
                marginTop: 4, fontSize: 12, color: '#8a93a8',
                background: 'rgba(248,113,113,0.08)',
                borderRadius: 4, padding: '4px 8px',
              }}>
                <code style={{
                  color: '#f87171',
                  background: 'rgba(248,113,113,0.12)',
                  padding: '1px 5px', borderRadius: 4, marginRight: 6,
                }}>
                  {v.code}
                </code>
                {v.detail}
              </div>
            ))}
          </div>
        );
      })}
    </div>
  );
}
