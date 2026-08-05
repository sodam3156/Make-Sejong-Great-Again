using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UIElements;

namespace Tats.Client.UI
{
    public sealed class TatsShellPresenter : IDisposable
    {
        private readonly VisualElement root;
        private readonly TatsMockViewModel viewModel;
        private readonly Dictionary<PrimaryMode, Button> modeButtons = new Dictionary<PrimaryMode, Button>();
        private readonly Dictionary<SimulationSpeed, Button> speedButtons = new Dictionary<SimulationSpeed, Button>();
        private readonly Dictionary<OverlayType, Button> overlayButtons = new Dictionary<OverlayType, Button>();
        private readonly Dictionary<AlgorithmPreset, Button> algorithmButtons = new Dictionary<AlgorithmPreset, Button>();
        private readonly VisualElement overlayTray;
        private readonly Label cityClock;
        private readonly Label points;
        private readonly Label settlement;
        private readonly Label aiOpponent;
        private readonly Label connection;
        private readonly Label contextTitle;
        private readonly Label contextSubtitle;
        private readonly Label contextPrimary;
        private readonly Label contextSecondary;
        private readonly Label helper;
        private readonly Label mapModeBadge;
        private readonly VisualElement signalEditorOverlay;
        private readonly VisualElement impactPreviewOverlay;
        private readonly VisualElement applyStatusOverlay;
        private readonly VisualElement draftValidationBanner;
        private readonly VisualElement connectionControl;
        private readonly VisualElement connectionRecoveryOverlay;
        private readonly VisualElement connectionLostPanel;
        private readonly VisualElement saveVerificationPanel;
        private readonly VisualElement resumeReadyPanel;
        private readonly VisualElement featurePanelOverlay;
        private readonly VisualElement skillbookPanel;
        private readonly VisualElement roadPanel;
        private readonly VisualElement buildingPanel;
        private readonly VisualElement aiComparePanel;
        private readonly Label signalEditorTitle;
        private readonly Label draftCycle;
        private readonly Label northSouthDuration;
        private readonly Label eastWestDuration;
        private readonly Label pedestrianDuration;
        private readonly Label draftValidation;
        private readonly Label draftSummary;
        private readonly Label previewTitle;
        private readonly Label previewCycle;
        private readonly Label previewQueue;
        private readonly Label previewSafety;
        private readonly Label previewNeighbor;
        private readonly Label previewValidation;
        private readonly Label applyReceipt;
        private readonly Label applySummary;
        private readonly Label reconnectRetry;
        private readonly Label resumeSpeed;
        private readonly Label resumeRetry;
        private readonly Label algorithmSelected;
        private readonly Label skillbookTarget;
        private readonly Label skillbookReceipt;
        private readonly Label roadStatus;
        private readonly Label roadReceipt;
        private readonly Label buildingLevel;
        private readonly Label buildingOutput;
        private readonly Label buildingReceipt;
        private readonly Button signalPreviewButton;
        private readonly Button skillbookGenerateButton;
        private readonly Button roadPurchaseButton;
        private readonly Button buildingUpgradeButton;

