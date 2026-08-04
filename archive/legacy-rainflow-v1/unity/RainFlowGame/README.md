# RainFlow Game — Unity vertical slice

Unity 6.3 LTS Windows x64 project for the deterministic RainFlow game loop.

## Open and run

1. Open this directory from Unity Hub with Unity 6.3 LTS and Windows Build Support.
2. Wait for packages to resolve.
3. Run **RainFlow > Setup Project** once. It creates the empty bootstrap scene and build settings.
4. Start the FastAPI backend with `python -m launcher.run_rainflow --port 8000` for live evaluation, or press Play without it to use the bundled fixture.
5. Press Play in the `Assets/Scenes/Main.unity` scene.

The runtime bootstrap creates the map, camera, game UI, local save service, API client, and animal pools. No cloud service or API key is required.

## Windows build

1. Build the backend release into `release/windows-x64`.
2. Use **RainFlow > Build Windows x64**.
3. The build script writes `build/unity-windows/RainFlowGame.exe` and copies the backend beside it when available.

All displayed traffic and property values are synthetic game estimates. They are not real property-price or policy-effect forecasts.
