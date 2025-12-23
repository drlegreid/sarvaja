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

**Last Updated:** 2024-12-24
