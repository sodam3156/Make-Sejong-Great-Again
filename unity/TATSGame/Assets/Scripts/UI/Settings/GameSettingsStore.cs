using System;
using System.IO;
using Newtonsoft.Json;

namespace Tats.Game.UI.Settings
{
    /// <summary>
    /// docs/23_TITLE_SCREEN_BACKLOG.md T4: 로컬 파일에 원자적으로 저장한다(임시 파일 → rename)
    /// 하고 이전 정상본 1개를 남긴다. 저장 위치·파일 이름 규칙은 문서 어디에도 없는 Unity 쪽
    /// 구현 결정이다 — T3의 GameSaveSlotStore와 같은 근거(backend/README.md에 세션·설정 API
    /// 구현 자체가 없다).
    /// </summary>
    public sealed class GameSettingsStore
    {
        readonly string _directoryPath;
        readonly string _filePath;
        readonly string _backupPath;
        readonly string _tempPath;

        public GameSettingsStore(string directoryPath)
        {
            _directoryPath = directoryPath ?? throw new ArgumentNullException(nameof(directoryPath));
            _filePath = Path.Combine(_directoryPath, "settings.json");
            _backupPath = Path.Combine(_directoryPath, "settings.json.bak");
            _tempPath = Path.Combine(_directoryPath, "settings.json.tmp");
        }

        public GameSettingsLoadResult Load()
        {
            if (TryReadFile(_filePath, out var settings, out var primaryFailure))
            {
                return GameSettingsLoadResult.Loaded(settings);
            }

            if (TryReadFile(_backupPath, out var backupSettings, out var backupFailure))
            {
                return GameSettingsLoadResult.LoadedFromBackup(backupSettings, primaryFailure);
            }

            return GameSettingsLoadResult.Defaults(primaryFailure ?? backupFailure);
        }

        /// <summary>
        /// 임시 파일에 쓴 뒤 rename으로 교체한다. 기존 파일이 있으면 <see cref="File.Replace(string, string, string)"/>가
        /// 그 이전 내용을 <c>settings.json.bak</c>으로 원자적으로 옮긴다 — 백업은 항상 최근 1개만 남는다.
        /// </summary>
        public void Save(GameSettings settings)
        {
            if (settings == null)
            {
                throw new ArgumentNullException(nameof(settings));
            }

            Directory.CreateDirectory(_directoryPath);
            var json = JsonConvert.SerializeObject(settings, Formatting.Indented);
            File.WriteAllText(_tempPath, json);

            if (File.Exists(_filePath))
            {
                File.Replace(_tempPath, _filePath, _backupPath);
            }
            else
            {
                File.Move(_tempPath, _filePath);
            }
        }

        static bool TryReadFile(string path, out GameSettings settings, out string failureReason)
        {
            settings = null;
            failureReason = null;

            if (!File.Exists(path))
            {
                failureReason = "파일 없음";
                return false;
            }

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

            GameSettings parsed;
            try
            {
                parsed = JsonConvert.DeserializeObject<GameSettings>(json);
            }
            catch (JsonException ex)
            {
                failureReason = ex.Message;
                return false;
            }

            if (parsed == null)
            {
                failureReason = "빈 파일";
                return false;
            }

            if (!IsValid(parsed))
            {
                failureReason = "값 범위를 벗어난 설정 파일";
                return false;
            }

            settings = parsed;
            return true;
        }

        static bool IsValid(GameSettings settings) =>
            Enum.IsDefined(typeof(SettingsResolution), settings.Resolution)
            && Enum.IsDefined(typeof(SettingsDefaultSpeed), settings.DefaultSpeed)
            && Enum.IsDefined(typeof(SettingsLanguage), settings.Language)
            && settings.MasterVolumePercent >= 0 && settings.MasterVolumePercent <= 100
            && settings.EffectVolumePercent >= 0 && settings.EffectVolumePercent <= 100;
    }
}
