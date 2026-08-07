using System;
using System.Collections.Generic;

namespace Tats.Game.UI.Continue
{
    /// <summary>
    /// docs/20_TATS_UX_FRONTEND_HANDOFF_V1.md 8.3절 <c>AsyncState</c> 중 로컬 파일을 동기로 읽는
    /// <see cref="GameSaveSlotStore"/>에 해당하는 값만 쓴다. 네트워크 조회가 아니라서
    /// Loading·Stale은 여기서 만들지 않는다.
    /// </summary>
    public enum GameSaveSlotListState
    {
        Empty,
        Ready,
        Error,
    }

    public sealed class GameSaveSlotListResult
    {
        public GameSaveSlotListState State { get; }
        public IReadOnlyList<GameSaveSlot> Slots { get; }

        /// <summary>파싱하지 못한 파일 이름과 사유. 일부만 손상됐어도 나머지는 Ready로 보여준다.</summary>
        public IReadOnlyList<string> UnreadableFiles { get; }

        GameSaveSlotListResult(GameSaveSlotListState state, IReadOnlyList<GameSaveSlot> slots, IReadOnlyList<string> unreadableFiles)
        {
            State = state;
            Slots = slots;
            UnreadableFiles = unreadableFiles;
        }

        public static GameSaveSlotListResult Empty() =>
            new GameSaveSlotListResult(GameSaveSlotListState.Empty, Array.Empty<GameSaveSlot>(), Array.Empty<string>());

        public static GameSaveSlotListResult Ready(IReadOnlyList<GameSaveSlot> slots, IReadOnlyList<string> unreadableFiles) =>
            new GameSaveSlotListResult(GameSaveSlotListState.Ready, slots, unreadableFiles);

        public static GameSaveSlotListResult Error(IReadOnlyList<string> unreadableFiles) =>
            new GameSaveSlotListResult(GameSaveSlotListState.Error, Array.Empty<GameSaveSlot>(), unreadableFiles);
    }
}
