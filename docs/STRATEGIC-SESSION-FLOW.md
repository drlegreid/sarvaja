# Strategic Session & Evidence Flow Design

**Status:** DRAFT
**Created:** 2024-12-24
**Per:** RULE-001 (Session Evidence), RULE-006 (Decision Logging)

---

## Problem Statement

Current session evidence capture is **manual**:
- Session logs written by hand
- Decisions scattered across docs
- No automatic indexing to TypeDB/ChromaDB
- Evidence not searchable across sessions

---

## Target Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    STRATEGIC SESSION FLOW                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────────┐    ┌────────────────┐   │
│  │  User/Agent  │───▶│ Session Collector │───▶│ Evidence Store │   │
│  │   Dialogue   │    │   (MCP Service)   │    │                │   │
│  └──────────────┘    └──────────────────┘    └────────────────┘   │
│                              │                       │             │
│                              ▼                       ▼             │
│                   ┌─────────────────────────────────────────┐     │
│                   │         Evidence Router                  │     │
│                   │                                         │     │
│                   │  ┌─────────┐  ┌─────────┐  ┌─────────┐ │     │
│                   │  │ TypeDB  │  │ChromaDB │  │Markdown │ │     │
│                   │  │ (typed) │  │(semantic)│  │ (docs)  │ │     │
│                   │  └─────────┘  └─────────┘  └─────────┘ │     │
│                   └─────────────────────────────────────────┘     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Session Collector (MCP Service)

```python
# governance/session_collector.py

@dataclass
class SessionEvent:
    """Single event in a session."""
    timestamp: str
    event_type: str  # prompt, response, decision, task, error
    content: str
    metadata: Dict[str, Any]


class SessionCollector:
    """Collects and routes session evidence."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.events: List[SessionEvent] = []
        self.decisions: List[Decision] = []
        self.tasks: List[Task] = []

    def capture_prompt(self, prompt: str) -> None:
        """Capture user prompt."""
        self.events.append(SessionEvent(
            timestamp=now(),
            event_type="prompt",
            content=prompt,
            metadata={"session_id": self.session_id}
        ))

    def capture_decision(self, decision: Decision) -> None:
        """Capture strategic decision."""
        self.decisions.append(decision)
        # Auto-index to TypeDB
        self._index_to_typedb(decision)

    def generate_session_log(self) -> str:
        """Generate markdown session log."""
        return render_session_markdown(
            session_id=self.session_id,
            events=self.events,
            decisions=self.decisions,
            tasks=self.tasks
        )
```

### 2. Evidence Router

| Evidence Type | Destination | Purpose |
|--------------|-------------|---------|
| **Decisions** | TypeDB | Typed relations, inference |
| **Tasks** | TypeDB | Task graph, dependencies |
| **Summaries** | ChromaDB | Semantic search |
| **Session Logs** | Markdown | Human-readable archive |
| **Raw Dialogue** | SQLite | Replay, audit |

### 3. MCP Tools for Session Evidence

```python
# governance/mcp_server.py (extend existing)

@mcp.tool()
def session_start(topic: str, session_type: str = "general") -> str:
    """Start a new session with evidence collection."""
    session_id = f"SESSION-{date.today()}-{topic.upper()}"
    collector = SessionCollector(session_id)
    return f"Session started: {session_id}"

@mcp.tool()
def session_decision(
    decision_id: str,
    title: str,
    rationale: str,
    impact: str = "medium"
) -> str:
    """Record a strategic decision in the current session."""
    decision = Decision(
        id=decision_id,
        title=title,
        rationale=rationale,
        status="active",
        date=str(date.today())
    )
    collector.capture_decision(decision)
    return f"Decision {decision_id} recorded and indexed"

@mcp.tool()
def session_end() -> str:
    """End session and generate evidence artifacts."""
    log_path = collector.generate_session_log()
    sync_status = collector.sync_to_chromadb()
    return f"Session ended. Log: {log_path}, Synced: {sync_status}"
```

---

## Integration with Agents

### Option A: Agent Tool Wrapping

```yaml
# agents.yaml
agents:
  governance:
    name: Governance Agent
    use_hybrid_knowledge: true
    tools:
      - session_start
      - session_decision
      - session_end
```

### Option B: Automatic Capture (Hook)

```python
# agent/session_hook.py

class SessionHook:
    """Automatically capture agent interactions."""

    def on_message(self, role: str, content: str):
        if role == "user":
            collector.capture_prompt(content)
        elif role == "assistant":
            collector.capture_response(content)
            self._extract_decisions(content)
```

---

## Evidence Flow by Session Type

### Strategic Sessions

```
START: session_start("STRATEGIC-VISION", "strategic")
  │
  ├── User discusses architecture
  │     └── Auto-extract: DECISION-XXX patterns
  │
  ├── session_decision("DECISION-003", "Use TypeDB", "...")
  │     └── Indexed to TypeDB immediately
  │
  └── END: session_end()
        ├── docs/SESSION-2024-12-24-STRATEGIC-VISION.md
        ├── evidence/SESSION-DECISIONS-2024-12-24.md (updated)
        └── ChromaDB: session summary indexed
```

### R&D Sessions

```
START: session_start("RD-HASKELL-MCP", "research")
  │
  ├── Research discussion
  │     └── Auto-extract: RD-XXX task patterns
  │
  ├── session_task("RD-001", "Haskell MCP prototype")
  │     └── Indexed to TypeDB task graph
  │
  └── END: session_end()
        ├── docs/SESSION-2024-12-24-RD-HASKELL-MCP.md
        └── docs/backlog/R&D-BACKLOG.md (updated)
```

---

## Implementation Phases

| Phase | Task | Priority | Effort |
|-------|------|----------|--------|
| **1** | SessionCollector class | HIGH | 2 hrs |
| **2** | MCP tools (start/decision/end) | HIGH | 2 hrs |
| **3** | TypeDB indexing | MEDIUM | 3 hrs |
| **4** | ChromaDB sync | MEDIUM | 1 hr |
| **5** | Agent tool wrapping | MEDIUM | 2 hrs |
| **6** | Auto-extraction hooks | LOW | 4 hrs |

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Session capture rate | 100% of sessions |
| Decision indexing latency | < 1 second |
| Session log generation | Automatic at end |
| Cross-session search | Via ChromaDB semantic |
| Decision graph queries | Via TypeDB inference |

---

## Related

- [MCP-LANDSCAPE.md](MCP-LANDSCAPE.md) - MCP tool inventory
- [RULES-DIRECTIVES.md](RULES-DIRECTIVES.md) - RULE-001, RULE-006
- [R&D-BACKLOG.md](backlog/R&D-BACKLOG.md) - Phase 3 tasks

---

*Per RULE-001: Session Evidence Logging*
