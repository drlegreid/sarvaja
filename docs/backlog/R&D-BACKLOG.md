# R&D Backlog - Sim.ai PoC

**Last Updated:** 2024-12-25 (Phase 7 complete - TypeDB-First Migration)
**Status:** Active Development

---

## Strategic Vision: Private Cluster AI Platform

**Goal:** Self-hosted platform with MCPs & UIs on private cluster

### Platform Pillars

| Pillar | Components | Current | Target |
|--------|------------|---------|--------|
| **Agents** | Orchestration, routing, playground | ✅ Agno/LiteLLM | TypeDB-enhanced |
| **Tasks/Projects** | Backlog, tracking, dependencies | ✅ Split docs | TypeDB graph |
| **Evidence/Sessions** | Decisions, logs, dumps | ✅ Markdown/scripts | Structured DB |
| **Rules** | RULE-001 to RULE-024 | ✅ TypeDB + Markdown | TypeDB inference |

### Architecture Target

```
┌─────────────────────────────────────────────────────────────────┐
│                    sim-ai v1.0 Target Architecture              │
├─────────────────────────────────────────────────────────────────┤
│  Agents (7777) ─────────────────────────────────────────────    │
│       │                                                         │
│       ├── LiteLLM (4000) ── Ollama (11434)                     │
│       │                                                         │
│       ├── ChromaDB (8001)     │  TypeDB (1729)                 │
│       │   └── Semantic search │  └── Inference + Types         │
│       │   └── Documents (53)  │  └── Rules (24) + Decisions    │
│       │                       │                                 │
│       └── HYBRID QUERY LAYER ─┴─────────────────────────────   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase Status

### Phase 1: TypeDB Container ✅ COMPLETE

- TypeDB running on port 1729
- Schema + 6 inference rules
- Python client (2.29.x driver)
- 68 tests passing
- 14 rules, 4 decisions, 3 agents

### Phase 2: Governance MCP ✅ COMPLETE

- Governance MCP server (11 tools)
- Multi-agent governance (RULE-011)
- Document cross-referencing (RULE-013)
- Rule dependencies tracked

### Phase 3: Stabilization ✅ COMPLETE

| Task | Status | Description |
|------|--------|-------------|
| P3.1 | ✅ DONE | Hybrid query router (TypeDB + ChromaDB) |
| P3.2 | ✅ DONE | Integration tests for MCP-TypeDB |
| P3.3 | ✅ DONE | ChromaDB sync bridge (rules, decisions, agents) |
| P3.4 | ✅ DONE | Agent hybrid layer (HybridVectorDb + playground) |
| P3.5 | ✅ DONE | Performance benchmarks (governance/benchmark.py + 12 tests) |
| P3.6 | ✅ DONE | v1.0.0 release (CHANGELOG.md, 472 tests) |

**Release:** v1.0.0 (2024-12-25)
**Tests:** 472 passed, 46 skipped

### Phase 4: Cross-Workspace Integration (IN PROGRESS)

| Task | Status | Description |
|------|--------|-------------|
| P4.1 | ✅ DONE | MCP → Agno @tool wrapping (from agno-agi) |
| P4.2 | ✅ DONE | Session evidence flow (SessionCollector) |
| P4.2b | ✅ DONE | Rule Quality Analyzer (orphans, shallow, circular, impact) |
| P4.3 | ✅ DONE | DSM tracker integration (RULE-012 Deep Sleep Protocol) |
| P4.4 | ✅ DONE | Pydantic AI type-safe tools (from local-gai) |
| P4.5 | ✅ DONE | LangGraph state machine for complex workflows |

### Phase 5: External MCP Integration ✅ COMPLETE

| Task | Status | Description |
|------|--------|-------------|
| P5.1 | ✅ DONE | PlaywrightTools (7 tools: navigate, snapshot, click, type, screenshot, evaluate, wait) |
| P5.2 | ✅ DONE | PowerShellTools (2 tools: run_script, run_command) |
| P5.3 | ✅ DONE | DesktopCommanderTools (7 tools: read, write, list, search, info, create, move) |
| P5.4 | ✅ DONE | OctoCodeTools (5 tools: search_code, get_file, view_structure, search_repos, search_prs) |

**Tests:** 62 passed, 2 skipped (64 total)
**Files:** `agent/external_mcp_tools.py`, `tests/test_external_mcp_tools.py`

### Phase 6: Agent UI Framework ✅ COMPLETE

| Task | Status | Description |
|------|--------|-------------|
| P6.1 | ✅ DONE | Task UI with AG-UI event streaming (29 tests) |
| P6.2 | ✅ DONE | Strategic architecture review (DECISION-003: TypeDB-First) |
| P6.3 | ✅ DONE | Trame frontend for task submission (12 tests) |
| RULE-018 | ✅ DONE | Objective Reporting rule |
| RULE-019 | ✅ DONE | UI/UX Design Standards rule |

**Framework Decision:** Trame (Python-native web UI framework)
**Files:** `agent/task_ui.py`, `agent/trame_ui.py`, `tests/test_task_ui.py`, `tests/test_trame_ui.py`
**Tests:** 41 tests (29 task_ui + 12 trame_ui)

### Phase 7: TypeDB-First Migration ✅ COMPLETE

| Task | Status | Description |
|------|--------|-------------|
| P7.1 | ✅ DONE | TypeDB vector schema (TypeDB 2.x bridge pattern) |
| P7.2 | ✅ DONE | Embedding pipeline (generate + store) |
| P7.3 | ✅ DONE | New data → TypeDB routing (DataRouter) |
| P7.4 | ✅ DONE | ChromaDB migration tool (ChromaMigration) |
| P7.5 | ✅ DONE | ChromaDB sunset (ChromaReadOnly) |

**P7.1 Complete:** TypeDB 2.x bridge pattern with JSON-encoded embeddings + Python similarity.
**Files:** `governance/schema.tql`, `governance/vector_store.py`, `tests/test_vector_store.py` (27 tests)

**P7.3 Complete:** DataRouter for routing new data to TypeDB with auto-detection, batch support, hooks.
**Files:** `governance/data_router.py`, `tests/test_data_router.py` (22 tests)

**P7.4 Complete:** ChromaMigration for migrating existing ChromaDB data to TypeDB.
**Files:** `governance/chroma_migration.py`, `tests/test_chroma_migration.py` (19 tests)

**P7.5 Complete:** ChromaReadOnly wrapper that deprecates writes and redirects to TypeDB.
**Files:** `governance/chroma_readonly.py`, `tests/test_chroma_readonly.py` (17 tests)

**P9.1 Complete:** 7 MCP tools for artifact viewing (sessions, decisions, tasks, evidence search).
**Files:** `governance/mcp_server.py`, `tests/test_mcp_evidence.py` (27 tests)

**P9.2 Complete:** Governance Dashboard UI with rules, decisions, sessions, tasks views.
**Files:** `agent/governance_ui.py`, `tests/test_governance_ui.py` (24 tests)

**P9.3 Complete:** Session Evidence Viewer with timeline, detail, search, and navigation.
**Files:** `agent/session_viewer.py`, `tests/test_session_viewer.py` (22 tests)

**P7.2 Complete:** Embedding pipeline for rules, decisions, and sessions with chunking support.
**Files:** `governance/embedding_pipeline.py`, `tests/test_embedding_pipeline.py` (19 tests)
**Tests:** 609 passed total (up from 590)

**Phase 7 Context:** Per DECISION-003, TypeDB 3.x has vector search. Unify semantic + logical queries in single database. See [DECISION-003-TYPEDB-FIRST-STRATEGY.md](../evidence/DECISION-003-TYPEDB-FIRST-STRATEGY.md).

**P9.4 Complete:** Rule Impact Analyzer with dependency graph visualization, risk assessment, and Mermaid diagrams.
**Files:** `agent/governance_ui/data_access.py`, `agent/governance_ui/state.py`, `agent/governance_dashboard.py`, `tests/test_impact_analyzer.py` (24 tests)
**Features:**
- Rule dependency and dependent lookup (TypeDB inference)
- Risk level calculation (LOW/MEDIUM/HIGH/CRITICAL)
- Critical rules impact detection
- Mermaid diagram generation for graph visualization
- Graph/List view toggle in dashboard

**P9.5 Complete:** Agent Trust Dashboard for RULE-011 multi-agent governance compliance.
**Files:** `agent/governance_ui/data_access.py`, `agent/governance_ui/state.py`, `agent/governance_dashboard.py`, `tests/test_trust_dashboard.py` (32 tests)
**Features:**
- Trust score calculation: Trust = (Compliance × 0.4) + (Accuracy × 0.3) + (Consistency × 0.2) + (Tenure × 0.1)
- Trust leaderboard with agent ranking (HIGH/MEDIUM/LOW levels)
- Governance proposals listing with status tracking
- Human escalation alerts for disputed proposals
- Agent detail view with compliance/accuracy/tenure metrics
- Consensus score calculation for weighted voting
- Governance stats aggregation (avg trust, pending proposals, approval rate)

### Phase 8: E2E Testing Framework ✅ COMPLETE

| Task | Status | Description |
|------|--------|-------------|
| P8.1 | ✅ DONE | Robot Framework + Browser Library setup |
| P8.2 | ✅ DONE | Exploratory test keywords (heuristic patterns) |
| P8.3 | ✅ DONE | Task UI E2E test suite |
| P8.4 | ✅ DONE | Add E2E to requirements |
| P8.5 | ✅ DONE | Apply RULE-020 TypeDB schema |
| RULE-020 | ✅ DONE | LLM-Driven E2E Test Generation rule |

**Framework:** Robot Framework + Playwright (Browser Library)
**Architecture:** LLM explores → Generates deterministic tests → No LLM at runtime
**Files:**
- `tests/e2e/task_ui.robot` - E2E test suite
- `tests/e2e/resources/exploratory.resource` - Heuristic keywords
- `tests/e2e/run_e2e.ps1` - PowerShell runner
- `agent/e2e_explorer.py` - LLM exploration framework
- `governance/schema.tql` - Exploration session entities
- `governance/data.tql` - RULE-020 data

**See:** [RULE-020 in RULES-OPERATIONAL.md](../rules/RULES-OPERATIONAL.md)

### Phase 9: Agentic Platform UI/MCP (STRATEGIC PRIORITY)

**Strategic Goal:** Functioning agentic system where we can view all task/session/evidence artifacts via MCP and UI and govern our agentic platform rules.

| Task | Status | Description |
|------|--------|-------------|
| P9.1 | ✅ DONE | Task/Session/Evidence MCP Tools (artifact access) |
| P9.2 | ✅ DONE | Governance Dashboard UI (Trame-based rule viewer) |
| P9.3 | ✅ DONE | Session Evidence Viewer (browse sessions, decisions) |
| P9.4 | ✅ DONE | Rule Impact Analyzer (dependency graph visualization) |
| P9.5 | ✅ DONE | Agent Trust Dashboard (RULE-011 compliance metrics) |
| P9.6 | ✅ DONE | Real-time Rule Monitoring (active governance feed) |
| P9.7 | ✅ DONE | **Journey Pattern Analyzer** (recurring question detection) |
| P9.8 | ✅ DONE | **Capability Journey Certification** (proving viewing via E2E) |

**P9.7 Complete:** Journey Pattern Analyzer for recurring question detection and knowledge gap identification.
**Files:** `agent/journey_analyzer.py`, `tests/test_journey_analyzer.py` (24 tests)
**Features:**
- Question Journal: Log all governor questions with timestamps
- Recurrence Detection: Flag questions asked 2+ times with semantic matching
- Anomaly Alerts: Auto-detect when questions recur beyond threshold
- Knowledge Gap Report: Identify unanswered recurring questions
- UI Suggestion Generator: Recommend dashboard widgets for common patterns
**Tests:** 80 passed total (36 governance_ui + 20 rule_monitor + 24 journey_analyzer)

**RULE-024 Complete:** AMNESIA Protocol (Autonomous Context Recovery)
**Files:** `docs/rules/RULES-OPERATIONAL.md`, `docs/RULES-DIRECTIVES.md`
**Features:**
- Multi-layer recovery hierarchy (TODO.md → R&D Backlog → Summary → Claude-Mem → GAP Index)
- Autonomous context recovery without asking user "what were we doing?"
- Claude-mem query patterns with project prefix isolation
- Integration with RULE-001, RULE-012, RULE-014, RULE-021
- Anti-patterns for context recovery

**P9.8 Complete:** Capability Journey Certification for proving viewing capabilities via E2E tests.
**Files:** `tests/e2e/capability_journey.robot`, `results/e2e/` (evidence directory)
**Journeys Certified:**
- J1: Rules Governance Data (view rules, filter, detail)
- J2: Agent Trust Data (trust scores, governance stats)
- J3: Session/Evidence Data (sessions, decisions)
- J4: Task Data (task list view)
- J5: Monitoring Data (event feed, alerts)
- J6: Journey Patterns (recurring questions, knowledge gaps)
**Evidence:** Screenshots + certification report in `results/e2e/`

**P9.7 Use Case: Governor Journey Pattern Analyzer**

**Problem Statement:** Users (governors) repeatedly ask the same questions across sessions, indicating:
1. Knowledge gaps in the UI/documentation
2. Missing dedicated views for common queries
3. Forgotten insights that should be surfaced proactively

**Example Recurring Query:** *"How is llm-sandbox Python MCP being used?"* - Asked 3+ times, answer lost each time.

**Features:**
- **Question Journal**: Log all governor questions with timestamps
- **Recurrence Detection**: Flag questions asked 2+ times within N days
- **Anomaly Alerts**: "You've asked this 3 times - creating a dashboard widget"
- **Auto UI Spec Generation**: Recurring patterns → suggest/create UI components
- **Knowledge Gap Report**: Which questions keep recurring? → Documentation gaps

**Business Value:**
- Reduces cognitive load on users (stop asking same questions)
- Self-healing UX: UI evolves based on actual usage patterns
- Evidence-based UI prioritization (build what's actually needed)
- Governance intelligence: Track what matters to governors

**Architecture Vision:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Agentic Platform UI/MCP Layer                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   Trame UI      │  │   MCP Tools     │  │   REST API      │             │
│  │   (Dashboard)   │  │   (Claude/LLM)  │  │   (External)    │             │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘             │
│           │                    │                    │                       │
│           └────────────────────┴────────────────────┘                       │
│                                │                                             │
│                    ┌───────────┴───────────┐                                │
│                    │   Governance Layer    │                                │
│                    │   (TypeDB + Hybrid)   │                                │
│                    └───────────┬───────────┘                                │
│                                │                                             │
│  ┌──────────────┬──────────────┼──────────────┬──────────────┐             │
│  │              │              │              │              │              │
│  ▼              ▼              ▼              ▼              ▼              │
│ Rules      Decisions      Sessions      Tasks       Evidence               │
│ (22)         (4+)       (logs/*.md)   (backlog)    (artifacts)             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**MCP Tool Targets (P9.1):**

| Tool | Purpose | Returns |
|------|---------|---------|
| `governance_list_sessions` | List all session evidence files | Session IDs, dates, summaries |
| `governance_get_session` | Get session details | Full session markdown content |
| `governance_list_decisions` | List all strategic decisions | DECISION-* with status |
| `governance_get_decision` | Get decision details | Context, rationale, impacts |
| `governance_list_tasks` | List R&D/backlog tasks | Task IDs, status, priority |
| `governance_get_task_deps` | Get task dependencies | Blocking/blocked-by graph |
| `governance_evidence_search` | Semantic search across evidence | Relevant session excerpts |

**UI Targets (P9.2-P9.6):**

| View | Purpose | Components |
|------|---------|------------|
| Dashboard | Overview | Rule status, agent health, recent sessions |
| Rule Browser | Navigate rules | Tree view, dependencies, conflicts |
| Session Viewer | Browse sessions | Timeline, search, diff view |
| Evidence Graph | Visualize relationships | D3.js/Mermaid rule graph |
| Trust Metrics | Agent compliance | Trust scores, vote history |

**Dependencies:**
- Phase 7 (TypeDB-First): Unified query layer required
- P3.5 Benchmarks: Performance baseline established
- P6.3 Trame: UI framework in place

---

## Cross-Workspace Tools Captured

**Source:** [CROSS-WORKSPACE-WISDOM.md](../CROSS-WORKSPACE-WISDOM.md)

### From local-gai

| Tool | Purpose | Integration |
|------|---------|-------------|
| **EBMSF** | MCP selection scoring | Apply to new MCP evaluations |
| **DSM Tracker** | `scripts/dsm_tracker.py` | Cycle evidence automation |
| **Docker Wrapper** | `scripts/docker_wrapper.py` | MCP dependency auto-start |
| **Pydantic Tools** | `photoprism_migration/pydantic_tools.py` | Type-safe MCP tools |
| **LangGraph Workflow** | `langgraph_workflow.py` | State machine patterns |
| **Watchdog Rules** | Memory thresholds, grace periods | RULE-005 enhancement |

### From agno-agi

| Tool | Purpose | Integration |
|------|---------|-------------|
| **agents.yaml** | Agent config template | Base for sim-ai agents |
| **playground.py** | Agno agent setup | Pattern for hybrid knowledge |
| **docker-compose** | Cluster template | Port/service standards |

### Integration Patterns

```python
# MCP → Agno @tool wrapping (target)
from agno.tools import tool
import httpx

