using System;
using System.Collections;
using System.IO;
using System.Text;
using Newtonsoft.Json;
using UnityEngine;
using UnityEngine.Networking;

namespace RainFlow.Game
{
    public sealed class RainFlowApiClient : MonoBehaviour
    {
        private BackendProcessManager _backend;
        private GameFixtureDto _fixture;

        public bool IsFixtureMode { get { return _backend == null || !_backend.IsLive; } }
        public string SourceLabel { get { return IsFixtureMode ? "fixture" : "live_simulation"; } }

        public void Configure(BackendProcessManager backend)
        {
            _backend = backend;
            LoadFixture();
        }

        public IEnumerator GetCatalog(Action<MissionCatalogDto> completed)
        {
            if (!IsFixtureMode)
            {
                string body = null;
                yield return GetWithRetry(_backend.BaseUrl + "/api/missions", value => body = value);
                if (!string.IsNullOrEmpty(body))
                {
                    MissionCatalogDto catalog = null;
                    try { catalog = JsonConvert.DeserializeObject<MissionCatalogDto>(body); }
                    catch (Exception error) { Debug.LogWarning(error.Message); }
                    if (catalog != null)
                    {
                        completed(catalog);
                        yield break;
                    }
                }
            }
            completed(_fixture != null ? _fixture.Catalog : new MissionCatalogDto());
        }

        public IEnumerator Evaluate(
            string missionId,
            MissionEvaluationRequestV1 payload,
            Action<MissionEvaluationV1, string> completed)
        {
            if (!IsFixtureMode)
            {
                var json = JsonConvert.SerializeObject(payload);
                string responseBody = null;
                string responseError = null;
                yield return PostWithRetry(
                    _backend.BaseUrl + "/api/missions/" + missionId + "/evaluate",
                    json,
                    (body, error) =>
                    {
                        responseBody = body;
                        responseError = error;
                    });
                if (!string.IsNullOrEmpty(responseBody))
                {
                    try
                    {
                        completed(
                            JsonConvert.DeserializeObject<MissionEvaluationV1>(responseBody),
                            null);
                        yield break;
                    }
                    catch (Exception error)
                    {
                        responseError = "응답 해석 실패: " + error.Message;
                    }
                }
                Debug.LogWarning("Live mission evaluation failed; using fixture: " + responseError);
            }

            MissionEvaluationV1 fallback;
            if (_fixture != null
                && _fixture.Evaluations != null
                && _fixture.Evaluations.TryGetValue(missionId, out fallback))
            {
                var clone = JsonConvert.DeserializeObject<MissionEvaluationV1>(
                    JsonConvert.SerializeObject(fallback));
                clone.ResultSource = "fixture";
                clone.RegionId = payload.RegionId;
                clone.Player.PolicyDesign = payload.PolicyDesign.Clone();
                completed(clone, "백엔드가 없어 검증된 기본 fixture를 재생합니다.");
                yield break;
            }
            completed(null, "사용 가능한 live 또는 fixture 결과가 없습니다.");
        }

        private IEnumerator GetWithRetry(string url, Action<string> completed)
        {
            for (var attempt = 0; attempt < 2; attempt++)
            {
                using (var request = UnityWebRequest.Get(url))
                {
                    request.timeout = 5;
                    yield return request.SendWebRequest();
                    if (request.result == UnityWebRequest.Result.Success)
                    {
                        completed(request.downloadHandler.text);
                        yield break;
                    }
                }
            }
            completed(null);
        }

        private IEnumerator PostWithRetry(
            string url,
            string json,
            Action<string, string> completed)
        {
            string lastError = null;
            for (var attempt = 0; attempt < 2; attempt++)
            {
                using (var request = new UnityWebRequest(url, "POST"))
                {
                    request.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(json));
                    request.downloadHandler = new DownloadHandlerBuffer();
                    request.SetRequestHeader("Content-Type", "application/json");
                    request.timeout = 8;
                    yield return request.SendWebRequest();
                    if (request.result == UnityWebRequest.Result.Success)
                    {
                        completed(request.downloadHandler.text, null);
                        yield break;
                    }
                    lastError = request.responseCode + " " + request.error + " "
                                + request.downloadHandler.text;
                }
            }
            completed(null, lastError);
        }

        private void LoadFixture()
        {
            try
            {
                var path = Path.Combine(
                    Application.streamingAssetsPath,
                    "fixture",
                    "game_missions.json");
                _fixture = JsonConvert.DeserializeObject<GameFixtureDto>(
                    File.ReadAllText(path));
            }
            catch (Exception error)
            {
                Debug.LogError("RainFlow fixture could not be loaded: " + error.Message);
                _fixture = null;
            }
        }
    }
}
