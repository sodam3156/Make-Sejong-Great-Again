using System;
using System.Collections.Generic;
using Newtonsoft.Json;

namespace RainFlow.Game
{
    [Serializable]
    public sealed class PolicyDesignV1
    {
        [JsonProperty("schema_version")] public string SchemaVersion = "policy-design-v1";
        [JsonProperty("trigger_occupancy_pct")] public int TriggerOccupancyPct = 80;
        [JsonProperty("metering_strength_pct")] public int MeteringStrengthPct = 60;
        [JsonProperty("diversion_strength")] public int DiversionStrength = 10;

        public PolicyDesignV1 Clone()
        {
            return new PolicyDesignV1
            {
                SchemaVersion = SchemaVersion,
                TriggerOccupancyPct = TriggerOccupancyPct,
                MeteringStrengthPct = MeteringStrengthPct,
                DiversionStrength = DiversionStrength
            };
        }
    }

    [Serializable]
    public sealed class PlayerProgressV1
    {
        [JsonProperty("attempts")] public int Attempts;
        [JsonProperty("last_score_margin")] public float? LastScoreMargin;
        [JsonProperty("last_completion_time_sec")] public float? LastCompletionTimeSec;
        [JsonProperty("building_level")] public int BuildingLevel = 1;
        [JsonProperty("equipment")] public List<string> Equipment = new List<string>();
    }

    [Serializable]
    public sealed class MissionEvaluationRequestV1
    {
        [JsonProperty("region_id")] public string RegionId;
        [JsonProperty("seed")] public int Seed = 42;
        [JsonProperty("policy_design")] public PolicyDesignV1 PolicyDesign = new PolicyDesignV1();
        [JsonProperty("progress")] public PlayerProgressV1 Progress = new PlayerProgressV1();
    }

    [Serializable]
    public sealed class GuardViolationDto
    {
        [JsonProperty("code")] public string Code;
        [JsonProperty("detail")] public string Detail;
    }

    [Serializable]
    public sealed class GuardDto
    {
        [JsonProperty("passed")] public bool Passed;
        [JsonProperty("violations")] public List<GuardViolationDto> Violations = new List<GuardViolationDto>();
        [JsonProperty("rule_version")] public string RuleVersion;
    }

    [Serializable]
    public sealed class LinkStateDto
    {
        [JsonProperty("link_id")] public string LinkId;
        [JsonProperty("occupancy_ratio")] public float OccupancyRatio;
        [JsonProperty("queue_veh")] public float QueueVehicles;
        [JsonProperty("spillback")] public bool Spillback;
    }

    [Serializable]
    public sealed class TimelineEntryDto
    {
        [JsonProperty("t_sec")] public float TimeSec;
        [JsonProperty("rain_level")] public string RainLevel;
        [JsonProperty("links")] public List<LinkStateDto> Links = new List<LinkStateDto>();
    }

    [Serializable]
    public sealed class KpiDto
    {
        [JsonProperty("spillback_time_sec")] public float SpillbackTimeSec;
        [JsonProperty("recovery_time_sec")] public float RecoveryTimeSec;
        [JsonProperty("recovery_observed")] public bool RecoveryObserved;
        [JsonProperty("total_travel_time_sec")] public float TotalTravelTimeSec;
        [JsonProperty("worst_approach_delay_sec")] public float WorstApproachDelaySec;
        [JsonProperty("completed_trips")] public int CompletedTrips;
        [JsonProperty("diverted_vehicles")] public float DivertedVehicles;
    }

    [Serializable]
    public sealed class CandidateResultDto
    {
        [JsonProperty("tier")] public string Tier;
        [JsonProperty("candidate_budget")] public int CandidateBudget;
        [JsonProperty("policy_design")] public PolicyDesignV1 PolicyDesign;
        [JsonProperty("score")] public float Score;
        [JsonProperty("kpi")] public KpiDto Kpi;
        [JsonProperty("guard")] public GuardDto Guard;
        [JsonProperty("timeline")] public List<TimelineEntryDto> Timeline = new List<TimelineEntryDto>();
    }

    [Serializable]
    public sealed class AdaptiveEventDto
    {
        [JsonProperty("mode")] public string Mode;
        [JsonProperty("title")] public string Title;
        [JsonProperty("reason")] public string Reason;
        [JsonProperty("demand_multiplier")] public float DemandMultiplier;
        [JsonProperty("effective_demand_multiplier")] public float EffectiveDemandMultiplier;
        [JsonProperty("rain_extension_sec")] public int RainExtensionSec;
        [JsonProperty("incident")] public bool Incident;
    }

