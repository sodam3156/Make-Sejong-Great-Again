using System;
using System.IO;
using NUnit.Framework;
using Tats.Game.UI.Settings;

namespace Tats.Game.Tests.Settings
{
    /// <summary>
    /// docs/23_TITLE_SCREEN_BACKLOG.md T4 검증. UnityEngine에는 의존하지 않는 순수 C#
    /// 로직(파일 읽기/쓰기·JSON 파싱)만 다루지만, T3의 GameSaveSlotStoreTests와 같은 이유로
    /// Unity Editor Test Runner 없이는 여전히 실행하지 못했다.
    /// </summary>
    public class GameSettingsStoreTests
    {
        string _directory;

        [SetUp]
        public void SetUp()
        {
            _directory = Path.Combine(Path.GetTempPath(), "tats-settings-store-tests-" + Guid.NewGuid().ToString("N"));
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
        public void Load_MissingFile_ReturnsDefaults()
        {
            var store = new GameSettingsStore(_directory);
            var result = store.Load();

            Assert.AreEqual(GameSettingsLoadState.Defaults, result.State);
            Assert.AreEqual(SettingsResolution.Res1440x900, result.Settings.Resolution);
            Assert.AreEqual(SettingsDefaultSpeed.X1, result.Settings.DefaultSpeed);
            Assert.AreEqual(100, result.Settings.MasterVolumePercent);
            Assert.AreEqual(100, result.Settings.EffectVolumePercent);
            Assert.AreEqual(SettingsLanguage.Korean, result.Settings.Language);
        }

        [Test]
        public void Save_ThenLoad_RoundTripsValues()
        {
            var store = new GameSettingsStore(_directory);
            var settings = GameSettings.Default();
            settings.Resolution = SettingsResolution.Res1280x720;
            settings.DefaultSpeed = SettingsDefaultSpeed.X3;
            settings.MasterVolumePercent = 40;
            settings.EffectVolumePercent = 60;

            store.Save(settings);
            var result = store.Load();

            Assert.AreEqual(GameSettingsLoadState.Loaded, result.State);
            Assert.AreEqual(SettingsResolution.Res1280x720, result.Settings.Resolution);
            Assert.AreEqual(SettingsDefaultSpeed.X3, result.Settings.DefaultSpeed);
            Assert.AreEqual(40, result.Settings.MasterVolumePercent);
            Assert.AreEqual(60, result.Settings.EffectVolumePercent);
        }

        [Test]
        public void Save_WritesThroughTempFile_NoLeftoverTempFile()
        {
            var store = new GameSettingsStore(_directory);
            store.Save(GameSettings.Default());

            Assert.IsFalse(File.Exists(Path.Combine(_directory, "settings.json.tmp")));
            Assert.IsTrue(File.Exists(Path.Combine(_directory, "settings.json")));
        }

        [Test]
        public void Save_Twice_KeepsExactlyOneBackupOfPreviousVersion()
        {
            var store = new GameSettingsStore(_directory);

            var first = GameSettings.Default();
            first.MasterVolumePercent = 20;
            store.Save(first);

            var second = GameSettings.Default();
            second.MasterVolumePercent = 80;
            store.Save(second);

            var backupPath = Path.Combine(_directory, "settings.json.bak");
            Assert.IsTrue(File.Exists(backupPath));

            var backupJson = File.ReadAllText(backupPath);
            StringAssert.Contains("\"masterVolumePercent\": 20", backupJson);

            var currentJson = File.ReadAllText(Path.Combine(_directory, "settings.json"));
            StringAssert.Contains("\"masterVolumePercent\": 80", currentJson);
        }

        [Test]
        public void Load_CorruptPrimaryWithValidBackup_FallsBackToBackup()
        {
            var store = new GameSettingsStore(_directory);
            var good = GameSettings.Default();
            good.MasterVolumePercent = 55;
            store.Save(good); // 1차 저장 — 아직 백업 없음(파일이 없었으므로 Move만 일어남)

            var updated = GameSettings.Default();
            updated.MasterVolumePercent = 77;
            store.Save(updated); // 2차 저장 — 이제 backup에는 masterVolumePercent=55가 남는다

            File.WriteAllText(Path.Combine(_directory, "settings.json"), "{not valid json");

            var result = store.Load();

            Assert.AreEqual(GameSettingsLoadState.LoadedFromBackup, result.State);
            Assert.AreEqual(55, result.Settings.MasterVolumePercent);
            Assert.IsNotNull(result.FailureReason);
        }

        [Test]
        public void Load_CorruptPrimaryNoBackup_ReturnsDefaults()
        {
            Directory.CreateDirectory(_directory);
            File.WriteAllText(Path.Combine(_directory, "settings.json"), "{not valid json");

            var store = new GameSettingsStore(_directory);
            var result = store.Load();

            Assert.AreEqual(GameSettingsLoadState.Defaults, result.State);
            Assert.AreEqual(SettingsResolution.Res1440x900, result.Settings.Resolution);
        }

        [Test]
        public void Load_OutOfRangeVolume_TreatedAsInvalid()
        {
            Directory.CreateDirectory(_directory);
            File.WriteAllText(
                Path.Combine(_directory, "settings.json"),
                "{\"schemaVersion\":1,\"resolution\":0,\"defaultSpeed\":0,\"masterVolumePercent\":150,\"effectVolumePercent\":50,\"language\":0}");

            var store = new GameSettingsStore(_directory);
            var result = store.Load();

            Assert.AreEqual(GameSettingsLoadState.Defaults, result.State);
        }

        [Test]
        public void Load_UnknownEnumValue_TreatedAsInvalid()
        {
            Directory.CreateDirectory(_directory);
            File.WriteAllText(
                Path.Combine(_directory, "settings.json"),
                "{\"schemaVersion\":1,\"resolution\":99,\"defaultSpeed\":0,\"masterVolumePercent\":50,\"effectVolumePercent\":50,\"language\":0}");

            var store = new GameSettingsStore(_directory);
            var result = store.Load();

            Assert.AreEqual(GameSettingsLoadState.Defaults, result.State);
        }
    }
}