        public TatsShellPresenter(VisualElement root, TatsMockViewModel viewModel)
        {
            this.root = root ?? throw new ArgumentNullException(nameof(root));
            this.viewModel = viewModel ?? throw new ArgumentNullException(nameof(viewModel));

            overlayTray = Require<VisualElement>("overlay-tray");
            cityClock = Require<Label>("city-clock");
            points = Require<Label>("points-value");
            settlement = Require<Label>("settlement-value");
            aiOpponent = Require<Label>("ai-opponent");
            connection = Require<Label>("connection-state");
            contextTitle = Require<Label>("context-title");
            contextSubtitle = Require<Label>("context-subtitle");
            contextPrimary = Require<Label>("context-primary-value");
            contextSecondary = Require<Label>("context-secondary-value");
            helper = Require<Label>("tool-help");
            mapModeBadge = Require<Label>("map-mode-badge");
            signalEditorOverlay = Require<VisualElement>("signal-editor-overlay");
            impactPreviewOverlay = Require<VisualElement>("impact-preview-overlay");
            applyStatusOverlay = Require<VisualElement>("apply-status-overlay");
            draftValidationBanner = Require<VisualElement>("draft-validation-banner");
            connectionControl = Require<VisualElement>("connection-control");
            connectionRecoveryOverlay = Require<VisualElement>("connection-recovery-overlay");
            connectionLostPanel = Require<VisualElement>("connection-lost-panel");
            saveVerificationPanel = Require<VisualElement>("save-verification-panel");
            resumeReadyPanel = Require<VisualElement>("resume-ready-panel");
            featurePanelOverlay = Require<VisualElement>("feature-panel-overlay");
            skillbookPanel = Require<VisualElement>("skillbook-panel");
            roadPanel = Require<VisualElement>("road-panel");
            buildingPanel = Require<VisualElement>("building-panel");
            aiComparePanel = Require<VisualElement>("ai-compare-panel");
            signalEditorTitle = Require<Label>("signal-editor-title");
            draftCycle = Require<Label>("draft-cycle");
            northSouthDuration = Require<Label>("phase-ns-value");
            eastWestDuration = Require<Label>("phase-ew-value");
            pedestrianDuration = Require<Label>("phase-ped-value");
            draftValidation = Require<Label>("draft-validation");
            draftSummary = Require<Label>("draft-summary-label");
            previewTitle = Require<Label>("preview-title");
            previewCycle = Require<Label>("preview-cycle");
            previewQueue = Require<Label>("preview-queue");
            previewSafety = Require<Label>("preview-safety");
            previewNeighbor = Require<Label>("preview-neighbor");
            previewValidation = Require<Label>("preview-validation");
            applyReceipt = Require<Label>("apply-receipt");
            applySummary = Require<Label>("apply-summary");
            reconnectRetry = Require<Label>("reconnect-retry");
            resumeSpeed = Require<Label>("resume-speed");
            resumeRetry = Require<Label>("resume-retry");
            algorithmSelected = Require<Label>("algorithm-selected");
            skillbookTarget = Require<Label>("skillbook-target");
            skillbookReceipt = Require<Label>("skillbook-receipt");
            roadStatus = Require<Label>("road-status");
            roadReceipt = Require<Label>("road-receipt");
            buildingLevel = Require<Label>("building-level");
            buildingOutput = Require<Label>("building-output");
            buildingReceipt = Require<Label>("building-receipt");
            signalPreviewButton = Require<Button>("signal-preview");
            skillbookGenerateButton = Require<Button>("skillbook-generate");
            roadPurchaseButton = Require<Button>("road-purchase");
            buildingUpgradeButton = Require<Button>("building-upgrade");

            BindModeButton("mode-select", PrimaryMode.Select);
            BindModeButton("mode-diagnose", PrimaryMode.Diagnose);
            BindModeButton("mode-signal-edit", PrimaryMode.SignalEdit);
            BindModeButton("mode-skillbook", PrimaryMode.Skillbook);
            BindModeButton("mode-road-unlock", PrimaryMode.RoadUnlock);
            BindModeButton("mode-building", PrimaryMode.Building);
            BindModeButton("mode-ai-compare", PrimaryMode.AICompare);

            BindSpeedButton("speed-paused", SimulationSpeed.Paused);
            BindSpeedButton("speed-x1", SimulationSpeed.X1);
            BindSpeedButton("speed-x3", SimulationSpeed.X3);
            BindSpeedButton("speed-x5", SimulationSpeed.X5);

            BindOverlayButton("overlay-traffic", OverlayType.Traffic);
            BindOverlayButton("overlay-queue", OverlayType.Queue);
            BindOverlayButton("overlay-pedestrian", OverlayType.PedestrianAbandonment);
            BindOverlayButton("overlay-signal", OverlayType.SignalPhase);
            BindOverlayButton("overlay-safety", OverlayType.SafetyRisk);
            BindOverlayButton("overlay-building", OverlayType.BuildingInflow);
            BindOverlayButton("overlay-road", OverlayType.RoadUnlock);

            BindIntersection("intersection-seonggeum", "intersection-seonggeum", "성금사거리");
            BindIntersection("intersection-cheongsa", "intersection-cheongsa", "청사교차로");
            BindIntersection("intersection-sejong", "intersection-sejong", "세종교차로");

            BindSignalPhaseButton("phase-ns-minus", SignalPhaseKind.NorthSouth, -5);
            BindSignalPhaseButton("phase-ns-plus", SignalPhaseKind.NorthSouth, 5);
            BindSignalPhaseButton("phase-ew-minus", SignalPhaseKind.EastWest, -5);
            BindSignalPhaseButton("phase-ew-plus", SignalPhaseKind.EastWest, 5);
            BindSignalPhaseButton("phase-ped-minus", SignalPhaseKind.Pedestrian, -5);
            BindSignalPhaseButton("phase-ped-plus", SignalPhaseKind.Pedestrian, 5);
            Require<Button>("signal-editor-close").clicked += viewModel.CloseSignalWorkflow;
            Require<Button>("signal-reset").clicked += viewModel.ResetSignalDraft;
            signalPreviewButton.clicked += viewModel.OpenImpactPreview;
            Require<Button>("preview-back").clicked += viewModel.BackToSignalEditor;
            Require<Button>("preview-schedule").clicked += viewModel.ScheduleSignalPlan;
            Require<Button>("apply-confirm").clicked += viewModel.ConfirmScheduledPlan;
            Require<Button>("connection-details").clicked += viewModel.ShowSaveVerification;
            Require<Button>("connection-retry").clicked += viewModel.RetryConnection;
            Require<Button>("verification-back").clicked += viewModel.BackToConnectionLost;
            Require<Button>("verification-confirm").clicked += viewModel.MarkSaveVerified;
            Require<Button>("resume-confirm").clicked += viewModel.ResumeAfterRecovery;
            connectionControl.RegisterCallback<ClickEvent>(OnConnectionControlClicked);

            BindAlgorithmButton("algorithm-balanced", AlgorithmPreset.Balanced);
            BindAlgorithmButton("algorithm-vehicle", AlgorithmPreset.VehicleFlow);
            BindAlgorithmButton("algorithm-pedestrian", AlgorithmPreset.PedestrianFirst);
            skillbookGenerateButton.clicked += viewModel.GenerateAiSignalDraft;
            roadPurchaseButton.clicked += viewModel.PurchaseRoadFixture;
            buildingUpgradeButton.clicked += viewModel.UpgradeBuildingFixture;
            Require<Button>("skillbook-close").clicked += viewModel.CloseFeaturePanel;
            Require<Button>("road-close").clicked += viewModel.CloseFeaturePanel;
            Require<Button>("building-close").clicked += viewModel.CloseFeaturePanel;
            Require<Button>("ai-compare-close").clicked += viewModel.CloseFeaturePanel;
            Require<Button>("ai-compare-confirm").clicked += viewModel.CloseFeaturePanel;

            root.focusable = true;
            root.RegisterCallback<KeyDownEvent>(OnKeyDown);
            viewModel.Changed += Render;
            Render();
            root.Focus();
        }

