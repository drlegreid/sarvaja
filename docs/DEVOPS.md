# DevOps Reference - Sarvaja

> **Parent:** [CLAUDE.md](../CLAUDE.md) | **Rule:** RULE-031, RULE-035, RULE-037
> **Last Updated:** 2026-01-12

---

## Container Runtime (CRITICAL)

**USE PODMAN, NOT DOCKER** - xubuntu migration 2026-01-09

| Command | Use Instead |
|---------|-------------|
| `docker` | `podman` |
| `docker-compose` | `podman compose` |
| `docker ps` | `podman compose --profile cpu ps` |

Data persistence: `/home/oderid/Documents/Docker/` (bind mounts)

### Podman Compose Configuration

Podman is configured to use `podman-compose` (Python package) instead of `docker-compose`:

```bash
# Configuration file: ~/.config/containers/containers.conf
[engine]
compose_providers = ["/home/oderid/.venv/sarvaja/bin/podman-compose"]
```

If `podman compose` shows "docker-compose" warning, install podman-compose:
```bash
source ~/.venv/sarvaja/bin/activate
pip install podman-compose
```

---

## CORE Dependencies

```
CORE_SERVICES = ["podman", "typedb", "chromadb"]
- Podman must be running (rootless mode)
- TypeDB (port 1729) - Rule inference engine
- ChromaDB (port 8001) - Semantic search for claude-mem
```

---

## Container Persistence (GAP-PERSIST-001)

**CRITICAL: Containers survive reboot only if these are configured:**

### 1. Linger Enabled (for rootless Podman)

```bash
# Check status
loginctl show-user $(whoami) --property=Linger

# Enable (REQUIRED - one-time setup)
loginctl enable-linger $(whoami)
```

Without linger, all containers stop when user logs out.

### 2. Restart Policies in docker-compose.yml

All services must have `restart: unless-stopped`:

```yaml
services:
  typedb:
    restart: unless-stopped  # Survives reboot
  chromadb:
    restart: unless-stopped
  # ... all other services
```

### 3. Podman Socket Enabled

```bash
# Enable (one-time setup)
systemctl --user enable podman.socket

# Check status
systemctl --user is-enabled podman.socket
```

---

## Container Profiles (CRITICAL)

| Profile | Use Case | Volume Mounts | Rebuild Needed |
|---------|----------|---------------|----------------|
| `dev` | Development | ✅ Yes | ❌ No |
| `cpu` | Production | ❌ No | ✅ Yes |

### DEV Profile - Live Reload (ALWAYS USE FOR DEVELOPMENT)

```bash
# Start with DEV profile - NO REBUILD NEEDED
podman compose --profile dev up -d

# Volume mounts enable live code changes:
#   ./agent:/app/agent:ro       - Dashboard UI code
#   ./governance:/app/governance:ro - MCP tools
#   ./docs:/app/docs:ro         - Documentation
#   ./evidence:/app/evidence:rw - Evidence output

# Ports
# 8081 = UI (Trame dashboard)
# 8082 = API (REST endpoints)
```

### Key Benefit: No Image Rebuild

Code changes in `agent/`, `governance/`, or `docs/` are **immediately reflected** without rebuilding. Just save and refresh.

> ⚠️ **WARNING**: PROD (`--profile cpu`) doesn't reflect code changes. This mistake has occurred 5+ times.

### When to Rebuild

Only rebuild when:
- `Dockerfile.dashboard` changes
- Python dependencies change (`requirements.txt`)
- System packages change

```bash
# Rebuild and start (only when Dockerfile changes)
podman compose --profile dev up -d --build
```

---

## MCP Server Containers (RULE-037)

MCP servers run in containers due to TypeDB driver Python version requirements.

```bash
# Build MCP container (Python 3.12)
podman build -f Dockerfile.mcp -t sarvaja-mcp:latest .

# MCP servers use scripts/mcp-runner.sh with container mode
MCP_MODE=container  # Default, uses containerized Python 3.12
MCP_MODE=venv       # Fallback to local venv
```

> Per RULE-037: Validate fixes in target environment before declaring ready

---

## Command Hierarchy

| Priority | Method | When to Use |
|----------|--------|-------------|
| 1 | `podman compose` | Standard container operations |
| 2 | `scripts/mcp-runner.sh` | MCP server management |
| 3 | Individual | Surgical container control |

### Podman Compose Commands

```bash
# Start CORE services only
podman compose --profile cpu up -d typedb chromadb

# Start all services
podman compose --profile cpu up -d

# Check running containers
podman compose --profile cpu ps

# View container logs
podman logs sarvaja-typedb-1 --tail 50

# Restart specific container
podman restart sarvaja-typedb-1

# Stop all
podman compose --profile cpu down
```

---

## Health Check Endpoints

| Service | Endpoint | Auth |
|---------|----------|------|
| TypeDB | `health_check()` | MCP |
| LiteLLM | `http://localhost:4000/health` | Bearer token |
| ChromaDB | `http://localhost:8001/api/v2/heartbeat` | None |
| Ollama | `http://localhost:11434/api/tags` | None |
| Agents | `http://localhost:7777/health` | None |
| Dashboard API | `http://localhost:8082/api/health` | None |

