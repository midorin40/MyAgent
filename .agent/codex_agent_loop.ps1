$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$ordersDir = Join-Path $root ".agent\orders"
$processingDir = Join-Path $root ".agent\processing"
$resultsDir = Join-Path $root ".agent\results"
$completedDir = Join-Path $root ".agent\completed"
$logDir = Join-Path $root ".agent\logs"
$logFile = Join-Path $logDir "codex_agent_loop.log"
$agentName = "codex"
$pollSeconds = 10
$codexCommand = if ($env:CODEX_CMD) { $env:CODEX_CMD } else { "codex" }

New-Item -ItemType Directory -Force -Path $ordersDir, $processingDir, $resultsDir, $logDir, $completedDir | Out-Null

function Write-LoopLog {
    param([string]$Message)

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    try {
        Add-Content -Path $logFile -Value "[$timestamp] $Message" -ErrorAction Stop
    } catch {
        Write-Host "[$timestamp] Log write failed: $($_.Exception.Message)"
    }
}

function Get-NextTaskFile {
    $processingTask = Get-ChildItem -Path $processingDir -Filter "$agentName`_*.md" -File |
        Sort-Object LastWriteTime |
        Select-Object -First 1
    if ($processingTask) {
        return $processingTask
    }

    $orderTask = Get-ChildItem -Path $ordersDir -Filter "$agentName`_*.md" -File |
        Sort-Object LastWriteTime |
        Select-Object -First 1
    if (-not $orderTask) {
        return $null
    }

    $destination = Join-Path $processingDir $orderTask.Name
    Move-Item -Path $orderTask.FullName -Destination $destination -Force
    return Get-Item -Path $destination
}

function Invoke-AgentTask {
    param([System.IO.FileInfo]$TaskFile)

    $resultFile = Join-Path $resultsDir ("result_" + $TaskFile.Name)
    $taskBody = Get-Content -Path $TaskFile.FullName -Raw -Encoding UTF8
    $prompt = @(
        "You are processing a queued agent task for Codex."
        ""
        "Task file path: $($TaskFile.FullName)"
        "Result file path: $resultFile"
        ""
        "Requirements:"
        "- Read and follow the task instructions from the task file content below."
        "- Perform the requested work inside $root."
        "- Write the final task report to $resultFile."
        "- Keep the final console response brief because the report file is the durable output."
        "- If the task cannot be completed, still write a result report that explains the blocker."
        "- If you need help from multiple agents, submit a dispatch request with python .agent/scripts/submit_dispatch.py."
        "- Use repeated --subtask JSON arguments and set --callback-agent codex so the orchestrator re-queues an integration task for you."
        "- Do not wait interactively for sibling tasks. Delegate and let the callback task continue the flow."
        ""
        "Task file content:"
        $taskBody
    ) -join "`n"

    Write-LoopLog "Starting task $($TaskFile.Name)"
    $outputFile = Join-Path $logDir ($TaskFile.BaseName + ".last_message.txt")
    $jsonLogFile = Join-Path $logDir ($TaskFile.BaseName + ".jsonl")

    if (Test-Path -Path $outputFile) {
        Remove-Item -Path $outputFile -Force
    }
    if (Test-Path -Path $jsonLogFile) {
        Remove-Item -Path $jsonLogFile -Force
    }

    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $codexCommand exec --skip-git-repo-check --full-auto -C $root -o $outputFile --json $prompt 2>&1 |
        Tee-Object -FilePath $jsonLogFile -Append |
        Out-Null
    $ErrorActionPreference = $previousErrorAction
    $exitCode = $LASTEXITCODE

    if ($exitCode -ne 0) {
        Write-LoopLog "Task $($TaskFile.Name) failed with exit code $exitCode"
        $failureReport = @(
            "# Task Result"
            ""
            "- Agent: Codex"
            "- Task: $($TaskFile.Name)"
            "- Status: failed"
            "- Exit code: $exitCode"
            ""
            "The automated Codex execution failed. See the loop logs below for details."
            ""
            "## Output log"
            ""
            '```'
            (Get-Content -Path $jsonLogFile -Raw)
            '```'
        ) -join "`n"
        Set-Content -Path $resultFile -Value $failureReport -Encoding UTF8
        return $false
    }

    if (-not (Test-Path -Path $resultFile)) {
        $fallbackReport = @(
            "# Task Result"
            ""
            "- Agent: Codex"
            "- Task: $($TaskFile.Name)"
            "- Status: completed_without_report"
            ""
            "Codex execution completed but did not create the requested result file."
            ""
            "## Last agent message"
            ""
            '```'
            (Get-Content -Path $outputFile -Raw)
            '```'
        ) -join "`n"
        Set-Content -Path $resultFile -Value $fallbackReport -Encoding UTF8
    }

    Write-LoopLog "Completed task $($TaskFile.Name)"
    return $true
}

Write-LoopLog "Codex agent loop starting"

while ($true) {
    try {
        $taskFile = Get-NextTaskFile
        if (-not $taskFile) {
            Start-Sleep -Seconds $pollSeconds
            continue
        }

        $success = Invoke-AgentTask -TaskFile $taskFile

        if ($success) {
            if (Test-Path -Path $completedDir) {
                Move-Item -Path $taskFile.FullName -Destination (Join-Path $completedDir $taskFile.Name) -Force
            } elseif (Test-Path -Path $taskFile.FullName) {
                Remove-Item -Path $taskFile.FullName -Force
            }
        }
    } catch {
        Write-LoopLog "Loop error: $($_.Exception.Message)"
        Start-Sleep -Seconds $pollSeconds
    }
}
