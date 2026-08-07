using UnityEngine;
using UnityEngine.UIElements;

namespace Tats.Client.UI
{
    [DisallowMultipleComponent]
    [RequireComponent(typeof(UIDocument))]
    public sealed class TatsUiBootstrap : MonoBehaviour
    {
        private const string ResourcePath = "TATS/UI/TatsMainShell";
        private const string ThemeResourcePath = "TATS/UI/UnityDefaultRuntimeTheme";

        private UIDocument document;
        private PanelSettings runtimePanelSettings;
        private TatsShellPresenter presenter;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void EnsureShellExists()
        {
            if (Object.FindFirstObjectByType<TatsUiBootstrap>() != null)
            {
                return;
            }

            var shell = new GameObject("TATS UI Shell");
            shell.SetActive(false);
            Object.DontDestroyOnLoad(shell);
            shell.AddComponent<TatsUiBootstrap>();
            shell.SetActive(true);
        }

        private void Awake()
        {
            var visualTree = Resources.Load<VisualTreeAsset>(ResourcePath);
            var themeStyleSheet = Resources.Load<ThemeStyleSheet>(ThemeResourcePath);
            if (visualTree == null || themeStyleSheet == null)
            {
                Debug.LogError(
                    $"TATS UI resources are missing at Resources/{ResourcePath} or Resources/{ThemeResourcePath}.",
                    this);
                enabled = false;
                return;
            }

            runtimePanelSettings = ScriptableObject.CreateInstance<PanelSettings>();
            runtimePanelSettings.name = "TATS Runtime Panel Settings";
            runtimePanelSettings.themeStyleSheet = themeStyleSheet;
            runtimePanelSettings.scaleMode = PanelScaleMode.ScaleWithScreenSize;
            runtimePanelSettings.screenMatchMode = PanelScreenMatchMode.MatchWidthOrHeight;
            runtimePanelSettings.referenceResolution = new Vector2Int(1920, 1080);
            runtimePanelSettings.match = 0.5f;

            document = GetComponent<UIDocument>();
            document.panelSettings = runtimePanelSettings;
            document.rootVisualElement.Clear();
            visualTree.CloneTree(document.rootVisualElement);

            var app = document.rootVisualElement.Q<VisualElement>("tats-app");
            if (app == null)
            {
                Debug.LogError("TATS UI root element 'tats-app' is missing.", this);
                enabled = false;
                return;
            }

            document.rootVisualElement.style.flexGrow = 1;

            presenter = new TatsShellPresenter(document.rootVisualElement, new TatsMockViewModel());
        }

        private void OnDestroy()
        {
            presenter?.Dispose();
            if (runtimePanelSettings != null)
            {
                Destroy(runtimePanelSettings);
            }
        }
    }
}
