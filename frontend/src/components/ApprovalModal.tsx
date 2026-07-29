// 승인·거절 모달 — operator_approval 상태일 때 표시
import type { Policy, PolicyId } from '../types/demo';

interface Props {
  policies: Policy[];
  approvalPolicyId: PolicyId;
  approvalReason: string;
  onApprove: () => void;
  onReject: () => void;
  decision: 'approved' | 'rejected' | null; // 이미 결정된 경우
}

export function ApprovalModal({
  policies,
  approvalPolicyId,
  approvalReason,
  onApprove,
  onReject,
  decision,
}: Props) {
  const chosen = policies.find((p) => p.policy_id === approvalPolicyId);

  return (
    <div style={{
      background: '#10151f',
      border: '1px solid #22293a',
      borderRadius: 10,
      padding: '16px 18px',
    }}>
      {/* 제목 */}
      <h3 style={{ margin: '0 0 14px', fontSize: 13, color: '#8a93a8', textTransform: 'uppercase', letterSpacing: '0.6px' }}>
        운영자 승인
      </h3>

      {/* 정책 정보 */}
      <dl style={{ display: 'grid', gridTemplateColumns: '90px 1fr', gap: '6px 10px', fontSize: 13, margin: '0 0 16px' }}>
        <dt style={{ color: '#8a93a8' }}>대상 정책</dt>
        <dd style={{ margin: 0, color: '#e6ebf5', fontWeight: 700 }}>
          {chosen?.label ?? approvalPolicyId}
        </dd>
        <dt style={{ color: '#8a93a8' }}>근거</dt>
        <dd style={{ margin: 0, color: '#e6ebf5' }}>{approvalReason}</dd>
        <dt style={{ color: '#8a93a8' }}>안전 가드</dt>
        <dd style={{ margin: 0, color: chosen?.guard.passed ? '#34d399' : '#f87171', fontWeight: 700 }}>
          {chosen?.guard.passed ? '✓ 통과' : '✗ 위반'}
        </dd>
      </dl>

      {/* 버튼 or 결과 */}
      {decision ? (
        <div style={{
          padding: '10px 14px',
          borderRadius: 8,
          background: decision === 'approved' ? 'rgba(52,211,153,0.1)' : 'rgba(248,113,113,0.1)',
          border: `1px solid ${decision === 'approved' ? 'rgba(52,211,153,0.3)' : 'rgba(248,113,113,0.3)'}`,
          color: decision === 'approved' ? '#34d399' : '#f87171',
          fontWeight: 700,
          fontSize: 13,
        }}>
          {decision === 'approved'
            ? `✓ ${chosen?.label ?? approvalPolicyId} 정책을 승인했습니다.`
            : '✗ 제안을 거절했습니다.'}
          <span style={{ fontWeight: 400, color: '#8a93a8', marginLeft: 8, fontSize: 12 }}>
            (fixture 데모 — 실제 반영 없음)
          </span>
        </div>
      ) : (
        <div style={{ display: 'flex', gap: 10 }}>
          <button
            onClick={onApprove}
            style={{
              padding: '8px 20px', borderRadius: 6, cursor: 'pointer',
              background: 'rgba(52,211,153,0.15)', color: '#34d399',
              border: '1px solid rgba(52,211,153,0.4)', fontWeight: 700, fontSize: 13,
            }}
          >
            승인
          </button>
          <button
            onClick={onReject}
            style={{
              padding: '8px 20px', borderRadius: 6, cursor: 'pointer',
              background: 'rgba(248,113,113,0.15)', color: '#f87171',
              border: '1px solid rgba(248,113,113,0.4)', fontWeight: 700, fontSize: 13,
            }}
          >
            거절
          </button>
        </div>
      )}
    </div>
  );
}
