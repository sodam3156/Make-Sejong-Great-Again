using System;

namespace Tats.Client.UI
{
    /// <summary>
    /// Development-only display state. It never calculates traffic, points, safety, or cost.
    /// Replace this class with a presenter adapter when the game-v2 contract is frozen.
    /// </summary>
    public sealed class TatsMockViewModel
    {
        private const int ClearanceSeconds = 15;
        private SimulationSpeed speedBeforeConnectionLoss = SimulationSpeed.Paused;
        private string pointsLabel = "40 pt";
        private string startIntersectionId = "intersection-seonggeum";
        private string startIntersectionLabel = "성금사거리";
        private string startOpponentLabel = "Luna";

        public event Action Changed;

        public TatsScreenState State { get; } = new TatsScreenState();

        public string CityClockLabel => "Day 1 · 03:00";
        public string PointsLabel => pointsLabel;
        public string SettlementLabel => "다음 정산 00:42";
        public string AiOpponentLabel => $"{startOpponentLabel} · +84 flow";
        public string AiComparisonEyebrow => $"AI RECORD · {startOpponentLabel.ToUpperInvariant()}";
        public string AiComparisonTitle => $"{startOpponentLabel} AI Record";
        public string StartIntersectionId => startIntersectionId;
        public string StartOpponentLabel => startOpponentLabel;
        public string StartConfigurationLabel => $"{startIntersectionLabel} · {startOpponentLabel} AI · Day 1 03:00";
        public string JourneyStageLabel
        {
            get
            {
                if (State.PrimaryMode == PrimaryMode.RoadUnlock || State.PrimaryMode == PrimaryMode.Building)
                {
                    return "06 · 도시 성장";
                }

                if (State.PrimaryMode == PrimaryMode.AICompare)
                {
                    return "07 · AI 기록 비교";
                }

                if (State.SignalWorkflowPanel == SignalWorkflowPanel.ImpactPreview)
                {
                    return "04 · 영향 검토";
                }

                if (State.SignalWorkflowPanel == SignalWorkflowPanel.ApplyStatus ||
                    State.SignalDraftStatus == SignalDraftStatus.Scheduled ||
                    State.SignalDraftStatus == SignalDraftStatus.SafeTransition)
                {
                    return "05 · 안전 적용";
                }

                return State.PrimaryMode switch
                {
                    PrimaryMode.Diagnose => "02 · 원인 진단",
                    PrimaryMode.SignalEdit => "03 · 신호 설계",
                    _ => State.SelectionKind == SelectionKind.None ? "01 · 지도 관찰" : "02 · 교차로 진단"
                };
            }
        }
        public string ConnectionLabel => State.ConnectionState switch
        {
            ConnectionState.Connected => "연결됨",
            ConnectionState.Applying => "적용 중",
            ConnectionState.Reconnecting => "재연결 중",
            ConnectionState.ResumeReady => "재개 준비",
            ConnectionState.ResumeFailed => "복구 실패",
            _ => State.ConnectionState.ToString()
        };
        public string SelectedTitle { get; private set; } = "선택 대상 없음";
        public string SelectedSubtitle { get; private set; } = "지도에서 교차로·건물·도로를 선택하세요.";
        public string SelectedPrimaryValue { get; private set; } = "—";
        public string SelectedSecondaryValue { get; private set; } = "—";
        public string HelperText { get; private set; } = "교차로·건물·도로를 선택합니다.";
        public int NorthSouthGreenSeconds { get; private set; } = 45;
        public int EastWestGreenSeconds { get; private set; } = 35;
        public int PedestrianSeconds { get; private set; } = 25;
        public int ReconnectRetryCount { get; private set; }
        public bool RoadUnlocked { get; private set; }
        public int BuildingLevel { get; private set; } = 1;
        public string FeatureReceiptLabel { get; private set; } = "아직 접수된 fixture 명령이 없습니다.";
        public int DraftCycleSeconds => NorthSouthGreenSeconds + EastWestGreenSeconds + PedestrianSeconds + ClearanceSeconds;
        public bool IsDraftValid =>
            NorthSouthGreenSeconds >= 20 &&
            EastWestGreenSeconds >= 20 &&
            PedestrianSeconds >= 5 &&
            DraftCycleSeconds >= 90 &&
            DraftCycleSeconds <= 150;
        public string SelectedIntersectionLabel => State.SelectionKind == SelectionKind.Intersection ? SelectedTitle : "교차로 미선택";
        public string DraftCycleLabel => $"{DraftCycleSeconds}초";
        public string DraftPhaseSummary =>
            $"남북 {NorthSouthGreenSeconds}초 · 동서 {EastWestGreenSeconds}초 · 보행 {PedestrianSeconds}초 · 정리 {ClearanceSeconds}초";
        public string DraftValidationLabel => IsDraftValid
            ? "충돌 관계 없음 · 최소 시간 충족 · 인접 오프셋 검토 완료"
            : "입력 범위를 확인하세요. 차량 20초·보행 5초 이상, 전체 주기 90~150초가 필요합니다.";
        public string CycleComparisonLabel => $"현재 120초 → 초안 {DraftCycleSeconds}초";
        public string QueuePreviewLabel => "북→남 대기 12대 → 9대 · fixture";
        public string SafetyPreviewLabel => "안전 점수 98.4 → 98.4 · fixture";
        public string NeighborPreviewLabel => "세종교차로 오프셋 +4초 · 청사교차로 영향 없음";
        public string ApplyReceiptLabel => "CMD-MOCK-2047-B · expectedTick 3,842";
        public string ReconnectRetryLabel => $"{ReconnectRetryCount}회 / 최대 3회";
        public string ResumeSpeedLabel => speedBeforeConnectionLoss switch
        {
            SimulationSpeed.X1 => "1×로 재개",
            SimulationSpeed.X3 => "3×로 재개",
            SimulationSpeed.X5 => "5×로 재개",
            _ => "정지 상태로 재개"
        };
        public string AlgorithmPresetLabel => State.AlgorithmPreset switch
        {
            AlgorithmPreset.Balanced => "균형 최적화",
            AlgorithmPreset.VehicleFlow => "차량 흐름 우선",
            AlgorithmPreset.PedestrianFirst => "보행 안전 우선",
            _ => State.AlgorithmPreset.ToString()
        };
        public string SkillbookTargetLabel => State.SelectionKind == SelectionKind.Intersection
            ? $"적용 대상 · {SelectedTitle}"
            : "적용 대상 · 교차로를 먼저 선택하세요";
        public string RoadStatusLabel => RoadUnlocked ? "개방 완료 · 어진동 연결로" : "구매 가능 · 20 pt";
        public string BuildingLevelLabel => $"Level {BuildingLevel} · 시청 복합건물";
        public string BuildingOutputLabel => BuildingLevel switch
        {
            1 => "유동인구 +12 / 시간 · fixture",
            2 => "유동인구 +19 / 시간 · fixture",
            _ => "유동인구 +27 / 시간 · fixture"
        };

