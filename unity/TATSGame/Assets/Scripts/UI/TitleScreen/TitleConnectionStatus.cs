namespace Tats.Game.UI.TitleScreen
{
    /// <summary>
    /// docs/23_TITLE_SCREEN_BACKLOG.md T7이 정의한 시작 화면 연결 표시 3상태(연결됨·재시도·끊김).
    /// docs/20_TATS_UX_FRONTEND_HANDOFF_V1.md 8.3절의 인게임 <c>ConnectionState</c>
    /// (Connected|Applying|Reconnecting|ResumeReady|ResumeFailed)는 <c>ConnectionPauseOverlay</c>(M14)용
    /// 별도 상태 집합이다 — 인게임 화면은 docs/23 "범위 밖"이므로 여기서 재사용하지 않고
    /// 시작 화면 전용으로 새로 정의한다.
    /// </summary>
    public enum TitleConnectionStatus
    {
        Connected,
        Retrying,
        Disconnected,
    }
}