        public void Dispose()
        {
            viewModel.Changed -= Render;
            root.UnregisterCallback<KeyDownEvent>(OnKeyDown);
            connectionControl.UnregisterCallback<ClickEvent>(OnConnectionControlClicked);
        }

        private void BindModeButton(string name, PrimaryMode mode)
        {
            var button = Require<Button>(name);
            modeButtons.Add(mode, button);
            button.clicked += () => viewModel.SetMode(mode);
        }

        private void BindSpeedButton(string name, SimulationSpeed speed)
        {
            var button = Require<Button>(name);
            speedButtons.Add(speed, button);
            button.clicked += () => viewModel.SetSpeed(speed);
        }

        private void BindOverlayButton(string name, OverlayType overlayType)
        {
            var button = Require<Button>(name);
            overlayButtons.Add(overlayType, button);
            button.clicked += () => viewModel.ToggleOverlay(overlayType);
        }

        private void BindIntersection(string buttonName, string elementId, string displayName)
        {
            Require<Button>(buttonName).clicked += () => viewModel.SelectIntersection(elementId, displayName);
        }

        private void BindSignalPhaseButton(string buttonName, SignalPhaseKind phaseKind, int deltaSeconds)
        {
            Require<Button>(buttonName).clicked += () => viewModel.AdjustSignalPhase(phaseKind, deltaSeconds);
        }

