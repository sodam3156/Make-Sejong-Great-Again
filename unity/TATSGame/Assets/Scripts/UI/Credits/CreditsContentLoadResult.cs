namespace Tats.Game.UI.Credits
{
    /// <summary>
    /// docs/20_TATS_UX_FRONTEND_HANDOFF_V1.md 8.3절 AsyncState 중 로컬 파일을 동기로 읽는
    /// <see cref="CreditsContentStore"/>에 해당하는 값만 쓴다 (T5의 HelpContentLoadResult와 같은 근거) —
    /// 네트워크 조회가 아니라서 Loading·Stale은 여기서 만들지 않는다.
    /// </summary>
    public enum CreditsContentLoadState
    {
        Loaded,
        Error,
    }

    public sealed class CreditsContentLoadResult
    {
        public CreditsContentLoadState State { get; }
        public CreditsContentDto Content { get; }
        public string FailureReason { get; }

        CreditsContentLoadResult(CreditsContentLoadState state, CreditsContentDto content, string failureReason)
        {
            State = state;
            Content = content;
            FailureReason = failureReason;
        }

        public static CreditsContentLoadResult Loaded(CreditsContentDto content) =>
            new CreditsContentLoadResult(CreditsContentLoadState.Loaded, content, null);

        public static CreditsContentLoadResult Error(string failureReason) =>
            new CreditsContentLoadResult(CreditsContentLoadState.Error, null, failureReason);
    }
}
