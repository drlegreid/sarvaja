# R&D Backlog - Sim.ai PoC

**Last Updated:** 2024-12-25
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
| **Rules** | RULE-001 to RULE-022 | ✅ TypeDB + Markdown | TypeDB inference |

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
│       │   └── Documents (53)  │  └── Rules (22) + Decisions    │
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

### Phase 3: Stabilization (IN PROGRESS)

| Task | Status | Description |
|------|--------|-------------|
| P3.1 | ✅ DONE | Hybrid query router (TypeDB + ChromaDB) |
| P3.2 | ✅ DONE | Integration tests for MCP-TypeDB |
| P3.3 | ✅ DONE | ChromaDB sync bridge (rules, decisions, agents) |
| P3.4 | ✅ DONE | Agent hybrid layer (HybridVectorDb + playground) |
| P3.5 | 📋 TODO | Performance benchmarks |
| P3.6 | 📋 TODO | v1.0 release |

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

### Phase 7: TypeDB-First Migration (NEXT)

| Task | Status | Description |
|------|--------|-------------|
| P7.1 | 📋 TODO | TypeDB vector schema (embeddings support) |
| P7.2 | 📋 TODO | Embedding pipeline (generate + store) |
| P7.3 | 📋 TODO | New data → TypeDB routing |
| P7.4 | 📋 TODO | ChromaDB migration tool |
| P7.5 | 📋 TODO | ChromaDB sunset (read-only) |

**Phase 7 Context:** Per DECISION-003, TypeDB 3.x has vector search. Unify semantic + logical queries in single database. See [DECISION-003-TYPEDB-FIRST-STRATEGY.md](../evidence/DECISION-003-TYPEDB-FIRST-STRATEGY.md).

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
| RD-001 | Haskell inference MCP prototype | 📋 TODO | HIGH | Learn domain via Servant API |
| RD-002 | Benchmark Python vs Haskell | 📋 TODO | MEDIUM | After RD-001 |
| RD-003 | Rust rewrite decision | ⏸️ BLOCKED | LOW | Requires RD-002 benchmarks |
| RD-004 | Robotics inference compatibility | 📋 TODO | FUTURE | ROS2/embedded targets |
| RD-005 | TypeDB 3.x alpha evaluation | 📋 TODO | LOW | Monitor releases |

### Frankel Hash R&D (RULE-022 Extension)

**Vision:** Digital twin evidence world with holographic navigation

| ID | Task | Status | Priority | Notes |
|----|------|--------|----------|-------|
| FH-001 | CLI zoom in/out on hash changes | 📋 TODO | HIGH | Navigate document changes at chunk level |
| FH-002 | Hash tree visualization (ASCII/terminal) | 📋 TODO | HIGH | Merkle tree depth navigation |
| FH-003 | 5D visualization framework | 📋 TODO | MEDIUM | Lighting + 3D + deformation mapping |
| FH-004 | Holographic mapping of evidence world | 📋 TODO | MEDIUM | Digital twin navigation for LLM + human |
| FH-005 | Game theory for hash convergence | 📋 TODO | FUTURE | Group theory, equilibria, stability |
| FH-006 | Sync R&D tasks with GitHub issues | 📋 TODO | HIGH | Automate issue creation from backlog |

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

*R&D tracking per RULE-010: Evidence-Based Wisdom*