class MCPToolWrapper:
    @tool
    def governance_query_rules(self, category: str = None) -> str:
        return self.client.post("/tools/governance_query_rules",
                                json={"category": category}).json()
```

---

## Deferred Items

| Item | Status | Notes |
|------|--------|-------|
| Mem0 / OpenMemory MCP | ⏸️ DEFERRED | Superseded by TypeDB |
| Replace Agno with Memory MCP | ⏸️ DEFERRED | Pending TypeDB outcome |
| Custom Session/Memory UI | ⏸️ DEFERRED | After TypeDB validation |
| MCP-Monitor | LOW | Nice-to-have |
| AnythingLLM | LOW | Evaluate later |

---

## Strategic R&D: Custom Inference Engine

**Context:** TypeDB 3.x is ALPHA. We use stable 2.29.1.

### DIRECTIVE: Learn Before Optimize

> **Principle:** Implement Haskell MCP service first to become domain experts
> before attempting creative optimizations. Test coverage validates dependencies.

```
Phase 1: Python (current) ──→ Validate logic, gather requirements
         │
Phase 2: Haskell MCP ──────→ Learn inference domain deeply
         │                   └── Lazy eval, pattern matching, type safety
         │
Phase 3: Optimize ─────────→ Rust rewrite ONLY if benchmarks demand
         │                   └── PyO3 bindings, sub-ms latency
         │
