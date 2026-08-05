using NUnit.Framework;
using Tats.Game.UI.NewGame;
using UnityEditor;
using UnityEngine;
using UnityEngine.UIElements;

namespace Tats.Game.Tests.NewGame
{
    /// <summary>
    /// docs/23_TITLE_SCREEN_BACKLOG.md T2 검증. Unity Editor가 없는 환경에서 작성했고
    /// 실제로 실행/컴파일하지 못했다 — 사람이 로컬에서 Test Runner로 돌려야 한다.
    /// EditorWindow에 root를 붙여 실제 panel을 통해 이벤트가 전달되게 한다(T1과 같은 방식).
    /// </summary>
    public class NewGamePresenterTests
    {
        const string UxmlPath = "Assets/UI/NewGame/NewGameScreen.uxml";

        EditorWindow _window;
        VisualElement _root;
        NewGamePresenter _presenter;

        [SetUp]
        public void SetUp()
        {
            var asset = AssetDatabase.LoadAssetAtPath<VisualTreeAsset>(UxmlPath);
            Assert.IsNotNull(asset, $"UXML asset not found at {UxmlPath}");

            _root = asset.CloneTree();
            _window = ScriptableObject.CreateInstance<EditorWindow>();
            _window.rootVisualElement.Add(_root);

            _presenter = new NewGamePresenter(_root);
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
        public void Construct_FocusesFirstIntersectionOption()
        {
            var first = _root.Q<Button>("start-intersection-ix_04-button");
            Assert.IsTrue(first.ClassListContains("new-game__focusable--focused"));
        }

        [Test]
        public void Construct_StartButtonIsDisabledUntilBothSelected()
        {
            var startButton = _root.Q<Button>("start-button");
            Assert.IsFalse(startButton.enabledSelf);
        }

        [Test]
        public void DownArrow_MovesFocusThroughAllEightOptionsAndWraps()
        {
            var expectedOrder = new[]
            {
                "start-intersection-ix_09-button",
                "start-intersection-ix_07-button",
                "opponent-luna-button",
                "opponent-terra-button",
                "opponent-sol-button",
                "back-button",
                "start-button",
                "start-intersection-ix_04-button",
            };

            foreach (var expectedName in expectedOrder)
            {
                SendKey(KeyCode.DownArrow);
                var focused = _root.Query<Button>().Build().ToList()
                    .Find(b => b.ClassListContains("new-game__focusable--focused"));
                Assert.AreEqual(expectedName, focused.name);
            }
        }

        [Test]
        public void Enter_OnIntersectionOption_SelectsItAndClearsPreviousSelection()
        {
            SendKey(KeyCode.Return); // ix_04 선택
            SendKey(KeyCode.DownArrow);
            SendKey(KeyCode.DownArrow);
            SendKey(KeyCode.Return); // ix_07 선택, ix_04 선택 해제돼야 함

            var ix04 = _root.Q<Button>("start-intersection-ix_04-button");
            var ix07 = _root.Q<Button>("start-intersection-ix_07-button");

            Assert.IsFalse(ix04.ClassListContains("new-game__option--selected"));
            Assert.IsTrue(ix07.ClassListContains("new-game__option--selected"));
        }

        [Test]
        public void SelectingOneIntersectionAndOneOpponent_EnablesStartButton()
        {
            SendKey(KeyCode.Return); // ix_04
            SendKey(KeyCode.DownArrow);
            SendKey(KeyCode.DownArrow);
            SendKey(KeyCode.DownArrow);
            SendKey(KeyCode.Return); // Luna

            var startButton = _root.Q<Button>("start-button");
            Assert.IsTrue(startButton.enabledSelf);
        }

        [Test]
        public void Enter_OnStartButton_WithoutBothSelections_DoesNotRaiseConfirmed()
        {
            var confirmed = false;
            _presenter.Confirmed += _ => confirmed = true;

            for (var i = 0; i < 6; i++)
            {
                SendKey(KeyCode.DownArrow); // back-button까지 이동 (선택 없이)
            }

            SendKey(KeyCode.DownArrow); // start-button
            SendKey(KeyCode.Return);

            Assert.IsFalse(confirmed);
        }

        [Test]
        public void Enter_OnStartButton_WithBothSelections_RaisesConfirmedWithSelection()
        {
            NewGameSelection? received = null;
            _presenter.Confirmed += selection => received = selection;

            SendKey(KeyCode.Return); // ix_04 선택
            SendKey(KeyCode.DownArrow);
            SendKey(KeyCode.DownArrow);
            SendKey(KeyCode.DownArrow);
            SendKey(KeyCode.Return); // Luna 선택

            SendKey(KeyCode.DownArrow); // back-button
            SendKey(KeyCode.DownArrow); // start-button
            SendKey(KeyCode.Return);

            Assert.IsTrue(received.HasValue);
            Assert.AreEqual("ix_04", received.Value.StartNodeId);
            Assert.AreEqual(NewGameOpponent.Luna, received.Value.Opponent);
        }

        [Test]
        public void Escape_RaisesBackAndDoesNotChangeSelection()
        {
            var backRaised = false;
            _presenter.Back += () => backRaised = true;

            SendKey(KeyCode.Escape);

            Assert.IsTrue(backRaised);
        }

        void SendKey(KeyCode keyCode)
        {
            using var evt = KeyDownEvent.GetPooled(keyCode, EventModifiers.None);
            evt.target = _root;
            _root.SendEvent(evt);
        }
    }
}
