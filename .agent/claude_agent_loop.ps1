$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$ordersDir = Join-Path $root ".agent\orders"
$processingDir = Join-Path $root ".agent\processing"
$resultsDir = Join-Path $root ".agent\results"
$completedDir = Join-Path $root ".agent\completed"
$logDir = Join-Path $root ".agent\logs"
$logFile = Join-Path $logDir "claude_agent_loop.log"
$agentName = "claude"
$pollSeconds = 10
$claudeCommand = if ($env:CLAUDE_CMD) { $env:CLAUDE_CMD } else { "claude" }

New-Item -ItemType Directory -Force -Path $ordersDir, $processingDir, $resultsDir, $logDir, $completedDir | Out-Null

function Write-LoopLog {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    try {
        Add-Content -Path $logFile -Value "[$timestamp] $Message" -ErrorAction Stop
    } catch {
        Write-Host "[$timestamp] Log write failed: $($_.Exception.Message)"
    }
    Write-Host "[$timestamp] $Message"
}

function Get-NextTaskFile {
    $processingTask = Get-ChildItem -Path $processingDir -Filter "$agentName`_*.md" -File | Sort-Object LastWriteTime | Select-Object -First 1
    if ($processingTask) { return $processingTask }

    $orderTask = Get-ChildItem -Path $ordersDir -Filter "$agentName`_*.md" -File | Sort-Object LastWriteTime | Select-Object -First 1
    if (-not $orderTask) { return $null }

    $destination = Join-Path $processingDir $orderTask.Name
    Move-Item -Path $orderTask.FullName -Destination $destination -Force
    return Get-Item -Path $destination
}

function Invoke-AgentTask {
    param([System.IO.FileInfo]$TaskFile)

    $resultFile = Join-Path $resultsDir ("result_" + $TaskFile.Name)
    $taskBody = Get-Content -Path $TaskFile.FullName -Raw -Encoding UTF8
    $prompt = @(
        "You are processing a queued agent task. You must work autonomously and exit when done."
        ""
        "Task file path: $($TaskFile.FullName)"
        "Result file path: $resultFile"
        ""
        "If you need other agents, use python .agent/scripts/submit_dispatch.py with repeated --subtask JSON blocks."
        "Set --callback-agent claude and provide --callback-content so the orchestrator sends you a follow-up task after all subtasks finish."
        "Do not wait interactively for delegated work."
        ""
        "Task file content:"
        $taskBody
    ) -join "`n"

    Write-LoopLog "Starting task $($TaskFile.Name)"
    $outputFile = Join-Path $logDir ($TaskFile.BaseName + "_output.txt")
    if (Test-Path -Path $outputFile) { Remove-Item -Path $outputFile -Force }

    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $claudeCommand -p $prompt 2>&1 | Tee-Object -FilePath $outputFile | Out-Null
    $ErrorActionPreference = $previousErrorAction
    $exitCode = $LASTEXITCODE

    if ($exitCode -ne 0) {
        Write-LoopLog "Task $($TaskFile.Name) failed with exit code $exitCode"
        $failureReport = @(
            "# Task Result"
            "- Agent: Claude"
            "- Task: $($TaskFile.Name)"
            "- Status: failed"
            "- Exit code: $exitCode"
            "## Output log"
            '```'
            (Get-Content -Path $outputFile -Raw)
            '```'
        ) -join "`n"
        Set-Content -Path $resultFile -Value $failureReport -Encoding UTF8
        return $false
    }

    if (-not (Test-Path -Path $resultFile)) {
        $fallbackReport = @(
            "# Task Result"
            "- Status: completed_without_report"
            "## Last agent message"
            '```'
            (Get-Content -Path $outputFile -Raw)
            '```'
        ) -join "`n"
        Set-Content -Path $resultFile -Value $fallbackReport -Encoding UTF8
    }

    Write-LoopLog "Completed task $($TaskFile.Name)"
    return $true
}

Write-LoopLog "Claude agent loop starting"

while ($true) {
    try {
        $taskFile = Get-NextTaskFile
        if (-not $taskFile) {
            Start-Sleep -Seconds $pollSeconds
            continue
        }

        $success = Invoke-AgentTask -TaskFile $taskFile
        if ($success) {
            Move-Item -Path $taskFile.FullName -Destination (Join-Path $completedDir $taskFile.Name) -Force
        }
    } catch {
        Write-LoopLog "Loop error: $($_.Exception.Message)"
        Start-Sleep -Seconds $pollSeconds
    }
}
