namespace Tats.Game.UI.NewGame
{
    /// <summary>
    /// 사용자가 확정한 시작 조건. docs/22_TATS_BACKEND_DESIGN_V1.md 9절
    /// <c>POST /api/game-sessions</c> 요청 필드 중 <c>startNodeId</c>·<c>opponentModel</c>과 같은 뜻이다.
    /// 이 항목(T2)은 이 값을 만들어 <see cref="NewGamePresenter.Confirmed"/>로 넘기는 데까지만 다룬다 —
    /// 실제 세션 생성 호출과 응답(GameSessionSnapshot)은 범위 밖이다. 저장소에 아직 세션 API 구현이
    /// 없고 GameSessionSnapshot의 필드 계약도 정의돼 있지 않다(계약 미정).
    /// </summary>
    public readonly struct NewGameSelection
    {
        public string StartNodeId { get; }
        public NewGameOpponent Opponent { get; }

        public NewGameSelection(string startNodeId, NewGameOpponent opponent)
        {
            StartNodeId = startNodeId;
            Opponent = opponent;
        }
    }
}
