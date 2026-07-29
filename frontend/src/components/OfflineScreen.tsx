// 오류·오프라인 화면 — 백엔드 연결 실패 시 표시

interface Props {
  onRetry?: () => void; // 재시도 버튼 콜백 (선택)
}

export function OfflineScreen({ onRetry }: Props) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: 300,
      padding: 32,
      background: '#10151f',
      border: '1px solid #22293a',
      borderRadius: 10,
      textAlign: 'center',
    }}>
      {/* 아이콘 */}
      <div style={{ fontSize: 40, marginBottom: 16 }}>📡</div>

      {/* 제목 */}
      <div style={{ fontSize: 16, fontWeight: 700, color: '#e6ebf5', marginBottom: 8 }}>
        백엔드 연결 실패
      </div>

      {/* 설명 */}
      <div style={{ fontSize: 13, color: '#8a93a8', marginBottom: 20, maxWidth: 360 }}>
        서버에 연결할 수 없습니다. fixture 데이터로 자동 전환합니다.
        <br />
        네트워크 또는 백엔드 서버 상태를 확인해주세요.
      </div>

      {/* fixture 폴백 안내 */}
      <div style={{
        fontSize: 12,
        color: '#fbbf24',
        background: 'rgba(251,191,36,0.1)',
        border: '1px solid rgba(251,191,36,0.3)',
        borderRadius: 6,
        padding: '6px 14px',
        marginBottom: onRetry ? 16 : 0,
      }}>
        ⚡ fixture 모드로 데모 재생 중 (실제 시뮬레이션 아님)
      </div>

      {/* 재시도 버튼 */}
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            padding: '8px 20px', borderRadius: 6, cursor: 'pointer',
            background: 'rgba(96,165,250,0.15)', color: '#60a5fa',
            border: '1px solid rgba(96,165,250,0.4)', fontWeight: 700, fontSize: 13,
          }}
        >
          재연결 시도
        </button>
      )}
    </div>
  );
}
