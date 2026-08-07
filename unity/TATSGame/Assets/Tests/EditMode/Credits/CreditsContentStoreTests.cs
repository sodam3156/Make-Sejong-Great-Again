using System;
using System.IO;
using NUnit.Framework;
using Tats.Game.UI.Credits;

namespace Tats.Game.Tests.Credits
{
    /// <summary>
    /// docs/23_TITLE_SCREEN_BACKLOG.md T6 검증. UnityEngine·UIElements에는 의존하지 않는 순수 C#
    /// 로직(파일 읽기·JSON 파싱)만 다루지만, Unity Editor Test Runner 없이는 여전히 실행하지 못했다 —
    /// T5의 HelpContentStoreTests와 같은 이유(asmdef가 Editor 플랫폼에서만 컴파일, Newtonsoft.Json
    /// 참조가 실제로 풀리는지 미검증).
    /// </summary>
    public class CreditsContentStoreTests
    {
        string _filePath;

        [SetUp]
        public void SetUp()
        {
            var directory = Path.Combine(Path.GetTempPath(), "tats-credits-store-tests-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(directory);
            _filePath = Path.Combine(directory, "credits.json");
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
            var store = new CreditsContentStore(_filePath);
            var result = store.Load();

            Assert.AreEqual(CreditsContentLoadState.Error, result.State);
            Assert.IsNull(result.Content);
        }

        [Test]
        public void Load_ValidFile_ParsesAllThreeSections()
        {
            File.WriteAllText(_filePath, ValidCreditsJson());

            var store = new CreditsContentStore(_filePath);
            var result = store.Load();

            Assert.AreEqual(CreditsContentLoadState.Loaded, result.State);
            Assert.AreEqual(1, result.Content.SchemaVersion);
            Assert.AreEqual("MSGA (Make Sejong Great Again)", result.Content.Team.Name);
            Assert.AreEqual(5, result.Content.Team.Members.Count);
            Assert.AreEqual(7, result.Content.PublicDataSources.Entries.Count);
            Assert.AreEqual(2, result.Content.OpenSourceNotices.Entries.Count);
            Assert.AreEqual("A/B Street", result.Content.OpenSourceNotices.Entries[0].Name);
        }

        [Test]
        public void Load_MissingSection_ReturnsError()
        {
            File.WriteAllText(_filePath, "{\"schemaVersion\":1}");

            var store = new CreditsContentStore(_filePath);
            var result = store.Load();

            Assert.AreEqual(CreditsContentLoadState.Error, result.State);
        }

        [Test]
        public void Load_MalformedJson_ReturnsErrorWithoutThrowing()
        {
            File.WriteAllText(_filePath, "{not valid json");

            var store = new CreditsContentStore(_filePath);
            var result = store.Load();

            Assert.AreEqual(CreditsContentLoadState.Error, result.State);
            Assert.IsNotNull(result.FailureReason);
        }

        static string ValidCreditsJson()
        {
            return "{"
                + "\"schemaVersion\":1,"
                + "\"team\":{\"title\":\"팀\",\"name\":\"MSGA (Make Sejong Great Again)\","
                + "\"members\":[\"백서준\",\"최영\",\"손시우\",\"김경은\",\"여하윤\"],\"source\":\"s\"},"
                + "\"publicDataSources\":{\"title\":\"공개 데이터 출처\",\"entries\":["
                + "{\"order\":1,\"name\":\"a\",\"url\":\"https://a\",\"note\":null},"
                + "{\"order\":2,\"name\":\"b\",\"url\":\"https://b\",\"note\":null},"
                + "{\"order\":3,\"name\":\"c\",\"url\":\"https://c\",\"note\":null},"
                + "{\"order\":4,\"name\":\"d\",\"url\":\"https://d\",\"note\":null},"
                + "{\"order\":5,\"name\":\"e\",\"url\":\"https://e\",\"note\":null},"
                + "{\"order\":6,\"name\":\"f\",\"url\":null,\"note\":\"n\"},"
                + "{\"order\":7,\"name\":\"g\",\"url\":\"https://g\",\"note\":null}"
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