Phase 4: Robotics ─────────→ Compatible inference for embedded/ROS
```

### Language Decision Matrix

| Factor | Python | Haskell | Rust |
|--------|--------|---------|------|
| **Learning** | ✅ Done | 🎯 Next | ⏳ Later |
| **Inference elegance** | ⚠️ Imperative | ✅ Natural | ⚠️ Manual |
| **Python FFI** | Native | HTTP/gRPC | PyO3 |
| **Robotics/ROS** | rospy | ❌ Hard | ✅ ros2-rust |
| **MCP deploy** | ✅ Easy | ⚠️ Runtime | ✅ Small binary |

### R&D Tasks

| ID | Task | Status | Priority | Notes |
|----|------|--------|----------|-------|
| RD-001 | Haskell inference MCP prototype | 📋 TODO | **FUTURE** | After strategic agentic platform complete |
| RD-002 | Benchmark Python vs Haskell | 📋 TODO | FUTURE | After RD-001 |
| RD-003 | Rust rewrite decision | ⏸️ BLOCKED | LOW | Requires RD-002 benchmarks |
| RD-004 | Robotics inference compatibility | 📋 TODO | FUTURE | ROS2/embedded targets |
| RD-005 | TypeDB 3.x alpha evaluation | 📋 TODO | LOW | Monitor releases |

> **NOTE:** Haskell MCP (RD-001) is a core infrastructure component. It should only begin
> AFTER the strategic agentic platform (Phase 9) is complete and functioning.

### MCP Tooling Efficiency R&D

**Goal:** Understand and optimize MCP tool usage patterns

| ID | Task | Status | Priority | Notes |
|----|------|--------|----------|-------|
| TOOL-001 | llm-sandbox usage audit | 📋 TODO | **HIGH** | What are we using it for? Efficiency? |
| TOOL-002 | MCP call frequency analysis | 📋 TODO | MEDIUM | Which tools called most? Bottlenecks? |
| TOOL-003 | Playwright MCP heuristic catalog | 📋 TODO | HIGH | Document all exploration patterns |
| TOOL-004 | PowerShell MCP use cases | 📋 TODO | LOW | Windows-specific automation |
| TOOL-005 | Desktop-Commander vs filesystem MCP | 📋 TODO | LOW | When to use which? |

### Document Management MCP R&D (STRATEGIC)

**Goal:** TypeDB-linked document management MCP used at core agent level

| ID | Task | Status | Priority | Notes |
|----|------|--------|----------|-------|
| DOC-001 | TypeDB→Document sync architecture | 📋 TODO | **HIGH** | Define relationship model |
| DOC-002 | Document Management MCP design | 📋 TODO | **HIGH** | Core-level file MCP for agents |
| DOC-003 | Cross-system agent integration | 📋 TODO | HIGH | Claude Code, other systems |
| DOC-004 | Document version tracking in TypeDB | 📋 TODO | MEDIUM | Link doc changes to TypeDB entities |
| DOC-005 | Evidence folder structure protocol | 📋 TODO | HIGH | DSP item: structure docs & tests |

**Architecture Vision:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│               Document Management MCP (Core Agent Layer)                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────┐      ┌─────────────────┐      ┌─────────────────┐  │
│  │  Claude Code   │      │  Agent Platform │      │  Other Systems  │  │
│  │  (VS Code)     │      │  (Trame UI)     │      │  (CI/CD, etc)   │  │
│  └───────┬────────┘      └────────┬────────┘      └────────┬────────┘  │
│          │                        │                        │           │
│          └────────────────────────┼────────────────────────┘           │
│                                   │                                     │
│                    ┌──────────────▼──────────────┐                     │
│                    │   Document Management MCP   │                     │
│                    │   • File CRUD (evidence/)   │                     │
│                    │   • TypeDB link management  │                     │
│                    │   • Version tracking        │                     │
│                    │   • Structure validation    │                     │
│                    └──────────────┬──────────────┘                     │
│                                   │                                     │
│          ┌────────────────────────┼────────────────────────┐           │
│          │                        │                        │           │
│          ▼                        ▼                        ▼           │
│  ┌───────────────┐      ┌─────────────────┐      ┌─────────────────┐  │
│  │  TypeDB       │      │  File System    │      │  Frankel Hash   │  │
│  │  (Links/Meta) │  ←→  │  (Documents)    │  ←→  │  (Integrity)    │  │
│  └───────────────┘      └─────────────────┘      └─────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**TypeDB Document Link Schema:**

```typeql
define
  document-reference sub entity,
    owns doc-path,           # "evidence/SESSION-*.md"
    owns doc-type,           # "session", "decision", "rule"
    owns doc-hash,           # Frankel hash for integrity
    owns last-synced,        # Timestamp of last sync
    plays doc-link:document;

  doc-link sub relation,
    relates document,        # The file reference
    relates entity;          # Rule, Decision, Session entity

  # Example inference: Documents not synced in 24h
  rule stale-document:
  when {
    $d isa document-reference, has last-synced $ts;
    $ts < now() - 86400000;  # 24 hours in ms
  } then {
    $d has needs-sync true;
  };
