# Production Deployment Guide - Sarvaja Dashboard

**Created:** 2026-01-21 | **Source:** EPIC-DR task DR-006
**Reference:** [DEVOPS.md](DEVOPS.md) for development environment

---

## Pre-Deployment Checklist

| Item | Check | Notes |
|------|-------|-------|
| Test suite passes | `pytest tests/ -v` | 306 unit, 65 e2e, 2 robot |
| TypeDB schema seeded | `python3 governance/seed_data.py` | Run after fresh install |
| No CRITICAL gaps | `gaps_critical()` | 0 critical gaps |
| Docker/Podman available | `podman version` | Rootless mode supported |

---

## Container Architecture

```
Production Stack (5 containers)
├── dashboard:8081,8082   # Trame UI + FastAPI
├── typedb:1729          # Rule inference (REQUIRED)
├── chromadb:8001        # Semantic search (REQUIRED)
├── litellm:4000         # Model proxy (OPTIONAL)
└── ollama:11434         # Local LLM (OPTIONAL)
```

---

## Quick Start

```bash
# 1. Clone and configure
git clone https://github.com/drlegreid/platform-gai.git
cd platform-gai
cp .env.example .env

# 2. Start core services
podman compose --profile dev up -d typedb chromadb

# 3. Wait for TypeDB (30s startup)
sleep 30
curl -s http://localhost:8001/api/v2/heartbeat  # ChromaDB

# 4. Seed TypeDB schema
source .venv/bin/activate  # Or: python3 -m venv .venv && source...
PYTHONPATH=. python3 governance/seed_data.py

# 5. Start dashboard
podman compose --profile dev up -d dashboard

# 6. Verify
curl -s http://localhost:8082/api/health
```

---

## Environment Configuration

### Required Variables (.env)

```bash
# TypeDB Connection
TYPEDB_HOST=typedb      # Container name or IP
TYPEDB_PORT=1729
TYPEDB_DATABASE=governance

# ChromaDB Connection
CHROMADB_HOST=chromadb  # Container name or IP
CHROMADB_PORT=8001

# Dashboard Settings
DASHBOARD_HOST=0.0.0.0  # Bind to all interfaces
DASHBOARD_PORT=8081     # UI port
API_PORT=8082           # REST API port
```

### Optional Variables

```bash
# LiteLLM (model proxy)
LITELLM_MASTER_KEY=sk-litellm-master-key
LITELLM_PORT=4000

# Ollama (local LLM)
OLLAMA_HOST=ollama
OLLAMA_PORT=11434
```

---

## Health Monitoring

### Health Endpoints

| Service | URL | Expected |
|---------|-----|----------|
| Dashboard API | `http://HOST:8082/api/health` | `{"status": "healthy"}` |
| TypeDB | MCP `health_check()` | `{"status": "healthy"}` |
| ChromaDB | `http://HOST:8001/api/v2/heartbeat` | `{"nanosecond heartbeat": ...}` |
| LiteLLM | `http://HOST:4000/health` | `{"status": "healthy"}` |

### Health Check Script

```bash
#!/bin/bash
# health-check.sh

check() {
    curl -sf "$1" > /dev/null && echo "OK: $2" || echo "FAIL: $2"
}

check "http://localhost:8082/api/health" "Dashboard API"
check "http://localhost:8001/api/v2/heartbeat" "ChromaDB"
check "http://localhost:4000/health" "LiteLLM"
```

---

## Container Management

### Start Services

```bash
# Start all production services
podman compose --profile dev up -d

# Start only required services (minimal)
podman compose --profile dev up -d typedb chromadb dashboard
```

### Stop Services

```bash
# Graceful stop
podman compose --profile dev stop

# Full teardown (removes containers)
podman compose --profile dev down
```

### Logs

```bash
# Dashboard logs
podman logs platform_dashboard_1 --tail 100 -f

# All service logs
podman compose --profile dev logs -f
```

### Restart

```bash
# Restart single service
podman restart platform_dashboard_1

# Restart all
podman compose --profile dev restart
```

---

## Persistence

### Data Volumes

| Path | Purpose | Backup Priority |
|------|---------|-----------------|
| `/home/oderid/Documents/Docker/typedb/` | TypeDB data | HIGH |
| `/home/oderid/Documents/Docker/chromadb/` | ChromaDB embeddings | MEDIUM |
| `./evidence/` | Session evidence files | HIGH |

### Backup Commands

```bash
# Backup TypeDB data
tar -czf typedb-backup-$(date +%Y%m%d).tar.gz \
    /home/oderid/Documents/Docker/typedb/

# Backup evidence
tar -czf evidence-backup-$(date +%Y%m%d).tar.gz ./evidence/
```

---

## Troubleshooting

### Dashboard Won't Start

```bash
# Check container status
podman compose --profile dev ps

# Check for port conflicts
ss -tlnp | grep -E '808[12]'

# View startup logs
podman logs platform_dashboard_1 --tail 200
```

### TypeDB Connection Failed

```bash
# Verify TypeDB is running
podman exec platform_typedb_1 /opt/typedb-core-all/typedb console

# Check port availability
curl -v telnet://localhost:1729

# Reseed if corrupted
PYTHONPATH=. python3 governance/seed_data.py
```

### API Returns 500

```bash
# Check API logs for stack trace
podman logs platform_dashboard_1 2>&1 | grep -A 10 "Error"

# Verify database connectivity
curl http://localhost:8082/api/rules  # Should return list
```

### Read-Only Filesystem Errors

The dashboard container uses read-only mounts for security. If you see:
```
[Errno 30] Read-only file system
```

This is expected for non-critical operations (metrics persistence). Critical operations will fall back to in-memory stores.

---

## Security Considerations

### Network Exposure

| Port | Expose Externally? | Notes |
|------|--------------------|-------|
| 8081 | YES | Dashboard UI |
| 8082 | YES (with auth) | REST API |
| 1729 | NO | TypeDB (internal only) |
| 8001 | NO | ChromaDB (internal only) |

### Recommended Reverse Proxy

```nginx
# nginx.conf snippet
server {
    listen 443 ssl;
    server_name dashboard.example.com;

    location / {
        proxy_pass http://localhost:8081;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /api/ {
        proxy_pass http://localhost:8082;
        # Add authentication here
    }
}
```

---

## Upgrade Procedure

```bash
# 1. Pull latest code
git pull origin master

# 2. Stop services
podman compose --profile dev stop

# 3. Rebuild if Dockerfile changed
podman compose --profile dev build dashboard

# 4. Start services
podman compose --profile dev up -d

# 5. Verify health
curl http://localhost:8082/api/health
```

---

## Test Verification

Before declaring production-ready, verify:

```bash
# Run full test suite
python3 -m pytest tests/ -v

# Expected results (2026-01-21):
# - 306 unit tests passed
# - 65 e2e tests passed
# - 2 robot tests passed
# - 1 xfailed (data quality - backfill needed)
```

---

*Per EPIC-DR task DR-006: Production deployment documentation*
*Per TEST-COMP-02-v1: Test Before Ship*
