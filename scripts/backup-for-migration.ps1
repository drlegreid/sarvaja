# Migration Script for Windows to Ubuntu
# Per RULE-024: AMNESIA Protocol
# Created: 2026-01-04
#
# This script:
#   1. Stops Docker Desktop
#   2. MOVES (not copies) all data to target location
#   3. Leaves source directories EMPTY
#
# Usage: .\scripts\backup-for-migration.ps1 -TargetPath "E:\saveNatikLaptop2\#COding"

param(
    [Parameter(Mandatory=$true)]
    [string]$TargetPath,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  SIM.AI MIGRATION SCRIPT" -ForegroundColor Cyan
Write-Host "  Target: $TargetPath" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "WARNING: This will MOVE all data (not copy)!" -ForegroundColor Red
Write-Host "Source directories will be EMPTIED after migration." -ForegroundColor Red
Write-Host ""

if (-not $Force) {
    $confirm = Read-Host "Type 'MIGRATE' to confirm"
    if ($confirm -ne "MIGRATE") {
        Write-Host "Migration cancelled." -ForegroundColor Yellow
        exit 0
    }
}

# Define paths
$vibeSource = "C:\Users\natik\Documents\Vibe"
$claudeMemSource = "C:\Users\natik\.claude-mem"
$vibeTarget = Join-Path $TargetPath "Vibe"
$dockerTarget = Join-Path $TargetPath "Docker"
$claudeMemTarget = Join-Path $TargetPath ".claude-mem"

# ============================================
# STEP 1: Stop Docker Desktop
# ============================================
Write-Host "`n[1/6] Stopping Docker Desktop..." -ForegroundColor Yellow

# Stop all containers first
Write-Host "  Stopping all containers..." -ForegroundColor Gray
docker stop $(docker ps -q) 2>$null
Start-Sleep -Seconds 3

# Export Docker volumes BEFORE stopping Docker Desktop
Write-Host "`n[2/6] Exporting Docker volumes (while Docker is running)..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $dockerTarget | Out-Null

$volumes = @(
    @{Name="sim-ai_typedb_data"; Target="typedb_data"},
    @{Name="sim-ai_chromadb_data"; Target="chromadb_data"},
    @{Name="sim-ai_ollama_data"; Target="ollama_data"},
    @{Name="claude-memory"; Target="claude_memory"}
)

foreach ($vol in $volumes) {
    $volName = $vol.Name
    $volTarget = Join-Path $dockerTarget $vol.Target

    Write-Host "  Exporting $volName..." -ForegroundColor Gray

    $exists = docker volume inspect $volName 2>$null
    if ($LASTEXITCODE -eq 0) {
        New-Item -ItemType Directory -Force -Path $volTarget | Out-Null
        docker run --rm -v "${volName}:/source:ro" -v "${volTarget}:/backup" alpine sh -c "cp -r /source/* /backup/ 2>/dev/null || true"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    $volName exported" -ForegroundColor Green
        }
    } else {
        Write-Host "    SKIP: $volName not found" -ForegroundColor Yellow
    }
}

# Now stop Docker Desktop
Write-Host "`n[3/6] Stopping Docker Desktop..." -ForegroundColor Yellow
$dockerDesktop = Get-Process "Docker Desktop" -ErrorAction SilentlyContinue
if ($dockerDesktop) {
    Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 5
    Write-Host "  Docker Desktop stopped" -ForegroundColor Green
} else {
    Write-Host "  Docker Desktop not running" -ForegroundColor Gray
}

# ============================================
# STEP 4: Create target and MOVE Vibe directory
# ============================================
Write-Host "`n[4/6] Moving Vibe directory..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $vibeTarget | Out-Null

if (Test-Path $vibeSource) {
    $items = Get-ChildItem -Path $vibeSource -Force
    $total = $items.Count
    $current = 0

    foreach ($item in $items) {
        $current++
        Write-Host "  [$current/$total] $($item.Name)" -ForegroundColor Gray
        Move-Item -Path $item.FullName -Destination $vibeTarget -Force
    }

    # Remove empty source
    Remove-Item -Path $vibeSource -Force -ErrorAction SilentlyContinue
    Write-Host "  Vibe moved. Source cleared." -ForegroundColor Green
} else {
    Write-Host "  WARNING: $vibeSource not found" -ForegroundColor Red
}

# ============================================
# STEP 5: MOVE claude-mem directory
# ============================================
Write-Host "`n[5/6] Moving claude-mem directory..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $claudeMemTarget | Out-Null

if (Test-Path $claudeMemSource) {
    $items = Get-ChildItem -Path $claudeMemSource -Force
    $total = $items.Count
    $current = 0

    foreach ($item in $items) {
        $current++
        Write-Host "  [$current/$total] $($item.Name)" -ForegroundColor Gray
        Move-Item -Path $item.FullName -Destination $claudeMemTarget -Force
    }

    Remove-Item -Path $claudeMemSource -Force -ErrorAction SilentlyContinue
    Write-Host "  Claude-mem moved. Source cleared." -ForegroundColor Green
} else {
    Write-Host "  WARNING: $claudeMemSource not found" -ForegroundColor Red
}

# ============================================
# STEP 6: Create inventory
# ============================================
Write-Host "`n[6/6] Creating migration inventory..." -ForegroundColor Yellow

$inventory = @{
    MigrationDate = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    SourceMachine = $env:COMPUTERNAME
    TargetPath = $TargetPath
    Type = "MOVE (sources cleared)"
    Components = @{
        Vibe = Test-Path $vibeTarget
        ClaudeMem = Test-Path $claudeMemTarget
        TypeDBData = Test-Path (Join-Path $dockerTarget "typedb_data")
        ChromaDBData = Test-Path (Join-Path $dockerTarget "chromadb_data")
    }
    RecoveryDoc = "Vibe\sim-ai\sim-ai\docs\RECOVERY.md"
}

$inventoryPath = Join-Path $TargetPath "MIGRATION_INVENTORY.json"
$inventory | ConvertTo-Json -Depth 3 | Out-File -FilePath $inventoryPath -Encoding UTF8

# ============================================
# Summary
# ============================================
Write-Host "`n============================================" -ForegroundColor Green
Write-Host "  MIGRATION COMPLETE" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Data moved to: $TargetPath" -ForegroundColor White
Write-Host ""
Write-Host "Contents:" -ForegroundColor White
Write-Host "  Vibe\        - All project files"
Write-Host "  .claude-mem\ - Memory database"
Write-Host "  Docker\      - Volume exports (TypeDB, ChromaDB, Ollama)"
Write-Host ""
Write-Host "Recovery: $TargetPath\Vibe\sim-ai\sim-ai\docs\RECOVERY.md" -ForegroundColor Cyan
Write-Host ""
Write-Host "Docker Desktop is STOPPED." -ForegroundColor Yellow
Write-Host ""
