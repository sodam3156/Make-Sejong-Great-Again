using System;
using System.IO;
using NUnit.Framework;
using Tats.Game.UI.Continue;
using UnityEditor;
using UnityEngine;
using UnityEngine.UIElements;

namespace Tats.Game.Tests.Continue
{
    /// <summary>
    /// docs/23_TITLE_SCREEN_BACKLOG.md T3 검증. Unity Editor가 없는 환경에서 작성했고 실제로
    /// 실행/컴파일하지 못했다 — 사람이 로컬에서 Test Runner로 돌려야 한다. T1·T2와 같은 방식으로
    /// EditorWindow에 root를 붙여 실제 panel을 통해 이벤트가 전달되게 한다.
    /// </summary>
    public class ContinuePresenterTests
    {
        const string UxmlPath = "Assets/UI/Continue/ContinueScreen.uxml";

        EditorWindow _window;
        VisualElement _root;
        ContinuePresenter _presenter;
        string _slotDirectory;

        [SetUp]
        public void SetUp()
        {
            var asset = AssetDatabase.LoadAssetAtPath<VisualTreeAsset>(UxmlPath);
            Assert.IsNotNull(asset, $"UXML asset not found at {UxmlPath}");

            _root = asset.CloneTree();
            _window = ScriptableObject.CreateInstance<EditorWindow>();
            _window.rootVisualElement.Add(_root);

            _slotDirectory = Path.Combine(Path.GetTempPath(), "tats-continue-tests-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(_slotDirectory);
            WriteSlot("slot-a", startNodeId: "ix_04", opponentModel: "Luna", lastConfirmedTick: 90000, resumeTick: 86400);
            WriteSlot("slot-b", startNodeId: "ix_07", opponentModel: "Sol", lastConfirmedTick: 3600, resumeTick: 0);

            _presenter = new ContinuePresenter(_root, new GameSaveSlotStore(_slotDirectory));
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

            if (Directory.Exists(_slotDirectory))
            {
                Directory.Delete(_slotDirectory, true);
            }
        }

        void WriteSlot(string fileName, string startNodeId, string opponentModel, long lastConfirmedTick, long resumeTick)
        {
            var json = "{"
                + "\"schemaVersion\":1,"
                + $"\"startNodeId\":\"{startNodeId}\","
                + $"\"opponentModel\":\"{opponentModel}\","
                + "\"resumeToken\":{"
                + $"\"tick\":{resumeTick},"
                + "\"seed\":1,\"mapVersion\":\"v1\",\"gameRuleVersion\":\"v1\",\"contentVersion\":\"v1\",\"stateChecksum\":\"deadbeef\""
                + "},"
                + "\"commandLog\":[],"
                + $"\"lastConfirmedTick\":{lastConfirmedTick}"
                + "}";
            File.WriteAllText(Path.Combine(_slotDirectory, fileName + ".json"), json);
        }

        [Test]
        public void Construct_ListsBothSlots_MostRecentTickFirstAndFocused()
        {
            var slotA = _root.Q<Button>("continue-slot-slot-a-button"); // tick 90000, 더 최근
            var slotB = _root.Q<Button>("continue-slot-slot-b-button");

            Assert.IsNotNull(slotA);
            Assert.IsNotNull(slotB);
            Assert.IsTrue(slotA.ClassListContains("continue__focusable--focused"));
        }

        [Test]
        public void Construct_ResumeButtonDisabledUntilSlotSelected()
        {
            var resumeButton = _root.Q<Button>("continue-resume-button");
            Assert.IsFalse(resumeButton.enabledSelf);
        }

        [Test]
        public void SelectingSlot_EnablesResumeButton()
        {
            SendKey(KeyCode.Return); // slot-a 선택

            var resumeButton = _root.Q<Button>("continue-resume-button");
            Assert.IsTrue(resumeButton.enabledSelf);
        }

        [Test]
        public void Confirm_WithSelectedSlot_RaisesResumeRequestedWithThatSlot()
        {
            GameSaveSlot? received = null;
            _presenter.ResumeRequested += slot => received = slot;

            SendKey(KeyCode.Return); // slot-a 선택
            SendKey(KeyCode.DownArrow); // slot-b로 포커스만 이동 (선택 아님)
            SendKey(KeyCode.DownArrow); // back-button
            SendKey(KeyCode.DownArrow); // resume-button
            SendKey(KeyCode.Return);

            Assert.IsTrue(received.HasValue);
            Assert.AreEqual("ix_04", received.Value.StartNodeId);
        }

        [Test]
        public void ReportResumeSucceeded_ShowsReadyPanelWithConfirmFocused()
        {
            SendKey(KeyCode.Return); // slot-a 선택
            SendKey(KeyCode.DownArrow);
            SendKey(KeyCode.DownArrow);
            SendKey(KeyCode.Return); // resume-button

            _presenter.ReportResumeSucceeded();

            var readyPanel = _root.Q<VisualElement>("continue-resume-ready");
            Assert.AreEqual(DisplayStyle.Flex, readyPanel.style.display.value);

            var confirmButton = _root.Q<Button>("continue-ready-confirm-button");
            Assert.IsTrue(confirmButton.ClassListContains("continue__focusable--focused"));
        }

        [Test]
        public void ReportResumeFailed_ShowsFailedPanelWithReason()
        {
            SendKey(KeyCode.Return); // slot-a
            SendKey(KeyCode.DownArrow);
            SendKey(KeyCode.DownArrow);
            SendKey(KeyCode.Return); // resume-button

            _presenter.ReportResumeFailed("버전이 맞지 않습니다.");

            var failedPanel = _root.Q<VisualElement>("continue-resume-failed");
            Assert.AreEqual(DisplayStyle.Flex, failedPanel.style.display.value);

            var reasonLabel = _root.Q<Label>("continue-failed-reason");
            Assert.AreEqual("버전이 맞지 않습니다.", reasonLabel.text);
        }

        [Test]
        public void ResumeFailed_QuitButton_RaisesQuit()
        {
            var quitRaised = false;
            _presenter.Quit += () => quitRaised = true;

            SendKey(KeyCode.Return); // slot-a
            SendKey(KeyCode.DownArrow);
            SendKey(KeyCode.DownArrow);
            SendKey(KeyCode.Return); // resume-button
            _presenter.ReportResumeFailed("사유");

            SendKey(KeyCode.UpArrow); // 기본 포커스(재시도)에서 종료로 이동
            SendKey(KeyCode.Return);

            Assert.IsTrue(quitRaised);
        }

        [Test]
        public void ResumeFailed_RetryButton_RaisesResumeRequestedAgainForSameSlot()
        {
            GameSaveSlot? received = null;

            SendKey(KeyCode.Return); // slot-a
            SendKey(KeyCode.DownArrow);
            SendKey(KeyCode.DownArrow);
            SendKey(KeyCode.Return); // resume-button
            _presenter.ReportResumeFailed("사유");

            _presenter.ResumeRequested += slot => received = slot;
            SendKey(KeyCode.Return); // 기본 포커스(재시도)

            Assert.IsTrue(received.HasValue);
            Assert.AreEqual("ix_04", received.Value.StartNodeId);
        }

        [Test]
        public void Escape_OnSlotList_RaisesBack()
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
