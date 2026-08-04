using System;
using System.Collections.Generic;
using System.IO;
using Newtonsoft.Json;
using UnityEngine;

namespace RainFlow.Game
{
    [Serializable]
    public sealed class RankingEntryV1
    {
        [JsonProperty("mission_id")] public string MissionId;
        [JsonProperty("region_id")] public string RegionId;
        [JsonProperty("actor")] public string Actor;
        [JsonProperty("score")] public float Score;
        [JsonProperty("completion_time_sec")] public float CompletionTimeSec;
        [JsonProperty("attempts")] public int Attempts;
        [JsonProperty("adaptive_mode")] public string AdaptiveMode;
        [JsonProperty("policy_design")] public PolicyDesignV1 PolicyDesign;
    }

    [Serializable]
    public sealed class GameSaveV1
    {
        [JsonProperty("save_version")] public string SaveVersion = "game-save-v1";
        [JsonProperty("selected_start_region")] public string SelectedStartRegion;
        [JsonProperty("current_stage")] public int CurrentStage;
        [JsonProperty("unlocked_regions")] public List<string> UnlockedRegions = new List<string>();
        [JsonProperty("completed_missions")] public List<string> CompletedMissions = new List<string>();
        [JsonProperty("credits")] public int Credits;
        [JsonProperty("equipment")] public List<string> Equipment = new List<string>();
        [JsonProperty("animal_skin_unlocked")] public bool AnimalSkinUnlocked;
        [JsonProperty("building_levels")] public Dictionary<string, int> BuildingLevels = new Dictionary<string, int>();
        [JsonProperty("mission_attempts")] public Dictionary<string, int> MissionAttempts = new Dictionary<string, int>();
        [JsonProperty("rankings")] public List<RankingEntryV1> Rankings = new List<RankingEntryV1>();
        [JsonProperty("last_score_margin")] public float? LastScoreMargin;
        [JsonProperty("last_completion_time_sec")] public float? LastCompletionTimeSec;
        [JsonProperty("updated_at_utc")] public string UpdatedAtUtc;

        public int GetBuildingLevel(string regionId)
        {
            int level;
            return BuildingLevels.TryGetValue(regionId, out level) ? Mathf.Clamp(level, 1, 3) : 1;
        }

        public int GetAttempts(string missionId)
        {
            int attempts;
            return MissionAttempts.TryGetValue(missionId, out attempts) ? attempts : 0;
        }
    }

    public sealed class GameSaveService
    {
        private const string FileName = "GameSaveV1.json";
        private readonly string _directory;

        public string SavePath { get { return Path.Combine(_directory, FileName); } }

        public GameSaveService(string directory = null)
        {
            _directory = string.IsNullOrWhiteSpace(directory)
                ? Application.persistentDataPath
                : directory;
        }

        public GameSaveV1 Load()
        {
            Directory.CreateDirectory(_directory);
            if (!File.Exists(SavePath))
            {
                return NewSave();
            }

            try
            {
                var json = File.ReadAllText(SavePath);
                var save = JsonConvert.DeserializeObject<GameSaveV1>(json);
                if (save == null || save.SaveVersion != "game-save-v1")
                {
                    throw new InvalidDataException("Unsupported or empty game save.");
                }
                Normalize(save);
                return save;
            }
            catch (Exception error)
            {
                var suffix = DateTime.UtcNow.ToString("yyyyMMddTHHmmssZ");
                var backup = Path.Combine(_directory, "GameSaveV1.corrupt." + suffix + ".json");
                File.Copy(SavePath, backup, true);
                Debug.LogWarning("RainFlow save was backed up and reset: " + error.Message);
                return NewSave();
            }
        }

        public void Save(GameSaveV1 save)
        {
            if (save == null) throw new ArgumentNullException("save");
            Directory.CreateDirectory(_directory);
            Normalize(save);
            save.UpdatedAtUtc = DateTime.UtcNow.ToString("O");

            var temporary = SavePath + ".tmp";
            var backup = SavePath + ".bak";
            var json = JsonConvert.SerializeObject(save, Formatting.Indented);
            File.WriteAllText(temporary, json);

            if (File.Exists(SavePath))
            {
                try
                {
                    File.Replace(temporary, SavePath, backup, true);
                }
                catch (PlatformNotSupportedException)
                {
                    File.Copy(SavePath, backup, true);
                    File.Delete(SavePath);
                    File.Move(temporary, SavePath);
                }
            }
            else
            {
                File.Move(temporary, SavePath);
            }
        }

        public GameSaveV1 Reset()
        {
            if (File.Exists(SavePath)) File.Delete(SavePath);
            var save = NewSave();
            Save(save);
            return save;
        }

        private static GameSaveV1 NewSave()
        {
            return new GameSaveV1
            {
                UpdatedAtUtc = DateTime.UtcNow.ToString("O")
            };
        }

        private static void Normalize(GameSaveV1 save)
        {
            if (save.UnlockedRegions == null) save.UnlockedRegions = new List<string>();
            if (save.CompletedMissions == null) save.CompletedMissions = new List<string>();
            if (save.Equipment == null) save.Equipment = new List<string>();
            if (save.BuildingLevels == null) save.BuildingLevels = new Dictionary<string, int>();
            if (save.MissionAttempts == null) save.MissionAttempts = new Dictionary<string, int>();
            if (save.Rankings == null) save.Rankings = new List<RankingEntryV1>();
            save.Credits = Math.Max(0, save.Credits);
            save.CurrentStage = Mathf.Clamp(save.CurrentStage, 0, 3);
            if (save.Rankings.Count > 100)
            {
                save.Rankings.RemoveRange(0, save.Rankings.Count - 100);
            }
        }
    }
}
