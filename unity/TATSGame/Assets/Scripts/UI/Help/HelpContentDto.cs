using System.Collections.Generic;
using Newtonsoft.Json;

namespace Tats.Game.UI.Help
{
    /// <summary>
    /// backend/content/help.json을 그대로 옮긴 DTO. docs/23_TITLE_SCREEN_BACKLOG.md T5: 본문은
    /// 코드가 아니라 이 JSON에 있어야 한다. 필드 이름은 이 항목에서 새로 정한 콘텐츠 계약이라
    /// docs/22_TATS_BACKEND_DESIGN_V1.md에는 없다 (그 문서는 <c>GET /api/content/algorithms</c>만 정의한다).
    /// </summary>
    public sealed class HelpStepDto
    {
        [JsonProperty("order")] public int Order;
        [JsonProperty("text")] public string Text;
    }

    public sealed class HelpFirstThreeMinutesDto
    {
        [JsonProperty("title")] public string Title;
        [JsonProperty("note")] public string Note;
        [JsonProperty("steps")] public List<HelpStepDto> Steps = new List<HelpStepDto>();
    }

    public sealed class HelpControlEntryDto
    {
        [JsonProperty("action")] public string Action;
        [JsonProperty("keys")] public List<string> Keys = new List<string>();
        [JsonProperty("description")] public string Description;
    }

    public sealed class HelpControlsDto
    {
        [JsonProperty("title")] public string Title;
        [JsonProperty("entries")] public List<HelpControlEntryDto> Entries = new List<HelpControlEntryDto>();
    }

    public sealed class HelpTermEntryDto
    {
        [JsonProperty("id")] public string Id;
        [JsonProperty("term")] public string Term;
        [JsonProperty("definition")] public string Definition;
        [JsonProperty("source")] public string Source;
    }

    public sealed class HelpTermsDto
    {
        [JsonProperty("title")] public string Title;
        [JsonProperty("entries")] public List<HelpTermEntryDto> Entries = new List<HelpTermEntryDto>();
    }

    public sealed class HelpContentDto
    {
        [JsonProperty("schemaVersion")] public int SchemaVersion;
        [JsonProperty("firstThreeMinutes")] public HelpFirstThreeMinutesDto FirstThreeMinutes;
        [JsonProperty("controls")] public HelpControlsDto Controls;
        [JsonProperty("terms")] public HelpTermsDto Terms;
    }
}
