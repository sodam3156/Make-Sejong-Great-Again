[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$ZipPath,

    [Parameter(Mandatory = $true)]
    [ValidatePattern("^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")]
    [string]$PcIdentifier,

    [Parameter(Mandatory = $true)]
    [ValidateRange(1, 2)]
    [int]$RunNumber,

    [string]$ChecksumPath,

    [ValidatePattern("^[0-9A-Fa-f]{64}$")]
    [string]$ExpectedSha256,

    [string]$EvidenceRoot,

    [ValidateRange(60, 120)]
    [int]$LauncherTimeoutSeconds = 70
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ($env:OS -ne "Windows_NT") {
    throw "External-PC validation must run on Windows."
}
if (-not [Environment]::Is64BitOperatingSystem) {
    throw "External-PC validation requires Windows x64."
}

$ResolvedZipPath = (Resolve-Path -LiteralPath $ZipPath).Path
if ([string]::IsNullOrWhiteSpace($EvidenceRoot)) {
    $EvidenceRoot = Join-Path (Get-Location).Path "external-pc-evidence"
}
elseif (-not [System.IO.Path]::IsPathRooted($EvidenceRoot)) {
    $EvidenceRoot = Join-Path (Get-Location).Path $EvidenceRoot
}
$EvidenceRoot = [System.IO.Path]::GetFullPath($EvidenceRoot)
$PcEvidenceDirectory = Join-Path $EvidenceRoot $PcIdentifier
$RunDirectory = Join-Path $PcEvidenceDirectory ("run-{0:D2}" -f $RunNumber)

if (Test-Path -LiteralPath $RunDirectory) {
    throw (
        "Evidence already exists for $PcIdentifier run $RunNumber. " +
        "The harness refuses to overwrite an external-PC run: $RunDirectory"
    )
}

New-Item -ItemType Directory -Path $PcEvidenceDirectory -Force | Out-Null
New-Item -ItemType Directory -Path $RunDirectory | Out-Null
$CommandLogDirectory = Join-Path $RunDirectory "commands"
New-Item -ItemType Directory -Path $CommandLogDirectory | Out-Null

$CommandProcessor = Join-Path $env:SystemRoot "System32\cmd.exe"
$StartedAt = (Get-Date).ToUniversalTime()
$CompletedAt = $null
$Failure = $null
$ValidationStatus = "FAIL"
$Lifecycle = [ordered]@{}
$Artifact = [ordered]@{}
$EnvironmentEvidence = [ordered]@{}
$CleanupEvidence = [ordered]@{}
$ServerProcessIdForCleanup = $null
$ExtractedExecutable = $null
$ExtractRoot = $null
$WorkingParent = $null
$PreviousNoBrowser = [Environment]::GetEnvironmentVariable(
    "RAINFLOW_NO_BROWSER",
    [EnvironmentVariableTarget]::Process
)
$PreviousNonInteractive = [Environment]::GetEnvironmentVariable(
    "RAINFLOW_NONINTERACTIVE",
    [EnvironmentVariableTarget]::Process
)

function Write-JsonFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        $Value
    )

    $Json = $Value | ConvertTo-Json -Depth 12
    [System.IO.File]::WriteAllText(
        $Path,
        $Json + "`n",
        [System.Text.UTF8Encoding]::new($false)
    )
}

function Write-HarnessLog {
    param([Parameter(Mandatory = $true)][string]$Message)

    $Line = "{0} {1}" -f (
        (Get-Date).ToUniversalTime().ToString("o")
    ), $Message
    [System.IO.File]::AppendAllText(
        (Join-Path $RunDirectory "harness.log"),
        $Line + "`n",
        [System.Text.UTF8Encoding]::new($false)
    )
    Write-Host $Message
}

function Get-Sha256Text {
    param([Parameter(Mandatory = $true)][string]$Text)

    $Sha256 = [System.Security.Cryptography.SHA256]::Create()
    try {
        $Bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
        return (
            [System.BitConverter]::ToString(
                $Sha256.ComputeHash($Bytes)
            ).Replace("-", "").ToLowerInvariant()
        )
    }
    finally {
        $Sha256.Dispose()
    }
}

