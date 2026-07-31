RainFlow Sejong - Windows x64 launcher
========================================

1. Extract the complete ZIP to any writable folder.
   Korean characters and spaces in the folder name are supported.
2. Double-click start.bat.
3. Wait for the browser to open (normally well under 60 seconds).

No Internet connection, API key, Node.js, Python, or SUMO installation is
required. Running start.bat again reopens the already-running local server.
If the previous process ended, the launcher automatically chooses a new free
localhost port.

RELEASE-METADATA.json records the exact source commit and release tag used for
this ZIP. SHA256SUMS.txt covers that metadata, the executable, and every
launcher file. Keep both files with the ZIP checksum when archiving evidence.

The app listens only on 127.0.0.1. Startup output is saved under logs\ and
the selected port/PID are saved under runtime\.
Simulation and approval audit records are stored under
_internal\backend\logs\.

Double-click stop.bat to stop the server before removing the folder. It only
stops the recorded PID when its executable path matches RainFlowSejong.exe in
this extracted folder.

If startup fails, keep the logs folder when reporting the problem.
