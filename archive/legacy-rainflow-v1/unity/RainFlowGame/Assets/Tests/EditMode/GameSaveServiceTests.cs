using System;
using System.IO;
using Newtonsoft.Json;
using NUnit.Framework;
using UnityEngine;

namespace RainFlow.Game.Tests
{
    public sealed class GameSaveServiceTests
    {
        private string _directory;

        [SetUp]
        public void SetUp()
        {
            _directory = Path.Combine(
                Path.GetTempPath(),
                "RainFlowGameTests",
                Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(_directory);
        }

        [TearDown]
        public void TearDown()
        {
            if (Directory.Exists(_directory)) Directory.Delete(_directory, true);
        }

        [Test]
        public void SaveRoundTripPreservesProgressAndRanking()
        {
            var service = new GameSaveService(_directory);
            var save = new GameSaveV1
            {
                SelectedStartRegion = "seonggeum_cheongsa",
                CurrentStage = 2,
                Credits = 120
            };
            save.Equipment.Add("smart_controller");
            save.BuildingLevels["seonggeum_cheongsa"] = 2;
            save.Rankings.Add(new RankingEntryV1 { Actor = "PLAYER", Score = 65.2f });
            service.Save(save);

            var loaded = service.Load();

            Assert.That(loaded.SelectedStartRegion, Is.EqualTo("seonggeum_cheongsa"));
            Assert.That(loaded.CurrentStage, Is.EqualTo(2));
            Assert.That(loaded.Credits, Is.EqualTo(120));
            Assert.That(loaded.GetBuildingLevel("seonggeum_cheongsa"), Is.EqualTo(2));
            Assert.That(loaded.Rankings, Has.Count.EqualTo(1));
        }

        [Test]
        public void CorruptSaveIsBackedUpAndReset()
        {
            var service = new GameSaveService(_directory);
            File.WriteAllText(service.SavePath, "{not-json");

            var loaded = service.Load();

            Assert.That(loaded.SaveVersion, Is.EqualTo("game-save-v1"));
            Assert.That(Directory.GetFiles(_directory, "*.corrupt.*.json"), Has.Length.EqualTo(1));
        }

        [Test]
        public void PolicyContractUsesSnakeCaseJson()
        {
            var json = JsonConvert.SerializeObject(new PolicyDesignV1
            {
                TriggerOccupancyPct = 65,
                MeteringStrengthPct = 90,
                DiversionStrength = 10
            });

            StringAssert.Contains("\"trigger_occupancy_pct\":65", json);
            StringAssert.Contains("\"metering_strength_pct\":90", json);
            StringAssert.Contains("\"diversion_strength\":10", json);
        }

        [Test]
        public void BundledFixtureContainsTheFullThreeMissionLoop()
        {
            var path = Path.Combine(
                Application.dataPath,
                "StreamingAssets",
                "fixture",
                "game_missions.json");
            var fixture = JsonConvert.DeserializeObject<GameFixtureDto>(File.ReadAllText(path));

            Assert.That(fixture.Catalog.Missions, Has.Count.EqualTo(3));
            Assert.That(fixture.Evaluations.ContainsKey("rain_commute"), Is.True);
            Assert.That(fixture.Evaluations.ContainsKey("rain_incident"), Is.True);
            Assert.That(fixture.Evaluations.ContainsKey("corridor_final"), Is.True);
        }
    }
}