        public void SelectStartIntersection(string elementId, string displayName)
        {
            startIntersectionId = elementId;
            startIntersectionLabel = displayName;
            NotifyChanged();
        }

        public void SelectStartOpponent(string opponentName)
        {
            startOpponentLabel = opponentName;
            NotifyChanged();
        }

        public void OpenFirstThreeMinutes()
        {
            State.ExperienceScreen = ExperienceScreen.FirstThreeMinutes;
            NotifyChanged();
        }

        public void ReturnToTitle()
        {
            State.ExperienceScreen = ExperienceScreen.Title;
            NotifyChanged();
        }

        public void EnterMainGame()
        {
            State.ExperienceScreen = ExperienceScreen.MainGame;
            State.PrimaryMode = PrimaryMode.Diagnose;
            State.OverlayType = OverlayType.SignalPhase;
            State.SimulationSpeed = SimulationSpeed.Paused;
            State.IsFeaturePanelOpen = false;
            State.SignalWorkflowPanel = SignalWorkflowPanel.Closed;
            ApplyIntersectionSelection(startIntersectionId, startIntersectionLabel);
            HelperText = "첫 3분 시작 · 현재 신호 현시를 읽고 선택 교차로의 계획을 진단하세요.";
            NotifyChanged();
        }

        public void SetMode(PrimaryMode mode)
        {
            State.PrimaryMode = mode;
            State.IsFeaturePanelOpen = IsFeatureMode(mode);
            if (mode != PrimaryMode.SignalEdit)
            {
                State.SignalWorkflowPanel = SignalWorkflowPanel.Closed;
            }

            if (mode != PrimaryMode.Diagnose)
            {
                State.OverlayType = OverlayType.None;
            }

            if (mode == PrimaryMode.SignalEdit)
            {
                if (State.SelectionKind != SelectionKind.Intersection)
                {
                    State.SignalWorkflowPanel = SignalWorkflowPanel.Closed;
                    HelperText = "먼저 지도에서 신호를 편집할 교차로를 선택하세요.";
                    NotifyChanged();
                    return;
                }

                State.SignalWorkflowPanel = SignalWorkflowPanel.Editor;
                State.IsFeaturePanelOpen = false;
                HelperText = $"{SelectedTitle} 신호 계획의 로컬 초안을 편집합니다.";
                NotifyChanged();
                return;
            }

            HelperText = mode switch
            {
                PrimaryMode.Select => "교차로·건물·도로를 선택합니다.",
                PrimaryMode.Diagnose => "혼잡·대기·이탈·위험 원인을 지도에서 찾습니다.",
                PrimaryMode.SignalEdit => "선택 교차로의 단계 순서·시간·우선순위를 설계합니다.",
                PrimaryMode.Skillbook => "알고리즘 원리와 trade-off를 읽고 AI 초안을 준비합니다.",
                PrimaryMode.RoadUnlock => "연결된 다음 도로의 비용과 신규 수요를 확인합니다.",
                PrimaryMode.Building => "건물 생산량과 다음 Level 변화를 확인합니다.",
                PrimaryMode.AICompare => "같은 조건의 AI 기록과 현재 운영을 비교합니다.",
                _ => string.Empty
            };

            NotifyChanged();
        }

