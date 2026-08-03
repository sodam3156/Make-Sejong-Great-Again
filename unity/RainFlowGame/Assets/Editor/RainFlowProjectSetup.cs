using System.IO;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace RainFlow.Game.Editor
{
    public static class RainFlowProjectSetup
    {
        private const string ScenePath = "Assets/Scenes/Main.unity";

        [MenuItem("RainFlow/Setup Project")]
        public static void SetupProject()
        {
            EnsureScene();
            PlayerSettings.companyName = "MSGA";
            PlayerSettings.productName = "RainFlow Game";
            PlayerSettings.defaultScreenWidth = 1440;
            PlayerSettings.defaultScreenHeight = 900;
            PlayerSettings.fullScreenMode = FullScreenMode.Windowed;
            PlayerSettings.colorSpace = ColorSpace.Linear;
            PlayerSettings.SetApplicationIdentifier(
                NamedBuildTarget.Standalone,
                "com.msga.rainflowgame");
            AssetDatabase.SaveAssets();
            Debug.Log("RainFlow project setup complete: " + ScenePath);
        }

        [MenuItem("RainFlow/Build Windows x64")]
        public static void BuildWindows()
        {
            SetupProject();
            var repositoryRoot = Path.GetFullPath(
                Path.Combine(Application.dataPath, "..", "..", ".."));
            var outputDirectory = Path.Combine(repositoryRoot, "build", "unity-windows");
            Directory.CreateDirectory(outputDirectory);
            var output = Path.Combine(outputDirectory, "RainFlowGame.exe");

            var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
            {
                scenes = new[] { ScenePath },
                locationPathName = output,
                target = BuildTarget.StandaloneWindows64,
                options = BuildOptions.None
            });
            if (report.summary.result != BuildResult.Succeeded)
            {
                throw new BuildFailedException(
                    "RainFlow Windows build failed: " + report.summary.result);
            }

            var backendSource = Path.Combine(repositoryRoot, "release", "windows-x64");
            var backendTarget = Path.Combine(outputDirectory, "Backend");
            if (Directory.Exists(backendSource))
            {
                if (Directory.Exists(backendTarget)) Directory.Delete(backendTarget, true);
                CopyDirectory(backendSource, backendTarget);
            }
            else
            {
                Debug.LogWarning(
                    "Packaged backend was not found. The game build will use fixture mode: "
                    + backendSource);
            }
            Debug.Log("RainFlow Windows build complete: " + output);
        }

        private static void EnsureScene()
        {
            if (!Directory.Exists("Assets/Scenes")) Directory.CreateDirectory("Assets/Scenes");
            if (!File.Exists(ScenePath))
            {
                var scene = EditorSceneManager.NewScene(
                    NewSceneSetup.EmptyScene,
                    NewSceneMode.Single);
                SceneManager.SetActiveScene(scene);
                EditorSceneManager.SaveScene(scene, ScenePath);
            }
            EditorBuildSettings.scenes = new[]
            {
                new EditorBuildSettingsScene(ScenePath, true)
            };
        }

        private static void CopyDirectory(string source, string destination)
        {
            Directory.CreateDirectory(destination);
            foreach (var file in Directory.GetFiles(source))
            {
                File.Copy(file, Path.Combine(destination, Path.GetFileName(file)), true);
            }
            foreach (var directory in Directory.GetDirectories(source))
            {
                CopyDirectory(
                    directory,
                    Path.Combine(destination, Path.GetFileName(directory)));
            }
        }
    }
}