```

**Questions to Answer:**
- How do we maintain TypeDB ↔ Document consistency?
- What happens when a document is moved/renamed?
- How do we handle document deletions (soft delete in TypeDB)?
- Should document content be indexed in TypeDB or just links?

**Questions to Answer:**
- What code execution patterns use llm-sandbox?
- Are we duplicating work that could be done locally?
- What's the latency overhead of sandboxed execution?
- Could some llm-sandbox use cases move to powershell MCP?

---

### Frankel Hash R&D (RULE-022 Extension)

**Vision:** Digital twin evidence world with holographic navigation

| ID | Task | Status | Priority | Notes |
|----|------|--------|----------|-------|
| FH-001 | CLI zoom in/out on hash changes | 📋 TODO | HIGH | Navigate document changes at chunk level |
| FH-002 | Hash tree visualization (ASCII/terminal) | 📋 TODO | HIGH | Merkle tree depth navigation |
| FH-003 | 5D visualization framework | 📋 TODO | MEDIUM | Lighting + 3D + deformation mapping |
| FH-004 | Holographic mapping of evidence world | 📋 TODO | MEDIUM | Digital twin navigation for LLM + human |
| FH-005 | Game theory for hash convergence | 📋 TODO | FUTURE | Group theory, equilibria, stability |
| FH-006 | Sync R&D tasks with GitHub issues | ✅ DONE | HIGH | governance/github_sync.py + 18 tests |

### Frankel Hash Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│              Frankel Hash Evidence Navigation                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Layer 1: CHUNK HASHING (Core)                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Document → Chunks (paragraphs/sections)                        │    │
│  │     └── Each chunk → Similarity hash (locality-sensitive)       │    │
│  │     └── Merkle tree of chunk hashes                             │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                               │                                          │
│                               ▼                                          │
│  Layer 2: CLI NAVIGATION (FH-001, FH-002)                               │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Terminal UI with zoom levels:                                  │    │
│  │     • Level 0: Document root hash (single hash)                 │    │
│  │     • Level 1: Section hashes (zoom in)                         │    │
│  │     • Level 2: Paragraph hashes (deeper zoom)                   │    │
│  │     • Level N: Line-level changes (maximum detail)              │    │
│  │  Commands: zoom-in, zoom-out, diff, navigate, highlight         │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                               │                                          │
│                               ▼                                          │
│  Layer 3: 5D VISUALIZATION (FH-003)                                     │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Dimensions:                                                     │    │
│  │     • X/Y/Z: Spatial position (3D tree structure)               │    │
│  │     • Lighting: Change intensity (brightness = delta)           │    │
│  │     • Deformation: Stability (warping = volatility)             │    │
│  │  Rendering: WebGL/Three.js or terminal (Blessed/Curses)         │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                               │                                          │
│                               ▼                                          │
│  Layer 4: HOLOGRAPHIC TWIN (FH-004)                                     │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Evidence World Navigation:                                     │    │
│  │     • Map all session evidence to hash-space                    │    │
│  │     • LLM queries: "Show me changes in RULE-011 since Dec 24"   │    │
│  │     • Human navigation: Fly through evidence topology           │    │
│  │     • Convergence visualization: Stable regions vs flux         │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                               │                                          │
│                               ▼                                          │
│  Layer 5: THEORY LAYER (FH-005)                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Mathematical foundations:                                       │    │
│  │     • Group theory: Hash transformations as group operations    │    │
│  │     • Game theory: Multi-agent convergence on evidence          │    │
│  │     • Topology: Continuous navigation in discrete hash space    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Frankel Hash TypeDB Integration

```typeql
define
  frankel-hash sub entity,
    owns hash-id,
    owns hash-value,
    owns chunk-level,      # 0=document, 1=section, 2=paragraph, N=line
    owns created-at,
    plays parent-child:parent,
    plays parent-child:child,
    plays document-hash:hash;

  parent-child sub relation,
    relates parent,
    relates child;

  document-hash sub relation,
    relates document,
    relates hash;