        public void SelectAlgorithmPreset(AlgorithmPreset preset)
        {
            State.AlgorithmPreset = preset;
            FeatureReceiptLabel = $"{AlgorithmPresetLabel} 프리셋을 선택했습니다. 아직 서버에 적용되지 않았습니다.";
            HelperText = $"스킬북에서 {AlgorithmPresetLabel} 프리셋을 선택했습니다.";
            NotifyChanged();
        }

        public void GenerateAiSignalDraft()
        {
            if (State.SelectionKind != SelectionKind.Intersection)
            {
                HelperText = "AI 신호 초안을 만들려면 먼저 지도에서 교차로를 선택하세요.";
                NotifyChanged();
                return;
            }

            switch (State.AlgorithmPreset)
            {
                case AlgorithmPreset.Balanced:
                    NorthSouthGreenSeconds = 45;
                    EastWestGreenSeconds = 35;
                    PedestrianSeconds = 25;
                    break;
                case AlgorithmPreset.VehicleFlow:
                    NorthSouthGreenSeconds = 55;
                    EastWestGreenSeconds = 40;
                    PedestrianSeconds = 15;
                    break;
                case AlgorithmPreset.PedestrianFirst:
                    NorthSouthGreenSeconds = 40;
                    EastWestGreenSeconds = 30;
                    PedestrianSeconds = 35;
                    break;
                default:
                    throw new ArgumentOutOfRangeException();
            }

            State.SignalDraftStatus = SignalDraftStatus.Dirty;
            State.PrimaryMode = PrimaryMode.SignalEdit;
            State.IsFeaturePanelOpen = false;
            State.SignalWorkflowPanel = SignalWorkflowPanel.Editor;
            FeatureReceiptLabel = $"AI fixture가 {SelectedTitle}의 {AlgorithmPresetLabel} 초안을 생성했습니다.";
            HelperText = "AI가 생성한 규칙 기반 초안을 열었습니다. 사용자가 직접 검토·수정해야 합니다.";
            NotifyChanged();
        }

