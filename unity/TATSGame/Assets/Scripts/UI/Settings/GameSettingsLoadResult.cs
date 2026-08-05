namespace Tats.Game.UI.Settings
{
    /// <summary>
    /// docs/20_TATS_UX_FRONTEND_HANDOFF_V1.md 8.3절 AsyncState 중 로컬 파일을 동기로 읽는
    /// <see cref="GameSettingsStore"/>에 해당하는 값만 쓴다. 네트워크 조회가 아니라서
    /// Loading·Stale은 여기서 만들지 않는다 (T3의 GameSaveSlotListResult와 같은 근거).
    /// </summary>
    public enum GameSettingsLoadState
    {
        Loaded,
        LoadedFromBackup,
        Defaults,
    }

    public sealed class GameSettingsLoadResult
    {
        public GameSettingsLoadState State { get; }
        public GameSettings Settings { get; }

        /// <summary>기본값(Defaults) 또는 백업 사용(LoadedFromBackup)으로 넘어간 이유. 정상 로드면 null.</summary>
        public string FailureReason { get; }

        GameSettingsLoadResult(GameSettingsLoadState state, GameSettings settings, string failureReason)
        {
            State = state;
            Settings = settings;
            FailureReason = failureReason;
        }

        public static GameSettingsLoadResult Loaded(GameSettings settings) =>
            new GameSettingsLoadResult(GameSettingsLoadState.Loaded, settings, null);

        public static GameSettingsLoadResult LoadedFromBackup(GameSettings settings, string primaryFailureReason) =>
            new GameSettingsLoadResult(GameSettingsLoadState.LoadedFromBackup, settings, primaryFailureReason);

        public static GameSettingsLoadResult Defaults(string failureReason) =>
            new GameSettingsLoadResult(GameSettingsLoadState.Defaults, GameSettings.Default(), failureReason);
    }
}