```bash
# Bash health checks (xubuntu)
curl -s http://localhost:8001/api/v2/heartbeat | jq
curl -s http://localhost:11434/api/tags | jq
curl -s http://localhost:7777/health | jq
curl -s -H "Authorization: Bearer sk-litellm-master-key" http://localhost:4000/health
```

---

## Key Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Stack orchestration (podman compatible) |
| `Dockerfile.mcp` | MCP server container (Python 3.12) |
| `scripts/mcp-runner.sh` | MCP server launcher |
| `config/litellm_config.yaml` | Model routing |
| `agents.yaml` | Agent definitions |
| `agent/playground.py` | Agent server code |
| `.env.example` | Environment template |

---

## Quick Deployment

```bash
# DEV mode - Full sequence (xubuntu)
podman compose --profile dev up -d

# PROD mode - Full sequence (when needed)
podman compose --profile cpu up -d
podman compose exec ollama ollama pull llama3.2:3b

# Seed TypeDB (after fresh install or data corruption)
source ~/.venv/sarvaja/bin/activate
PYTHONPATH=. python governance/seed_data.py

# Verify MCP health
health_check()  # Via Claude Code MCP

# Push to GitHub (excludes credentials)
git add -A && git commit -m "message" && git push origin master
```

---

## Pre-commit Hooks (GAP-009)

Code quality enforcement via pre-commit hooks.

### Setup (One-time)

```bash
source ~/.venv/sarvaja/bin/activate
pip install pre-commit
pre-commit install
```

### What's Enforced

| Hook | Purpose |
|------|---------|
| trailing-whitespace | Remove trailing spaces |
| end-of-file-fixer | Ensure newline at EOF |
| check-yaml/json | Validate syntax |
| black | Python formatting |
| isort | Import sorting |
| ruff | Python linting |
| detect-secrets | Security check |
| no-commit-to-branch | Block direct main/master commits |

### Manual Run

```bash
pre-commit run --all-files  # Check all
pre-commit run black        # Single hook
```

---

## Test Profiles (GAP-TEST-PROFILES)

Tests are organized by dependency requirements using pytest markers.

### Available Profiles

| Marker | Environment | Dependencies | Command |
|--------|-------------|--------------|---------|
| `unit` | Container OR Host | None | `pytest -m unit` |
| `integration` | Host | TypeDB, ChromaDB | `pytest -m integration` |
| `e2e` | Host | All services | `pytest -m e2e` |
| `browser` | Host + Display | pytest-playwright | `pytest -m browser --headed` |
| `api` | Host | REST server :8082 | `pytest -m api` |

### Auto-Marking

Tests are automatically marked based on path:
- `tests/unit/*` → `unit`
- `tests/integration/*` → `integration`
- `tests/e2e/*` → `e2e`
- Files with `playwright` imports → `browser`

### Running Tests

```bash
# Container-safe (no external deps)
scripts/pytest.sh tests/ -m "unit"

# Host-only (needs services)
python3 -m pytest tests/ -m "integration"

# Host-only with browser
python3 -m pytest tests/ -m "browser" --headed

# Exclude browser tests
python3 -m pytest tests/ -m "not browser"

# Run all E2E except browser
python3 -m pytest tests/e2e/ -m "e2e and not browser"
```

### Why Container Tests Fail (Legacy)

Old issue: `scripts/pytest.sh` runs in isolated container that can't reach host services.

**Solutions:**
1. **Containerized Tests (Recommended):** Use `test-runner` service with proper networking
2. **Host Tests:** Run `python3 -m pytest` directly on host
3. **Unit Only:** Use markers `scripts/pytest.sh -m unit`

---

## Containerized Testing (Option B)

Full container networking for tests using `test-runner` service.

### Quick Start

```bash
# Ensure services are running
podman compose --profile dev up -d

# Run all tests (except browser)
./scripts/test-container.sh

# Run specific test file
./scripts/test-container.sh tests/integration/test_mcp_rest_sessions.py

# Run with markers
./scripts/test-container.sh -m "integration"

# Rebuild image first
./scripts/test-container.sh --build tests/
```

### Direct Podman Usage

```bash
# Run with custom command
podman compose --profile test run --rm test-runner \
    python3 -m pytest tests/integration -v -s

# Interactive shell in test container
podman compose --profile test run --rm test-runner bash
```

### Volume Mounts

Test container mounts local dev assets:
- `./tests:/app/tests:ro` - Test code
- `./governance:/app/governance:ro` - MCP tools
- `./shared:/app/shared:ro` - Shared constants
- `./results:/app/results:rw` - Test results output

### Environment Variables

Container uses service names via env vars:
- `TYPEDB_HOST=typedb` (not localhost)
- `CHROMADB_HOST=chromadb`
- `CHROMADB_PORT=8000` (internal port)

---

## E2E Testing (RULE-037)

Browser tests require dashboard running on port 8081.

```bash
# Install browser (Flatpak recommended)
flatpak install flathub org.mozilla.firefox

# Or via Playwright
source ~/.venv/sarvaja/bin/activate
playwright install firefox

# Run E2E tests
pytest tests/e2e/ -v --browser firefox
```

---

*Per RULE-031: DevOps commands reference*
*Per RULE-035: Shell command environment selection*
*Per RULE-037: Fix Validation Protocol*