        public void PurchaseRoadFixture()
        {
            if (RoadUnlocked)
            {
                return;
            }

            RoadUnlocked = true;
            pointsLabel = BuildingLevel > 1 ? "10 pt" : "20 pt";
            FeatureReceiptLabel = "ROAD-MOCK-020 · 어진동 연결로 개방 접수 완료";
            HelperText = "도로 개방 fixture가 반영됐습니다. 실제 수요·비용은 서버가 결정합니다.";
            NotifyChanged();
        }

        public void UpgradeBuildingFixture()
        {
            if (BuildingLevel >= 3)
            {
                return;
            }

            BuildingLevel += 1;
            pointsLabel = BuildingLevel switch
            {
                2 => RoadUnlocked ? "10 pt" : "30 pt",
                _ => RoadUnlocked ? "0 pt" : "20 pt"
            };
            FeatureReceiptLabel = $"BUILDING-MOCK-L{BuildingLevel} · 시청 복합건물 업그레이드 접수";
            HelperText = "건물 업그레이드 fixture가 반영됐습니다. 유동인구 결과는 서버 표시값입니다.";
            NotifyChanged();
        }

        public void CloseFeaturePanel()
        {
            State.IsFeaturePanelOpen = false;
            State.PrimaryMode = PrimaryMode.Select;
            HelperText = "기능 패널을 닫고 선택 모드로 돌아왔습니다.";
            NotifyChanged();
        }

        public void SetSpeed(SimulationSpeed speed)
        {
            State.SimulationSpeed = speed;
            NotifyChanged();
        }

        public void ToggleOverlay(OverlayType overlayType)
        {
            State.PrimaryMode = PrimaryMode.Diagnose;
            State.OverlayType = State.OverlayType == overlayType ? OverlayType.None : overlayType;
            HelperText = State.OverlayType == OverlayType.None
                ? "진단 레이어를 선택하세요. 한 번에 하나만 활성화됩니다."
                : $"{GetOverlayLabel(State.OverlayType)} 레이어가 활성화됐습니다. 선택과 배속은 유지됩니다.";
            NotifyChanged();
        }

        public void SelectIntersection(string elementId, string displayName)
        {
            ApplyIntersectionSelection(elementId, displayName);
            HelperText = $"{displayName}을(를) 선택했습니다. 신호 편집으로 이어갈 수 있습니다.";
            NotifyChanged();
        }

        public void AdjustSignalPhase(SignalPhaseKind phaseKind, int deltaSeconds)
        {
            switch (phaseKind)
            {
                case SignalPhaseKind.NorthSouth:
                    NorthSouthGreenSeconds = Clamp(NorthSouthGreenSeconds + deltaSeconds, 20, 70);
                    break;
                case SignalPhaseKind.EastWest:
                    EastWestGreenSeconds = Clamp(EastWestGreenSeconds + deltaSeconds, 20, 70);
                    break;
                case SignalPhaseKind.Pedestrian:
                    PedestrianSeconds = Clamp(PedestrianSeconds + deltaSeconds, 5, 40);
                    break;
                default:
                    throw new ArgumentOutOfRangeException(nameof(phaseKind), phaseKind, null);
            }

            State.SignalDraftStatus = SignalDraftStatus.Dirty;
            HelperText = IsDraftValid
                ? "로컬 초안이 변경됐습니다. 영향 미리보기에서 적용 전후를 확인하세요."
                : "로컬 초안의 입력 범위를 확인하세요.";
            NotifyChanged();
        }

        public void ResetSignalDraft()
        {
            NorthSouthGreenSeconds = 45;
            EastWestGreenSeconds = 35;
            PedestrianSeconds = 25;
            State.SignalDraftStatus = SignalDraftStatus.Clean;
            HelperText = "신호 계획 초안을 서버 운영 계획 값으로 되돌렸습니다.";
            NotifyChanged();
        }

        public void OpenImpactPreview()
        {
            if (!IsDraftValid)
            {
                HelperText = DraftValidationLabel;
                NotifyChanged();
                return;
            }

            State.SignalDraftStatus = SignalDraftStatus.Validating;
            State.SignalWorkflowPanel = SignalWorkflowPanel.ImpactPreview;
            HelperText = "fixture 기반 영향 범위와 안전 전환 조건을 표시합니다.";
            NotifyChanged();
        }

