<#
.SYNOPSIS
    MCP Configuration Backup Script (PowerShell Wrapper)

.DESCRIPTION
    Creates timestamped backups of MCP configuration files and manages restoration.

.PARAMETER BackupOnly
    Only create backup, don't show status

.PARAMETER Restore
    Restore from a specific backup file

.PARAMETER List
    List available backup files

.PARAMETER Status
    Show current MCP configuration status

.EXAMPLE
    .\mcp-backup.ps1
    # Show status and create backup

.EXAMPLE
    .\mcp-backup.ps1 -List
    # List available backups

.EXAMPLE
    .\mcp-backup.ps1 -Restore mcp-backup.20260104_123456.json
    # Restore from specific backup

.NOTES
    Per R&D TOOL-009: MCP optimization for memory management.
#>

param(
    [switch]$BackupOnly,
    [string]$Restore,
    [switch]$List,
    [switch]$Status,
    [switch]$Help
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonScript = Join-Path $ScriptDir "mcp-backup.py"

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

if ($Status) {
    $args += "--status"
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
    Write-Error "Failed to run MCP backup script: $_"
    exit 1
}