```

### Haskell MCP Interface (Target)

```haskell
-- Servant API for inference MCP
type InferenceAPI =
       "query" :> ReqBody '[JSON] Query :> Post '[JSON] QueryResult
  :<|> "deps"  :> Capture "ruleId" Text :> Get '[JSON] [RuleId]
  :<|> "conflicts" :> Get '[JSON] [Conflict]
  :<|> "health" :> Get '[JSON] HealthStatus
```

### Why This Order?

1. **Python**: Already working, validates business logic
2. **Haskell**: Forces deep understanding of inference patterns
3. **Rust**: Only if latency <1ms is required (measure first!)
4. **Robotics**: Long-term - inference on edge devices

**Trigger for Rust rewrite:**
- Haskell inference >10ms on 1K rules
- Need WASM/embedded deployment
- Team prefers Rust ecosystem

---

### Testing Strategy R&D (STRATEGIC - DSP Coherence)

**Vision:** Tactical day (implementation), Strategic night (prepare for next move)

**Core Principle:** Tests are living contracts that evolve with business requirements.
During active development, focus on functionality. During DSP cycles, restructure
tests for long-term maintainability and strategic coherence.

| ID | Task | Status | Priority | Notes |
|----|------|--------|----------|-------|
| TEST-001 | Refine testing rules for reusability | 📋 TODO | **HIGH** | See detailed design below |
| TEST-002 | Evidence collection at trace level | 📋 TODO | **HIGH** | Full traces during certification runs |
| TEST-003 | Debug workflow trace minimization | 📋 TODO | HIGH | Minimize to error instance for LLM context |
| TEST-004 | Test restructuring for rules conformity | 📋 TODO | **HIGH** | DSP principle: align tests with rules |
| TEST-005 | GitHub milestone certification reporting | 📋 TODO | **HIGH** | Full test trace report at each milestone |
| TEST-006 | DevOps test strategy | 📋 TODO | HIGH | Reusable patterns, CI/CD integration |

#### TEST-001: Test Framework Reusability Design (CRITICAL)

**Principle:** Tests REUSE implementation objects, not duplicate them.

```
SHARED OBJECTS FROM IMPLEMENTATION:

