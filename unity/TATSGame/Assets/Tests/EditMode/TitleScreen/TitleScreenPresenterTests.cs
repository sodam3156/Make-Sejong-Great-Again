using System.Linq;
using NUnit.Framework;
using Tats.Game.UI.TitleScreen;
using UnityEditor;
using UnityEngine;
using UnityEngine.UIElements;

namespace Tats.Game.Tests.TitleScreen
{
    /// <summary>
    /// docs/23_TITLE_SCREEN_BACKLOG.md T1 검증. Unity Editor가 없는 환경에서 작성했고
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
            var names = _root.Query<Button>().Build().ToList().Select(b => b.name).ToList();

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
        public void Escape_DoesNotChangeFocusedMenuItemAndDoesNotActivate()
        {
            var activated = false;
            _presenter.MenuItemActivated += _ => activated = true;

            SendKey(KeyCode.Escape);

            var newGameButton = _root.Q<Button>("new-game-button");
            Assert.IsTrue(newGameButton.ClassListContains("title-screen__menu-item--focused"));
            Assert.IsFalse(activated);
        }

        void SendKey(KeyCode keyCode)
        {
            using var evt = KeyDownEvent.GetPooled(keyCode, EventModifiers.None);
            evt.target = _root;
            _root.SendEvent(evt);
        }
    }
}
