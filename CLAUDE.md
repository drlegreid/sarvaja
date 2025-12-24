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

## Running Services (via deploy.ps1)
```powershell
# Start stack
.\deploy.ps1 -Action up -Profile cpu

# Check status
.\deploy.ps1 -Action status

# View logs
.\deploy.ps1 -Action logs

# Health check
.\deploy.ps1 -Action health

# Run tests
.\deploy.ps1 -Action test

# Pull Ollama models
.\deploy.ps1 -Action pull-models

# Start Opik dashboard
.\deploy.ps1 -Action opik

# Rebuild containers
.\deploy.ps1 -Action rebuild

# Stop stack
.\deploy.ps1 -Action down
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
# Full deployment sequence
.\deploy.ps1 -Action up
.\deploy.ps1 -Action pull-models
.\deploy.ps1 -Action health
.\deploy.ps1 -Action test

# Start monitoring
.\deploy.ps1 -Action opik

# Push to GitHub (excludes credentials)
git add -A; git commit -m "message"; git push origin master
```

## Windsurf Workflows

See `.windsurf/workflows.md` for:
- Session start protocol
- Gap discovery & documentation
- Session evidence export
- DevOps operations
- Integration testing
- Memory interaction protocol

---
*See TODO.md for gaps and tasks. See docs/ for detailed documentation.*
