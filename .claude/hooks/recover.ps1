<#
.SYNOPSIS
    Claude Code Settings Recovery Script (PowerShell Wrapper)

.DESCRIPTION
    Creates a backup of settings.local.json with timestamp suffix and restores
    to a clean minimal configuration.

.PARAMETER BackupOnly
    Only create backup, don't restore to minimal settings

.PARAMETER Restore
    Restore from a specific backup file

.PARAMETER List
    List available backup files

.EXAMPLE
    .\recover.ps1
    # Backup current settings and restore to minimal

.EXAMPLE
    .\recover.ps1 -BackupOnly
    # Only create backup

.EXAMPLE
    .\recover.ps1 -List
    # List available backups

.EXAMPLE
    .\recover.ps1 -Restore settings.local.json.20260104_123456.bak
    # Restore from specific backup

.NOTES
    Per EPIC-006: Used when hooks cause Claude Code startup failures.
#>

param(
    [switch]$BackupOnly,
    [string]$Restore,
    [switch]$List,
    [switch]$Help
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonScript = Join-Path $ScriptDir "recover.py"

if ($Help) {
    Get-Help $MyInvocation.MyCommand.Path -Detailed
    exit 0
}

# Build arguments
$args = @()

if ($BackupOnly) {
    $args += "--backup-only"
}

if ($List) {
    $args += "--list"
}

if ($Restore) {
    $args += "--restore"
    $args += $Restore
}

# Run Python script
try {
    if ($args.Count -gt 0) {
        python $PythonScript @args
    } else {
        python $PythonScript
    }
    exit $LASTEXITCODE
}
catch {
    Write-Error "Failed to run recovery script: $_"
    Write-Host ""
    Write-Host "Manual recovery steps:" -ForegroundColor Yellow
    Write-Host "1. Rename .claude/settings.local.json to .claude/settings.local.json.bak"
    Write-Host "2. Create new .claude/settings.local.json with minimal content:"
    Write-Host '   { "hooks": {} }'
    Write-Host "3. Restart Claude Code"
    exit 1
}
