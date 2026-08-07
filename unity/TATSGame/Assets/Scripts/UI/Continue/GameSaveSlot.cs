namespace Tats.Game.UI.Continue
{
    /// <summary>
    /// 화면에 보여줄 저장 슬롯 하나. <see cref="SlotId"/>는 저장 파일 이름(확장자 제외)이고,
    /// 나머지 필드는 docs/22_TATS_BACKEND_DESIGN_V1.md 10절 GameSave 계약 필드 그대로다.
    /// 슬롯을 파일 하나로 두는 구성 자체는 그 절이 정하지 않은 Unity 쪽 구현 결정이다.
    /// </summary>
    public readonly struct GameSaveSlot
    {
        public string SlotId { get; }
        public int SchemaVersion { get; }
        public string StartNodeId { get; }
        public string OpponentModel { get; }
        public long LastConfirmedTick { get; }
        public long ResumeTokenTick { get; }

        /// <summary>재개 요청을 실제로 보낼 때(T3 범위 밖) 그대로 전달할 원본 GameSave JSON.</summary>
        public string RawJson { get; }

        public GameSaveSlot(
            string slotId,
            int schemaVersion,
            string startNodeId,
            string opponentModel,
            long lastConfirmedTick,
            long resumeTokenTick,
            string rawJson)
        {
            SlotId = slotId;
            SchemaVersion = schemaVersion;
            StartNodeId = startNodeId;
            OpponentModel = opponentModel;
            LastConfirmedTick = lastConfirmedTick;
            ResumeTokenTick = resumeTokenTick;
            RawJson = rawJson;
        }
    }
}
