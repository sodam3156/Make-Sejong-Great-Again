using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace RainFlow.Game
{
    public sealed class RainFlowGameController : MonoBehaviour
    {
        private enum ScreenState
        {
            RegionSelect,
            PolicyDesign,
            Result,
            Victory
        }

        private BackendProcessManager _backend;
        private RainFlowApiClient _api;
        private MapWorldController _map;
        private AnimalPoolController _animals;
        private GameSaveService _saveService;
        private GameSaveV1 _save;
        private MissionCatalogDto _catalog;
        private PolicyDesignV1 _policy = new PolicyDesignV1();
        private PolicyAdviceDto _lastAdvice;
        private MissionEvaluationV1 _evaluation;
        private ScreenState _screen;
        private int _missionStage;
        private bool _busy;
        private bool _replayStarted;
        private bool _replayFinished;
        private string _message;
        private float _missionStartedAt;
        private GUIStyle _title;
        private GUIStyle _subtitle;
        private GUIStyle _body;
        private GUIStyle _small;
        private GUIStyle _card;
        private GUIStyle _button;
        private GUIStyle _primaryButton;
        private GUIStyle _dangerButton;
        private Texture2D _panelTexture;
        private Texture2D _cardTexture;
        private Texture2D _primaryTexture;
        private Texture2D _buttonTexture;

        public void Configure(
            BackendProcessManager backend,
            RainFlowApiClient api,
            MapWorldController map,
            AnimalPoolController animals)
        {
            _backend = backend;
            _api = api;
            _map = map;
            _animals = animals;
            _api.Configure(_backend);
            _animals.ConfigureRoutes(_map.Routes);
            _saveService = new GameSaveService();
            _save = _saveService.Load();
            _animals.SetAlternateSkin(_save.AnimalSkinUnlocked);

            if (string.IsNullOrEmpty(_save.SelectedStartRegion))
            {
                _screen = ScreenState.RegionSelect;
                _missionStage = 0;
            }
            else
            {
                _missionStage = Mathf.Clamp(_save.CurrentStage, 1, 3);
                _screen = ScreenState.PolicyDesign;
                PrepareMissionView();
            }
            StartCoroutine(InitializeServices());
        }

        private IEnumerator InitializeServices()
        {
            _message = "로컬 시뮬레이션을 확인하고 있습니다.";
            yield return _backend.Initialize(live =>
            {
                _message = live
                    ? "실시간 로컬 시뮬레이션 준비 완료"
                    : "fixture 모드: 검증된 기본 결과를 재생합니다.";
            });
            yield return _api.GetCatalog(catalog => _catalog = catalog);
        }

        private void OnGUI()
        {
            EnsureStyles();
            DrawHeader();
            switch (_screen)
            {
                case ScreenState.RegionSelect:
                    DrawRegionSelect();
                    break;
                case ScreenState.PolicyDesign:
                    DrawPolicyDesign();
                    break;
                case ScreenState.Result:
                    DrawResult();
                    break;
                case ScreenState.Victory:
                    DrawVictory();
                    break;
            }
            DrawRealityNote();
        }

        private void DrawHeader()
        {
            var header = new Rect(24, 18, Screen.width - 48, 70);
            GUI.Box(header, GUIContent.none, _card);
            GUI.Label(new Rect(44, 29, 520, 30), "RAIN•FLOW  어진동 복구본부", _title);
            GUI.Label(
                new Rect(44, 59, 700, 20),
                "지역을 성장시키고 Luna · Terra · Sol을 이겨라",
                _small);
            GUI.Label(
                new Rect(Screen.width - 390, 35, 340, 22),
                (_backend != null ? _backend.StatusMessage : "초기화 중")
                + "   |   " + (_save != null ? _save.Credits : 0) + " CR",
                _small);
        }

        private void DrawRegionSelect()
        {
            var panel = MainPanel(520, 430);
            GUI.Box(panel, GUIContent.none, _card);
            GUI.Label(Inset(panel, 28, 24, 28), "어디서부터 복구할까요?", _title);
            GUI.Label(
                Inset(panel, 28, 67, 58),
                "관심 있는 생활권을 선택하세요. 두 선택지는 같은 교통 조건으로 시작하고, 완료하면 인접 지역이 열립니다.",
                _body);

            var left = new Rect(panel.x + 28, panel.y + 145, panel.width - 56, 86);
            if (GUI.Button(left, "성금–청사 생활권\n짧은 도심 연결로부터 시작", _primaryButton))
            {
                SelectStartRegion("seonggeum_cheongsa");
            }
            var right = new Rect(panel.x + 28, panel.y + 247, panel.width - 56, 86);
            if (GUI.Button(right, "청사–세종 생활권\n정부청사 회랑에서 시작", _button))
            {
                SelectStartRegion("cheongsa_sejong");
            }
            GUI.Label(
                new Rect(panel.x + 28, panel.y + 355, panel.width - 56, 45),
                "마우스 휠: 확대/축소   ·   가운데 버튼 드래그: 지도 이동",
                _small);
        }

        private void DrawPolicyDesign()
        {
            var panel = new Rect(24, 106, 450, Screen.height - 156);
            GUI.Box(panel, GUIContent.none, _card);
            var missionId = CurrentMissionId();
            GUI.Label(new Rect(panel.x + 24, panel.y + 20, 390, 28), MissionTitle(missionId), _title);
            GUI.Label(
                new Rect(panel.x + 24, panel.y + 53, 390, 42),
                CurrentRegionLabel() + " · 상대 " + CurrentBotName(),
                _subtitle);

            var y = panel.y + 112;
            _policy.TriggerOccupancyPct = DrawSlider(
                panel,
                ref y,
                "작동 점유율",
                _policy.TriggerOccupancyPct,
                65,
                95,
                5,
                "%");
            var strengthStep = HasEquipment("smart_controller") ? 5 : 10;
            _policy.MeteringStrengthPct = DrawSlider(
                panel,
                ref y,
                "유입 제한 강도",
                _policy.MeteringStrengthPct,
                0,
                100,
                strengthStep,
                "%");
            var diversionMax = HasEquipment("dynamic_guidance") ? 20 : 10;
            _policy.DiversionStrength = DrawSlider(
                panel,
                ref y,
                "우회 유도 강도",
                _policy.DiversionStrength,
                0,
                diversionMax,
                5,
                "");

            GUI.Box(new Rect(panel.x + 20, y + 4, panel.width - 40, 108), GUIContent.none, _card);
            if (_lastAdvice == null)
            {
                GUI.Label(
                    new Rect(panel.x + 38, y + 19, panel.width - 76, 70),
                    "AI 코치\n첫 실행 후 역류·공정성·통행시간을 분석해 다음 조합을 추천합니다.",
                    _body);
            }
            else
            {
                GUI.Label(
                    new Rect(panel.x + 38, y + 16, panel.width - 150, 75),
                    _lastAdvice.Title + "\n" + _lastAdvice.Reason + "\n주의: " + _lastAdvice.Tradeoff,
                    _small);
                if (GUI.Button(
                    new Rect(panel.x + panel.width - 132, y + 31, 92, 48),
                    "추천 적용",
                    _button))
                {
                    _policy = _lastAdvice.RecommendedPolicy.Clone();
                }
            }
            y += 130;

            DrawShop(panel, ref y);
            GUI.enabled = !_busy;
            if (GUI.Button(
                new Rect(panel.x + 24, panel.yMax - 70, panel.width - 48, 48),
                _busy ? "AI가 동일 조건을 탐색 중…" : "정책 실행 · " + CurrentBotName() + " 대결",
                _primaryButton))
            {
                RunMission();
            }
            GUI.enabled = true;
        }

        private void DrawShop(Rect panel, ref float y)
        {
            GUI.Label(new Rect(panel.x + 24, y, 140, 24), "신호 장비", _subtitle);
            y += 30;
            if (!HasEquipment("smart_controller"))
            {
                if (GUI.Button(
                    new Rect(panel.x + 24, y, panel.width - 48, 34),
                    "스마트 신호제어기 · 50 CR · 제한 강도 5% 조정",
                    _button))
                {
                    BuyEquipment("smart_controller", 50);
                }
                y += 40;
            }
            if (!HasEquipment("dynamic_guidance"))
            {
                if (GUI.Button(
                    new Rect(panel.x + 24, y, panel.width - 48, 34),
                    "동적 우회 안내판 · 50 CR · 우회 상한 20",
                    _button))
                {
                    BuyEquipment("dynamic_guidance", 50);
                }
                y += 40;
            }
            if (!_save.AnimalSkinUnlocked)
            {
                if (GUI.Button(
                    new Rect(panel.x + 24, y, panel.width - 48, 34),
                    "보랏빛 동물 스킨 · 30 CR",
                    _button))
                {
                    if (_save.Credits >= 30)
                    {
                        _save.Credits -= 30;
                        _save.AnimalSkinUnlocked = true;
                        _animals.SetAlternateSkin(true);
                        _saveService.Save(_save);
                    }
                    else _message = "크레딧이 부족합니다.";
                }
            }
        }

        private void DrawResult()
        {
            var panel = MainPanel(650, 590);
            GUI.Box(panel, GUIContent.none, _card);
            var result = _evaluation;
            var eventDto = result.AdaptiveEvent;
            GUI.Label(new Rect(panel.x + 28, panel.y + 20, panel.width - 56, 30), eventDto.Title, _title);
            GUI.Label(
                new Rect(panel.x + 28, panel.y + 55, panel.width - 56, 42),
                eventDto.Reason + "  ·  유효 수요 ×" + eventDto.EffectiveDemandMultiplier.ToString("0.00"),
                _body);

            var winText = result.Success ? "복구 성공" : "다시 설계하세요";
            GUI.Label(new Rect(panel.x + 28, panel.y + 112, 240, 32), winText, _title);
            GUI.Label(
                new Rect(panel.x + 28, panel.y + 154, panel.width - 56, 30),
                "PLAYER " + result.Player.Score.ToString("0.000")
                + "    vs    " + result.Opponent.Tier.ToUpperInvariant()
                + " " + result.Opponent.Score.ToString("0.000")
                + "    차이 " + Signed(result.Progression.OpponentScoreMargin),
                _subtitle);

            var cardsY = panel.y + 205;
            DrawMetricCard(panel.x + 28, cardsY, 180, "교통 만족도", result.Satisfaction.Traffic.ToString("0"));
            DrawMetricCard(panel.x + 234, cardsY, 180, "보행 만족도*", result.Satisfaction.PedestrianProxy.ToString("0"));
            DrawMetricCard(panel.x + 440, cardsY, 180, "가상 가치지수", result.Progression.VirtualPropertyValueIndex.ToString("0.0"));

            GUI.Label(
                new Rect(panel.x + 28, panel.y + 300, panel.width - 56, 48),
                "건물 Level " + result.Progression.BuildingLevelBefore + " → "
                + result.Progression.BuildingLevelAfter
                + "   ·   다음 수요 +" + result.Progression.NextDemandBonusPct + "%"
                + "   ·   획득 " + result.Progression.CreditsEarned + " CR",
                _body);

            if (result.Player.Guard != null && !result.Player.Guard.Passed)
            {
                var detail = result.Player.Guard.Violations.Count > 0
                    ? result.Player.Guard.Violations[0].Detail
                    : "안전·공정성 기준을 통과하지 못했습니다.";
                GUI.Label(new Rect(panel.x + 28, panel.y + 355, panel.width - 56, 45), detail, _small);
            }
            else if (result.Advice != null && result.Advice.Count > 0)
            {
                var advice = result.Advice[0];
                GUI.Label(
                    new Rect(panel.x + 28, panel.y + 355, panel.width - 56, 58),
                    "AI 코치: " + advice.Title + "\n" + advice.Reason + " · " + advice.Tradeoff,
                    _small);
            }

            if (!_replayStarted)
            {
                if (GUI.Button(
                    new Rect(panel.x + 28, panel.yMax - 78, panel.width - 56, 48),
                    "이벤트 확인 · 동물 교통 재생",
                    _primaryButton))
                {
                    _replayStarted = true;
                    StartCoroutine(ReplayTimeline());
                }
            }
            else
            {
                var label = _replayFinished
                    ? (result.Success ? "다음 지역으로" : "정책 다시 설계")
                    : "재생 건너뛰기";
                if (GUI.Button(
                    new Rect(panel.x + 28, panel.yMax - 78, panel.width - 56, 48),
                    label,
                    result.Success ? _primaryButton : _button))
                {
                    _replayFinished = true;
                    ContinueAfterResult();
                }
            }
        }

        private void DrawVictory()
        {
            var panel = MainPanel(620, 420);
            GUI.Box(panel, GUIContent.none, _card);
            GUI.Label(new Rect(panel.x + 32, panel.y + 35, panel.width - 64, 40), "SOL 격파 · 어진동 복구 완료", _title);
            GUI.Label(
                new Rect(panel.x + 32, panel.y + 95, panel.width - 64, 95),
                "두 생활권의 성장 수요를 견디고 AI보다 나은 안전 정책을 설계했습니다.\n\n이 기록은 로컬 정책 후보 탐색 데이터이며 실제 정책 성과를 뜻하지 않습니다.",
                _body);
            GUI.Label(
                new Rect(panel.x + 32, panel.y + 220, panel.width - 64, 50),
                "로컬 랭킹 기록: " + _save.Rankings.Count + "개   ·   보유 크레딧: " + _save.Credits,
                _subtitle);
            if (GUI.Button(
                new Rect(panel.x + 32, panel.yMax - 85, panel.width - 64, 48),
                "새 게임 시작 (로컬 저장 초기화)",
                _dangerButton))
            {
                _save = _saveService.Reset();
                _missionStage = 0;
                _policy = new PolicyDesignV1();
                _evaluation = null;
                _lastAdvice = null;
                _screen = ScreenState.RegionSelect;
            }
        }

        private void DrawRealityNote()
        {
            GUI.Label(
                new Rect(30, Screen.height - 35, Screen.width - 60, 22),
                (_message ?? string.Empty)
                + "   ·   *보행 만족도는 접근로 공정성 기반 게임 proxy입니다. 실제 부동산·정책 예측이 아닙니다.",
                _small);
        }

        private void SelectStartRegion(string regionId)
        {
            _save.SelectedStartRegion = regionId;
            _save.CurrentStage = 1;
            _missionStage = 1;
            if (!_save.UnlockedRegions.Contains(regionId)) _save.UnlockedRegions.Add(regionId);
            if (!_save.BuildingLevels.ContainsKey(regionId)) _save.BuildingLevels[regionId] = 1;
            _saveService.Save(_save);
            _screen = ScreenState.PolicyDesign;
            PrepareMissionView();
        }

        private void RunMission()
        {
            if (_busy) return;
            _busy = true;
            var missionId = CurrentMissionId();
            var attempts = _save.GetAttempts(missionId) + 1;
            _save.MissionAttempts[missionId] = attempts;
            var regionId = CurrentRegionId();
            var elapsed = Mathf.Max(0f, Time.realtimeSinceStartup - _missionStartedAt);
            var request = new MissionEvaluationRequestV1
            {
                RegionId = regionId,
                Seed = 42,
                PolicyDesign = _policy.Clone(),
                Progress = new PlayerProgressV1
                {
                    Attempts = attempts,
                    LastScoreMargin = _save.LastScoreMargin,
                    LastCompletionTimeSec = _save.LastCompletionTimeSec,
                    BuildingLevel = _save.GetBuildingLevel(regionId),
                    Equipment = new List<string>(_save.Equipment)
                }
            };
            StartCoroutine(_api.Evaluate(missionId, request, (result, error) =>
            {
                _busy = false;
                if (result == null)
                {
                    _message = error;
                    return;
                }
                _evaluation = result;
                _message = error ?? (result.ResultSource == "fixture" ? "fixture 결과" : "live 결과");
                _save.LastScoreMargin = result.Progression.OpponentScoreMargin;
                _save.LastCompletionTimeSec = elapsed;
                _lastAdvice = result.Advice != null && result.Advice.Count > 0 ? result.Advice[0] : null;
                ApplyProgress(result, elapsed, attempts);
                _screen = ScreenState.Result;
                _replayStarted = false;
                _replayFinished = false;
            }));
        }

        private void ApplyProgress(MissionEvaluationV1 result, float elapsed, int attempts)
        {
            AddRanking(result, elapsed, attempts, "PLAYER", result.Player);
            AddRanking(result, 0f, 1, result.Opponent.Tier.ToUpperInvariant(), result.Opponent);
            if (result.Success)
            {
                if (!_save.CompletedMissions.Contains(result.MissionId))
                {
                    _save.CompletedMissions.Add(result.MissionId);
                    _save.Credits += result.Progression.CreditsEarned;
                }
                _save.BuildingLevels[result.RegionId] = result.Progression.BuildingLevelAfter;
                _map.SetBuildingLevel(result.RegionId, result.Progression.BuildingLevelAfter);
                if (_missionStage < 3)
                {
                    _save.CurrentStage = _missionStage + 1;
                    var nextRegion = _missionStage == 1 ? OtherStartingRegion() : "eojin_corridor";
                    if (!_save.UnlockedRegions.Contains(nextRegion)) _save.UnlockedRegions.Add(nextRegion);
                }
            }
            _saveService.Save(_save);
        }

        private void AddRanking(
            MissionEvaluationV1 result,
            float elapsed,
            int attempts,
            string actor,
            CandidateResultDto candidate)
        {
            _save.Rankings.Add(new RankingEntryV1
            {
                MissionId = result.MissionId,
                RegionId = result.RegionId,
                Actor = actor,
                Score = candidate.Score,
                CompletionTimeSec = elapsed,
                Attempts = attempts,
                AdaptiveMode = result.AdaptiveEvent.Mode,
                PolicyDesign = candidate.PolicyDesign != null ? candidate.PolicyDesign.Clone() : null
            });
        }

        private IEnumerator ReplayTimeline()
        {
            var timeline = _evaluation.Player.Timeline;
            if (timeline == null || timeline.Count == 0)
            {
                _replayFinished = true;
                yield break;
            }
            foreach (var entry in timeline)
            {
                var occupancy = entry.Links == null || entry.Links.Count == 0
                    ? 0f
                    : entry.Links.Average(link => link.OccupancyRatio);
                _map.ApplyCongestion(occupancy);
                _animals.ApplyState(occupancy, _evaluation.Progression.BuildingLevelAfter);
                yield return new WaitForSecondsRealtime(0.18f);
                if (_replayFinished) yield break;
            }
            _replayFinished = true;
        }

        private void ContinueAfterResult()
        {
            StopAllCoroutines();
            if (_evaluation.Success)
            {
                if (_missionStage >= 3)
                {
                    _screen = ScreenState.Victory;
                    return;
                }
                _missionStage = Mathf.Clamp(_save.CurrentStage, 1, 3);
                _policy = new PolicyDesignV1();
            }
            _evaluation = null;
            _screen = ScreenState.PolicyDesign;
            PrepareMissionView();
        }

        private void PrepareMissionView()
        {
            var region = CurrentRegionId();
            _map.SetSelectedRegion(region);
            _map.SetBuildingLevel(region, _save.GetBuildingLevel(region));
            _missionStartedAt = Time.realtimeSinceStartup;
        }

        private string CurrentMissionId()
        {
            return _missionStage <= 1
                ? "rain_commute"
                : _missionStage == 2
                    ? "rain_incident"
                    : "corridor_final";
        }

        private string CurrentRegionId()
        {
            if (_missionStage >= 3) return "eojin_corridor";
            return _missionStage == 1 ? _save.SelectedStartRegion : OtherStartingRegion();
        }

        private string OtherStartingRegion()
        {
            return _save.SelectedStartRegion == "seonggeum_cheongsa"
                ? "cheongsa_sejong"
                : "seonggeum_cheongsa";
        }

        private string CurrentRegionLabel()
        {
            var id = CurrentRegionId();
            if (id == "seonggeum_cheongsa") return "성금–청사 생활권";
            if (id == "cheongsa_sejong") return "청사–세종 생활권";
            return "어진동 통합 회랑";
        }

        private string CurrentBotName()
        {
            return _missionStage <= 1 ? "Luna" : _missionStage == 2 ? "Terra" : "Sol";
        }

        private static string MissionTitle(string missionId)
        {
            if (missionId == "rain_commute") return "출퇴근 집중호우";
            if (missionId == "rain_incident") return "강우·사고 복구";
            return "어진동 AI 회랑전";
        }

        private bool HasEquipment(string equipmentId)
        {
            return _save.Equipment.Contains(equipmentId);
        }

        private void BuyEquipment(string equipmentId, int cost)
        {
            if (_save.Credits < cost)
            {
                _message = "크레딧이 부족합니다.";
                return;
            }
            _save.Credits -= cost;
            _save.Equipment.Add(equipmentId);
            _saveService.Save(_save);
        }

        private int DrawSlider(
            Rect panel,
            ref float y,
            string label,
            int value,
            int minimum,
            int maximum,
            int step,
            string suffix)
        {
            GUI.Label(new Rect(panel.x + 24, y, 240, 24), label, _body);
            GUI.Label(new Rect(panel.xMax - 110, y, 82, 24), value + suffix, _subtitle);
            var raw = GUI.HorizontalSlider(
                new Rect(panel.x + 24, y + 31, panel.width - 48, 18),
                value,
                minimum,
                maximum);
            y += 72;
            return Mathf.Clamp(Mathf.RoundToInt(raw / step) * step, minimum, maximum);
        }

        private void DrawMetricCard(float x, float y, float width, string label, string value)
        {
            GUI.Box(new Rect(x, y, width, 72), GUIContent.none, _card);
            GUI.Label(new Rect(x + 14, y + 10, width - 28, 18), label, _small);
            GUI.Label(new Rect(x + 14, y + 31, width - 28, 30), value, _title);
        }

        private static string Signed(float value)
        {
            return value >= 0 ? "+" + value.ToString("0.000") : value.ToString("0.000");
        }

        private static Rect MainPanel(float width, float height)
        {
            return new Rect(
                (Screen.width - width) * 0.5f,
                Mathf.Max(105, (Screen.height - height) * 0.5f),
                width,
                height);
        }

        private static Rect Inset(Rect rect, float x, float y, float height)
        {
            return new Rect(rect.x + x, rect.y + y, rect.width - x * 2, height);
        }

        private void EnsureStyles()
        {
            if (_title != null) return;
            _panelTexture = SolidTexture(new Color(0.06f, 0.08f, 0.12f, 0.96f));
            _cardTexture = SolidTexture(new Color(0.095f, 0.12f, 0.17f, 0.96f));
            _primaryTexture = SolidTexture(new Color(0.22f, 0.76f, 0.64f, 1f));
            _buttonTexture = SolidTexture(new Color(0.16f, 0.20f, 0.27f, 1f));
            _title = NewLabel(22, FontStyle.Bold, Color.white);
            _subtitle = NewLabel(16, FontStyle.Bold, new Color(0.55f, 0.91f, 0.82f));
            _body = NewLabel(14, FontStyle.Normal, new Color(0.88f, 0.91f, 0.95f));
            _small = NewLabel(12, FontStyle.Normal, new Color(0.65f, 0.72f, 0.80f));
            _card = new GUIStyle(GUI.skin.box)
            {
                normal = { background = _cardTexture },
                padding = new RectOffset(16, 16, 16, 16)
            };
            _button = NewButton(_buttonTexture, Color.white);
            _primaryButton = NewButton(_primaryTexture, new Color(0.04f, 0.12f, 0.10f));
            _dangerButton = NewButton(SolidTexture(new Color(0.62f, 0.20f, 0.22f)), Color.white);
        }

        private static GUIStyle NewLabel(int size, FontStyle style, Color color)
        {
            return new GUIStyle(GUI.skin.label)
            {
                fontSize = size,
                fontStyle = style,
                normal = { textColor = color },
                wordWrap = true
            };
        }

        private static GUIStyle NewButton(Texture2D background, Color color)
        {
            return new GUIStyle(GUI.skin.button)
            {
                fontSize = 14,
                fontStyle = FontStyle.Bold,
                alignment = TextAnchor.MiddleCenter,
                wordWrap = true,
                normal = { background = background, textColor = color },
                hover = { background = background, textColor = color },
                active = { background = background, textColor = color },
                padding = new RectOffset(12, 12, 8, 8)
            };
        }

        private static Texture2D SolidTexture(Color color)
        {
            var texture = new Texture2D(1, 1);
            texture.SetPixel(0, 0, color);
            texture.Apply();
            return texture;
        }
    }
}
