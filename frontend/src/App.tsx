import { FIXTURE_DATA } from './data/fixture';
import { KpiGrid } from './components/KpiGrid';
import { PolicyCompare } from './components/PolicyCompare';

const data = FIXTURE_DATA;

// corridor_gating (index 2) KPI를 기본으로 표시
const corridorGatingKpi = data.policies.find((p) => p.policy_id === 'corridor_gating')!.kpi;

export default function App() {
  return (
    <div style={{
      background: '#0a0e14',
      color: '#e6ebf5',
      minHeight: '100vh',
      padding: 24,
      fontFamily: '-apple-system, "Segoe UI", "Malgun Gothic", system-ui, sans-serif',
    }}>
      {/* 헤더 */}
      <h1 style={{ fontSize: 18, marginBottom: 4 }}>RainFlow Sejong — 컴포넌트 목업</h1>
      <p style={{ fontSize: 12, color: '#8a93a8', marginBottom: 24 }}>
        fixture 데이터 기반 · run_id: {data.run_id}
      </p>

      {/* KPI 카드 4종 */}
      <h2 style={{ fontSize: 13, color: '#8a93a8', textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: 10 }}>
        핵심 KPI (corridor_gating 기준)
      </h2>
      <KpiGrid kpi={corridorGatingKpi} />

      {/* 정책 비교 패널 */}
      <h2 style={{ fontSize: 13, color: '#8a93a8', textTransform: 'uppercase', letterSpacing: '0.6px', marginTop: 32, marginBottom: 10 }}>
        대응안 비교 (무대응 대비)
      </h2>
      <div style={{ background: '#10151f', border: '1px solid #22293a', borderRadius: 10, padding: '14px 16px' }}>
        <PolicyCompare
          policies={data.policies}
          approvedPolicyId={data.approval.policy_id}
        />
      </div>
    </div>
  );
}
