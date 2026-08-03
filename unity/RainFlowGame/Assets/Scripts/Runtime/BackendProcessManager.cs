using System;
using System.Collections;
using System.Diagnostics;
using System.IO;
using UnityEngine;
using UnityEngine.Networking;
using Debug = UnityEngine.Debug;

namespace RainFlow.Game
{
    public sealed class BackendProcessManager : MonoBehaviour
    {
        private static readonly int[] PackagedPorts = { 8765, 8766, 8767 };
        private Process _ownedProcess;

        public string BaseUrl { get; private set; }
        public bool IsLive { get; private set; }
        public string StatusMessage { get; private set; } = "백엔드 확인 중";

        public IEnumerator Initialize(Action<bool> completed)
        {
            // Development convenience: reuse a manually started FastAPI server.
            yield return CheckHealth("http://127.0.0.1:8000", 1.5f);
            if (IsLive)
            {
                completed(true);
                yield break;
            }

            var executable = ResolvePackagedExecutable();
            if (string.IsNullOrEmpty(executable))
            {
                StatusMessage = "백엔드 실행 파일 없음 · fixture 모드";
                completed(false);
                yield break;
            }

            foreach (var port in PackagedPorts)
            {
                StopOwnedProcess();
                try
                {
                    _ownedProcess = Process.Start(new ProcessStartInfo
                    {
                        FileName = executable,
                        Arguments = "--host 127.0.0.1 --port " + port + " --log-level warning",
                        WorkingDirectory = Path.GetDirectoryName(executable),
                        UseShellExecute = false,
                        CreateNoWindow = true,
                        WindowStyle = ProcessWindowStyle.Hidden
                    });
                }
                catch (Exception error)
                {
                    Debug.LogWarning("RainFlow backend start failed: " + error.Message);
                    continue;
                }

                yield return CheckHealth("http://127.0.0.1:" + port, 5f);
                if (IsLive)
                {
                    completed(true);
                    yield break;
                }
            }

            StopOwnedProcess();
            StatusMessage = "백엔드 연결 실패 · fixture 모드";
            completed(false);
        }

        private IEnumerator CheckHealth(string baseUrl, float timeoutSeconds)
        {
            IsLive = false;
            var deadline = Time.realtimeSinceStartup + timeoutSeconds;
            while (Time.realtimeSinceStartup < deadline)
            {
                using (var request = UnityWebRequest.Get(baseUrl + "/api/health"))
                {
                    request.timeout = 1;
                    yield return request.SendWebRequest();
                    if (request.result == UnityWebRequest.Result.Success
                        && request.downloadHandler.text.Contains("\"status\""))
                    {
                        BaseUrl = baseUrl;
                        IsLive = true;
                        StatusMessage = "로컬 시뮬레이션 연결됨";
                        yield break;
                    }
                }
                yield return new WaitForSecondsRealtime(0.2f);
            }
        }

        private static string ResolvePackagedExecutable()
        {
            var root = Directory.GetParent(Application.dataPath);
            if (root == null) return null;
            var candidates = new[]
            {
                Path.Combine(root.FullName, "Backend", "RainFlowSejong.exe"),
                Path.Combine(root.FullName, "Backend", "RainFlow.exe"),
                Path.Combine(Application.streamingAssetsPath, "Backend", "RainFlowSejong.exe"),
                Path.Combine(Application.streamingAssetsPath, "Backend", "RainFlow.exe")
            };
            foreach (var candidate in candidates)
            {
                if (File.Exists(candidate)) return candidate;
            }
            return null;
        }

        private void OnApplicationQuit()
        {
            StopOwnedProcess();
        }

        private void OnDestroy()
        {
            StopOwnedProcess();
        }

        private void StopOwnedProcess()
        {
            if (_ownedProcess == null) return;
            try
            {
                if (!_ownedProcess.HasExited)
                {
                    _ownedProcess.Kill();
                    _ownedProcess.WaitForExit(1500);
                }
            }
            catch (Exception error)
            {
                Debug.LogWarning("RainFlow backend stop failed: " + error.Message);
            }
            finally
            {
                _ownedProcess.Dispose();
                _ownedProcess = null;
            }
        }
    }
}
