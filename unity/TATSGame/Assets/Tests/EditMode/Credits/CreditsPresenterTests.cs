using System;
using System.IO;
using NUnit.Framework;
using Tats.Game.UI.Credits;
using UnityEditor;
using UnityEngine;
using UnityEngine.UIElements;

namespace Tats.Game.Tests.Credits
{
    /// <summary>
    /// docs/23_TITLE_SCREEN_BACKLOG.md T6 검증. Unity Editor가 없는 환경에서 작성했고 실제로
    /// 실행/컴파일하지 못했다 — 사람이 로컬에서 Test Runner로 돌려야 한다. T1~T5와 같은 방식으로
    /// EditorWindow에 root를 붙여 실제 panel을 통해 이벤트가 전달되게 한다.
    /// </summary>
    public class CreditsPresenterTests
    {
        const string UxmlPath = "Assets/UI/Credits/CreditsScreen.uxml";

        EditorWindow _window;
        VisualElement _root;
        CreditsPresenter _presenter;
        string _filePath;

        [SetUp]
        public void SetUp()
        {
            var asset = AssetDatabase.LoadAssetAtPath<VisualTreeAsset>(UxmlPath);
            Assert.IsNotNull(asset, $"UXML asset not found at {UxmlPath}");

            _root = asset.CloneTree();
            _window = ScriptableObject.CreateInstance<EditorWindow>();
            _window.rootVisualElement.Add(_root);

            var directory = Path.Combine(Path.GetTempPath(), "tats-credits-presenter-tests-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(directory);
            _filePath = Path.Combine(directory, "credits.json");
            File.WriteAllText(_filePath, ValidCreditsJson());

            _presenter = new CreditsPresenter(_root, new CreditsContentStore(_filePath));
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
        public void Construct_ShowsTeamTabActiveAndFocused()
        {
            var teamTab = _root.Q<Button>("credits-tab-team-button");
            Assert.IsTrue(teamTab.ClassListContains("credits__tab--active"));
            Assert.IsTrue(teamTab.ClassListContains("credits__focusable--focused"));

            var content = _root.Q<VisualElement>("credits-content");
            Assert.Greater(content.childCount, 0);
        }

        [Test]
        public void DownArrow_MovesFocusThroughFourItems_AndWraps()
        {
            for (var i = 0; i < 4; i++)
            {
                SendKey(KeyCode.DownArrow);
            }

            var teamTab = _root.Q<Button>("credits-tab-team-button");
            Assert.IsTrue(teamTab.ClassListContains("credits__focusable--focused"));
        }

        [Test]
        public void Enter_OnOpenSourceTab_SwitchesActiveTabAndRendersTwoEntries()
        {
            SendKey(KeyCode.DownArrow); // public data sources
            SendKey(KeyCode.DownArrow); // open source notices
            SendKey(KeyCode.Return);

            var openSourceTab = _root.Q<Button>("credits-tab-open-source-button");
            Assert.IsTrue(openSourceTab.ClassListContains("credits__tab--active"));

            var content = _root.Q<VisualElement>("credits-content");
            Assert.AreEqual(2, content.childCount);
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

            SendKey(KeyCode.DownArrow); // public data sources
            SendKey(KeyCode.DownArrow); // open source notices
            SendKey(KeyCode.DownArrow); // back
            SendKey(KeyCode.Return);

            Assert.IsTrue(backRaised);
        }

        [Test]
        public void MissingCreditsFile_ShowsErrorLabelInsteadOfContent()
        {
            _presenter.Dispose();
            File.Delete(_filePath);

            _presenter = new CreditsPresenter(_root, new CreditsContentStore(_filePath));

            var errorLabel = _root.Q<Label>("credits-error-label");
            Assert.AreEqual(DisplayStyle.Flex, errorLabel.style.display.value);
            Assert.IsNotEmpty(errorLabel.text);
        }

        void SendKey(KeyCode keyCode)
        {
            using var evt = KeyDownEvent.GetPooled(keyCode, EventModifiers.None);
            evt.target = _root;
            _root.SendEvent(evt);
        }

        static string ValidCreditsJson()
        {
            return "{"
                + "\"schemaVersion\":1,"
                + "\"team\":{\"title\":\"팀\",\"name\":\"MSGA (Make Sejong Great Again)\","
                + "\"members\":[\"백서준\",\"최영\",\"손시우\",\"김경은\",\"여하윤\"],\"source\":\"s\"},"
                + "\"publicDataSources\":{\"title\":\"공개 데이터 출처\",\"entries\":["
                + "{\"order\":1,\"name\":\"a\",\"url\":\"https://a\",\"note\":null}"
                + "],\"source\":\"s\"},"
                + "\"openSourceNotices\":{\"title\":\"오픈소스 고지\",\"entries\":["
                + "{\"name\":\"A/B Street\",\"license\":\"Apache License 2.0\",\"licenseSpdx\":\"Apache-2.0\","
                + "\"upstreamUrl\":\"https://u\",\"forkUrl\":\"https://f\",\"pinnedCommit\":\"abc\","
                + "\"pinnedCommitUrl\":\"https://c\",\"note\":\"n\"},"
                + "{\"name\":\"OpenStreetMap data\",\"license\":\"ODbL\",\"copyrightUrl\":\"https://cr\","
                + "\"attributionGuidanceUrl\":\"https://ag\",\"note\":\"n\"}"
                + "],\"source\":\"s\"}"
                + "}";
        }
    }
}