┌─────────────────────────────────────────────────────────────────────────┐
│  IMPLEMENTATION (source of truth)     →     TESTS (consumers)           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  API Models (Pydantic/dataclass):                                       │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  governance/models.py:                                          │    │
│  │     • RuleResponse, RuleRequest                                 │    │
│  │     • DecisionResponse, SessionResponse                         │    │
│  │                                                                  │    │
│  │  tests/ IMPORTS these, never duplicates:                        │    │
│  │     from governance.models import RuleResponse                  │    │
│  │     # Assertions use same model as implementation               │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  UI Page Objects (align with implementation):                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  agent/ui_components.py:                                        │    │
│  │     • RulesTable, RuleForm, RuleDetail components              │    │
│  │                                                                  │    │
│  │  tests/ui/pages/rules_page.py:                                  │    │
│  │     • RulesPage mirrors component structure                     │    │
│  │     • Locators match data-testid in implementation              │    │
│  │     • Methods align with user actions                           │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

BDD PATTERN (Given/When/Then specificity):

  Given (Presets - Setup state):
  ┌─────────────────────────────────────────────────────────────────┐
  │  • Load test fixtures using SHARED factories                   │
  │  • Navigate to known state                                     │
  │  • Set up preconditions                                        │
  │  Example:                                                      │
  │    Given I Have Rules In The System                           │
  │    Given The Governance Dashboard Is Open                      │
  └─────────────────────────────────────────────────────────────────┘

  When (Actions - User interactions):
  ┌─────────────────────────────────────────────────────────────────┐
  │  • Use Page Object methods                                     │
  │  • Single responsibility per step                              │
  │  Example:                                                      │
  │    When I Click On Rule "RULE-001"                            │
  │    When I Submit The Rule Form                                │
  └─────────────────────────────────────────────────────────────────┘

  Then (Assertions - Verify outcomes):
  ┌─────────────────────────────────────────────────────────────────┐
  │  • Assertions use SAME models as implementation               │
  │  • Specific, measurable outcomes                               │
  │  • One assertion concept per step                              │
  │  Example:                                                      │
  │    Then I Should See Rule Details                             │
  │    Then The Rule Title Should Be "Session Evidence Logging"   │
  │    Then The Response Should Match RuleResponse Schema         │
  └─────────────────────────────────────────────────────────────────┘
