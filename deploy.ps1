<#
.SYNOPSIS
    Sim.ai PoC Deployment Script for Windows
.DESCRIPTION
    Deploys the full stack: Ollama + LiteLLM + Opik + ChromaDB + Agents
    Optimized for i7/16GB laptop with CPU-only profile
.PARAMETER Profile
    Deployment profile: 'cpu' (default), 'full' (with UI)
.PARAMETER Action
    Action: 'up', 'down', 'status', 'logs', 'pull-models'
.EXAMPLE
    .\deploy.ps1 -Action up -Profile cpu
#>

param(
    [ValidateSet('cpu', 'full')]
    [string]$Profile = 'cpu',
    
    [ValidateSet('up', 'down', 'status', 'logs', 'pull-models', 'health')]
    [string]$Action = 'up'
)

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== Sim.ai PoC Deployment ===" -ForegroundColor Cyan
Write-Host "Profile: $Profile | Action: $Action" -ForegroundColor Gray

# Check prerequisites
function Test-Prerequisites {
    Write-Host "`nChecking prerequisites..." -ForegroundColor Yellow
    
    # Docker
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error "Docker not found. Install Docker Desktop first."
        exit 1
    }
    
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker daemon not running. Start Docker Desktop."
        exit 1
    }
    Write-Host "  [OK] Docker running" -ForegroundColor Green
    
    # .env file
    $envFile = Join-Path $ScriptDir ".env"
    if (-not (Test-Path $envFile)) {
        Write-Host "  [!] .env not found, copying from .env.example" -ForegroundColor Yellow
        Copy-Item (Join-Path $ScriptDir ".env.example") $envFile
        Write-Host "  [!] Edit .env and set ANTHROPIC_API_KEY before continuing" -ForegroundColor Red
        exit 1
    }
    Write-Host "  [OK] .env exists" -ForegroundColor Green
    
    # Check API key is set
    $envContent = Get-Content $envFile -Raw
    if ($envContent -match "ANTHROPIC_API_KEY=sk-ant-your-key-here") {
        Write-Error ".env has placeholder API key. Set your real ANTHROPIC_API_KEY."
        exit 1
    }
    Write-Host "  [OK] API key configured" -ForegroundColor Green
}

# Pull Ollama models
function Install-OllamaModels {
    Write-Host "`nPulling Ollama models (this may take a while)..." -ForegroundColor Yellow
    
    # Start Ollama container if not running
    docker compose --profile cpu up -d ollama
    Start-Sleep -Seconds 5
    
    # Pull lightweight model for CPU
    Write-Host "  Pulling gemma3:4b (CPU-friendly)..." -ForegroundColor Gray
    docker exec sim-ai-ollama-1 ollama pull gemma3:4b
    
    Write-Host "  [OK] Models ready" -ForegroundColor Green
}

# Deploy stack
function Start-Stack {
    Test-Prerequisites
    
    Write-Host "`nStarting services with profile: $Profile" -ForegroundColor Yellow
    
    # Create data directories
    $dataDir = Join-Path $ScriptDir "data"
    if (-not (Test-Path $dataDir)) {
        New-Item -ItemType Directory -Path $dataDir | Out-Null
    }
    
    # Start stack
    docker compose --profile $Profile up -d --build
    
    Write-Host "`nWaiting for services to be healthy..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    Show-Status
}

# Stop stack
function Stop-Stack {
    Write-Host "`nStopping all services..." -ForegroundColor Yellow
    docker compose --profile $Profile down
    Write-Host "  [OK] Stack stopped" -ForegroundColor Green
}

# Show status
function Show-Status {
    Write-Host "`n=== Service Status ===" -ForegroundColor Cyan
    docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
    
    Write-Host "`n=== Endpoints ===" -ForegroundColor Cyan
    Write-Host "  Agents API:  http://localhost:7777" -ForegroundColor White
    Write-Host "  LiteLLM:     http://localhost:4000" -ForegroundColor White
    Write-Host "  Opik UI:     http://localhost:5173" -ForegroundColor White
    Write-Host "  ChromaDB:    http://localhost:8001" -ForegroundColor White
    Write-Host "  Ollama:      http://localhost:11434" -ForegroundColor White
    if ($Profile -eq 'full') {
        Write-Host "  Agent UI:    http://localhost:3000" -ForegroundColor White
    }
}

# Show logs
function Show-Logs {
    param([string]$Service = '')
    
    if ($Service) {
        docker compose logs -f $Service
    } else {
        docker compose logs -f --tail 50
    }
}

# Health check
function Test-Health {
    Write-Host "`n=== Health Checks ===" -ForegroundColor Cyan
    
    $endpoints = @{
        'LiteLLM' = 'http://localhost:4000/health'
        'ChromaDB' = 'http://localhost:8001/api/v1/heartbeat'
        'Ollama' = 'http://localhost:11434/api/tags'
        'Agents' = 'http://localhost:7777/health'
    }
    
    foreach ($svc in $endpoints.Keys) {
        try {
            $response = Invoke-WebRequest -Uri $endpoints[$svc] -TimeoutSec 5 -ErrorAction SilentlyContinue
            Write-Host "  [OK] $svc" -ForegroundColor Green
        } catch {
            Write-Host "  [X] $svc - Not responding" -ForegroundColor Red
        }
    }
}

# Main
switch ($Action) {
    'up' { Start-Stack }
    'down' { Stop-Stack }
    'status' { Show-Status }
    'logs' { Show-Logs }
    'pull-models' { Install-OllamaModels }
    'health' { Test-Health }
}

Write-Host "`nDone." -ForegroundColor Cyan
