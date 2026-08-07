using System;
using System.IO;
using Newtonsoft.Json;

namespace Tats.Game.UI.Help
{
    /// <summary>
    /// docs/23_TITLE_SCREEN_BACKLOG.md T5: <c>backend/content/help.json</c>이 정본이다. Unity는
    /// <c>GET /api/content/help</c>를 아직 호출하지 않는다 — backend/README.md대로 세션·콘텐츠
    /// API 구현 자체가 저장소에 없다. 대신 build 시점에 같은 내용을 그대로 옮겨 둔
    /// <c>Assets/StreamingAssets/content/help.json</c> 사본을 읽는다. 이 방식은 map 데이터가 이미 쓰는
    /// 것과 같다 — <c>backend/content/map_eojin_playable.json</c>(시뮬레이션 원본)과
    /// <c>StreamingAssets/map/eojin_map.json</c>(표시용 사본)의 관계와 같은 이유다(unity/TATSGame/README.md).
    /// 실제 API 연동은 "6. 실제 server adapter 연결" 단계로 남는다.
    /// </summary>
    public sealed class HelpContentStore
    {
        readonly string _filePath;

        public HelpContentStore(string filePath)
        {
            _filePath = filePath ?? throw new ArgumentNullException(nameof(filePath));
        }

        public HelpContentLoadResult Load()
        {
            if (!File.Exists(_filePath))
            {
                return HelpContentLoadResult.Error($"파일 없음: {_filePath}");
            }

            string json;
            try
            {
                json = File.ReadAllText(_filePath);
            }
            catch (IOException ex)
            {
                return HelpContentLoadResult.Error(ex.Message);
            }

            HelpContentDto content;
            try
            {
                content = JsonConvert.DeserializeObject<HelpContentDto>(json);
            }
            catch (JsonException ex)
            {
                return HelpContentLoadResult.Error(ex.Message);
            }

            if (content?.FirstThreeMinutes == null || content.Controls == null || content.Terms == null)
            {
                return HelpContentLoadResult.Error("필수 섹션 누락 (firstThreeMinutes/controls/terms)");
            }

            return HelpContentLoadResult.Loaded(content);
        }
    }
}
