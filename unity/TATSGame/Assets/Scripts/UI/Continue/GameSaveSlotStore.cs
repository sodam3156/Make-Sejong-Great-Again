using System;
using System.Collections.Generic;
using System.IO;
using Newtonsoft.Json;

namespace Tats.Game.UI.Continue
{
    /// <summary>
    /// docs/23_TITLE_SCREEN_BACKLOG.md T3: 로컬 GameSave 슬롯 목록을 읽는다. 저장 파일 한 필드 한 필드는
    /// docs/22_TATS_BACKEND_DESIGN_V1.md 10절 GameSave 계약을 그대로 따르지만, 저장 위치(디렉터리 경로)와
    /// "슬롯 하나 = 파일 하나"라는 구성은 그 절이 정하지 않은 Unity 쪽 구현 결정이다 — 문서 어디에도
    /// 파일 이름 규칙이나 디렉터리 경로가 없다. 아직 어떤 코드도 실제로 GameSave를 쓰지 않는다
    /// (백엔드에 세션·resume API 구현이 없다, backend/README.md) — 그래서 검증할 실제 저장 파일이
    /// 저장소에 없고, 이 클래스는 아직 한 번도 진짜 파일을 읽어본 적이 없다.
    /// </summary>
    public sealed class GameSaveSlotStore
    {
        static readonly HashSet<string> KnownOpponentModels = new HashSet<string> { "Luna", "Terra", "Sol" };

        readonly string _directoryPath;

        public GameSaveSlotStore(string directoryPath)
        {
            _directoryPath = directoryPath ?? throw new ArgumentNullException(nameof(directoryPath));
        }

        public GameSaveSlotListResult LoadSlots()
        {
            if (!Directory.Exists(_directoryPath))
            {
                return GameSaveSlotListResult.Empty();
            }

            string[] files;
            try
            {
                files = Directory.GetFiles(_directoryPath, "*.json");
            }
            catch (IOException ex)
            {
                return GameSaveSlotListResult.Error(new[] { ex.Message });
            }

            if (files.Length == 0)
            {
                return GameSaveSlotListResult.Empty();
            }

            var slots = new List<GameSaveSlot>();
            var unreadable = new List<string>();

            foreach (var file in files)
            {
                if (TryParseSlot(file, out var slot, out var reason))
                {
                    slots.Add(slot);
                }
                else
                {
                    unreadable.Add($"{Path.GetFileName(file)}: {reason}");
                }
            }

            if (slots.Count == 0)
            {
                // 파일은 있는데 전부 못 읽었다 — "저장된 게임 없음"과는 다른, 진짜 오류 상태다.
                return GameSaveSlotListResult.Error(unreadable);
            }

            slots.Sort((a, b) => b.LastConfirmedTick.CompareTo(a.LastConfirmedTick));
            return GameSaveSlotListResult.Ready(slots, unreadable);
        }

        static bool TryParseSlot(string path, out GameSaveSlot slot, out string failureReason)
        {
            slot = default;
            failureReason = null;

            string json;
            try
            {
                json = File.ReadAllText(path);
            }
            catch (IOException ex)
            {
                failureReason = ex.Message;
                return false;
            }

            GameSaveDto dto;
            try
            {
                dto = JsonConvert.DeserializeObject<GameSaveDto>(json);
            }
            catch (JsonException ex)
            {
                failureReason = ex.Message;
                return false;
            }

            if (dto == null
                || string.IsNullOrEmpty(dto.StartNodeId)
                || string.IsNullOrEmpty(dto.OpponentModel)
                || dto.ResumeToken == null)
            {
                failureReason = "필수 필드 누락 (docs/22_TATS_BACKEND_DESIGN_V1.md 10절 GameSave 계약)";
                return false;
            }

            if (!KnownOpponentModels.Contains(dto.OpponentModel))
            {
                failureReason = $"알 수 없는 opponentModel '{dto.OpponentModel}'";
                return false;
            }

            slot = new GameSaveSlot(
                Path.GetFileNameWithoutExtension(path),
                dto.SchemaVersion,
                dto.StartNodeId,
                dto.OpponentModel,
                dto.LastConfirmedTick,
                dto.ResumeToken.Tick,
                json);
            return true;
        }
    }
}
