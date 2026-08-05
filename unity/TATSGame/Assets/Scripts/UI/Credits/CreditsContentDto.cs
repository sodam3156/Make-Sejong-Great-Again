using System.Collections.Generic;
using Newtonsoft.Json;

namespace Tats.Game.UI.Credits
{
    /// <summary>
    /// backend/content/credits.json을 그대로 옮긴 DTO. docs/23_TITLE_SCREEN_BACKLOG.md T6: 팀 명단·
    /// 공개 데이터 출처·오픈소스 고지는 코드가 아니라 이 JSON에 있어야 한다. 그 JSON 자체도
    /// `scripts/build_contributors_content.py`가 THIRD_PARTY_NOTICES.md·third_party/abstreet.lock.json·
    /// 팀 구성 원본 문서를 실제로 읽어 만든 것이라 손으로 옮겨 적은 사본이 아니다. 필드 이름은 이
    /// 항목에서 새로 정한 콘텐츠 계약이라 docs/22_TATS_BACKEND_DESIGN_V1.md에는 없다(T5의 help.json과
    /// 같은 이유).
    /// </summary>
    public sealed class CreditsTeamDto
    {
        [JsonProperty("title")] public string Title;
        [JsonProperty("name")] public string Name;
        [JsonProperty("members")] public List<string> Members = new List<string>();
        [JsonProperty("source")] public string Source;
    }

    public sealed class CreditsPublicDataSourceEntryDto
    {
        [JsonProperty("order")] public int Order;
        [JsonProperty("name")] public string Name;
        [JsonProperty("url")] public string Url;
        [JsonProperty("note")] public string Note;
    }

    public sealed class CreditsPublicDataSourcesDto
    {
        [JsonProperty("title")] public string Title;
        [JsonProperty("entries")] public List<CreditsPublicDataSourceEntryDto> Entries = new List<CreditsPublicDataSourceEntryDto>();
        [JsonProperty("source")] public string Source;
    }

    public sealed class CreditsOpenSourceNoticeEntryDto
    {
        [JsonProperty("name")] public string Name;
        [JsonProperty("license")] public string License;
        [JsonProperty("licenseSpdx")] public string LicenseSpdx;
        [JsonProperty("upstreamUrl")] public string UpstreamUrl;
        [JsonProperty("forkUrl")] public string ForkUrl;
        [JsonProperty("pinnedCommit")] public string PinnedCommit;
        [JsonProperty("pinnedCommitUrl")] public string PinnedCommitUrl;
        [JsonProperty("copyrightUrl")] public string CopyrightUrl;
        [JsonProperty("attributionGuidanceUrl")] public string AttributionGuidanceUrl;
        [JsonProperty("note")] public string Note;
    }

    public sealed class CreditsOpenSourceNoticesDto
    {
        [JsonProperty("title")] public string Title;
        [JsonProperty("entries")] public List<CreditsOpenSourceNoticeEntryDto> Entries = new List<CreditsOpenSourceNoticeEntryDto>();
        [JsonProperty("source")] public string Source;
    }

    public sealed class CreditsContentDto
    {
        [JsonProperty("schemaVersion")] public int SchemaVersion;
        [JsonProperty("team")] public CreditsTeamDto Team;
        [JsonProperty("publicDataSources")] public CreditsPublicDataSourcesDto PublicDataSources;
        [JsonProperty("openSourceNotices")] public CreditsOpenSourceNoticesDto OpenSourceNotices;
    }
}