        private void BindAlgorithmButton(string buttonName, AlgorithmPreset preset)
        {
            var button = Require<Button>(buttonName);
            algorithmButtons.Add(preset, button);
            button.clicked += () => viewModel.SelectAlgorithmPreset(preset);
        }

        private void Render()
        {
            var state = viewModel.State;
            cityClock.text = viewModel.CityClockLabel;
            points.text = viewModel.PointsLabel;
            settlement.text = viewModel.SettlementLabel;
            aiOpponent.text = viewModel.AiOpponentLabel;
            connection.text = viewModel.ConnectionLabel;
            contextTitle.text = viewModel.SelectedTitle;
            contextSubtitle.text = viewModel.SelectedSubtitle;
            contextPrimary.text = viewModel.SelectedPrimaryValue;
            contextSecondary.text = viewModel.SelectedSecondaryValue;
            helper.text = viewModel.HelperText;
            mapModeBadge.text = state.OverlayType == OverlayType.None
                ? GetModeLabel(state.PrimaryMode)
                : $"진단 · {TatsMockViewModel.GetOverlayLabel(state.OverlayType)}";

            signalEditorTitle.text = $"{viewModel.SelectedIntersectionLabel} 신호 편집";
            draftCycle.text = viewModel.DraftCycleLabel;
            northSouthDuration.text = $"{viewModel.NorthSouthGreenSeconds}초";
            eastWestDuration.text = $"{viewModel.EastWestGreenSeconds}초";
            pedestrianDuration.text = $"{viewModel.PedestrianSeconds}초";
            draftValidation.text = viewModel.DraftValidationLabel;
            draftSummary.text = viewModel.DraftPhaseSummary;
            previewTitle.text = $"{viewModel.SelectedIntersectionLabel} 영향 미리보기";
            previewCycle.text = viewModel.CycleComparisonLabel;
            previewQueue.text = viewModel.QueuePreviewLabel;
            previewSafety.text = viewModel.SafetyPreviewLabel;
            previewNeighbor.text = viewModel.NeighborPreviewLabel;
            previewValidation.text = viewModel.DraftValidationLabel;
            applyReceipt.text = viewModel.ApplyReceiptLabel;
            applySummary.text = $"{viewModel.SelectedIntersectionLabel} · 전체 주기 {viewModel.DraftCycleLabel}";
            reconnectRetry.text = viewModel.ReconnectRetryLabel;
            resumeSpeed.text = viewModel.ResumeSpeedLabel;
            resumeRetry.text = viewModel.ReconnectRetryLabel;
            algorithmSelected.text = viewModel.AlgorithmPresetLabel;
            skillbookTarget.text = viewModel.SkillbookTargetLabel;
            skillbookReceipt.text = viewModel.FeatureReceiptLabel;
            roadStatus.text = viewModel.RoadStatusLabel;
            roadReceipt.text = viewModel.FeatureReceiptLabel;
            buildingLevel.text = viewModel.BuildingLevelLabel;
            buildingOutput.text = viewModel.BuildingOutputLabel;
            buildingReceipt.text = viewModel.FeatureReceiptLabel;

            signalEditorOverlay.style.display = state.SignalWorkflowPanel == SignalWorkflowPanel.Editor
                ? DisplayStyle.Flex
                : DisplayStyle.None;
            impactPreviewOverlay.style.display = state.SignalWorkflowPanel == SignalWorkflowPanel.ImpactPreview
                ? DisplayStyle.Flex
                : DisplayStyle.None;
            applyStatusOverlay.style.display = state.SignalWorkflowPanel == SignalWorkflowPanel.ApplyStatus
                ? DisplayStyle.Flex
                : DisplayStyle.None;
            connectionRecoveryOverlay.style.display = state.ConnectionRecoveryPanel == ConnectionRecoveryPanel.Closed
                ? DisplayStyle.None
                : DisplayStyle.Flex;
            connectionLostPanel.style.display = state.ConnectionRecoveryPanel == ConnectionRecoveryPanel.ConnectionLost
                ? DisplayStyle.Flex
                : DisplayStyle.None;
            saveVerificationPanel.style.display = state.ConnectionRecoveryPanel == ConnectionRecoveryPanel.SaveVerification
                ? DisplayStyle.Flex
                : DisplayStyle.None;
            resumeReadyPanel.style.display = state.ConnectionRecoveryPanel == ConnectionRecoveryPanel.ResumeReady
                ? DisplayStyle.Flex
                : DisplayStyle.None;
            featurePanelOverlay.style.display = state.IsFeaturePanelOpen ? DisplayStyle.Flex : DisplayStyle.None;
            skillbookPanel.style.display = state.IsFeaturePanelOpen && state.PrimaryMode == PrimaryMode.Skillbook
                ? DisplayStyle.Flex
                : DisplayStyle.None;
            roadPanel.style.display = state.IsFeaturePanelOpen && state.PrimaryMode == PrimaryMode.RoadUnlock
                ? DisplayStyle.Flex
                : DisplayStyle.None;
            buildingPanel.style.display = state.IsFeaturePanelOpen && state.PrimaryMode == PrimaryMode.Building
                ? DisplayStyle.Flex
                : DisplayStyle.None;
            aiComparePanel.style.display = state.IsFeaturePanelOpen && state.PrimaryMode == PrimaryMode.AICompare
                ? DisplayStyle.Flex
                : DisplayStyle.None;
            connectionControl.EnableInClassList("is-recovering", state.ConnectionState != ConnectionState.Connected);
            draftValidationBanner.EnableInClassList("is-invalid", !viewModel.IsDraftValid);
            signalPreviewButton.SetEnabled(viewModel.IsDraftValid);
            skillbookGenerateButton.SetEnabled(state.SelectionKind == SelectionKind.Intersection);
            roadPurchaseButton.SetEnabled(!viewModel.RoadUnlocked);
            roadPurchaseButton.text = viewModel.RoadUnlocked ? "개방 완료" : "20 pt로 도로 개방";
            buildingUpgradeButton.SetEnabled(viewModel.BuildingLevel < 3);
            buildingUpgradeButton.text = viewModel.BuildingLevel < 3 ? "다음 Level 업그레이드" : "최대 Level 도달";

            overlayTray.style.display = state.PrimaryMode == PrimaryMode.Diagnose ? DisplayStyle.Flex : DisplayStyle.None;

            foreach (var pair in modeButtons)
            {
                pair.Value.EnableInClassList("is-active", pair.Key == state.PrimaryMode);
            }

            foreach (var pair in speedButtons)
            {
                pair.Value.EnableInClassList("is-active", pair.Key == state.SimulationSpeed);
            }

            foreach (var pair in overlayButtons)
            {
                pair.Value.EnableInClassList("is-active", pair.Key == state.OverlayType);
            }

            foreach (var pair in algorithmButtons)
            {
                pair.Value.EnableInClassList("is-active", pair.Key == state.AlgorithmPreset);
            }

            SetIntersectionActive("intersection-seonggeum", state.SelectedElementId == "intersection-seonggeum");
            SetIntersectionActive("intersection-cheongsa", state.SelectedElementId == "intersection-cheongsa");
            SetIntersectionActive("intersection-sejong", state.SelectedElementId == "intersection-sejong");
        }

