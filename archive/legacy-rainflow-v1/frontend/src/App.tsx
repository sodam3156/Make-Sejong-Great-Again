import { useState } from 'react';
import { FIXTURE_DATA } from './data/fixture';
import { KpiGrid } from './components/KpiGrid';
import { PolicyCompare } from './components/PolicyCompare';
import { RainWarningBanner } from './components/RainWarningBanner';
import { ApprovalModal } from './components/ApprovalModal';
import { SafetyReviewPanel } from './components/SafetyReviewPanel';
import { OfflineScreen } from './components/OfflineScreen';

const data = FIXTURE_DATA;
const corridorGatingKpi = data.policies.find((p) => p.policy_id === 'corridor_gating')!.kpi;

export default function App() {
  const [decision, setDecision] = useState<'approved' | 'rejected' | null>(null);

  return (
    <div style={{
      background: '#ffffff',
      color: '#0f172a',
      minHeight: '100vh',
      padding: 24,
      fontFamily: '-apple-system, "Segoe UI", "Malgun Gothic", system-ui, sans-serif',
    }}>
      <h1 style={{ fontSize: 18, marginBottom: 4 }}>RainFlow Sejong — 컴포넌트 목업</h1>
      <p style={{ fontSize: 12, color: '#475569', marginBottom: 24 }}>
        fixture 데이터 기반 · run_id: {data.run_id}
      </p>

      {/* 1. 경고창 */}
      <h2 style={sectionTitle}>① 경고창 (rain_warning)</h2>
      <RainWarningBanner rainLevel="moderate" visible={true} />
      <RainWarningBanner rainLevel="heavy" visible={true} />

      {/* 2. KPI 카드 */}
      <h2 style={{ ...sectionTitle, marginTop: 32 }}>② KPI 카드 (corridor_gating 기준)</h2>
      <KpiGrid kpi={corridorGatingKpi} />

      {/* 3. 정책 비교 */}
      <h2 style={{ ...sectionTitle, marginTop: 32 }}>③ 정책 비교 (policy_compare)</h2>
      <div style={panel}>
        <PolicyCompare policies={data.policies} approvedPolicyId={data.approval.policy_id} />
      </div>

      {/* 4. 안전 검토 패널 */}
      <h2 style={{ ...sectionTitle, marginTop: 32 }}>④ 안전 가드 심사 (safety_review)</h2>
      <SafetyReviewPanel policies={data.policies} />

      {/* 5. 승인·거절 모달 */}
      <h2 style={{ ...sectionTitle, marginTop: 32 }}>⑤ 운영자 승인 (operator_approval)</h2>
      <ApprovalModal
        policies={data.policies}
        approvalPolicyId={data.approval.policy_id}
        approvalReason={data.approval.reason}
        decision={decision}
        onApprove={() => setDecision('approved')}
        onReject={() => setDecision('rejected')}
      />

      {/* 6. 오류·오프라인 화면 */}
      <h2 style={{ ...sectionTitle, marginTop: 32 }}>⑥ 오류·오프라인 화면</h2>
      <OfflineScreen onRetry={() => alert('재연결 시도 (데모)')} />

    </div>
  );
}

const sectionTitle: React.CSSProperties = {
  fontSize: 13,
  color: '#475569',
  textTransform: 'uppercase',
  letterSpacing: '0.6px',
  marginBottom: 10,
};

const panel: React.CSSProperties = {
  background: '#f1f5f9',
  border: '1px solid #cbd5e1',
  borderRadius: 10,
  padding: '14px 16px',
};
