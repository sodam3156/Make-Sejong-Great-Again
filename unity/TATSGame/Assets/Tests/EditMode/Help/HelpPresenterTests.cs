using System;
using System.IO;
using NUnit.Framework;
using Tats.Game.UI.Help;
using UnityEditor;
using UnityEngine;
using UnityEngine.UIElements;

namespace Tats.Game.Tests.Help
{
    /// <summary>
    /// docs/23_TITLE_SCREEN_BACKLOG.md T5 검증. Unity Editor가 없는 환경에서 작성했고 실제로
    /// 실행/컴파일하지 못했다 — 사람이 로컬에서 Test Runner로 돌려야 한다. T1~T4와 같은 방식으로
    /// EditorWindow에 root를 붙여 실제 panel을 통해 이벤트가 전달되게 한다.
    /// </summary>
    public class HelpPresenterTests
    {
        const string UxmlPath = "Assets/UI/Help/HelpScreen.uxml";

        EditorWindow _window;
        VisualElement _root;
        HelpPresenter _presenter;
        string _filePath;

        [SetUp]
        public void SetUp()
        {
            var asset = AssetDatabase.LoadAssetAtPath<VisualTreeAsset>(UxmlPath);
            Assert.IsNotNull(asset, $"UXML asset not found at {UxmlPath}");

            _root = asset.CloneTree();
            _window = ScriptableObject.CreateInstance<EditorWindow>();
            _window.rootVisualElement.Add(_root);

            var directory = Path.Combine(Path.GetTempPath(), "tats-help-presenter-tests-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(directory);
            _filePath = Path.Combine(directory, "help.json");
            File.WriteAllText(_filePath, ValidHelpJson());

            _presenter = new HelpPresenter(_root, new HelpContentStore(_filePath));
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

            var directory = Path.GetDirectoryName(_filePath);
            if (directory != null && Directory.Exists(directory))
            {
                Directory.Delete(directory, true);
            }
        }

        [Test]
        public void Construct_ShowsFirstThreeMinutesTabActiveAndFocused()
        {
            var firstTab = _root.Q<Button>("help-tab-first3min-button");
            Assert.IsTrue(firstTab.ClassListContains("help__tab--active"));
            Assert.IsTrue(firstTab.ClassListContains("help__focusable--focused"));

            var content = _root.Q<VisualElement>("help-content");
            Assert.Greater(content.childCount, 0);
        }

        [Test]
        public void DownArrow_MovesFocusThroughFourItems_AndWraps()
        {
            for (var i = 0; i < 4; i++)
            {
                SendKey(KeyCode.DownArrow);
            }

            var firstTab = _root.Q<Button>("help-tab-first3min-button");
            Assert.IsTrue(firstTab.ClassListContains("help__focusable--focused"));
        }

        [Test]
        public void Enter_OnTermsTab_SwitchesActiveTabAndRendersFourEntries()
        {
            SendKey(KeyCode.DownArrow); // controls
            SendKey(KeyCode.DownArrow); // terms
            SendKey(KeyCode.Return);

            var termsTab = _root.Q<Button>("help-tab-terms-button");
            Assert.IsTrue(termsTab.ClassListContains("help__tab--active"));

            var content = _root.Q<VisualElement>("help-content");
            Assert.AreEqual(4, content.childCount);
        }

        [Test]
        public void Escape_RaisesBack()
        {
            var backRaised = false;
            _presenter.Back += () => backRaised = true;

            SendKey(KeyCode.Escape);

            Assert.IsTrue(backRaised);
        }

        [Test]
        public void BackButtonFocused_Enter_RaisesBack()
        {
            var backRaised = false;
            _presenter.Back += () => backRaised = true;

            SendKey(KeyCode.DownArrow); // controls
            SendKey(KeyCode.DownArrow); // terms
            SendKey(KeyCode.DownArrow); // back
            SendKey(KeyCode.Return);

            Assert.IsTrue(backRaised);
        }

        [Test]
        public void MissingHelpFile_ShowsErrorLabelInsteadOfContent()
        {
            _presenter.Dispose();
            File.Delete(_filePath);

            _presenter = new HelpPresenter(_root, new HelpContentStore(_filePath));

            var errorLabel = _root.Q<Label>("help-error-label");
            Assert.AreEqual(DisplayStyle.Flex, errorLabel.style.display.value);
            Assert.IsNotEmpty(errorLabel.text);
        }

        void SendKey(KeyCode keyCode)
        {
            using var evt = KeyDownEvent.GetPooled(keyCode, EventModifiers.None);
            evt.target = _root;
            _root.SendEvent(evt);
        }

        static string ValidHelpJson()
        {
            return "{"
                + "\"schemaVersion\":1,"
                + "\"firstThreeMinutes\":{\"title\":\"첫 3분\",\"note\":\"안내\","
                + "\"steps\":[{\"order\":1,\"text\":\"Day 1 03:00 정지 상태에서 시작한다.\"}]},"
                + "\"controls\":{\"title\":\"조작법\",\"entries\":["
                + "{\"action\":\"메뉴 이동\",\"keys\":[\"ArrowUp\",\"ArrowDown\"],\"description\":\"포커스 이동\"}]},"
                + "\"terms\":{\"title\":\"용어\",\"entries\":["
                + "{\"id\":\"queue\",\"term\":\"대기행렬\",\"definition\":\"d1\",\"source\":\"s1\"},"
                + "{\"id\":\"spillback\",\"term\":\"spillback\",\"definition\":\"d2\",\"source\":\"s2\"},"
                + "{\"id\":\"conflict\",\"term\":\"상충\",\"definition\":\"d3\",\"source\":\"s3\"},"
                + "{\"id\":\"saturation\",\"term\":\"포화도\",\"definition\":\"d4\",\"source\":\"s4\"}"
                + "]}"
                + "}";
        }
    }
}
