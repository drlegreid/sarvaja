# MCP Landscape - Sim.ai Platform

**Last Updated:** 2024-12-24
**Status:** Active

---

## Available MCPs (Current Session)

| MCP | Category | Purpose | Tools |
|-----|----------|---------|-------|
| **playwright** | Browsing | Browser automation, screenshots, testing | 20+ browser tools |
| **godot-mcp** | Game Dev | Godot engine scene/script control | create_node, edit_script, etc. |
| **desktop-commander** | System | File ops, process management, search | read/write/search files |
| **octocode** | GitHub | Code search, repo exploration | githubSearchCode, etc. |
| **git** | VCS | Git operations | add, commit, diff, log |
| **claude-mem** | Memory | Chroma vector DB for memories | query/add documents |
| **filesystem** | Files | Direct file read/write | read_file, write_file |
| **llm-sandbox** | Execution | Sandboxed code execution | execute_code |
| **sequential-thinking** | Reasoning | Structured problem solving | sequentialthinking |
| **powershell** | Shell | PowerShell command execution | run_powershell |

---

## MCP → Agno Tool Wrapping (P3.5 Target)

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Agno Agent (agents.yaml)                                       │
│       │                                                         │
│       ├── tools: [                                              │
│       │     @tool governance_query  ← wraps MCP call            │
│       │     @tool governance_deps   ← wraps MCP call            │
│       │     @tool browser_snapshot  ← wraps playwright          │
│       │     @tool godot_create_node ← wraps godot-mcp           │
│       │   ]                                                     │
│       │                                                         │
│       └── MCP Tool Wrapper (agent/mcp_tools.py)                │
│             │                                                   │
│             ├── HTTP → Governance MCP (port 8081)               │
│             ├── HTTP → Playwright MCP                           │
│             └── HTTP → Godot MCP                                │
└─────────────────────────────────────────────────────────────────┘
```

### Wrapper Pattern (from local-gai)

```python
# agent/mcp_tools.py
from agno.tools import tool
import httpx

class MCPToolWrapper:
    """Wraps MCP server calls as Agno @tool functions."""

    def __init__(self, mcp_url: str):
        self.client = httpx.Client(base_url=mcp_url)

    @tool
    def governance_query_rules(self, category: str = None) -> str:
        """Query governance rules from TypeDB."""
        return self.client.post("/tools/governance_query_rules",
                                json={"category": category}).json()

    @tool
    def governance_get_dependencies(self, rule_id: str) -> str:
        """Get rule dependencies via TypeDB inference."""
        return self.client.post("/tools/governance_get_dependencies",
                                json={"rule_id": rule_id}).json()
```

---

## Docker Bundling Strategy

### Option A: Sidecar MCPs (Recommended)

```yaml
# docker-compose.yml
services:
  agents:
    image: sim-ai-agents
    ports: ["7777:7777"]
    environment:
      - MCP_GOVERNANCE_URL=http://governance-mcp:8081
      - MCP_PLAYWRIGHT_URL=http://playwright-mcp:3000
    depends_on:
      - governance-mcp
      - playwright-mcp

  governance-mcp:
    image: sim-ai-governance-mcp
    ports: ["8081:8081"]
    environment:
      - TYPEDB_HOST=typedb
      - CHROMADB_HOST=chromadb

  playwright-mcp:
    image: mcr.microsoft.com/playwright:v1.40.0
    ports: ["3000:3000"]
```

### Option B: Embedded in Agent Container

```dockerfile
# Dockerfile.agents
FROM python:3.12-slim
# Install MCP servers as Python packages
RUN pip install mcp-server-governance mcp-server-playwright
# Agent code with MCP wrappers
COPY agent/ /app/agent/
```

---

## Session Evidence Flow (RULE-001)

### Current Flow

```
User Request → Agent → Response
                ↓
           evidence/SESSION-{date}.md (manual)
```

### Target Flow (Strategic)

```
User Request → Agent → Response
                ↓
           ┌───────────────────────────────────────────┐
           │ Session Evidence Collector                │
           │  - Auto-capture prompts/responses         │
           │  - Extract decisions → TypeDB             │
           │  - Index memories → ChromaDB              │
           │  - Generate session summary               │
           └───────────────────────────────────────────┘
                ↓
           TypeDB (decisions, rules)
                ↓
           ChromaDB (semantic search)
                ↓
           ./docs/SESSION-{date}-{topic}.md (generated)
```

---

## MCP Selection Criteria (from EBMSF)

| Metric | Weight | Description |
|--------|--------|-------------|
| Token Preservation | 35% | Reduces tokens via caching/memory |
| Task Acceleration | 30% | Speeds up task completion |
| Error Reduction | 20% | Prevents manual errors |
| Learning Curve | 15% | Time to productive use |

### Current MCP Priority

| MCP | Impact | Risk | Decision |
|-----|--------|------|----------|
| claude-mem | 2.85 | LOW | MUST_HAVE |
| governance | 2.65 | LOW | MUST_HAVE |
| filesystem | 2.55 | MEDIUM | MUST_HAVE |
| playwright | 2.30 | LOW | RECOMMENDED |
| godot-mcp | 2.00 | LOW | OPTIONAL (project-specific) |
| llm-sandbox | 1.80 | MEDIUM | OPTIONAL |

---

---

## Cross-Workspace Resources

| Workspace | Path | Purpose |
|-----------|------|---------|
| **local-gai** | `C:\Users\natik\Documents\Vibe\localgai` | EBMSF methodology, MCP health checks |
| **agno-agi** | `C:\Users\natik\Documents\Vibe\agno-agi` | Base Agno cluster template |
| **sim-ai** | `C:\Users\natik\Documents\Vibe\sim-ai\sim-ai` | This project (TypeDB + hybrid) |

### Key Files

| File | Purpose |
|------|---------|
| `localgai/mcp_servers.json` | EBMSF methodology + MCP config template |
| `localgai/.mcp.json` | Project-scoped MCP config |
| `agno-agi/docker-compose.yml` | Base Agno cluster architecture |
| `agno-agi/agent/playground.py` | Base Agno agent implementation |

---

## Session Documentation Status

**Last Verified:** 2024-12-24

| Date | Sessions | Location |
|------|----------|----------|
| 2024-12-24 | 9 docs | `docs/SESSION-*.md`, `evidence/SESSION-*.md` |

### Session Doc Types

| Type | Purpose | Location |
|------|---------|----------|
| STRATEGIC | Strategic decisions, vision | `docs/SESSION-*-STRATEGIC*.md` |
| DEPLOYMENT | Infrastructure work | `docs/SESSION-*-DEPLOYMENT*.md` |
| DSP | Document Structure Protocol | `docs/SESSION-*-DSP*.md` |
| R&D | Research & development | `docs/SESSION-*-RD-*.md` |
| DECISIONS | Decision log | `evidence/SESSION-DECISIONS-*.md` |

---

## References

- [local-gai EBMSF Methodology](../../../localgai/mcp_servers.json)
- [MCP Official Servers](https://github.com/modelcontextprotocol/servers)
- [MCP Market](https://mcpmarket.com/)
- [Awesome MCP Servers](https://github.com/punkpeye/awesome-mcp-servers)

---

*Per RULE-013: Document Cross-Referencing*
