# Cross-Workspace Wisdom Index

**Status:** Active
**Created:** 2024-12-24
**Per:** RULE-010 (Evidence-Based Wisdom), RULE-013 (Cross-Referencing)

---

## Executive Summary

This document captures reusable patterns, tools, and wisdom from across the Vibe ecosystem workspaces for use in sim-ai development.

| Workspace | Path | Key Patterns |
|-----------|------|--------------|
| **local-gai** | `C:\Users\natik\Documents\Vibe\localgai` | EBMSF, DSM cycles, MCP wrappers, Pydantic AI, LangGraph |
| **agno-agi** | `C:\Users\natik\Documents\Vibe\agno-agi` | Base Agno cluster template, Docker patterns |
| **angelgai** | `C:\Users\natik\Documents\Vibe\angelgai` | Watchdog service, crash recovery |
| **sim-ai** | Current | TypeDB hybrid, Governance MCP |

---

## 1. EBMSF - Evidence-Based MCP Selection Framework

**Source:** `localgai/mcp_servers.json`

### Selection Criteria

| Metric | Weight | Description |
|--------|--------|-------------|
| Token Preservation | 35% | Reduces tokens via caching/memory |
| Task Acceleration | 30% | Speeds up task completion |
| Error Reduction | 20% | Prevents manual errors |
| Learning Curve | 15% | Time to productive use |

### MCP Scoring Formula

```
Impact = (token_save × 0.35) + (task_accel × 0.30) + (error_reduce × 0.20) + (learn_curve × 0.15)

ADOPT if Impact > 2.0 AND Risk < HIGH
DEFER if Impact < 1.5 OR Risk = HIGH
```

### MCP Test/Fix Workflow (6 Phases)

```
Phase 1: DISCOVERY    → Scan mcp.json for errors
Phase 2: DIAGNOSIS    → Check process, ports, logs
Phase 3: TRIAGE       → Prioritize by impact score
Phase 4: REPAIR       → Apply fixes (restart, config, reinstall)
Phase 5: VERIFICATION → Test tool functionality
Phase 6: EVIDENCE     → Document in session logs
```

---

## 2. DSM - Deep Sleep Mode Optimization

**Source:** `localgai/scripts/dsm_tracker.py`

### DSM Cycle Phases

```
AUDIT → HYPOTHESIZE → MEASURE → OPTIMIZE → VALIDATE
```

### DSM Tracker CLI

```bash
# Start a batch
python dsm_tracker.py start 1001-1100

# Create checkpoint
python dsm_tracker.py checkpoint

# Generate evidence
python dsm_tracker.py evidence

# Show status
python dsm_tracker.py status

# Complete batch
python dsm_tracker.py complete
```

### Evidence Template

```
evidence/{date}_dsm_cycles_{batch}.md

Structure:
- Summary
- Achievements
- Metrics (tests, docs, files, PRs)
- Checkpoints (timestamps)
- Next Phase
- JoyFull Moment (joke)
```

---

## 3. MCP Wrapper Patterns

**Source:** `localgai/scripts/docker_wrapper.py`, `godot_wrapper.py`

### Docker Desktop Auto-Start

```python
def wait_for_docker(timeout: int = 120, check_interval: int = 5) -> bool:
    """Wait for Docker to become ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_docker_running():
            return True
        time.sleep(check_interval)
    return False
```

### Pattern: Wrapper → Auto-Start → Wait → Run MCP

1. Check if dependency is running
2. Start dependency if not
3. Wait with timeout
4. Run actual MCP server
5. Pass through stdin/stdout

---

## 4. Pydantic AI Type-Safe Tools

**Source:** `localgai/photoprism_migration/pydantic_tools.py`

### Type-Safe Models

```python
class MigrationConfig(BaseModel):
    source_path: str
    target_path: str
    backup_path: Optional[str] = None
    dry_run: bool = True

    @field_validator('source_path', 'target_path')
    @classmethod
    def validate_path(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return str(Path(v))

class MigrationResult(BaseModel):
    status: Literal["success", "failed", "partial", "dry_run"]
    files_processed: int = Field(ge=0)
    files_succeeded: int = Field(ge=0)
    files_failed: int = Field(ge=0)
    bytes_transferred: int = Field(ge=0)
    duration_seconds: float = Field(ge=0)
    errors: list[str] = Field(default_factory=list)
    rollback_available: bool
```

### FastMCP Integration

```python
from fastmcp import FastMCP

mcp = FastMCP("Migration Tools")

@mcp.tool()
async def analyze(source_path: str, dry_run: bool = True) -> dict:
    """Analyze source directory for migration."""
    config = MigrationConfig(source_path=source_path, target_path="", dry_run=dry_run)
    result = await analyze_source(config)
    return result.model_dump()
```

---

## 5. Watchdog Service Patterns

**Source:** `localgai/docs/WATCHDOG_OPERATIONAL_RULES.md`

### Memory Thresholds

