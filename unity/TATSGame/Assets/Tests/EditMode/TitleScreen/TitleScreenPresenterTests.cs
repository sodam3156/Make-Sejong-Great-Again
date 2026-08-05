using System.Linq;
using NUnit.Framework;
using Tats.Game.UI.TitleScreen;
using UnityEditor;
using UnityEngine;
using UnityEngine.UIElements;

namespace Tats.Game.Tests.TitleScreen
{
    /// <summary>
    /// docs/23_TITLE_SCREEN_BACKLOG.md T1·T7 검증. Unity Editor가 없는 환경에서 작성했고
    /// 실제로 실행/컴파일하지 못했다 — 사람이 로컬에서 Test Runner로 돌려야 한다.
    /// EditorWindow에 root를 붙여 실제 panel을 통해 이벤트가 전달되게 한다.
    /// </summary>
    public class TitleScreenPresenterTests
    {
        const string UxmlPath = "Assets/UI/TitleScreen/TitleScreen.uxml";

        EditorWindow _window;
        VisualElement _root;
        Tats.Game.UI.TitleScreen.TitleScreenPresenter _presenter;

        [SetUp]
        public void SetUp()
        {
            var asset = AssetDatabase.LoadAssetAtPath<VisualTreeAsset>(UxmlPath);
            Assert.IsNotNull(asset, $"UXML asset not found at {UxmlPath}");

            _root = asset.CloneTree();
            _window = ScriptableObject.CreateInstance<EditorWindow>();
            _window.rootVisualElement.Add(_root);

            _presenter = new Tats.Game.UI.TitleScreen.TitleScreenPresenter(_root);
        }

        [TearDown]
        public void TearDown()
        {
            _presenter.Dispose();
            if (_window != null)
            {
                _window.Close();
                _window = null;
            }
        }

        [Test]
        public void AllFiveMenuItemsExist_InBacklogOrder()
        {
            var names = _root.Query<Button>().Build().ToList()
                .Select(b => b.name)
                .Where(n => n.EndsWith("-button") && !n.StartsWith("title-screen-quit"))
                .ToList();

            CollectionAssert.AreEqual(
                new[]
                {
                    "new-game-button",
                    "continue-button",
                    "settings-button",
                    "help-button",
                    "credits-button",
                },
                names);
        }

        [Test]
        public void Construct_FocusesFirstMenuItem()
        {
            var newGameButton = _root.Q<Button>("new-game-button");
            Assert.IsTrue(newGameButton.ClassListContains("title-screen__menu-item--focused"));
        }

        [Test]
        public void Construct_DefaultsToRetryingConnectionStatus()
        {
            var label = _root.Q<Label>("title-screen-connection-label");
            Assert.AreEqual("재시도 중", label.text);

            var newGameButton = _root.Q<Button>("new-game-button");
            var continueButton = _root.Q<Button>("continue-button");
            Assert.IsTrue(newGameButton.enabledSelf);
            Assert.IsTrue(continueButton.enabledSelf);
        }

        [Test]
        public void DownArrow_MovesFocusToNextMenuItem()
        {
            SendKey(KeyCode.DownArrow);

            var continueButton = _root.Q<Button>("continue-button");
            Assert.IsTrue(continueButton.ClassListContains("title-screen__menu-item--focused"));
        }

        [Test]
        public void UpArrow_FromFirstItem_WrapsToLastMenuItem()
        {
            SendKey(KeyCode.UpArrow);

            var creditsButton = _root.Q<Button>("credits-button");
            Assert.IsTrue(creditsButton.ClassListContains("title-screen__menu-item--focused"));
        }

        [Test]
        public void Enter_RaisesMenuItemActivatedForFocusedItem()
        {
            TitleScreenMenuItem? activated = null;
            _presenter.MenuItemActivated += item => activated = item;

            SendKey(KeyCode.Return);

            Assert.AreEqual(TitleScreenMenuItem.NewGame, activated);
        }

        [Test]
        public void Escape_DoesNotActivateAMenuItem()
        {
            // T7: Esc는 더 이상 흡수만 되지 않고 종료 확인을 연다 — 메뉴 자체를 활성화하지는 않는다.
            var activated = false;
            _presenter.MenuItemActivated += _ => activated = true;

            SendKey(KeyCode.Escape);

            Assert.IsFalse(activated);
        }

        [Test]
        public void Escape_OpensQuitConfirm_WithCancelFocusedByDefault()
        {
            SendKey(KeyCode.Escape);

            var menuPanel = _root.Q<VisualElement>("title-screen-menu-panel");
            var quitPanel = _root.Q<VisualElement>("title-screen-quit-confirm");
            var cancelButton = _root.Q<Button>("title-screen-quit-cancel-button");

            Assert.AreEqual(DisplayStyle.None, menuPanel.style.display.value);
            Assert.AreEqual(DisplayStyle.Flex, quitPanel.style.display.value);
            Assert.IsTrue(cancelButton.ClassListContains("title-screen__quit-action--focused"));
        }

