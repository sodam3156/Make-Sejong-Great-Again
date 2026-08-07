using System;
using System.IO;
using NUnit.Framework;
using Tats.Game.UI.Settings;
using UnityEditor;
using UnityEngine;
using UnityEngine.UIElements;

namespace Tats.Game.Tests.Settings
{
    /// <summary>
    /// docs/23_TITLE_SCREEN_BACKLOG.md T4 검증. Unity Editor가 없는 환경에서 작성했고 실제로
    /// 실행/컴파일하지 못했다 — 사람이 로컬에서 Test Runner로 돌려야 한다. T1~T3와 같은 방식으로
    /// EditorWindow에 root를 붙여 실제 panel을 통해 이벤트가 전달되게 한다.
    /// </summary>
    public class SettingsPresenterTests
    {
        const string UxmlPath = "Assets/UI/Settings/SettingsScreen.uxml";

        EditorWindow _window;
        VisualElement _root;
        SettingsPresenter _presenter;
        string _directory;

        [SetUp]
        public void SetUp()
        {
            var asset = AssetDatabase.LoadAssetAtPath<VisualTreeAsset>(UxmlPath);
            Assert.IsNotNull(asset, $"UXML asset not found at {UxmlPath}");

            _root = asset.CloneTree();
            _window = ScriptableObject.CreateInstance<EditorWindow>();
            _window.rootVisualElement.Add(_root);

            _directory = Path.Combine(Path.GetTempPath(), "tats-settings-presenter-tests-" + Guid.NewGuid().ToString("N"));
            _presenter = new SettingsPresenter(_root, new GameSettingsStore(_directory));
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

            if (Directory.Exists(_directory))
            {
                Directory.Delete(_directory, true);
            }
        }

        [Test]
        public void Construct_ShowsDefaultsAndFocusesResolutionRow()
        {
            var resolutionButton = _root.Q<Button>("settings-resolution-value");
            Assert.AreEqual("1440×900", resolutionButton.text);
            Assert.IsTrue(resolutionButton.ClassListContains("settings__focusable--focused"));

            var speedButton = _root.Q<Button>("settings-speed-value");
            Assert.AreEqual("×1", speedButton.text);

            var masterVolumeButton = _root.Q<Button>("settings-master-volume-value");
            Assert.AreEqual("100%", masterVolumeButton.text);

            var languageButton = _root.Q<Button>("settings-language-value");
            Assert.AreEqual("한국어", languageButton.text);
        }

        [Test]
        public void RightArrow_OnResolutionRow_CyclesToNextResolution()
        {
            SendKey(KeyCode.RightArrow);

            var resolutionButton = _root.Q<Button>("settings-resolution-value");
            Assert.AreEqual("1280×720", resolutionButton.text);
        }

        [Test]
        public void RightArrow_OnResolutionRow_WrapsAroundBackToFirst()
        {
            SendKey(KeyCode.RightArrow);
            SendKey(KeyCode.RightArrow);

            var resolutionButton = _root.Q<Button>("settings-resolution-value");
            Assert.AreEqual("1440×900", resolutionButton.text);
        }

        [Test]
        public void RightArrow_OnMasterVolumeRow_IncreasesByTenAndClampsAtHundred()
        {
            SendKey(KeyCode.DownArrow); // speed
            SendKey(KeyCode.DownArrow); // master volume
            for (var i = 0; i < 5; i++)
            {
                SendKey(KeyCode.RightArrow);
            }

            var masterVolumeButton = _root.Q<Button>("settings-master-volume-value");
            Assert.AreEqual("100%", masterVolumeButton.text); // 이미 100%에서 시작 — 클램프 확인
        }

        [Test]
        public void LeftArrow_OnMasterVolumeRow_DecreasesByTenAndClampsAtZero()
        {
            SendKey(KeyCode.DownArrow); // speed
            SendKey(KeyCode.DownArrow); // master volume
            for (var i = 0; i < 11; i++)
            {
                SendKey(KeyCode.LeftArrow);
            }

            var masterVolumeButton = _root.Q<Button>("settings-master-volume-value");
            Assert.AreEqual("0%", masterVolumeButton.text);
        }

        [Test]
        public void DownArrow_MovesFocusThroughAllSevenRows_AndWraps()
        {
            for (var i = 0; i < 7; i++)
            {
                SendKey(KeyCode.DownArrow);
            }

            var resolutionButton = _root.Q<Button>("settings-resolution-value");
            Assert.IsTrue(resolutionButton.ClassListContains("settings__focusable--focused"));
        }

        [Test]
        public void Save_WritesFileAndRaisesSavedWithWorkingValues()
        {
            GameSettings saved = null;
            _presenter.Saved += settings => saved = settings;

            SendKey(KeyCode.RightArrow); // resolution -> 1280x720

            for (var i = 0; i < 6; i++)
            {
                SendKey(KeyCode.DownArrow); // save 버튼으로 이동
            }

            SendKey(KeyCode.Return);

            Assert.IsNotNull(saved);
            Assert.AreEqual(SettingsResolution.Res1280x720, saved.Resolution);
            Assert.IsTrue(File.Exists(Path.Combine(_directory, "settings.json")));

            var savedLabel = _root.Q<Label>("settings-saved-label");
            Assert.AreEqual("저장했습니다.", savedLabel.text);
        }

        [Test]
        public void Escape_RaisesBackWithoutWritingFile()
        {
            var backRaised = false;
            _presenter.Back += () => backRaised = true;

            SendKey(KeyCode.RightArrow); // 값을 바꿨지만 저장하지 않음
            SendKey(KeyCode.Escape);

            Assert.IsTrue(backRaised);
            Assert.IsFalse(File.Exists(Path.Combine(_directory, "settings.json")));
        }

        void SendKey(KeyCode keyCode)
        {
            using var evt = KeyDownEvent.GetPooled(keyCode, EventModifiers.None);
            evt.target = _root;
            _root.SendEvent(evt);
        }
    }
}