        public void BackToSignalEditor()
        {
            State.SignalDraftStatus = SignalDraftStatus.Dirty;
            State.SignalWorkflowPanel = SignalWorkflowPanel.Editor;
            HelperText = "영향 미리보기에서 신호 편집으로 돌아왔습니다.";
            NotifyChanged();
        }

        public void ScheduleSignalPlan()
        {
            State.SignalDraftStatus = SignalDraftStatus.Scheduled;
            State.ConnectionState = ConnectionState.Applying;
            State.SignalWorkflowPanel = SignalWorkflowPanel.ApplyStatus;
            HelperText = "명령이 접수됐습니다. 현재 주기 종료 후 안전 전환이 시작됩니다.";
            NotifyChanged();
        }

        public void ConfirmScheduledPlan()
        {
            State.SignalDraftStatus = SignalDraftStatus.SafeTransition;
            State.ConnectionState = ConnectionState.Connected;
            State.SignalWorkflowPanel = SignalWorkflowPanel.Closed;
            State.PrimaryMode = PrimaryMode.Building;
            State.IsFeaturePanelOpen = true;
            SelectedPrimaryValue = $"안전 전환 예약 · 초안 {DraftCycleSeconds}초";
            SelectedSecondaryValue = "활성 예정 tick 3,842 · fixture";
            HelperText = "안전 전환 예약을 확인했습니다. 같은 운영 흐름에서 건물 성장 단계로 이어집니다.";
            NotifyChanged();
        }

        public void OpenAiComparison()
        {
            State.PrimaryMode = PrimaryMode.AICompare;
            State.IsFeaturePanelOpen = true;
            HelperText = "성장 결과를 같은 조건의 Luna AI Record와 비교합니다.";
            NotifyChanged();
        }

        public void CloseSignalWorkflow()
        {
            State.SignalWorkflowPanel = SignalWorkflowPanel.Closed;
            HelperText = State.SignalDraftStatus == SignalDraftStatus.Dirty
                ? "로컬 초안은 유지됩니다. 신호 편집을 다시 열어 계속할 수 있습니다."
                : "신호 편집을 닫았습니다.";
            NotifyChanged();
        }

        public void SimulateConnectionLoss()
        {
            if (State.ConnectionRecoveryPanel != ConnectionRecoveryPanel.Closed)
            {
                return;
            }

            speedBeforeConnectionLoss = State.SimulationSpeed;
            State.SimulationSpeed = SimulationSpeed.Paused;
            State.ConnectionState = ConnectionState.Reconnecting;
            State.ConnectionRecoveryPanel = ConnectionRecoveryPanel.ConnectionLost;
            State.SignalWorkflowPanel = SignalWorkflowPanel.Closed;
            State.IsFeaturePanelOpen = false;
            ReconnectRetryCount = 0;
            HelperText = "연결 중단 fixture가 활성화됐습니다. 시뮬레이션과 편집 입력을 자동 정지했습니다.";
            NotifyChanged();
        }

        public void ShowSaveVerification()
        {
            State.ConnectionRecoveryPanel = ConnectionRecoveryPanel.SaveVerification;
            HelperText = "GameSave.json의 서명·스키마·마지막 확인 tick fixture를 표시합니다.";
            NotifyChanged();
        }

        public void BackToConnectionLost()
        {
            State.ConnectionRecoveryPanel = ConnectionRecoveryPanel.ConnectionLost;
            HelperText = "연결 중단 상태로 돌아왔습니다. 명시적 재개 전까지 입력은 잠겨 있습니다.";
            NotifyChanged();
        }

        public void RetryConnection()
        {
            ReconnectRetryCount = Clamp(ReconnectRetryCount + 1, 0, 3);
            State.ConnectionState = ConnectionState.ResumeReady;
            State.ConnectionRecoveryPanel = ConnectionRecoveryPanel.ResumeReady;
            HelperText = "서버 fixture 검증이 완료됐습니다. 사용자가 명시적으로 재개할 때까지 정지합니다.";
            NotifyChanged();
        }