        [Test]
        public void Escape_Twice_ClosesQuitConfirmAndReturnsToMenuWithoutQuitting()
        {
            var activated = false;
            _presenter.QuitConfirmed += () => activated = true;

            SendKey(KeyCode.Escape);
            SendKey(KeyCode.Escape);

            var menuPanel = _root.Q<VisualElement>("title-screen-menu-panel");
            var quitPanel = _root.Q<VisualElement>("title-screen-quit-confirm");
            var newGameButton = _root.Q<Button>("new-game-button");

            Assert.AreEqual(DisplayStyle.Flex, menuPanel.style.display.value);
            Assert.AreEqual(DisplayStyle.None, quitPanel.style.display.value);
            Assert.IsTrue(newGameButton.ClassListContains("title-screen__menu-item--focused"));
            Assert.IsFalse(activated);
        }

        [Test]
        public void QuitConfirm_EnterOnDefaultCancelFocus_DoesNotRaiseQuitConfirmed()
        {
            var activated = false;
            _presenter.QuitConfirmed += () => activated = true;

            SendKey(KeyCode.Escape);
            SendKey(KeyCode.Return);

            Assert.IsFalse(activated);
        }

        [Test]
        public void QuitConfirm_MoveFocusThenEnter_RaisesQuitConfirmed()
        {
            var activated = false;
            _presenter.QuitConfirmed += () => activated = true;

            SendKey(KeyCode.Escape);
            SendKey(KeyCode.DownArrow); // 취소 -> 종료
            SendKey(KeyCode.Return);

            Assert.IsTrue(activated);
        }

        [Test]
        public void ReportConnectionStatus_Disconnected_DisablesNewGameAndContinueOnly()
        {
            _presenter.ReportConnectionStatus(TitleConnectionStatus.Disconnected, "서버에 연결할 수 없습니다.");

            var newGameButton = _root.Q<Button>("new-game-button");
            var continueButton = _root.Q<Button>("continue-button");
            var settingsButton = _root.Q<Button>("settings-button");
            var helpButton = _root.Q<Button>("help-button");
            var creditsButton = _root.Q<Button>("credits-button");

            Assert.IsFalse(newGameButton.enabledSelf);
            Assert.IsFalse(continueButton.enabledSelf);
            Assert.IsTrue(settingsButton.enabledSelf);
            Assert.IsTrue(helpButton.enabledSelf);
            Assert.IsTrue(creditsButton.enabledSelf);

            var label = _root.Q<Label>("title-screen-connection-label");
            var reason = _root.Q<Label>("title-screen-connection-reason");
            var menuReason = _root.Q<Label>("title-screen-menu-disabled-reason");

            Assert.AreEqual("연결 끊김", label.text);
            Assert.AreEqual("서버에 연결할 수 없습니다.", reason.text);
            Assert.AreEqual(DisplayStyle.Flex, reason.style.display.value);
            Assert.AreEqual(DisplayStyle.Flex, menuReason.style.display.value);
        }

        [Test]
        public void ReportConnectionStatus_Disconnected_MovesFocusAwayFromDisabledFirstItem()
        {
            // 시작 시 포커스는 `새로 시작`(index 0). 연결이 끊기면 그 버튼이 비활성화되므로
            // 포커스는 다음으로 사용 가능한 항목(`환경설정`)으로 넘어가야 한다.
            _presenter.ReportConnectionStatus(TitleConnectionStatus.Disconnected, "타임아웃");

            var settingsButton = _root.Q<Button>("settings-button");
            var newGameButton = _root.Q<Button>("new-game-button");

            Assert.IsTrue(settingsButton.ClassListContains("title-screen__menu-item--focused"));
            Assert.IsFalse(newGameButton.ClassListContains("title-screen__menu-item--focused"));
        }

        [Test]
        public void ReportConnectionStatus_Reconnected_ReenablesButtonsAndHidesReason()
        {
            _presenter.ReportConnectionStatus(TitleConnectionStatus.Disconnected, "타임아웃");
            _presenter.ReportConnectionStatus(TitleConnectionStatus.Connected);

            var newGameButton = _root.Q<Button>("new-game-button");
            var continueButton = _root.Q<Button>("continue-button");
            var label = _root.Q<Label>("title-screen-connection-label");
            var reason = _root.Q<Label>("title-screen-connection-reason");
            var menuReason = _root.Q<Label>("title-screen-menu-disabled-reason");

            Assert.IsTrue(newGameButton.enabledSelf);
            Assert.IsTrue(continueButton.enabledSelf);
            Assert.AreEqual("연결됨", label.text);
            Assert.AreEqual(DisplayStyle.None, reason.style.display.value);
            Assert.AreEqual(DisplayStyle.None, menuReason.style.display.value);
        }

        void SendKey(KeyCode keyCode)
        {
            using var evt = KeyDownEvent.GetPooled(keyCode, EventModifiers.None);
            evt.target = _root;
            _root.SendEvent(evt);
        }
    }
}
