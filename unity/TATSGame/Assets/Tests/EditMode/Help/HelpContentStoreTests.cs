using System;
using System.IO;
using NUnit.Framework;
using Tats.Game.UI.Help;

namespace Tats.Game.Tests.Help
{
    /// <summary>
    /// docs/23_TITLE_SCREEN_BACKLOG.md T5 검증. UnityEngine·UIElements에는 의존하지 않는 순수 C#
    /// 로직(파일 읽기·JSON 파싱)만 다루지만, Unity Editor Test Runner 없이는 여전히 실행하지 못했다 —
    /// T3의 GameSaveSlotStoreTests와 같은 이유(asmdef가 Editor 플랫폼에서만 컴파일, Newtonsoft.Json
    /// 참조가 실제로 풀리는지 미검증).
    /// </summary>
    public class HelpContentStoreTests
    {
        string _filePath;

        [SetUp]
        public void SetUp()
        {
            var directory = Path.Combine(Path.GetTempPath(), "tats-help-store-tests-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(directory);
            _filePath = Path.Combine(directory, "help.json");
        }

        [TearDown]
        public void TearDown()
        {
            var directory = Path.GetDirectoryName(_filePath);
            if (directory != null && Directory.Exists(directory))
            {
                Directory.Delete(directory, true);
            }
        }

        [Test]
        public void Load_MissingFile_ReturnsError()
        {
            var store = new HelpContentStore(_filePath);
            var result = store.Load();

            Assert.AreEqual(HelpContentLoadState.Error, result.State);
            Assert.IsNull(result.Content);
        }

        [Test]
        public void Load_ValidFile_ParsesAllThreeSections()
        {
            File.WriteAllText(_filePath, ValidHelpJson());

            var store = new HelpContentStore(_filePath);
            var result = store.Load();

            Assert.AreEqual(HelpContentLoadState.Loaded, result.State);
            Assert.AreEqual(1, result.Content.SchemaVersion);
            Assert.AreEqual(1, result.Content.FirstThreeMinutes.Steps.Count);
            Assert.AreEqual("Day 1 03:00 정지 상태에서 시작한다.", result.Content.FirstThreeMinutes.Steps[0].Text);
            Assert.AreEqual(1, result.Content.Controls.Entries.Count);
            Assert.AreEqual(4, result.Content.Terms.Entries.Count);
            Assert.AreEqual("queue", result.Content.Terms.Entries[0].Id);
        }

        [Test]
        public void Load_MissingSection_ReturnsError()
        {
            File.WriteAllText(_filePath, "{\"schemaVersion\":1}");

            var store = new HelpContentStore(_filePath);
            var result = store.Load();

            Assert.AreEqual(HelpContentLoadState.Error, result.State);
        }

        [Test]
        public void Load_MalformedJson_ReturnsErrorWithoutThrowing()
        {
            File.WriteAllText(_filePath, "{not valid json");

            var store = new HelpContentStore(_filePath);
            var result = store.Load();

            Assert.AreEqual(HelpContentLoadState.Error, result.State);
            Assert.IsNotNull(result.FailureReason);
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
