[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z0-9._:|+/-]{3,240}$')]
    [string]$TaskKey,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Owner,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Summary,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Action,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Evidence,

    [string]$Due = 'Before the next 2-hour check',
    [string]$ChangeToken = '',
    [ValidateRange(1, 168)]
    [int]$ReminderHours = 4,
    [ValidateRange(1, 3)]
    [int]$MaxAttempts = 2,
    [ValidateRange(5, 30)]
    [int]$TimeoutSec = 15,
    [string]$StatePath = '',
    [string]$NowUtc = '',
    [switch]$Resolve,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-Sha256Text {
    param([Parameter(Mandatory = $true)][string]$Text)

    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
        return ([System.BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant()
    }
    finally {
        $sha.Dispose()
    }
}

function Write-JsonAtomic {
    param(
        [Parameter(Mandatory = $true)][object]$Value,
        [Parameter(Mandatory = $true)][string]$Path
    )

    $directory = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $directory)) {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
    }

    $temporaryPath = Join-Path $directory (([System.IO.Path]::GetRandomFileName()) + '.tmp')
    try {
        $json = $Value | ConvertTo-Json -Depth 8
        [System.IO.File]::WriteAllText($temporaryPath, $json, [System.Text.UTF8Encoding]::new($false))
        Move-Item -LiteralPath $temporaryPath -Destination $Path -Force
    }
    finally {
        if (Test-Path -LiteralPath $temporaryPath) {
            Remove-Item -LiteralPath $temporaryPath -Force
        }
    }
}

function Write-AuditEvent {
    param(
        [Parameter(Mandatory = $true)][string]$AuditPath,
        [Parameter(Mandatory = $true)][object]$Event
    )

    $directory = Split-Path -Parent $AuditPath
    if (-not (Test-Path -LiteralPath $directory)) {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
    }

    $line = ($Event | ConvertTo-Json -Depth 6 -Compress) + [Environment]::NewLine
    [System.IO.File]::AppendAllText($AuditPath, $line, [System.Text.UTF8Encoding]::new($false))
}

if ([string]::IsNullOrWhiteSpace($StatePath)) {
    if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
        throw 'LOCALAPPDATA is unavailable; pass -StatePath explicitly.'
    }
    $StatePath = Join-Path $env:LOCALAPPDATA 'MSGA\pm-automation\discord-state.json'
}

$stateDirectory = Split-Path -Parent $StatePath
$auditPath = Join-Path $stateDirectory 'audit.jsonl'
$now = if ([string]::IsNullOrWhiteSpace($NowUtc)) {
    [DateTimeOffset]::UtcNow
}
else {
    [DateTimeOffset]::Parse($NowUtc).ToUniversalTime()
}

$state = [ordered]@{
    schemaVersion = 1
    tasks = @()
}

if (Test-Path -LiteralPath $StatePath) {
    $rawState = [System.IO.File]::ReadAllText($StatePath, [System.Text.Encoding]::UTF8)
    if (-not [string]::IsNullOrWhiteSpace($rawState)) {
        $parsed = $rawState | ConvertFrom-Json
        $state.schemaVersion = if ($null -ne $parsed.schemaVersion) { [int]$parsed.schemaVersion } else { 1 }
        $state.tasks = @($parsed.tasks)
    }
}

$existing = @($state.tasks | Where-Object { $_.taskKey -eq $TaskKey } | Select-Object -First 1)
$existingTask = if ($existing.Count -gt 0) { $existing[0] } else { $null }

if ($Resolve) {
    $remaining = @($state.tasks | Where-Object { $_.taskKey -ne $TaskKey })
    if ($null -ne $existingTask) {
        $remaining += [pscustomobject][ordered]@{
            taskKey = $TaskKey
            owner = $Owner
            summary = $Summary
            changeToken = if ($existingTask.changeToken) { [string]$existingTask.changeToken } else { '' }
            firstSeenAtUtc = [string]$existingTask.firstSeenAtUtc
            lastChangedAtUtc = [string]$existingTask.lastChangedAtUtc
            lastSentAtUtc = [string]$existingTask.lastSentAtUtc
            lastEventKey = [string]$existingTask.lastEventKey
            status = 'resolved'
            resolvedAtUtc = $now.ToString('o')
        }
    }
    $state.tasks = $remaining
    if (-not $DryRun) {
        Write-JsonAtomic -Value $state -Path $StatePath
        Write-AuditEvent -AuditPath $auditPath -Event ([ordered]@{
            atUtc = $now.ToString('o')
            taskKey = $TaskKey
            decision = 'resolved'
        })
    }
    [pscustomobject]@{ TaskKey = $TaskKey; Decision = 'resolved'; Sent = $false }
    return
}

if ([string]::IsNullOrWhiteSpace($ChangeToken)) {
    $ChangeToken = Get-Sha256Text -Text ($Summary + "`n" + $Action + "`n" + $Evidence + "`n" + $Due)
}

