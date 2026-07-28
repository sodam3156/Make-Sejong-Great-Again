import type { KPI } from '../types/demo';

const KPI_DEFS: { key: keyof KPI; label: string; unit: string }[] = [
  { key: 'spillback_time_sec',       label: 'Spillback 시간',    unit: '초' },
  { key: 'recovery_time_sec',        label: '회복 시간',          unit: '초' },
  { key: 'total_travel_time_sec',    label: '총 통행시간',         unit: '초' },
  { key: 'worst_approach_delay_sec', label: '최악 진입로 지체',    unit: '초' },
];

interface Props {
  kpi: KPI;
}

export function KpiGrid({ kpi }: Props) {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(4, 1fr)',
      gap: 10,
    }}>
      {KPI_DEFS.map((def) => (
        <div
          key={def.key}
          style={{
            background: '#151b28',
            border: '1px solid #22293a',
            borderRadius: 8,
            padding: '10px 12px',
          }}
        >
          <div style={{ fontSize: 11, color: '#8a93a8', marginBottom: 4 }}>
            {def.label}
          </div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>
            {kpi[def.key]}
            <span style={{ fontSize: 11, color: '#8a93a8', marginLeft: 3 }}>
              {def.unit}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
