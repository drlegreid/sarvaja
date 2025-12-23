# Sim.ai PoC Project Rules

## Quick Context
- **Project**: Multi-agent platform with LiteLLM, ChromaDB, Opik
- **Location**: `C:\Users\natik\Documents\Vibe\sim-ai\sim-ai`
- **Repo**: https://github.com/drlegreid/platform-gai
- **Updated**: 2024-12-24

## Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                      Sim.ai PoC Stack                       │
├─────────────────────────────────────────────────────────────┤
│  Agents (7777)  │  LiteLLM (4000)  │  Opik (5173/5174)     │
├─────────────────────────────────────────────────────────────┤
│  ChromaDB (8001)  │  Ollama (11434)                        │
└─────────────────────────────────────────────────────────────┘
```

## Core Rules
1. **Session Evidence**: Every session produces `./docs/SESSION-{date}-{topic}.md`
2. **Rules Governance**: Follow `./docs/RULES-DIRECTIVES.md` (RULE-001, RULE-002)
3. **Gaps as Tasks**: Track gaps in `./TODO.md` with priority/status
4. **Tests First**: Run `pytest tests/ -v` before claiming completion
5. **Credential Safety**: Never commit `.env` - use `.env.example` template

## Running Services
```powershell
# Start stack
docker compose --profile cpu up -d

# Check status
docker ps --format "table {{.Names}}\t{{.Status}}"

# View logs
docker compose --profile cpu logs -f

# Run tests
pytest tests/ -v --tb=short
```

## Key Files
| File | Purpose |
|------|---------|
| `docker-compose.yml` | Stack orchestration |
| `config/litellm_config.yaml` | Model routing |
| `agents.yaml` | Agent definitions |
| `agent/playground.py` | Agent server code |
| `agent/sync_agent.py` | Sync agent skeleton |
| `.env.example` | Environment template |

## Health Checks
```powershell
# LiteLLM
Invoke-WebRequest -Uri "http://localhost:4000/health" -Headers @{Authorization="Bearer sk-litellm-master-key-change-me"}

# ChromaDB
Invoke-WebRequest -Uri "http://localhost:8001/api/v2/heartbeat"

# Ollama
Invoke-WebRequest -Uri "http://localhost:11434/api/tags"

# Agents
Invoke-WebRequest -Uri "http://localhost:7777/health"
```

## Session Directives
- **Evidence Trail**: Document decisions and rationale in session logs
- **Gap Tracking**: Add discovered gaps to TODO.md immediately
- **Test Coverage**: Update tests when fixing issues
- **Sync to GitHub**: Push significant changes to drlegreid/platform-gai

## Quick Commands
```powershell
# Start Opik dashboard
cd opik; .\opik.ps1

# Pull Ollama model
docker exec sim-ai-ollama-1 ollama pull gemma3:4b

# Push to GitHub (excludes credentials)
git add -A; git commit -m "message"; git push origin master
```

---
*See TODO.md for gaps and tasks. See docs/ for detailed documentation.*
