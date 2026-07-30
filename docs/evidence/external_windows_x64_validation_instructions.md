# External Windows x64 validation procedure (unexecuted template)

This document defines how to collect the missing two-PC, two-run evidence. It
does not claim that any external-PC run has occurred.

## Required inputs

Copy these three files to each clean Windows x64 PC:

- `RainFlowSejong-windows-x64.zip`
- `RainFlowSejong-windows-x64.zip.sha256`
- `scripts/validate_external_windows.ps1`

Before each run, disconnect Ethernet and disable Wi-Fi. The harness fails rather
than records a pass when a physical adapter is `Up` or Windows reports Internet
connectivity. It also fails if Node.js, Python, SUMO, a 32-bit host process, or a
known AI API credential environment-variable name is detected.

Run 64-bit Windows PowerShell 5.1 from a writable evidence directory. Use stable,
non-personal PC identifiers:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\validate_external_windows.ps1 `
  -ZipPath .\RainFlowSejong-windows-x64.zip `
  -PcIdentifier PC-A `
  -RunNumber 1 `
  -EvidenceRoot .\external-pc-evidence
```

Repeat with `-RunNumber 2` on the same PC, then run `1` and `2` with
`-PcIdentifier PC-B` on the second PC. The script refuses to overwrite an
existing `PC-X\run-0N` directory; do not delete or reuse a failed run as a pass.

## Automated gates and evidence

Each run independently verifies:

1. the ZIP against its sidecar SHA-256;
2. the presence of `RELEASE-METADATA.json` and every extracted file against
   the ZIP's `SHA256SUMS.txt`;
3. extraction under a fresh path containing Korean characters and spaces;
4. `start.bat`, health HTTP 200 with `status=ok`, and startup within 60 seconds;
5. a second `start.bat` reusing the same PID and port;
6. `stop.bat`, PID/port-file removal, process exit, and health unavailability;
7. Internet-off state before and after the lifecycle.

The evidence directory contains environment and adapter snapshots, artifact
hashes, lifecycle/process records, command stdout/stderr, copied application
logs, a `PASS` or `FAIL` result, and `evidence-SHA256SUMS.txt`. The machine UUID
and raw adapter MAC addresses are not stored; stable SHA-256 fingerprints are
recorded so the two distinct PCs and the two runs per PC can be aligned without
publishing the raw hardware identifiers. A Windows Store `python.exe` execution
alias is recorded but is not treated as an installed Python runtime.

Verify an evidence manifest from its run directory:

```powershell
Get-Content .\evidence-SHA256SUMS.txt | ForEach-Object {
  if ($_ -notmatch '^([0-9a-f]{64}) \*(.+)$') { throw "Invalid manifest line: $_" }
  $actual = (Get-FileHash -LiteralPath $Matches[2] -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($actual -ne $Matches[1]) { throw "Hash mismatch: $($Matches[2])" }
}
```

## Completion gate

Do not mark the external-PC requirement complete until all four run directories
exist and satisfy all of these checks:

- each `result.json` has `status: "PASS"`;
- both runs for a PC have the same machine fingerprint;
- PC-A and PC-B have different machine fingerprints;
- all four runs have the same release ZIP SHA-256;
- all four evidence manifests verify;
- any required UI walkthrough screenshots are attached separately to the
  corresponding immutable run directory.