$decision = 'suppressed'
$shouldSend = $false
$firstSeenAt = $now
$lastChangedAt = $now
$lastSentAt = $null

if ($null -eq $existingTask -or [string]$existingTask.status -eq 'resolved') {
    $decision = 'initial'
    $shouldSend = $true
}
else {
    $firstSeenAt = [DateTimeOffset]::Parse([string]$existingTask.firstSeenAtUtc)
    $lastChangedAt = [DateTimeOffset]::Parse([string]$existingTask.lastChangedAtUtc)
    if (-not [string]::IsNullOrWhiteSpace([string]$existingTask.lastSentAtUtc)) {
        $lastSentAt = [DateTimeOffset]::Parse([string]$existingTask.lastSentAtUtc)
    }

    if ([string]$existingTask.changeToken -ne $ChangeToken) {
        $decision = 'changed'
        $shouldSend = $true
        $lastChangedAt = $now
    }
    elseif ($null -eq $lastSentAt -or (($now - $lastSentAt).TotalHours -ge $ReminderHours)) {
        $decision = 'stale-reminder'
        $shouldSend = $true
    }
}

$eventKey = $TaskKey + '|rev=' + (Get-Sha256Text -Text $ChangeToken).Substring(0, 16) + '|' + $decision
$kindLabel = switch ($decision) {
    'initial' { 'New action' }
    'changed' { 'Change detected' }
    'stale-reminder' { "No update for ${ReminderHours}h" }
    default { 'Duplicate suppressed' }
}

$message = @(
    "[$Owner] $Summary"
    "Type: $kindLabel"
    "Action: $Action"
    "Evidence: $Evidence"
    "Due/recheck: $Due"
    "task_key: $TaskKey"
) -join "`n"

if ($message.Length -gt 1950) {
    $message = $message.Substring(0, 1947) + '...'
}

if (-not $shouldSend) {
    if (-not $DryRun) {
        Write-AuditEvent -AuditPath $auditPath -Event ([ordered]@{
            atUtc = $now.ToString('o')
            taskKey = $TaskKey
            decision = $decision
            eventKey = $eventKey
        })
    }
    [pscustomobject]@{ TaskKey = $TaskKey; Decision = $decision; Sent = $false }
    return
}

if ($DryRun) {
    [pscustomobject]@{
        TaskKey = $TaskKey
        Decision = $decision
        Sent = $false
        Preview = $message
    }
    return
}

$webhook = [Environment]::GetEnvironmentVariable('SEJONG_AX_DISCORD_WEBHOOK', 'Process')
if ([string]::IsNullOrWhiteSpace($webhook)) {
    $webhook = [Environment]::GetEnvironmentVariable('SEJONG_AX_DISCORD_WEBHOOK', 'User')
}
if ([string]::IsNullOrWhiteSpace($webhook)) {
    Write-AuditEvent -AuditPath $auditPath -Event ([ordered]@{
        atUtc = $now.ToString('o')
        taskKey = $TaskKey
        decision = 'failed'
        reason = 'webhook-environment-variable-missing'
    })
    throw 'SEJONG_AX_DISCORD_WEBHOOK is not configured.'
}

$payload = [ordered]@{
    username = 'MSGA PM Bot'
    content = $message
} | ConvertTo-Json -Compress

$sent = $false
$lastError = $null
for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
    try {
        Invoke-RestMethod -Uri $webhook -Method Post -ContentType 'application/json; charset=utf-8' -Body $payload -TimeoutSec $TimeoutSec | Out-Null
        $sent = $true
        break
    }
    catch {
        $lastError = $_.Exception.Message
        if ($attempt -lt $MaxAttempts) {
            Start-Sleep -Seconds 2
        }
    }
}

if (-not $sent) {
    Write-AuditEvent -AuditPath $auditPath -Event ([ordered]@{
        atUtc = $now.ToString('o')
        taskKey = $TaskKey
        decision = 'failed'
        reason = $lastError
        attempts = $MaxAttempts
    })
    throw "Discord delivery failed after $MaxAttempts attempt(s)."
}

$remainingTasks = @($state.tasks | Where-Object { $_.taskKey -ne $TaskKey })
$remainingTasks += [pscustomobject][ordered]@{
    taskKey = $TaskKey
    owner = $Owner
    summary = $Summary
    changeToken = $ChangeToken
    firstSeenAtUtc = $firstSeenAt.ToString('o')
    lastChangedAtUtc = $lastChangedAt.ToString('o')
    lastSentAtUtc = $now.ToString('o')
    lastEventKey = $eventKey
    status = 'open'
    resolvedAtUtc = $null
}
$state.tasks = $remainingTasks
Write-JsonAtomic -Value $state -Path $StatePath
Write-AuditEvent -AuditPath $auditPath -Event ([ordered]@{
    atUtc = $now.ToString('o')
    taskKey = $TaskKey
    decision = $decision
    eventKey = $eventKey
    attempts = $attempt
})

[pscustomobject]@{ TaskKey = $TaskKey; Decision = $decision; Sent = $true }