```

**Anti-patterns to AVOID:**
```
❌ Duplicating models in tests (create test-specific versions)
❌ Hardcoding expected values (use shared fixtures)
❌ Testing implementation details (test behavior, not code)
❌ Mixing Given/When/Then in single step
❌ Generic assertions ("should work", "no errors")
```

**Good patterns to FOLLOW:**
```
✅ Import models from implementation
✅ Page Objects mirror UI components
✅ Fixtures generated from implementation factories
✅ Each step has single responsibility
✅ Assertions are specific and measurable
```

### Testing Framework Reusability Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   Test Framework Reusability Model                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  LAYER 1: SHARED CONTRACTS (TEST-001)                                   │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  API Models (Pydantic/dataclass)                                │    │
│  │     • RuleResponse, DecisionResponse, SessionResponse           │    │
│  │     • Request schemas, validation rules                         │    │
│  │                                                                  │    │
│  │  UI Structures (Page Objects)                                   │    │
│  │     • BasePage → RulesPage, DecisionsPage, SessionsPage         │    │
│  │     • Locator registry (data-testid selectors)                  │    │
│  │                                                                  │    │
│  │  Shared by: Unit tests, Integration tests, E2E tests            │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                               │                                          │
│                               ▼                                          │
│  LAYER 2: TRACE COLLECTION (TEST-002, TEST-003)                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Certification Mode (Full Trace):                               │    │
│  │     • Every assertion logged with timestamp                     │    │
│  │     • Screenshots at each step                                  │    │
│  │     • API request/response captured                             │    │
│  │     • Evidence folder: evidence/certification/{milestone}/      │    │
│  │                                                                  │    │
│  │  Debug Mode (Minimal Trace):                                    │    │
│  │     • Only error context captured                               │    │
│  │     • Stack trace + last N steps                                │    │
│  │     • Minimize LLM context flooding                             │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                               │                                          │
│                               ▼                                          │
│  LAYER 3: MILESTONE CERTIFICATION (TEST-005)                            │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Per Milestone:                                                  │    │
│  │     1. Run full test suite (robot --include all)                │    │
│  │     2. Generate certification report                            │    │
│  │     3. Post to GitHub issue with:                               │    │
│  │        • Test count (passed/failed/skipped)                     │    │
│  │        • Coverage metrics                                       │    │
│  │        • Performance benchmarks                                 │    │
│  │        • Gap closure summary                                    │    │
│  │     4. Link evidence artifacts                                  │    │
│  │                                                                  │    │
│  │  Prod-Ready Claim requires:                                     │    │
│  │     • 100% smoke tests passing                                  │    │
│  │     • 90%+ functional tests passing                             │    │
│  │     • All P0 gaps closed                                        │    │
│  │     • Performance within SLA                                    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### DSP Test Hygiene Protocol

```
NIGHT CYCLE (DSP - Strategic Preparation):

1. TEST RESTRUCTURING (TEST-004)
   └── Align test files with RULE-* structure
   └── Ensure each test traces to a rule or gap
   └── Remove orphan tests (no traceability)
   └── Update test documentation

2. RULES CONFORMITY CHECK
   └── RULE-004: All tests use POM pattern?
   └── RULE-020: E2E tests generated via LLM exploration?
   └── RULE-023: Test levels (L1-L4) defined?
   └── Update gaps for non-conforming tests

3. CERTIFICATION PREP
   └── Stage test artifacts for certification
   └── Prepare GitHub issue template
   └── Validate all evidence folder links

