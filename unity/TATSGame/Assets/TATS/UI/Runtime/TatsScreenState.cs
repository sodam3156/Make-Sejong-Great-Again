using System;

namespace Tats.Client.UI
{
    public enum ExperienceScreen
    {
        Title,
        FirstThreeMinutes,
        MainGame
    }

    public enum PrimaryMode
    {
        Select,
        Diagnose,
        SignalEdit,
        Skillbook,
        RoadUnlock,
        Building,
        AICompare
    }

    public enum SelectionKind
    {
        None,
        Intersection,
        Building,
        Road,
        DiagnosticSegment
    }

    public enum OverlayType
    {
        None,
        Traffic,
        Queue,
        PedestrianAbandonment,
        SignalPhase,
        SafetyRisk,
        BuildingInflow,
        RoadUnlock
    }

    public enum SimulationSpeed
    {
        Paused,
        X1,
        X3,
        X5
    }

    public enum ConnectionState
    {
        Connected,
        Applying,
        Reconnecting,
        ResumeReady,
        ResumeFailed
    }

    public enum SignalDraftStatus
    {
        Clean,
        Dirty,
        Validating,
        Scheduled,
        SafeTransition,
        Active,
        Rejected
    }

    public enum SignalWorkflowPanel
    {
        Closed,
        Editor,
        ImpactPreview,
        ApplyStatus
    }

    public enum SignalPhaseKind
    {
        NorthSouth,
        EastWest,
        Pedestrian
    }

    public enum ConnectionRecoveryPanel
    {
        Closed,
        ConnectionLost,
        SaveVerification,
        ResumeReady
    }

    public enum AlgorithmPreset
    {
        Balanced,
        VehicleFlow,
        PedestrianFirst
    }

    public enum AsyncState
    {
        Loading,
        Ready,
        Empty,
        Error,
        Stale
    }

    [Serializable]
    public sealed class TatsScreenState
    {
        public ExperienceScreen ExperienceScreen = ExperienceScreen.Title;
        public PrimaryMode PrimaryMode = PrimaryMode.Select;
        public SelectionKind SelectionKind = SelectionKind.None;
        public OverlayType OverlayType = OverlayType.None;
        public SimulationSpeed SimulationSpeed = SimulationSpeed.Paused;
        public ConnectionState ConnectionState = ConnectionState.Connected;
        public SignalDraftStatus SignalDraftStatus = SignalDraftStatus.Clean;
        public SignalWorkflowPanel SignalWorkflowPanel = SignalWorkflowPanel.Closed;
        public ConnectionRecoveryPanel ConnectionRecoveryPanel = ConnectionRecoveryPanel.Closed;
        public AlgorithmPreset AlgorithmPreset = AlgorithmPreset.Balanced;
        public bool IsFeaturePanelOpen;
        public AsyncState AsyncState = AsyncState.Ready;
        public string SelectedElementId = string.Empty;
    }
}
