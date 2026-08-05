namespace Tats.Game.UI.Help
{
    /// <summary>
    /// docs/20_TATS_UX_FRONTEND_HANDOFF_V1.md 8.3절 AsyncState 중 로컬 파일을 동기로 읽는
    /// <see cref="HelpContentStore"/>에 해당하는 값만 쓴다 (T4의 GameSettingsLoadResult와 같은 근거) —
    /// 네트워크 조회가 아니라서 Loading·Stale은 여기서 만들지 않는다.
    /// </summary>
    public enum HelpContentLoadState
    {
        Loaded,
        Error,
    }

    public sealed class HelpContentLoadResult
    {
        public HelpContentLoadState State { get; }
        public HelpContentDto Content { get; }
        public string FailureReason { get; }

        HelpContentLoadResult(HelpContentLoadState state, HelpContentDto content, string failureReason)
        {
            State = state;
            Content = content;
            FailureReason = failureReason;
        }

        public static HelpContentLoadResult Loaded(HelpContentDto content) =>
            new HelpContentLoadResult(HelpContentLoadState.Loaded, content, null);

        public static HelpContentLoadResult Error(string failureReason) =>
            new HelpContentLoadResult(HelpContentLoadState.Error, null, failureReason);
    }
}