function Get-NetworkSnapshot {
    $Adapters = @(
        Get-NetAdapter -IncludeHidden -ErrorAction Stop |
            Sort-Object ifIndex |
            ForEach-Object {
                [ordered]@{
                    name = [string]$_.Name
                    description = [string]$_.InterfaceDescription
                    interface_index = [int]$_.ifIndex
                    status = [string]$_.Status
                    link_speed = [string]$_.LinkSpeed
                    mac_address_sha256 = if (
                        [string]::IsNullOrWhiteSpace([string]$_.MacAddress)
                    ) {
                        $null
                    }
                    else {
                        Get-Sha256Text -Text ([string]$_.MacAddress)
                    }
                    physical = [bool]$_.PhysicalMediaType
                }
            }
    )
    $PhysicalAdapters = @(
        Get-NetAdapter -Physical -ErrorAction Stop |
            Sort-Object ifIndex |
            ForEach-Object {
                [ordered]@{
                    name = [string]$_.Name
                    description = [string]$_.InterfaceDescription
                    interface_index = [int]$_.ifIndex
                    status = [string]$_.Status
                    link_speed = [string]$_.LinkSpeed
                    mac_address_sha256 = if (
                        [string]::IsNullOrWhiteSpace([string]$_.MacAddress)
                    ) {
                        $null
                    }
                    else {
                        Get-Sha256Text -Text ([string]$_.MacAddress)
                    }
                }
            }
    )
    $Profiles = @(
        Get-NetConnectionProfile -ErrorAction SilentlyContinue |
            Sort-Object InterfaceIndex |
            ForEach-Object {
                [ordered]@{
                    name = [string]$_.Name
                    interface_alias = [string]$_.InterfaceAlias
                    interface_index = [int]$_.InterfaceIndex
                    network_category = [string]$_.NetworkCategory
                    ipv4_connectivity = [string]$_.IPv4Connectivity
                    ipv6_connectivity = [string]$_.IPv6Connectivity
                }
            }
    )
    $DefaultRoutes = @(
        Get-NetRoute `
            -DestinationPrefix "0.0.0.0/0" `
            -ErrorAction SilentlyContinue |
            Sort-Object RouteMetric, InterfaceMetric |
            ForEach-Object {
                [ordered]@{
                    interface_index = [int]$_.ifIndex
                    interface_alias = [string]$_.InterfaceAlias
                    next_hop = [string]$_.NextHop
                    route_metric = [int]$_.RouteMetric
                    interface_metric = [int]$_.InterfaceMetric
                    state = [string]$_.State
                }
            }
    )

    return [ordered]@{
        captured_at_utc = (Get-Date).ToUniversalTime().ToString("o")
        adapters = $Adapters
        physical_adapters = $PhysicalAdapters
        connection_profiles = $Profiles
        ipv4_default_routes = $DefaultRoutes
    }
}

function Assert-NetworkIsOffline {
    param(
        [Parameter(Mandatory = $true)]
        $Snapshot,

        [Parameter(Mandatory = $true)]
        [string]$Phase
    )

    $ConnectedPhysical = @(
        $Snapshot.physical_adapters |
            Where-Object { $_.status -eq "Up" }
    )
    if ($ConnectedPhysical.Count -gt 0) {
        $Names = ($ConnectedPhysical | ForEach-Object { $_.name }) -join ", "
        throw (
            "Internet-off gate failed during ${Phase}: physical adapter(s) " +
            "are still Up: $Names. Disconnect Ethernet and disable Wi-Fi."
        )
    }

    $InternetProfiles = @(
        $Snapshot.connection_profiles |
            Where-Object {
                $_.ipv4_connectivity -eq "Internet" -or
                $_.ipv6_connectivity -eq "Internet"
            }
    )
    if ($InternetProfiles.Count -gt 0) {
        $Names = ($InternetProfiles | ForEach-Object { $_.interface_alias }) -join ", "
        throw (
            "Internet-off gate failed during ${Phase}: Windows reports " +
            "Internet connectivity on: $Names."
        )
    }
}

function Get-Health {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port,

        [int]$TimeoutSeconds = 2
    )

    try {
        $Response = Invoke-WebRequest `
            -UseBasicParsing `
            -Uri "http://127.0.0.1:$Port/api/health" `
            -Method Get `
            -TimeoutSec $TimeoutSeconds
        $ParsedBody = $Response.Content | ConvertFrom-Json
        return [ordered]@{
            reachable = $true
            status_code = [int]$Response.StatusCode
            status = [string]$ParsedBody.status
            response_body = [string]$Response.Content
            checked_at_utc = (Get-Date).ToUniversalTime().ToString("o")
        }
    }
    catch {
        return [ordered]@{
            reachable = $false
            error = [string]$_.Exception.Message
            checked_at_utc = (Get-Date).ToUniversalTime().ToString("o")
        }
    }
}

function Assert-Health {
    param(
        [Parameter(Mandatory = $true)]
        $Health,

        [Parameter(Mandatory = $true)]
        [string]$Phase
    )

    if (
        -not $Health.reachable -or
        $Health.status_code -ne 200 -or
        $Health.status -ne "ok"
    ) {
        throw "Health gate failed after $Phase."
    }
}

function Read-RuntimeInteger {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [string]$Label,

        [Parameter(Mandatory = $true)]
        [int]$Minimum,

        [Parameter(Mandatory = $true)]
        [int]$Maximum
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Runtime $Label file was not created."
    }
    $Text = (Get-Content -LiteralPath $Path -Raw).Trim()
    $Value = 0
    if (
        -not [int]::TryParse($Text, [ref]$Value) -or
        $Value -lt $Minimum -or
        $Value -gt $Maximum
    ) {
        throw "Runtime $Label value is invalid: '$Text'."
    }
    return $Value
}

