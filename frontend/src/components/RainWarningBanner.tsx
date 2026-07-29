// 경고창 컴포넌트 — rain_warning 상태일 때 화면 상단에 표시

interface Props {
  rainLevel: string; // 'moderate' | 'heavy' | 'dry' 등
  visible: boolean;
}

export function RainWarningBanner({ rainLevel, visible }: Props) {
  if (!visible) return null;

  const isHeavy = rainLevel === 'heavy';

  return (
    <div style={{
      background: isHeavy ? 'rgba(248,113,113,0.15)' : 'rgba(251,191,36,0.15)',
      border: `1px solid ${isHeavy ? 'rgba(248,113,113,0.5)' : 'rgba(251,191,36,0.5)'}`,
      borderRadius: 8,
      padding: '10px 16px',
      marginBottom: 16,
      display: 'flex',
      alignItems: 'center',
      gap: 10,
    }}>
      {/* 아이콘 */}
      <span style={{ fontSize: 18 }}>{isHeavy ? '🚨' : '⚠️'}</span>

      {/* 메시지 */}
      <div>
        <span style={{
          fontWeight: 700,
          color: isHeavy ? '#f87171' : '#fbbf24',
          fontSize: 14,
          marginRight: 8,
        }}>
          {isHeavy ? '강우 위험' : '강우 경보'}
        </span>
        <span style={{ color: '#e6ebf5', fontSize: 13 }}>
          강우 강도: <strong>{rainLevel}</strong> — 회랑 역류(spillback) 위험 감지
        </span>
      </div>

      {/* result_source 표시 */}
      <span style={{
        marginLeft: 'auto',
        fontSize: 11,
        color: '#fbbf24',
        background: 'rgba(251,191,36,0.1)',
        padding: '2px 8px',
        borderRadius: 999,
        border: '1px solid rgba(251,191,36,0.3)',
      }}>
        fixture
      </span>
    </div>
  );
}
