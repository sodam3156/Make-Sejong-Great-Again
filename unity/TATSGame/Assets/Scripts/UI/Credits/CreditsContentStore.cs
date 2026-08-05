using System;
using System.IO;
using Newtonsoft.Json;

namespace Tats.Game.UI.Credits
{
    /// <summary>
    /// docs/23_TITLE_SCREEN_BACKLOG.md T6: <c>backend/content/credits.json</c>이 정본이다. Unity는
    /// 세션·콘텐츠 API를 아직 호출하지 않는다 — backend/README.md대로 그런 서버 구현 자체가
    /// 저장소에 없다(T5의 HelpContentStore와 같은 근거). 대신 build 시점에 같은 내용을 그대로
    /// 옮겨 둔 <c>Assets/StreamingAssets/content/credits.json</c> 사본을 읽는다. 실제 API 연동은
    /// "6. 실제 server adapter 연결" 단계로 남는다(unity/TATSGame/README.md).
    /// </summary>
    public sealed class CreditsContentStore
    {
        readonly string _filePath;

        public CreditsContentStore(string filePath)
        {
            _filePath = filePath ?? throw new ArgumentNullException(nameof(filePath));
        }

        public CreditsContentLoadResult Load()
        {
            if (!File.Exists(_filePath))
            {
                return CreditsContentLoadResult.Error($"파일 없음: {_filePath}");
            }

            string json;
            try
            {
                json = File.ReadAllText(_filePath);
            }
            catch (IOException ex)
            {
                return CreditsContentLoadResult.Error(ex.Message);
            }

            CreditsContentDto content;
            try
            {
                content = JsonConvert.DeserializeObject<CreditsContentDto>(json);
            }
            catch (JsonException ex)
            {
                return CreditsContentLoadResult.Error(ex.Message);
            }

            if (content?.Team == null || content.PublicDataSources == null || content.OpenSourceNotices == null)
            {
                return CreditsContentLoadResult.Error("필수 섹션 누락 (team/publicDataSources/openSourceNotices)");
            }

            return CreditsContentLoadResult.Loaded(content);
        }
    }
}
