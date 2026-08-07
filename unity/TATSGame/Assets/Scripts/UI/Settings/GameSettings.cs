using Newtonsoft.Json;

namespace Tats.Game.UI.Settings
{
    /// <summary>
    /// docs/20_TATS_UX_FRONTEND_HANDOFF_V1.md 111행: 기준 해상도 1440×900, 최소 지원 해상도
    /// 1280×720 두 값만 정본이 정의한다.
    /// </summary>
    public enum SettingsResolution
    {
        Res1440x900,
        Res1280x720,
    }

    /// <summary>
    /// docs/20_TATS_UX_FRONTEND_HANDOFF_V1.md 8.3절 SimulationSpeed(Paused|X1|X3|X5) 중 Paused를
    /// 뺀 세 값. 145~146행: 온보딩 뒤 기본값은 1배속이다 — "기본 배속" 설정이 고를 수 있는 값도
    /// 실행 중 배속과 같은 세 값으로 한정한다.
    /// </summary>
    public enum SettingsDefaultSpeed
    {
        X1,
        X3,
        X5,
    }

    /// <summary>
    /// 저장소 어디에도 지원 언어 목록이 없다 — 모든 정본 문서·콘텐츠가 한국어뿐이다. 추가 언어
    /// 목록은 계약 미정으로 남기고, 지금은 실제로 쓰이는 한 값만 둔다.
    /// </summary>
    public enum SettingsLanguage
    {
        Korean,
    }

    /// <summary>
    /// docs/23_TITLE_SCREEN_BACKLOG.md T4 범위: 해상도, 기본 배속, 마스터·효과음 볼륨, 언어.
    /// 여기 담긴 값은 모두 게임 규칙에 영향을 주지 않는 로컬 UI 설정이다
    /// (docs/00_TATS_SOURCE_OF_TRUTH.md 구현 경계: Unity는 점수·안전·비용·교통 결과를 계산하지 않는다).
    /// </summary>
    public sealed class GameSettings
    {
        [JsonProperty("schemaVersion")] public int SchemaVersion = 1;
        [JsonProperty("resolution")] public SettingsResolution Resolution = SettingsResolution.Res1440x900;
        [JsonProperty("defaultSpeed")] public SettingsDefaultSpeed DefaultSpeed = SettingsDefaultSpeed.X1;
        [JsonProperty("masterVolumePercent")] public int MasterVolumePercent = 100;
        [JsonProperty("effectVolumePercent")] public int EffectVolumePercent = 100;
        [JsonProperty("language")] public SettingsLanguage Language = SettingsLanguage.Korean;

        public static GameSettings Default() => new GameSettings();

        public GameSettings Clone() => new GameSettings
        {
            SchemaVersion = SchemaVersion,
            Resolution = Resolution,
            DefaultSpeed = DefaultSpeed,
            MasterVolumePercent = MasterVolumePercent,
            EffectVolumePercent = EffectVolumePercent,
            Language = Language,
        };
    }
}
