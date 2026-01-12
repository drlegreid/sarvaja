<#
.SYNOPSIS
    Run E2E tests for Sim.ai Task UI

.DESCRIPTION
    Executes Robot Framework + Playwright tests with configurable options.
    Per Phase 7: E2E Testing Infrastructure

.PARAMETER Suite
    Test suite to run (default: all)

.PARAMETER Tags
    Tags to include (e.g., "smoke", "api")

.PARAMETER Headless
    Run in headless mode (default: true)

.PARAMETER BaseUrl
    Base URL for tests (default: http://localhost:8081)

.EXAMPLE
    .\run_e2e.ps1
    .\run_e2e.ps1 -Tags "smoke"
    .\run_e2e.ps1 -Suite "task_ui.robot" -Headless $false
#>

param(
    [string]$Suite = "*.robot",
    [string]$Tags = "",
    [bool]$Headless = $true,
    [string]$BaseUrl = "http://localhost:8081",
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"

# Paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ResultsDir = Join-Path $ScriptDir "results"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# Create results directory
if (-not (Test-Path $ResultsDir)) {
    New-Item -ItemType Directory -Path $ResultsDir -Force | Out-Null
}

# Build robot command
$RobotArgs = @(
    "--outputdir", $ResultsDir,
    "--output", "output_$Timestamp.xml",
    "--log", "log_$Timestamp.html",
    "--report", "report_$Timestamp.html",
    "--loglevel", "INFO",
    "--variable", "HEADLESS:$($Headless.ToString().ToLower())",
    "--variable", "AGENT_URL:$BaseUrl",
    "--variable", "UI_URL:$BaseUrl/ui"
)

# Add tags if specified
if ($Tags) {
    $RobotArgs += "--include"
    $RobotArgs += $Tags
}

# Add verbose if requested
if ($Verbose) {
    $RobotArgs += "--loglevel"
    $RobotArgs += "DEBUG"
}

# Add suite path
$SuitePath = Join-Path $ScriptDir $Suite
$RobotArgs += $SuitePath

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Sim.ai E2E Tests (Robot + Playwright)     " -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Suite:    $Suite"
Write-Host "  Tags:     $(if ($Tags) { $Tags } else { 'all' })"
Write-Host "  Headless: $Headless"
Write-Host "  Base URL: $BaseUrl"
Write-Host "  Results:  $ResultsDir"
Write-Host ""

# Check if agent is running
Write-Host "Checking agent health..." -ForegroundColor Yellow
try {
    $health = Invoke-WebRequest -Uri "$BaseUrl/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "  Agent is healthy (HTTP $($health.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "  WARNING: Agent not responding at $BaseUrl" -ForegroundColor Red
    Write-Host "  Start agent with: python agent/playground.py" -ForegroundColor Yellow
    Write-Host ""
}

# Run tests
Write-Host "Running tests..." -ForegroundColor Yellow
Write-Host "  robot $($RobotArgs -join ' ')" -ForegroundColor DarkGray
Write-Host ""

$StartTime = Get-Date
& robot @RobotArgs
$ExitCode = $LASTEXITCODE
$Duration = (Get-Date) - $StartTime

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Test Execution Complete                   " -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Duration: $($Duration.ToString('mm\:ss'))" -ForegroundColor Yellow
Write-Host "Results:  $ResultsDir" -ForegroundColor Yellow

if ($ExitCode -eq 0) {
    Write-Host "Status:   PASSED" -ForegroundColor Green
} else {
    Write-Host "Status:   FAILED (exit code: $ExitCode)" -ForegroundColor Red
}

# Open report in browser (optional)
$ReportPath = Join-Path $ResultsDir "report_$Timestamp.html"
if (Test-Path $ReportPath) {
    Write-Host ""
    Write-Host "Report: $ReportPath" -ForegroundColor Cyan
    # Uncomment to auto-open: Start-Process $ReportPath
}

exit $ExitCode