| Threshold | Value | Action |
|-----------|-------|--------|
| WARNING | 2500 MB | Log warning |
| CRITICAL | 4500 MB | Kill after 3 consecutive |
| Node Process Limit | 30 | Leak warning |

### Grace Period Rules

1. **Startup Spike is Normal** - 3.5-4GB at MCP init expected
2. **120s Grace Period** - No kills during startup
3. **Consecutive Criticals** - Require 3 readings before kill
4. **Fallback Actions** - GC, cache clear before kill

---

## 6. Agent Framework Assessment

**Source:** `localgai/docs/AI_AGENT_FRAMEWORKS_ASSESSMENT.md`

### Framework Recommendations

| Framework | Rating | Use Case |
|-----------|--------|----------|
| Claude Agent SDK | Primary | File/bash operations, MCP native |
| Pydantic AI | Recommended | Type-safe custom MCP tools |
| LangGraph | Medium-term | Complex stateful workflows |
| CrewAI | Future | Multi-agent team patterns |
| LangChain | Optional | RAG applications |
| n8n | Backlog | Visual workflow automation |

### MCP Native Support

- Claude Agent SDK: Native
- Pydantic AI: Native (via FastMCP)
- Others: Require wrapping

---

## 7. Base Agno Cluster Template

**Source:** `agno-agi/agno-agi/`

### agents.yaml Structure

```yaml
agents:
  agent_name:
    name: Display Name
    description: Agent purpose
    instructions: |
      System prompt here
    model:
      name: ${MODEL_NAME}
      provider: anthropic
    markdown: true
    use_knowledge: true   # ChromaDB
    use_hybrid_knowledge: true  # TypeDB + ChromaDB (sim-ai extension)
    chat: true
```

### Docker Services

| Service | Port | Purpose |
|---------|------|---------|
| agents | 7777 | AgentOS API |
| agent-ui | 3000 | Next.js Web UI |
| chromadb | 8001 | Vector database |

---

## 8. sim-ai Unique Patterns

### TypeDB Hybrid Query Layer

```python
from governance.hybrid_router import HybridQueryRouter

router = HybridQueryRouter()
result = router.query(
    query_text="What depends on RULE-001?",
    query_type="inference"  # → TypeDB
)
result = router.query(
    query_text="Tell me about authentication",
    query_type="semantic"  # → ChromaDB
)
```

### HybridVectorDb for Agents

```python
from agent.hybrid_vectordb import HybridVectorDb

db = HybridVectorDb(auto_connect=True)
results = db.search("What depends on RULE-001?")  # Auto-routes
```

### Governance MCP (11 Tools)

| Tool | Purpose |
|------|---------|
| governance_query_rules | Query rules by category |
| governance_get_dependencies | Rule dependency graph |
| governance_check_conflicts | Conflict detection |
| governance_sync_to_chromadb | Sync TypeDB → ChromaDB |
| governance_health_check | Backend health status |

---

## 9. Strategic Session Flow (Design)

**Source:** `docs/STRATEGIC-SESSION-FLOW.md`

### SessionCollector Pattern

```python
class SessionCollector:
    def capture_prompt(self, prompt: str) -> None
    def capture_decision(self, decision: Decision) -> None
    def capture_task(self, task: Task) -> None
    def generate_session_log(self) -> str
    def sync_to_chromadb(self) -> bool
```

### Evidence Router

| Evidence Type | Destination | Purpose |
|--------------|-------------|---------|
| Decisions | TypeDB | Typed relations, inference |
| Tasks | TypeDB | Task graph, dependencies |
| Summaries | ChromaDB | Semantic search |
| Session Logs | Markdown | Human-readable archive |
| Raw Dialogue | SQLite | Replay, audit |

---

## 10. Rules for Strategic Alignment

### RULE-015: Cross-Workspace Pattern Reuse (PROPOSED)

> Before implementing new functionality, check cross-workspace wisdom index for existing patterns.

### RULE-016: MCP Wrapper Standard (PROPOSED)

> All MCP servers requiring external dependencies MUST use wrapper pattern with:
> - Dependency check
> - Auto-start
> - Timeout wait
> - Graceful fallback

### RULE-017: Type-Safe Tool Development (PROPOSED)

> Custom MCP tools SHOULD use Pydantic models for:
> - Input validation
> - Output schema
> - Runtime type checking

---

## References

| Document | Purpose |
|----------|---------|
| [MCP-LANDSCAPE.md](MCP-LANDSCAPE.md) | Available MCPs, bundling |
| [STRATEGIC-SESSION-FLOW.md](STRATEGIC-SESSION-FLOW.md) | Evidence flow design |
| [R&D-BACKLOG.md](backlog/R&D-BACKLOG.md) | R&D task tracking |
| [RULES-DIRECTIVES.md](RULES-DIRECTIVES.md) | Active rules |

---

*Per RULE-010: Evidence-Based Wisdom*