        private void SetIntersectionActive(string name, bool active)
        {
            Require<Button>(name).EnableInClassList("is-selected", active);
        }

        private void OnKeyDown(KeyDownEvent evt)
        {
            if (evt.keyCode != KeyCode.Escape)
            {
                return;
            }

            viewModel.HandleEscape();
            evt.StopPropagation();
        }

        private void OnConnectionControlClicked(ClickEvent evt)
        {
            viewModel.SimulateConnectionLoss();
            evt.StopPropagation();
        }

        private T Require<T>(string name) where T : VisualElement
        {
            var element = root.Q<T>(name);
            if (element == null)
            {
                throw new InvalidOperationException($"Required UI element '{name}' was not found in TatsMainShell.uxml.");
            }

            return element;
        }

        private static string GetModeLabel(PrimaryMode mode)
        {
            return mode switch
            {
                PrimaryMode.Select => "선택 모드",
                PrimaryMode.Diagnose => "진단 모드",
                PrimaryMode.SignalEdit => "신호 편집",
                PrimaryMode.Skillbook => "스킬북",
                PrimaryMode.RoadUnlock => "도로 개방",
                PrimaryMode.Building => "건물 관리",
                PrimaryMode.AICompare => "AI 비교",
                _ => mode.ToString()
            };
        }
    }
}
