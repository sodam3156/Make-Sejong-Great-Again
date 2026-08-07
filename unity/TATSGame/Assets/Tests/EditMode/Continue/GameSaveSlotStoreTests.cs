using System;
using System.IO;
using NUnit.Framework;
using Tats.Game.UI.Continue;

namespace Tats.Game.Tests.Continue
{
    /// <summary>
    /// docs/23_TITLE_SCREEN_BACKLOG.md T3 검증. UnityEngine·UIElements에는 의존하지 않는 순수 C#
    /// 로직(파일 읽기·JSON 파싱)만 다루지만, Unity Editor Test Runner 없이는 여전히 실행하지 못했다 —
    /// Tats.Game.Tests.asmdef가 Editor 플랫폼에서만 컴파일되고, Newtonsoft.Json 참조가 실제로 풀리는지도
    /// 검증 못했다.
    /// </summary>
    public class GameSaveSlotStoreTests
    {
        string _directory;

        [SetUp]
        public void SetUp()
        {
            _directory = Path.Combine(Path.GetTempPath(), "tats-slot-store-tests-" + Guid.NewGuid().ToString("N"));
        }

        [TearDown]
        public void TearDown()
        {
            if (Directory.Exists(_directory))
            {
                Directory.Delete(_directory, true);
            }
        }

        [Test]
        public void LoadSlots_MissingDirectory_ReturnsEmpty()
        {
            var store = new GameSaveSlotStore(_directory);
            var result = store.LoadSlots();

            Assert.AreEqual(GameSaveSlotListState.Empty, result.State);
            Assert.AreEqual(0, result.Slots.Count);
        }

        [Test]
        public void LoadSlots_EmptyDirectory_ReturnsEmpty()
        {
            Directory.CreateDirectory(_directory);
            var store = new GameSaveSlotStore(_directory);
            var result = store.LoadSlots();

            Assert.AreEqual(GameSaveSlotListState.Empty, result.State);
        }

        [Test]
        public void LoadSlots_ValidFile_ParsesDocumentedFields()
        {
            Directory.CreateDirectory(_directory);
            File.WriteAllText(
                Path.Combine(_directory, "slot-a.json"),
                ValidSaveJson(startNodeId: "ix_09", opponentModel: "Terra", lastConfirmedTick: 172800, resumeTick: 172000));

            var store = new GameSaveSlotStore(_directory);
            var result = store.LoadSlots();

            Assert.AreEqual(GameSaveSlotListState.Ready, result.State);
            Assert.AreEqual(1, result.Slots.Count);

            var slot = result.Slots[0];
            Assert.AreEqual("slot-a", slot.SlotId);
            Assert.AreEqual(1, slot.SchemaVersion);
            Assert.AreEqual("ix_09", slot.StartNodeId);
            Assert.AreEqual("Terra", slot.OpponentModel);
            Assert.AreEqual(172800, slot.LastConfirmedTick);
            Assert.AreEqual(172000, slot.ResumeTokenTick);
        }

        [Test]
        public void LoadSlots_MultipleFiles_SortsByLastConfirmedTickDescending()
        {
            Directory.CreateDirectory(_directory);
            File.WriteAllText(Path.Combine(_directory, "older.json"), ValidSaveJson("ix_04", "Luna", 3600, 0));
            File.WriteAllText(Path.Combine(_directory, "newer.json"), ValidSaveJson("ix_04", "Luna", 90000, 86400));

            var store = new GameSaveSlotStore(_directory);
            var result = store.LoadSlots();

            Assert.AreEqual("newer", result.Slots[0].SlotId);
            Assert.AreEqual("older", result.Slots[1].SlotId);
        }

        [Test]
        public void LoadSlots_MissingRequiredField_MarksFileUnreadableAndKeepsOthers()
        {
            Directory.CreateDirectory(_directory);
            File.WriteAllText(Path.Combine(_directory, "broken.json"), "{\"schemaVersion\":1}");
            File.WriteAllText(Path.Combine(_directory, "ok.json"), ValidSaveJson("ix_04", "Sol", 100, 0));

            var store = new GameSaveSlotStore(_directory);
            var result = store.LoadSlots();

            Assert.AreEqual(GameSaveSlotListState.Ready, result.State);
            Assert.AreEqual(1, result.Slots.Count);
            Assert.AreEqual(1, result.UnreadableFiles.Count);
        }

        [Test]
        public void LoadSlots_UnknownOpponentModel_MarksFileUnreadable()
        {
            Directory.CreateDirectory(_directory);
            File.WriteAllText(Path.Combine(_directory, "unknown.json"), ValidSaveJson("ix_04", "Nova", 100, 0));

            var store = new GameSaveSlotStore(_directory);
            var result = store.LoadSlots();

            Assert.AreEqual(GameSaveSlotListState.Error, result.State);
            Assert.AreEqual(0, result.Slots.Count);
            Assert.AreEqual(1, result.UnreadableFiles.Count);
        }

        static string ValidSaveJson(string startNodeId, string opponentModel, long lastConfirmedTick, long resumeTick)
        {
            return "{"
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
        }
    }
}
