using System.Collections.Generic;

namespace Tats.Game.UI.NewGame
{
    /// <summary>
    /// docs/23_TITLE_SCREEN_BACKLOG.md T2: 시작 교차로 목록은 backend/content/map_eojin_playable.json의
    /// startIntersectionIds에서 읽는다. Unity가 그 파일을 실제로 로드할 경로·계약은 아직 정해지지 않았다
    /// (unity/TATSGame/README.md 구현 순서: mock ViewModel이 실제 server adapter 연결보다 먼저다).
    /// 그래서 이 값은 커밋 시점의 map_eojin_playable.json 내용을 그대로 옮긴 mock이고, 지도 콘텐츠가
    /// 바뀌면 손으로 갱신해야 한다. 실제 로딩 경로가 정해지면 이 provider를 교체한다.
    /// </summary>
    public static class NewGameContent
    {
        public static readonly IReadOnlyList<NewGameStartOption> StartOptions = new[]
        {
            new NewGameStartOption("ix_04", "성금교차로"),
            new NewGameStartOption("ix_09", "청사교차로"),
            new NewGameStartOption("ix_07", "어진교차로"),
        };

        public static readonly IReadOnlyList<NewGameOpponent> Opponents = new[]
        {
            NewGameOpponent.Luna,
            NewGameOpponent.Terra,
            NewGameOpponent.Sol,
        };
    }
}
