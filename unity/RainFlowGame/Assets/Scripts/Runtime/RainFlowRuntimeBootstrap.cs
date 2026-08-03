using UnityEngine;

namespace RainFlow.Game
{
    public static class RainFlowRuntimeBootstrap
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void StartGame()
        {
            if (Object.FindFirstObjectByType<RainFlowGameController>() != null) return;

            Application.targetFrameRate = 60;
            var root = new GameObject("RainFlow Game Root");
            Object.DontDestroyOnLoad(root);

            var map = root.AddComponent<MapWorldController>();
            var animals = root.AddComponent<AnimalPoolController>();
            animals.ConfigureRoutes(map.Routes);
            var backend = root.AddComponent<BackendProcessManager>();
            var api = root.AddComponent<RainFlowApiClient>();
            var game = root.AddComponent<RainFlowGameController>();
            game.Configure(backend, api, map, animals);
        }
    }
}
