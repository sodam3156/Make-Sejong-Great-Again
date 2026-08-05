using System.Collections.Generic;
using Newtonsoft.Json;

namespace Tats.Game.UI.Continue
{
    /// <summary>
    /// docs/22_TATS_BACKEND_DESIGN_V1.md 10절 resumeToken 필드를 그대로 옮긴 DTO.
    /// <c>worldState</c>는 Unity가 계산하지 않고 보관만 하는 값이라("Unity는 이걸 계산하지 않고
    /// 보관만 한다") 구조를 풀어내지 않고 opaque JSON으로만 남긴다.
    /// </summary>
    public sealed class GameSaveResumeTokenDto
    {
        [JsonProperty("worldState")] public object WorldState;
        [JsonProperty("tick")] public long Tick;
        [JsonProperty("seed")] public long Seed;
        [JsonProperty("mapVersion")] public string MapVersion;
        [JsonProperty("gameRuleVersion")] public string GameRuleVersion;
        [JsonProperty("contentVersion")] public string ContentVersion;
        [JsonProperty("stateChecksum")] public string StateChecksum;
    }

    /// <summary>
    /// docs/22_TATS_BACKEND_DESIGN_V1.md 10절 GameSave 계약을 그대로 옮긴 DTO.
    /// <c>GameSave = { schemaVersion, startNodeId, opponentModel, resumeToken, commandLog[], lastConfirmedTick }</c>
    /// </summary>
    public sealed class GameSaveDto
    {
        [JsonProperty("schemaVersion")] public int SchemaVersion;
        [JsonProperty("startNodeId")] public string StartNodeId;
        [JsonProperty("opponentModel")] public string OpponentModel;
        [JsonProperty("resumeToken")] public GameSaveResumeTokenDto ResumeToken;
        [JsonProperty("commandLog")] public List<object> CommandLog = new List<object>();
        [JsonProperty("lastConfirmedTick")] public long LastConfirmedTick;
    }
}
