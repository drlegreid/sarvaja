# Sim.ai PoC - Local Agent Platform

Multi-agent orchestration platform with observability and hybrid inference (Claude remote + Ollama local).

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AGENT LAYER                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
│  │ Orchestrator│ │Rules Curator│ │  Researcher │ │   Coder    │ │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └─────┬──────┘ │
│         └───────────────┴───────────────┴───────────────┘       │
│                              │ AgentOS :7777                     │
├──────────────────────────────┼──────────────────────────────────┤
│                        ROUTING LAYER                             │
│                    ┌─────────┴─────────┐                        │
│                    │     LiteLLM       │ :4000                  │
│                    │  (Model Router)   │                        │
│                    └────┬─────────┬────┘                        │
│           ┌─────────────┘         └─────────────┐               │
│           ▼                                     ▼               │
│    ┌──────────────┐                    ┌──────────────┐         │
│    │ Claude Opus  │ (Remote)           │   Ollama     │ :11434  │
│    │ Claude Sonnet│                    │ gemma3:4b    │ (Local) │
│    └──────────────┘                    └──────────────┘         │
├─────────────────────────────────────────────────────────────────┤
│                     OBSERVABILITY LAYER                          │
│                    ┌──────────────────┐                         │
│                    │       Opik       │ :5173/:5174             │
│                    │  (Tracing/Eval)  │                         │
│                    └──────────────────┘                         │
├─────────────────────────────────────────────────────────────────┤
│                       STORAGE LAYER                              │
│    ┌──────────────┐              ┌──────────────┐               │
│    │   ChromaDB   │ :8001        │    SQLite    │               │
│    │  (Vectors)   │              │ (Agent State)│               │
│    └──────────────┘              └──────────────┘               │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

```powershell
# 1. Configure environment
cp .env.example .env
# Edit .env → Set ANTHROPIC_API_KEY

# 2. Deploy (CPU profile for laptop)
.\deploy.ps1 -Action up -Profile cpu

# 3. Pull Ollama models
.\deploy.ps1 -Action pull-models

# 4. Check health
.\deploy.ps1 -Action health

# 5. Run tests
.\deploy.ps1 -Action test

# 6. Start monitoring (optional)
.\deploy.ps1 -Action opik
```

## DevOps Commands

| Command | Description |
|---------|-------------|
| `.\deploy.ps1 -Action up` | Start all services |
| `.\deploy.ps1 -Action down` | Stop all services |
| `.\deploy.ps1 -Action status` | Show container status |
| `.\deploy.ps1 -Action logs` | Tail service logs |
| `.\deploy.ps1 -Action health` | Run health checks |
| `.\deploy.ps1 -Action test` | Run pytest suite |
| `.\deploy.ps1 -Action pull-models` | Pull Ollama models |
| `.\deploy.ps1 -Action opik` | Start Opik dashboard |
| `.\deploy.ps1 -Action rebuild` | Rebuild containers |

See `docs/DEPLOYMENT.md` for detailed deployment guide.

## Services

| Service | Port | Description |
|---------|------|-------------|
| **Agents API** | 7777 | AgentOS multi-agent API |
| **LiteLLM** | 4000 | Model routing proxy |
| **Opik** | 5173/5174 | Tracing UI and API |
| **ChromaDB** | 8001 | Vector database |
| **Ollama** | 11434 | Local CPU inference |
| **Agent UI** | 3000 | Web interface (full profile) |

## Resource Requirements

**CPU Profile (laptop):**
- RAM: ~8GB allocated
- CPU: 4 cores recommended
- Disk: ~10GB for models

**Full Profile (server):**
- RAM: 16GB+ recommended
- Add Agent UI service

## Model Routing

LiteLLM routes requests based on model name:

| Model | Backend | Use Case |
|-------|---------|----------|
| `claude-opus` | Anthropic API | Complex R&D, reasoning |
| `claude-sonnet` | Anthropic API | Balanced tasks |
| `gemma-local` | Ollama | Simple tasks, offline |
| `llama-local` | Ollama | Medium complexity |

## Agents

1. **Task Orchestrator** - Routes tasks by complexity
2. **Rules Curator** - Manages rules in ChromaDB
3. **Research Agent** - Deep analysis (Claude Opus)
4. **Code Agent** - Programming tasks
5. **Local Assistant** - Simple tasks (Ollama)

## Commands

```powershell
# Start stack
.\deploy.ps1 -Action up -Profile cpu

# Stop stack
.\deploy.ps1 -Action down

# View logs
.\deploy.ps1 -Action logs

# Health check
.\deploy.ps1 -Action health

# Pull Ollama models
.\deploy.ps1 -Action pull-models

# Manual Docker commands
docker compose --profile cpu up -d
docker compose logs -f agents
docker compose down
```

## Observability

Access Opik UI at http://localhost:5173 to:
- View trace timelines
- Analyze token usage
- Evaluate agent responses
- Track multi-agent workflows

## Integration with Existing Stack

This PoC integrates with your existing infrastructure:
- **agno-agi**: Shares ChromaDB data patterns
- **localgai**: Compatible MCP architecture
- **mcp_trials**: Windsurf configuration compatible

## Troubleshooting

**Docker not running:**
```powershell
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
```

**Ollama model pull fails:**
```powershell
docker exec -it sim-ai-ollama-1 ollama pull gemma3:4b
```

**Memory issues:**
Reduce Ollama memory limit in docker-compose.yml:
```yaml
deploy:
  resources:
    limits:
      memory: 2G  # Lower from 4G
```

## Skeptical Notes

Per the counter-analysis:
- **CPU bottleneck**: Expect 1-2 tokens/s on i7 for local inference
- **RAM limits**: Monitor with `docker stats`, stay under 12GB total
- **Integration debt**: Test Opik traces before trusting metrics
- **ChromaDB drift**: Validate embeddings periodically

## Current Status

- [x] Docker stack deployed (LiteLLM, ChromaDB, Ollama, Agents)
- [x] 5 agents running on port 7777
- [x] Kayba ACE framework available (`pip install ace-framework`)
- [x] Opik cloned locally (start with `cd opik && ./opik.sh`)
- [x] Python test suite created
- [x] Rules governance framework documented
- [x] Sync agent skeleton implemented
- [ ] Pull Ollama model: `docker exec sim-ai-ollama-1 ollama pull gemma3:4b`
- [ ] Start Opik dashboard
- [ ] Add XAI_API_KEY for Grok integration

## Next Steps

1. [ ] Scale to server with `--profile full`
2. [ ] Integrate pgvector for visual workflows
3. [ ] Add failure injection for resilience testing
4. [ ] Fix ChromaDB knowledge integration with Agno wrapper