DAY CYCLE (Tactical Implementation):

1. Focus on GREEN phase (make tests pass)
2. Minimal test changes (only what's needed)
3. Log insights but defer restructuring
4. Capture traces for later analysis
```

### DevOps Test Strategy (TEST-006)

```yaml
devops_test_strategy:
  ci_cd_gates:
    - pre_commit: smoke tests (< 30s)
    - pr_merge: functional tests (< 5min)
    - release: full suite + certification (< 30min)

  reusable_patterns:
    - shared_fixtures: pytest fixtures, Robot keywords
    - test_data: factories, mock builders
    - environment_configs: dev, staging, prod configs

  parallel_execution:
    - pytest: -n auto (xdist)
    - robot: --parallel (pabot)

  reporting:
    - format: JUnit XML + HTML
    - destination: GitHub Actions artifacts
    - retention: 30 days

  certification_flow:
    trigger: milestone tag (v*.*.*)
    steps:
      1. Run full suite
      2. Generate report
      3. Create GitHub issue
      4. Link evidence
      5. Notify stakeholders
```

---

## Strategy Cycle End Directives

### DIRECTIVE: E2E Test Evidence Management

**Established:** 2024-12-25 (End of P9.6 cycle)

#### 1. E2E Test Results Evidence Location

| Artifact Type | Location | Retention |
|---------------|----------|-----------|
| **Robot Framework Output** | `results/output.xml` | Per run |
| **HTML Reports** | `results/report.html`, `results/log.html` | Per run |
| **Playwright Logs** | `results/playwright-log-*.txt` | Per run |
| **Browser Artifacts** | `results/browser/` | Per run |
| **Certification Runs** | `evidence/certification/{milestone}/` | Permanent |
| **Screenshot Evidence** | `results/browser/screenshots/` | Per milestone |

**Run Command:**
```powershell
# Standard run (evidence to results/)
.\tests\e2e\run_e2e.ps1

# Certification run (permanent evidence)
.\tests\e2e\run_e2e.ps1 -OutputDir evidence/certification/v1.1.0
```

#### 2. GitHub Certification Issue Integration

**Decision:** YES - Share detailed test evidence to certification GitHub issue

| Item | Status | Details |
|------|--------|---------|
| Create certification issue template | 📋 TODO | `.github/ISSUE_TEMPLATE/certification.md` |
| Auto-post test summary | 📋 TODO | GitHub Actions workflow |
| Link evidence artifacts | 📋 TODO | Upload to release or link to repo |
| Badge integration | 📋 TODO | Display test status in README |

**Certification Issue Structure:**
```markdown
## Milestone Certification: v{VERSION}

### Test Summary
- Total: {TOTAL}
- Passed: {PASSED} ✅
- Failed: {FAILED} ❌
- Skipped: {SKIPPED} ⏭️

### Capability Journeys Verified
- [ ] Agent data viewing
- [ ] Task data viewing
- [ ] Evidence data viewing
- [ ] Rules governance data viewing
- [ ] Monitoring data viewing

### Evidence Links
- Report: [report.html]({LINK})
- Full Log: [log.html]({LINK})

### Sign-off
- [ ] All P0 tests passing
- [ ] No critical gaps open
- [ ] Performance within SLA
```

#### 3. Capability Journey from Passing UI Tests

**Concept:** Each passing E2E test proves a user can complete a specific capability journey.

**P9.8 Capability Journey Matrix:**

| Capability | E2E Test | Views | Proof |
|------------|----------|-------|-------|
| **View Agent Data** | `test_view_agents` | Trust Dashboard | Agent leaderboard + detail |
| **View Task Data** | `test_view_tasks` | Tasks List | R&D backlog items |
| **View Evidence Data** | `test_view_sessions` | Sessions Timeline | Session cards + detail |
| **View Rules Governance** | `test_view_rules` | Rules List + Detail | Rule CRUD operations |
| **View Monitoring Data** | `test_view_monitoring` | Monitor Dashboard | Event feed + alerts |

**Journey Test Pattern:**
```robot
*** Test Cases ***
Capability Journey: View All Governance Artifacts
    [Documentation]    Proves user can view all platform data types
    [Tags]    capability-journey    p0    certification

    # Agent data capability
    Navigate To Trust Dashboard
    Verify Agent Leaderboard Visible
    Click Agent And Verify Detail

    # Task data capability
    Navigate To Tasks View
    Verify Tasks List Visible
    Verify Task Has Phase Column

    # Evidence data capability
    Navigate To Sessions View
    Verify Session Timeline Visible
    Click Session And Verify Content

    # Rules governance capability
    Navigate To Rules View
    Verify Rules Table Visible
    Click Rule And Verify Detail

    # Monitoring capability
    Navigate To Monitoring View
    Verify Event Feed Visible
    Verify Alerts Panel Visible
```

**Implementation Priority:**
1. Create capability journey test file: `tests/e2e/capability_journey.robot`
2. Add GitHub Actions workflow for certification runs
3. Create certification issue template
4. Document in RULES-OPERATIONAL.md as RULE-024

---

*R&D tracking per RULE-010: Evidence-Based Wisdom*