        public void MarkSaveVerified()
        {
            ReconnectRetryCount = Clamp(ReconnectRetryCount + 1, 0, 3);
            State.ConnectionState = ConnectionState.ResumeReady;
            State.ConnectionRecoveryPanel = ConnectionRecoveryPanel.ResumeReady;
            HelperText = "저장 서명과 state hash가 일치합니다. 명시적 재개가 필요합니다.";
            NotifyChanged();
        }

        public void ResumeAfterRecovery()
        {
            State.ConnectionState = ConnectionState.Connected;
            State.ConnectionRecoveryPanel = ConnectionRecoveryPanel.Closed;
            State.SimulationSpeed = speedBeforeConnectionLoss;
            HelperText = $"검증된 tick에서 {ResumeSpeedLabel}했습니다. 로컬 입력 잠금을 해제합니다.";
            NotifyChanged();
        }

        public void HandleEscape()
        {
            if (State.ExperienceScreen == ExperienceScreen.FirstThreeMinutes)
            {
                ReturnToTitle();
                return;
            }
            else if (State.ExperienceScreen == ExperienceScreen.Title)
            {
                return;
            }
            else if (State.ConnectionRecoveryPanel == ConnectionRecoveryPanel.SaveVerification)
            {
                BackToConnectionLost();
                return;
            }
            else if (State.ConnectionRecoveryPanel != ConnectionRecoveryPanel.Closed)
            {
                HelperText = "연결 복구 중에는 화면을 닫을 수 없습니다. 검증 후 명시적으로 재개하세요.";
                NotifyChanged();
                return;
            }
            else if (State.IsFeaturePanelOpen)
            {
                CloseFeaturePanel();
                return;
            }
            else if (State.SignalWorkflowPanel == SignalWorkflowPanel.ImpactPreview)
            {
                BackToSignalEditor();
                return;
            }
            else if (State.SignalWorkflowPanel != SignalWorkflowPanel.Closed)
            {
                CloseSignalWorkflow();
                return;
            }
            else if (State.OverlayType != OverlayType.None)
            {
                State.OverlayType = OverlayType.None;
                HelperText = "진단 레이어를 닫았습니다. 선택과 배속은 유지됩니다.";
            }
            else if (State.PrimaryMode != PrimaryMode.Select)
            {
                State.PrimaryMode = PrimaryMode.Select;
                HelperText = "선택 모드로 돌아왔습니다.";
            }
            else if (State.SelectionKind != SelectionKind.None)
            {
                State.SelectionKind = SelectionKind.None;
                State.SelectedElementId = string.Empty;
                SelectedTitle = "선택 대상 없음";
                SelectedSubtitle = "지도에서 교차로·건물·도로를 선택하세요.";
                SelectedPrimaryValue = "—";
                SelectedSecondaryValue = "—";
            }

            NotifyChanged();
        }

        public static string GetOverlayLabel(OverlayType overlayType)
        {
            return overlayType switch
            {
                OverlayType.Traffic => "교통량",
                OverlayType.Queue => "대기열",
                OverlayType.PedestrianAbandonment => "보행 이탈",
                OverlayType.SignalPhase => "신호 현시",
                OverlayType.SafetyRisk => "안전 위험",
                OverlayType.BuildingInflow => "건물 유입",
                OverlayType.RoadUnlock => "도로 개방",
                _ => "기본 지도"
            };
        }

        private void NotifyChanged()
        {
            Changed?.Invoke();
        }

        private void ApplyIntersectionSelection(string elementId, string displayName)
        {
            State.SelectionKind = SelectionKind.Intersection;
            State.SelectedElementId = elementId;
            SelectedTitle = displayName;
            SelectedSubtitle = "교차로 · 현재 계획";
            SelectedPrimaryValue = "1단계 활성 · 주기 120초";
            SelectedSecondaryValue = "대기 12대 · 안전 98.4";
        }

        private static int Clamp(int value, int minimum, int maximum)
        {
            return value < minimum ? minimum : value > maximum ? maximum : value;
        }

        private static bool IsFeatureMode(PrimaryMode mode)
        {
            return mode == PrimaryMode.Skillbook ||
                   mode == PrimaryMode.RoadUnlock ||
                   mode == PrimaryMode.Building ||
                   mode == PrimaryMode.AICompare;
        }
    }
}
