# Sim.ai Deployment Guide

## Overview

This document provides complete deployment instructions for the Sim.ai PoC platform.

**Primary Tool:** `deploy.ps1` - PowerShell script for all deployment operations.

---

## Prerequisites

1. **Docker Desktop** - Running with WSL2 backend
2. **PowerShell** - Version 5.1+ (Windows default)
3. **Git** - For version control
4. **Python 3.10+** - For tests (optional)

---

## Environment Setup

```powershell
# 1. Clone repository
git clone https://github.com/drlegreid/platform-gai.git
cd platform-gai

# 2. Configure environment
cp .env.example .env
notepad .env  # Set your ANTHROPIC_API_KEY
```

### Required Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude API key |
| `XAI_API_KEY` | No | Grok API key (optional) |
| `LITELLM_MASTER_KEY` | Yes | LiteLLM proxy auth |
| `CHROMA_AUTH_TOKEN` | Yes | ChromaDB auth token |

---

## Deployment Commands

### deploy.ps1 Actions

| Action | Description | Example |
|--------|-------------|---------|
| `up` | Start all services | `.\deploy.ps1 -Action up` |
| `down` | Stop all services | `.\deploy.ps1 -Action down` |
| `status` | Show container status | `.\deploy.ps1 -Action status` |
| `logs` | Tail service logs | `.\deploy.ps1 -Action logs` |
| `health` | Run health checks | `.\deploy.ps1 -Action health` |
| `test` | Run pytest suite | `.\deploy.ps1 -Action test` |
| `pull-models` | Pull Ollama models | `.\deploy.ps1 -Action pull-models` |
| `opik` | Start Opik dashboard | `.\deploy.ps1 -Action opik` |
| `rebuild` | Rebuild containers | `.\deploy.ps1 -Action rebuild` |

### Profiles

| Profile | Services | Use Case |
|---------|----------|----------|
| `cpu` | Core services (no UI) | Laptop/development |
| `full` | All services + Agent UI | Server/production |

```powershell
# CPU profile (default)
.\deploy.ps1 -Action up -Profile cpu

# Full profile with UI
.\deploy.ps1 -Action up -Profile full

# Dev profile with live reload
docker compose --profile dev up -d
```

---

## Development vs Production Mode

### Overview

The Governance Dashboard has two deployment modes to support different workflows:

| Mode | Container | Port | Code Loading | Use Case |
|------|-----------|------|--------------|----------|
| **Production** | `governance-dashboard` | 8081 | Baked into image | CI/CD, demos, testing |
| **Development** | `governance-dashboard-dev` | 8081 | Volume-mounted | Live code editing |

### Port Conflict Warning

**Both modes use port 8081 - they are mutually exclusive.**

Only one dashboard container can run at a time. Docker will fail to start the second container with a port binding error.

### Production Mode (cpu/full profiles)

Code is baked into the Docker image at build time.

```powershell
# Start production dashboard
.\deploy.ps1 -Action up -Profile cpu

# Or rebuild with latest code
.\deploy.ps1 -Action rebuild
```

**When to use:**
- Running automated tests
- CI/CD pipelines
- Demos and presentations
- Verifying changes work in container

### Development Mode (dev profile)

Code is volume-mounted from local filesystem for live editing.

```powershell
# Stop production dashboard first (if running)
docker stop sim-ai-governance-dashboard-1

# Start development dashboard
docker compose --profile dev up -d governance-dashboard-dev

# Verify it's running
docker ps | Select-String governance-dashboard-dev
```

**Volume Mounts (read-only):**
```
./agent      → /app/agent
./governance → /app/governance
./docs       → /app/docs
./evidence   → /app/evidence
```

**When to use:**
- Active development
- Debugging UI issues
- Testing code changes without rebuilding

### Switching Between Modes

```powershell
# From prod to dev
docker stop sim-ai-governance-dashboard-1
docker compose --profile dev up -d governance-dashboard-dev

# From dev to prod
docker stop sim-ai-governance-dashboard-dev-1
.\deploy.ps1 -Action up -Profile cpu

# Or just rebuild and restart
.\deploy.ps1 -Action rebuild
```

### Verifying Which Mode is Running

```powershell
# List running containers
docker ps --format "table {{.Names}}\t{{.Status}}"

# Should see ONE of:
# - sim-ai-governance-dashboard-1     (production)
# - sim-ai-governance-dashboard-dev-1 (development)
```

---

## Full Deployment Sequence

```powershell
# 1. Start core services
.\deploy.ps1 -Action up -Profile cpu

# 2. Wait for services to initialize
Start-Sleep -Seconds 30

# 3. Pull Ollama models (first time only)
.\deploy.ps1 -Action pull-models

# 4. Verify health
.\deploy.ps1 -Action health

# 5. Run tests
.\deploy.ps1 -Action test

# 6. (Optional) Start Opik monitoring
.\deploy.ps1 -Action opik
```

---

## Service Endpoints

| Service | Port | Health Endpoint |
|---------|------|-----------------|
| Agents API | 7777 | `/health` |
| LiteLLM | 4000 | `/health` |
| ChromaDB | 8001 | `/api/v2/heartbeat` |
| Ollama | 11434 | `/api/tags` |
| Opik UI | 5173 | N/A |
| Agent UI | 3000 | N/A (full profile) |

---

## Troubleshooting

### Docker not running
```powershell
# Start Docker Desktop manually or:
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
```

### Container unhealthy
```powershell
# Check logs
.\deploy.ps1 -Action logs

# Rebuild from scratch
.\deploy.ps1 -Action down
.\deploy.ps1 -Action rebuild
```

### Ollama model not found
```powershell
# Pull models explicitly
docker exec sim-ai-ollama-1 ollama pull gemma3:4b
```

### ChromaDB connection failed
```powershell
# Check ChromaDB is running
docker ps | Select-String chromadb

# Restart ChromaDB
docker restart sim-ai-chromadb-1
```

---

## CI/CD Integration

### GitHub Actions (Example)

```yaml
name: Deploy Sim.ai
on:
  push:
    branches: [master]

jobs:
  deploy:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        run: |
          cp .env.example .env
          # Set secrets via GitHub Secrets
          .\deploy.ps1 -Action up
          .\deploy.ps1 -Action health
          .\deploy.ps1 -Action test
```

---

## Related Documentation

- [README.md](../README.md) - Project overview
- [CLAUDE.md](../CLAUDE.md) - Project rules
- [TODO.md](../TODO.md) - Task tracking
- [RULES-DIRECTIVES.md](./RULES-DIRECTIVES.md) - Governance rules

---

**Last Updated:** 2024-12-31