    [Serializable]
    public sealed class PolicyAdviceDto
    {
        [JsonProperty("code")] public string Code;
        [JsonProperty("title")] public string Title;
        [JsonProperty("reason")] public string Reason;
        [JsonProperty("tradeoff")] public string Tradeoff;
        [JsonProperty("recommended_policy")] public PolicyDesignV1 RecommendedPolicy;
        [JsonProperty("precise")] public bool Precise;
    }

    [Serializable]
    public sealed class SatisfactionDto
    {
        [JsonProperty("traffic")] public float Traffic;
        [JsonProperty("pedestrian_proxy")] public float PedestrianProxy;
        [JsonProperty("accessibility")] public float Accessibility;
    }

    [Serializable]
    public sealed class ProgressionDto
    {
        [JsonProperty("building_level_before")] public int BuildingLevelBefore;
        [JsonProperty("building_level_after")] public int BuildingLevelAfter;
        [JsonProperty("next_demand_bonus_pct")] public int NextDemandBonusPct;
        [JsonProperty("virtual_property_value_index")] public float VirtualPropertyValueIndex;
        [JsonProperty("credits_earned")] public int CreditsEarned;
        [JsonProperty("opponent_score_margin")] public float OpponentScoreMargin;
    }

    [Serializable]
    public sealed class MissionEvaluationV1
    {
        [JsonProperty("evaluation_version")] public string EvaluationVersion;
        [JsonProperty("mission_id")] public string MissionId;
        [JsonProperty("region_id")] public string RegionId;
        [JsonProperty("result_source")] public string ResultSource;
        [JsonProperty("reality_level")] public string RealityLevel;
        [JsonProperty("adaptive_event")] public AdaptiveEventDto AdaptiveEvent;
        [JsonProperty("player")] public CandidateResultDto Player;
        [JsonProperty("opponent")] public CandidateResultDto Opponent;
        [JsonProperty("advice")] public List<PolicyAdviceDto> Advice = new List<PolicyAdviceDto>();
        [JsonProperty("success")] public bool Success;
        [JsonProperty("satisfaction")] public SatisfactionDto Satisfaction;
        [JsonProperty("progression")] public ProgressionDto Progression;
        [JsonProperty("note")] public string Note;
    }

    [Serializable]
    public sealed class RegionCatalogDto
    {
        [JsonProperty("region_id")] public string RegionId;
        [JsonProperty("label")] public string Label;
        [JsonProperty("adjacent_region_id")] public string AdjacentRegionId;
        [JsonProperty("starting_region")] public bool StartingRegion;
    }

    [Serializable]
    public sealed class MissionCatalogItemDto
    {
        [JsonProperty("mission_id")] public string MissionId;
        [JsonProperty("title")] public string Title;
        [JsonProperty("description")] public string Description;
        [JsonProperty("bot_tier")] public string BotTier;
        [JsonProperty("stage")] public int Stage;
    }

    [Serializable]
    public sealed class MissionCatalogDto
    {
        [JsonProperty("catalog_version")] public string CatalogVersion;
        [JsonProperty("reality_note")] public string RealityNote;
        [JsonProperty("regions")] public List<RegionCatalogDto> Regions = new List<RegionCatalogDto>();
        [JsonProperty("missions")] public List<MissionCatalogItemDto> Missions = new List<MissionCatalogItemDto>();
    }

    [Serializable]
    public sealed class GameFixtureDto
    {
        [JsonProperty("fixture_version")] public string FixtureVersion;
        [JsonProperty("catalog")] public MissionCatalogDto Catalog;
        [JsonProperty("evaluations")] public Dictionary<string, MissionEvaluationV1> Evaluations;
    }

    [Serializable]
    public sealed class MapPointDto
    {
        public float X;
        public float Y;

        public static MapPointDto FromArray(float[] values)
        {
            return new MapPointDto { X = values[0], Y = values[1] };
        }
    }

    [Serializable]
    public sealed class RoadDto
    {
        [JsonProperty("road_id")] public string RoadId;
        [JsonProperty("name")] public string Name;
        [JsonProperty("lanes")] public int Lanes;
        [JsonProperty("rank")] public string Rank;
        [JsonProperty("points")] public List<float[]> Points = new List<float[]>();
    }

    [Serializable]
    public sealed class MapRegionDto
    {
        [JsonProperty("region_id")] public string RegionId;
        [JsonProperty("label")] public string Label;
        [JsonProperty("position")] public float[] Position;
    }

    [Serializable]
    public sealed class GameMapDto
    {
        [JsonProperty("map_version")] public string MapVersion;
        [JsonProperty("note")] public string Note;
        [JsonProperty("regions")] public List<MapRegionDto> Regions = new List<MapRegionDto>();
        [JsonProperty("roads")] public List<RoadDto> Roads = new List<RoadDto>();
    }
}