function Invoke-BatchLauncher {
    param(
        [Parameter(Mandatory = $true)]
        [string]$BatchPath,

        [Parameter(Mandatory = $true)]
        [string]$EvidenceName,

        [Parameter(Mandatory = $true)]
        [int]$TimeoutSeconds
    )

    $StdoutPath = Join-Path $CommandLogDirectory "$EvidenceName.stdout.log"
    $StderrPath = Join-Path $CommandLogDirectory "$EvidenceName.stderr.log"
    $Stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $QuotedBatchPath = '"' + $BatchPath + '"'
    $LauncherProcess = Start-Process `
        -FilePath $CommandProcessor `
        -ArgumentList @("/d", "/c", $QuotedBatchPath) `
        -WorkingDirectory $ExtractRoot `
        -RedirectStandardOutput $StdoutPath `
        -RedirectStandardError $StderrPath `
        -WindowStyle Hidden `
        -PassThru
    if (-not $LauncherProcess.WaitForExit($TimeoutSeconds * 1000)) {
        Stop-Process -Id $LauncherProcess.Id -Force -ErrorAction SilentlyContinue
        $Stopwatch.Stop()
        throw (
            "$EvidenceName timed out after $TimeoutSeconds seconds. " +
            "Command logs were preserved."
        )
    }
    $Stopwatch.Stop()
    return [ordered]@{
        exit_code = [int]$LauncherProcess.ExitCode
        elapsed_seconds = [math]::Round($Stopwatch.Elapsed.TotalSeconds, 3)
        stdout_file = "commands/$EvidenceName.stdout.log"
        stderr_file = "commands/$EvidenceName.stderr.log"
        completed_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    }
}

function Get-ProcessEvidence {
    param(
        [Parameter(Mandatory = $true)]
        [int]$ProcessId
    )

    $Process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($null -eq $Process) {
        throw "Recorded server PID $ProcessId is not running."
    }
    $ExecutablePath = $null
    try {
        $ExecutablePath = $Process.Path
    }
    catch {
        throw "Unable to inspect executable path for server PID $ProcessId."
    }
    if (
        $Process.ProcessName -ne "RainFlowSejong" -or
        -not [string]::Equals(
            [System.IO.Path]::GetFullPath($ExecutablePath),
            [System.IO.Path]::GetFullPath($ExtractedExecutable),
            [System.StringComparison]::OrdinalIgnoreCase
        )
    ) {
        throw "Recorded PID $ProcessId is not this extracted RainFlowSejong.exe."
    }

    return [ordered]@{
        pid = [int]$Process.Id
        process_name = [string]$Process.ProcessName
        executable_path = [string]$ExecutablePath
        executable_sha256 = (
            Get-FileHash -LiteralPath $ExecutablePath -Algorithm SHA256
        ).Hash.ToLowerInvariant()
        start_time_utc = $Process.StartTime.ToUniversalTime().ToString("o")
        responding = [bool]$Process.Responding
    }
}

function Assert-InternalManifest {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ReleaseRoot
    )

    $ManifestPath = Join-Path $ReleaseRoot "SHA256SUMS.txt"
    if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
        throw "Extracted ZIP is missing SHA256SUMS.txt."
    }

    $ExpectedByPath = @{}
    $ReleaseRootFull = [System.IO.Path]::GetFullPath($ReleaseRoot).TrimEnd("\")
    foreach ($Line in Get-Content -LiteralPath $ManifestPath) {
        if ([string]::IsNullOrWhiteSpace($Line)) {
            continue
        }
        $Match = [regex]::Match(
            $Line,
            "^([0-9A-Fa-f]{64})\s+[* ](.+)$"
        )
        if (-not $Match.Success) {
            throw "Invalid SHA256SUMS.txt line: '$Line'."
        }
        $ExpectedHash = $Match.Groups[1].Value.ToLowerInvariant()
        $RelativePath = $Match.Groups[2].Value.Replace("/", "\")
        $Segments = @($RelativePath.Split("\"))
        if (
            [System.IO.Path]::IsPathRooted($RelativePath) -or
            $Segments -contains ".."
        ) {
            throw "Unsafe SHA256SUMS.txt path: '$RelativePath'."
        }
        if ($ExpectedByPath.ContainsKey($RelativePath)) {
            throw "Duplicate SHA256SUMS.txt path: '$RelativePath'."
        }
        $CandidatePath = [System.IO.Path]::GetFullPath(
            (Join-Path $ReleaseRootFull $RelativePath)
        )
        if (-not $CandidatePath.StartsWith(
            $ReleaseRootFull + "\",
            [System.StringComparison]::OrdinalIgnoreCase
        )) {
            throw "SHA256SUMS.txt path escapes the release root: '$RelativePath'."
        }
        if (-not (Test-Path -LiteralPath $CandidatePath -PathType Leaf)) {
            throw "SHA256SUMS.txt entry is missing: '$RelativePath'."
        }
        $ActualHash = (
            Get-FileHash -LiteralPath $CandidatePath -Algorithm SHA256
        ).Hash.ToLowerInvariant()
        if ($ActualHash -ne $ExpectedHash) {
            throw "SHA256 mismatch inside ZIP: '$RelativePath'."
        }
        $ExpectedByPath[$RelativePath] = $ExpectedHash
    }

    $ActualRelativePaths = @(
        Get-ChildItem -LiteralPath $ReleaseRoot -File -Recurse |
            Where-Object { $_.FullName -ne $ManifestPath } |
            ForEach-Object {
                $_.FullName.Substring($ReleaseRootFull.Length + 1)
            }
    )
    foreach ($ActualRelativePath in $ActualRelativePaths) {
        if (-not $ExpectedByPath.ContainsKey($ActualRelativePath)) {
            throw "Extracted file is not covered by SHA256SUMS.txt: '$ActualRelativePath'."
        }
    }
    if ($ExpectedByPath.Count -ne $ActualRelativePaths.Count) {
        throw (
            "SHA256SUMS.txt entry count does not match extracted file count " +
            "($($ExpectedByPath.Count) vs $($ActualRelativePaths.Count))."
        )
    }

    return [ordered]@{
        verified_entries = [int]$ExpectedByPath.Count
        manifest_sha256 = (
            Get-FileHash -LiteralPath $ManifestPath -Algorithm SHA256
        ).Hash.ToLowerInvariant()
    }
}

function Copy-EvidenceTree {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Source,

        [Parameter(Mandatory = $true)]
        [string]$Destination
    )

    if (-not (Test-Path -LiteralPath $Source -PathType Container)) {
        return
    }
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    Get-ChildItem -LiteralPath $Source -Force | ForEach-Object {
        Copy-Item `
            -LiteralPath $_.FullName `
            -Destination $Destination `
            -Recurse `
            -Force
    }
}

function Write-EvidenceManifest {
    $ManifestPath = Join-Path $RunDirectory "evidence-SHA256SUMS.txt"
    $Lines = @(
        Get-ChildItem -LiteralPath $RunDirectory -File -Recurse |
            Where-Object { $_.FullName -ne $ManifestPath } |
            Sort-Object FullName |
            ForEach-Object {
                $RelativePath = $_.FullName.Substring(
                    $RunDirectory.Length + 1
                ).Replace("\", "/")
                $Hash = (
                    Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256
                ).Hash.ToLowerInvariant()
                "$Hash *$RelativePath"
            }
    )
    [System.IO.File]::WriteAllLines(
        $ManifestPath,
        [string[]]$Lines,
        [System.Text.UTF8Encoding]::new($false)
    )
}

Write-HarnessLog (
    "Starting external-PC validation for $PcIdentifier run $RunNumber. " +
    "No prior external run is inferred or imported."
)

try {
    $Os = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
    $ComputerSystem = Get-CimInstance Win32_ComputerSystem -ErrorAction Stop
    $ComputerProduct = Get-CimInstance Win32_ComputerSystemProduct -ErrorAction Stop
    $WindowsMachineGuid = [string](
        Get-ItemProperty `
            -LiteralPath "HKLM:\SOFTWARE\Microsoft\Cryptography" `
            -Name "MachineGuid" `
            -ErrorAction Stop
    ).MachineGuid
    $MachineFingerprint = Get-Sha256Text -Text (
        [string]$ComputerProduct.UUID + "|" +
        $WindowsMachineGuid + "|" +
        [string]$ComputerSystem.Manufacturer + "|" +
        [string]$ComputerSystem.Model
    )
    $ToolNames = @(
        "node.exe",
        "python.exe",
        "python3.exe",
        "py.exe",
        "sumo.exe",
        "sumo-gui.exe"
    )
    $IgnoredExecutionAliases = @()
    $DetectedTools = @(
        foreach ($ToolName in $ToolNames) {
            $Command = Get-Command $ToolName -CommandType Application -ErrorAction SilentlyContinue |
                Select-Object -First 1
            if ($null -ne $Command) {
                $CommandPath = [string]$Command.Source
                $IsUninstalledPythonStoreAlias = (
                    $ToolName -match "^python3?\.exe$" -and
                    $CommandPath -match (
                        "(?i)\\Microsoft\\WindowsApps\\python(?:3)?\.exe$"
                    )
                )
                if ($IsUninstalledPythonStoreAlias) {
                    $IgnoredExecutionAliases += [ordered]@{
                        name = $ToolName
                        path = $CommandPath
                        reason = "Windows Store execution alias is not an installed Python runtime."
                    }
                }
                else {
                    [ordered]@{
                        name = $ToolName
                        path = $CommandPath
                    }
                }
            }
        }
    )
    $AiCredentialVariablePattern = (
        "^(OPENAI_API_KEY|ANTHROPIC_API_KEY|GOOGLE_API_KEY|" +
        "GEMINI_API_KEY|AZURE_OPENAI_API_KEY|AZURE_OPENAI_ENDPOINT|" +
        "MISTRAL_API_KEY|COHERE_API_KEY|OLLAMA_HOST)$"
    )
    $DetectedAiCredentialVariables = @(
        Get-ChildItem Env: |
            Where-Object { $_.Name -match $AiCredentialVariablePattern } |
            ForEach-Object { [string]$_.Name } |
            Sort-Object
    )
    $NetworkBefore = Get-NetworkSnapshot

    $EnvironmentEvidence = [ordered]@{
        captured_at_utc = (Get-Date).ToUniversalTime().ToString("o")
        pc_identifier = $PcIdentifier
        machine_fingerprint_sha256 = $MachineFingerprint
        machine_fingerprint_sources = @(
            "computer-system-product UUID",
            "Windows MachineGuid",
            "manufacturer",
            "model"
        )
        computer_name = [string]$env:COMPUTERNAME
        os_caption = [string]$Os.Caption
        os_version = [string]$Os.Version
        os_build_number = [string]$Os.BuildNumber
        os_architecture = [string]$Os.OSArchitecture
        manufacturer = [string]$ComputerSystem.Manufacturer
        model = [string]$ComputerSystem.Model
        process_is_64_bit = [Environment]::Is64BitProcess
        operating_system_is_64_bit = [Environment]::Is64BitOperatingSystem
        detected_development_tools = $DetectedTools
        ignored_uninstalled_execution_aliases = $IgnoredExecutionAliases
        detected_ai_credential_variable_names = $DetectedAiCredentialVariables
        network_before = $NetworkBefore
    }
    Write-JsonFile `
        -Path (Join-Path $RunDirectory "environment-before.json") `
        -Value $EnvironmentEvidence

    if (-not [Environment]::Is64BitProcess) {
        throw "Run the harness with 64-bit Windows PowerShell."
    }
    if ($DetectedTools.Count -gt 0) {
        $Names = ($DetectedTools | ForEach-Object { $_.name }) -join ", "
        throw "Clean-PC gate failed; development tool(s) were found: $Names."
    }
    if ($DetectedAiCredentialVariables.Count -gt 0) {
        throw (
            "API-key-free gate failed; AI credential environment variable name(s) " +
            "were found: $($DetectedAiCredentialVariables -join ', ')."
        )
    }
    Assert-NetworkIsOffline -Snapshot $NetworkBefore -Phase "preflight"
    Write-HarnessLog "Clean Windows x64 and internet-off preflight passed."

    $ResolvedChecksumPath = $null
    $ChecksumFromFile = $null
    if (-not [string]::IsNullOrWhiteSpace($ChecksumPath)) {
        $ResolvedChecksumPath = (Resolve-Path -LiteralPath $ChecksumPath).Path
    }
    elseif (Test-Path -LiteralPath "$ResolvedZipPath.sha256" -PathType Leaf) {
        $ResolvedChecksumPath = (Resolve-Path -LiteralPath "$ResolvedZipPath.sha256").Path
    }
    if ($null -ne $ResolvedChecksumPath) {
        $ChecksumText = Get-Content -LiteralPath $ResolvedChecksumPath -Raw
        $ChecksumMatch = [regex]::Match($ChecksumText, "(?i)\b[0-9a-f]{64}\b")
        if (-not $ChecksumMatch.Success) {
            throw "Checksum file does not contain a SHA-256 value."
        }
        $ChecksumFromFile = $ChecksumMatch.Value.ToLowerInvariant()
        Copy-Item `
            -LiteralPath $ResolvedChecksumPath `
            -Destination (Join-Path $RunDirectory "artifact-checksum-source.txt")
    }
    if (
        [string]::IsNullOrWhiteSpace($ExpectedSha256) -and
        $null -eq $ChecksumFromFile
    ) {
        throw (
            "A checksum is required. Place '<zip>.sha256' beside the ZIP, " +
            "or pass -ChecksumPath or -ExpectedSha256."
        )
    }
    if (
        -not [string]::IsNullOrWhiteSpace($ExpectedSha256) -and
        $null -ne $ChecksumFromFile -and
        $ExpectedSha256.ToLowerInvariant() -ne $ChecksumFromFile
    ) {
        throw "The explicit and file-based ZIP checksums disagree."
    }
    $ExpectedZipHash = if (-not [string]::IsNullOrWhiteSpace($ExpectedSha256)) {
        $ExpectedSha256.ToLowerInvariant()
    }
    else {
        $ChecksumFromFile
    }
    $ActualZipHash = (
        Get-FileHash -LiteralPath $ResolvedZipPath -Algorithm SHA256
    ).Hash.ToLowerInvariant()
    if ($ActualZipHash -ne $ExpectedZipHash) {
        throw "Release ZIP SHA-256 does not match the expected checksum."
    }
    $Artifact = [ordered]@{
        zip_file_name = [System.IO.Path]::GetFileName($ResolvedZipPath)
        zip_size_bytes = [long](Get-Item -LiteralPath $ResolvedZipPath).Length
        expected_zip_sha256 = $ExpectedZipHash
        actual_zip_sha256 = $ActualZipHash
        checksum_source_file = if ($null -eq $ResolvedChecksumPath) {
            $null
        }
        else {
            [System.IO.Path]::GetFileName($ResolvedChecksumPath)
        }
        verified_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    }
    Write-HarnessLog "Release ZIP SHA-256 verified: $ActualZipHash"

    $WorkingParent = Join-Path (
        [System.IO.Path]::GetTempPath()
    ) ("rainflow-external-" + [guid]::NewGuid().ToString("N"))
    $UnicodePrefix = -join @(
        [char]0xD55C,
        [char]0xAE00,
        [char]0x0020,
        [char]0xC678,
        [char]0xBD80,
        [char]0x0020,
        [char]0xAC80,
        [char]0xC99D
    )
    $ExtractRoot = Join-Path $WorkingParent (
        "$UnicodePrefix $PcIdentifier run $RunNumber"
    )
    New-Item -ItemType Directory -Path $ExtractRoot -Force | Out-Null
    Expand-Archive -LiteralPath $ResolvedZipPath -DestinationPath $ExtractRoot

    $RequiredRootFiles = @(
        "RainFlowSejong.exe",
        "start.bat",
        "launch.ps1",
        "stop.bat",
        "stop.ps1",
        "README.txt",
        "RELEASE-METADATA.json",
        "SHA256SUMS.txt"
    )
    foreach ($RequiredRootFile in $RequiredRootFiles) {
        if (-not (Test-Path -LiteralPath (
            Join-Path $ExtractRoot $RequiredRootFile
        ) -PathType Leaf)) {
            throw "Extracted ZIP root is missing $RequiredRootFile."
        }
    }
    if (-not (Test-Path -LiteralPath (
        Join-Path $ExtractRoot "_internal"
    ) -PathType Container)) {
        throw "Extracted ZIP root is missing the _internal directory."
    }
    $InternalManifest = Assert-InternalManifest -ReleaseRoot $ExtractRoot
    $Artifact.extracted_path = $ExtractRoot
    $Artifact.extracted_path_contains_space = $ExtractRoot.Contains(" ")
    $Artifact.extracted_path_contains_non_ascii = [bool](
        $ExtractRoot.ToCharArray() | Where-Object { [int]$_ -gt 127 }
    )
    $Artifact.internal_manifest = $InternalManifest
    Copy-Item `
        -LiteralPath (Join-Path $ExtractRoot "SHA256SUMS.txt") `
        -Destination (Join-Path $RunDirectory "extracted-SHA256SUMS.txt")
    Write-JsonFile `
        -Path (Join-Path $RunDirectory "artifact.json") `
        -Value $Artifact
    Write-HarnessLog (
        "ZIP extracted to a Korean-and-space path; " +
        "$($InternalManifest.verified_entries) internal hashes verified."
    )

    $ExtractedExecutable = Join-Path $ExtractRoot "RainFlowSejong.exe"
    $RuntimeDirectory = Join-Path $ExtractRoot "runtime"
    $PortFile = Join-Path $RuntimeDirectory "rainflow.port"
    $PidFile = Join-Path $RuntimeDirectory "rainflow.pid"
    $StartBatch = Join-Path $ExtractRoot "start.bat"
    $StopBatch = Join-Path $ExtractRoot "stop.bat"

    [Environment]::SetEnvironmentVariable(
        "RAINFLOW_NO_BROWSER",
        "1",
        [EnvironmentVariableTarget]::Process
    )
    [Environment]::SetEnvironmentVariable(
        "RAINFLOW_NONINTERACTIVE",
        "1",
        [EnvironmentVariableTarget]::Process
    )

    Write-HarnessLog "[1/4] Starting extracted release."
    $FirstStart = Invoke-BatchLauncher `
        -BatchPath $StartBatch `
        -EvidenceName "start-first" `
        -TimeoutSeconds $LauncherTimeoutSeconds
    if ($FirstStart.exit_code -ne 0) {
        throw "First start.bat exited with code $($FirstStart.exit_code)."
    }
    if ($FirstStart.elapsed_seconds -gt 60) {
        throw (
            "First start exceeded the 60-second external-PC gate " +
            "($($FirstStart.elapsed_seconds) seconds)."
        )
    }
    $FirstPort = Read-RuntimeInteger `
        -Path $PortFile `
        -Label "port" `
        -Minimum 1 `
        -Maximum 65535
    $FirstPid = Read-RuntimeInteger `
        -Path $PidFile `
        -Label "PID" `
        -Minimum 1 `
        -Maximum ([int]::MaxValue)
    $ServerProcessIdForCleanup = $FirstPid
    $FirstHealth = Get-Health -Port $FirstPort
    Assert-Health -Health $FirstHealth -Phase "first start"
    $FirstProcess = Get-ProcessEvidence -ProcessId $FirstPid
    $Lifecycle.first_start = [ordered]@{
        command = $FirstStart
        port = $FirstPort
        health = $FirstHealth
        process = $FirstProcess
    }
    Write-HarnessLog (
        "[2/4] Health is HTTP 200/status ok on port $FirstPort; " +
        "re-running start.bat."
    )

    $SecondStart = Invoke-BatchLauncher `
        -BatchPath $StartBatch `
        -EvidenceName "start-second" `
        -TimeoutSeconds $LauncherTimeoutSeconds
    if ($SecondStart.exit_code -ne 0) {
        throw "Second start.bat exited with code $($SecondStart.exit_code)."
    }
    $SecondPort = Read-RuntimeInteger `
        -Path $PortFile `
        -Label "port" `
        -Minimum 1 `
        -Maximum 65535
    $SecondPid = Read-RuntimeInteger `
        -Path $PidFile `
        -Label "PID" `
        -Minimum 1 `
        -Maximum ([int]::MaxValue)
    if ($SecondPort -ne $FirstPort) {
        throw "Second start changed the port ($FirstPort -> $SecondPort)."
    }
    if ($SecondPid -ne $FirstPid) {
        throw "Second start created another process ($FirstPid -> $SecondPid)."
    }
    $SecondHealth = Get-Health -Port $SecondPort
    Assert-Health -Health $SecondHealth -Phase "second start"
    $SecondProcess = Get-ProcessEvidence -ProcessId $SecondPid
    $Lifecycle.second_start = [ordered]@{
        command = $SecondStart
        port = $SecondPort
        health = $SecondHealth
        process = $SecondProcess
        reused_same_port = $true
        reused_same_pid = $true
    }

    Write-HarnessLog "[3/4] Stopping extracted release."
    $StopResult = Invoke-BatchLauncher `
        -BatchPath $StopBatch `
        -EvidenceName "stop" `
        -TimeoutSeconds 20
    if ($StopResult.exit_code -ne 0) {
        throw "stop.bat exited with code $($StopResult.exit_code)."
    }
    $ShutdownDeadline = (Get-Date).AddSeconds(10)
    do {
        $RemainingProcess = Get-Process -Id $FirstPid -ErrorAction SilentlyContinue
        if ($null -eq $RemainingProcess) {
            break
        }
        Start-Sleep -Milliseconds 200
    } while ((Get-Date) -lt $ShutdownDeadline)
    if ($null -ne $RemainingProcess) {
        throw "RainFlowSejong PID $FirstPid remains after stop.bat."
    }
    $ServerProcessIdForCleanup = $null
    if (
        (Test-Path -LiteralPath $PidFile) -or
        (Test-Path -LiteralPath $PortFile)
    ) {
        throw "Runtime PID or port file remains after stop.bat."
    }

    Write-HarnessLog "[4/4] Confirming health is unavailable after stop."
    Start-Sleep -Milliseconds 500
    $PostStopHealth = Get-Health -Port $FirstPort
    if ($PostStopHealth.reachable) {
        throw "Health endpoint still responds after stop.bat."
    }
    $Lifecycle.stop = [ordered]@{
        command = $StopResult
        process_running_after_stop = $false
        pid_file_exists_after_stop = $false
        port_file_exists_after_stop = $false
        post_stop_health = $PostStopHealth
    }

    $NetworkAfter = Get-NetworkSnapshot
    Assert-NetworkIsOffline -Snapshot $NetworkAfter -Phase "post-run"
    $EnvironmentEvidence.network_after = $NetworkAfter
    $ValidationStatus = "PASS"
    Write-HarnessLog (
        "External-PC lifecycle passed: start -> health 200 -> second start " +
        "(same PID/port) -> stop."
    )
}
catch {
    $Failure = $_
    Write-HarnessLog "VALIDATION FAILED: $($_.Exception.Message)"
}
finally {
    [Environment]::SetEnvironmentVariable(
        "RAINFLOW_NO_BROWSER",
        $PreviousNoBrowser,
        [EnvironmentVariableTarget]::Process
    )
    [Environment]::SetEnvironmentVariable(
        "RAINFLOW_NONINTERACTIVE",
        $PreviousNonInteractive,
        [EnvironmentVariableTarget]::Process
    )

    if (
        $null -ne $ServerProcessIdForCleanup -and
        $null -ne $ExtractedExecutable
    ) {
        $CleanupProcess = Get-Process `
            -Id $ServerProcessIdForCleanup `
            -ErrorAction SilentlyContinue
        if ($null -ne $CleanupProcess) {
            $CleanupProcessPath = $null
            try {
                $CleanupProcessPath = $CleanupProcess.Path
            }
            catch {
                $CleanupProcessPath = $null
            }
            if (
                $CleanupProcess.ProcessName -eq "RainFlowSejong" -and
                $null -ne $CleanupProcessPath -and
                [string]::Equals(
                    [System.IO.Path]::GetFullPath($CleanupProcessPath),
                    [System.IO.Path]::GetFullPath($ExtractedExecutable),
                    [System.StringComparison]::OrdinalIgnoreCase
                )
            ) {
                Stop-Process `
                    -Id $ServerProcessIdForCleanup `
                    -Force `
                    -ErrorAction SilentlyContinue
                $CleanupProcess.WaitForExit(5000) | Out-Null
                $CleanupEvidence.forced_stop_of_owned_process = $true
            }
            else {
                $CleanupEvidence.forced_stop_of_owned_process = $false
                $CleanupEvidence.refused_unverified_process_stop = $true
            }
        }
    }

    if ($null -ne $ExtractRoot) {
        Copy-EvidenceTree `
            -Source (Join-Path $ExtractRoot "logs") `
            -Destination (Join-Path $RunDirectory "collected\release-logs")
        Copy-EvidenceTree `
            -Source (Join-Path $ExtractRoot "_internal\backend\logs") `
            -Destination (Join-Path $RunDirectory "collected\backend-logs")
    }

    if ($null -ne $WorkingParent -and (Test-Path -LiteralPath $WorkingParent)) {
        Remove-Item `
            -LiteralPath $WorkingParent `
            -Recurse `
            -Force `
            -ErrorAction SilentlyContinue
        $CleanupEvidence.temporary_extract_removed = -not (
            Test-Path -LiteralPath $WorkingParent
        )
    }

    if (-not $EnvironmentEvidence.Contains("network_after")) {
        try {
            $EnvironmentEvidence.network_after = Get-NetworkSnapshot
        }
        catch {
            $EnvironmentEvidence.network_after_error = [string]$_.Exception.Message
        }
    }
    if ($EnvironmentEvidence.Count -gt 0) {
        Write-JsonFile `
            -Path (Join-Path $RunDirectory "environment.json") `
            -Value $EnvironmentEvidence
    }
    if ($Artifact.Count -gt 0) {
        Write-JsonFile `
            -Path (Join-Path $RunDirectory "artifact.json") `
            -Value $Artifact
    }
    if ($Lifecycle.Count -gt 0) {
        Write-JsonFile `
            -Path (Join-Path $RunDirectory "lifecycle.json") `
            -Value $Lifecycle
    }
    if ($CleanupEvidence.Count -gt 0) {
        Write-JsonFile `
            -Path (Join-Path $RunDirectory "cleanup.json") `
            -Value $CleanupEvidence
    }

    $CompletedAt = (Get-Date).ToUniversalTime()
    $Result = [ordered]@{
        schema_version = 1
        status = $ValidationStatus
        pc_identifier = $PcIdentifier
        run_number = $RunNumber
        started_at_utc = $StartedAt.ToString("o")
        completed_at_utc = $CompletedAt.ToString("o")
        duration_seconds = [math]::Round(
            ($CompletedAt - $StartedAt).TotalSeconds,
            3
        )
        zip_sha256 = if ($Artifact.Contains("actual_zip_sha256")) {
            $Artifact.actual_zip_sha256
        }
        else {
            $null
        }
        machine_fingerprint_sha256 = if (
            $EnvironmentEvidence.Contains("machine_fingerprint_sha256")
        ) {
            $EnvironmentEvidence.machine_fingerprint_sha256
        }
        else {
            $null
        }
        error = if ($null -eq $Failure) {
            $null
        }
        else {
            [string]$Failure.Exception.Message
        }
        claim_scope = (
            "This result describes only the named PC and run executed by this " +
            "harness. It does not establish any unexecuted PC or run."
        )
    }
    Write-JsonFile -Path (Join-Path $RunDirectory "result.json") -Value $Result
    Write-EvidenceManifest
}

if ($null -ne $Failure) {
    throw (
        "External-PC validation failed. Evidence was preserved at " +
        "'$RunDirectory': $($Failure.Exception.Message)"
    )
}

Write-Host ""
Write-Host "External-PC evidence recorded:"
Write-Host "  PC/run:  $PcIdentifier / $RunNumber"
Write-Host "  Status:  PASS"
Write-Host "  Evidence: $RunDirectory"
