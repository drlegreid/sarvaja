# Sim.ai Platform Roadmap

**Created:** 2024-12-24
**Updated:** 2024-12-31
**Status:** Phase 4 Active (TypeDB Differentiation)
**Vision:** Enterprise-grade AI agent platform with inference, type safety, and institutional knowledge

---

## 🎯 Strategic Vision

```
┌─────────────────────────────────────────────────────────────────┐
│                    SIM.AI PLATFORM VISION                       │
├─────────────────────────────────────────────────────────────────┤
│  Phase 1: Foundation     → Working PoC with basic agents        │
│  Phase 2: Knowledge      → Inherit data lakes, proven patterns  │
│  Phase 3: Simplify       → Replace Agno ChromaDb → Memory MCP   │
│  Phase 4: Differentiate  → TypeDB inference engine (upsell)     │
│  Phase 5: Scale          → Enterprise packaging                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Foundation ✅

**Status:** 100% Complete ✅  
**Timeline:** Dec 2024

### Completed ✅
- [x] Docker stack (LiteLLM, ChromaDB, Ollama, Agents)
- [x] Agno agent orchestration
- [x] GAP-001: ChromaDB integration (HttpClient injection)
- [x] GAP-002: Opik config (now removed)
- [x] GAP-003: Ollama model pull (gemma3:4b)
- [x] LiteLLM DB/auth fix
- [x] Documentation structure with cross-links
- [x] GitHub sync workflow
- [x] RULE-006: Decision logging
- [x] **DECISION-001: Remove Opik** (overkill for current needs)

### Stack (Simplified)
```
LiteLLM (4000) → Ollama (11434) → ChromaDB (8001) → Agents (7777)
```

---

## Phase 2: Knowledge + Custom UI ✅

**Status:** 100% Complete ✅
**Timeline:** Dec 2024
**Priority:** Complete

### Objective
1. Inherit 114+ docs from existing data lakes
2. Build custom session/memory UI (replaces Opik per DECISION-001)

### Data Sources
| Source | Docs | Migrated | Content |
|--------|------|----------|---------|
| claude-mem | 114 | **53** | Governance, sessions, workflows |
| angelgai | ~10 | 0 | Crash recovery, MCP stability |
| localgai | ~20 | 0 | EBMSF, DSM, scripts |

### Deliverables
- [x] Export claude-mem -> sim-ai ChromaDB (53 high-value docs)
- [x] Migration script: `scripts/migrate_claude_mem.py`
- [x] Session dump workflow: `scripts/session_dump.py`
- [x] Agent configured to use sim_ai_knowledge collection
- [x] DSM tracker integrated (governance/dsm_tracker.py)
- [x] Session memory manager (governance/session_memory.py)
- [x] **Custom Governance Dashboard UI** (Trame/Vuetify) - 12 view modules

---

## Phase 3: Simplification ⏸️

**Status:** Deferred (superseded by TypeDB-First)
**Timeline:** TBD
**Priority:** Low (TypeDB handles this better)

### Objective
Replace hacky Agno ChromaDb integration with proven memory MCP.

### Status Update (2024-12-31)
**Decision:** TypeDB-First architecture (DECISION-003) supersedes Phase 3 goals.
- TypeDB now handles structured data (rules, tasks, sessions, agents)
- ChromaDB remains for semantic search (53 docs)
- Hybrid query layer routes appropriately

### Why Deferred?
| Aspect | Original Plan | Current Reality |
|--------|---------------|-----------------|
| Memory | Replace Agno ChromaDb | TypeDB handles structured data |
| Search | Memory MCP | Hybrid: TypeDB (inference) + ChromaDB (semantic) |
| Agents | Keep Agno only | Agno + TypeDB-backed governance |

### Deliverables (Deferred)
- [ ] Keep Agno for agent orchestration only
- [ ] Replace `create_chromadb_knowledge()` with memory MCP
- [x] Preserve bicameral governance model (via TypeDB)
- [x] Test agent knowledge queries (TypeDB client)

---

## Phase 4: Differentiation (TypeDB) 🚧

**Status:** 90% Complete (Active Development)
**Timeline:** Dec 2024 - Jan 2025
**Priority:** #1 (Current Focus)
**Business Value:** Enterprise upsell

### Objective
Build in-house TypeDB-based rules engine for enterprise clients.

### Completed ✅
| Feature | Status | Evidence |
|---------|--------|----------|
| TypeDB Schema | ✅ Complete | governance/schema.tql |
| 25 Governance Rules | ✅ Loaded | governance/data.tql |
| 8 Strategic Decisions | ✅ Tracked | TypeDB + evidence files |
| Rule Inference | ✅ Working | Dependency chains, conflicts |
| MCP Integration | ✅ 40+ tools | governance/mcp_tools/ |
| REST API | ✅ 35 endpoints | governance/routes/ (8 modules) |
| Governance Dashboard | ✅ 12 views | agent/governance_ui/views/ |
| TypeDB Client | ✅ Modular | governance/typedb/ (6 modules) |
| Kanren Constraints | ✅ 39 tests | governance/kanren_constraints.py |

### Remaining Work
| Item | Status | Priority |
|------|--------|----------|
| Haskell client integration | 📋 TODO | FUTURE (RD-HASKELL-MCP) |
| Agent orchestration (ORCH-001-007) | 🚧 IN_PROGRESS | CRITICAL |
| Enterprise packaging | 📋 TODO | Phase 5 |

### Architecture Achieved
```
┌─────────────────────────────────────────────────────────────────┐
│                    TypeDB-First Architecture                     │
├─────────────────────────────────────────────────────────────────┤
│  Governance Dashboard (8081) ──── REST API (8082)               │
│       │                               │                          │
│       └── Trame/Vuetify UI           └── FastAPI + Pydantic     │
│                                           │                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  TypeDB (1729)              │  ChromaDB (8001)              ││
│  │  └── 25 Rules               │  └── 53 Documents             ││
│  │  └── 8 Decisions            │  └── Semantic Search          ││
│  │  └── Tasks, Sessions        │                               ││
│  │  └── Inference Engine       │                               ││
│  └─────────────────────────────┴───────────────────────────────┘│
│                    HYBRID QUERY LAYER                            │
└─────────────────────────────────────────────────────────────────┘
```

### Upsell Potential
- Enterprise compliance (audit trails via TypeDB)
- Complex rule chains (inference engine)
- On-premise deployment (Docker stack)
- Type-safe integrations (Pydantic + TypeDB types)

---

## Phase 5: Scale 📋

**Status:** Future  
**Timeline:** Q2 2025

### Deliverables
- [ ] CI/CD pipeline (GAP-010)
- [ ] Pre-commit hooks (GAP-009)
- [ ] Multi-tenant support
- [ ] Enterprise documentation
- [ ] Pricing/licensing model

---

## Quick Reference

### Current Gaps (by Priority)

| ID | Gap | Priority | Phase |
|----|-----|----------|-------|
| GAP-DATA-001 | Tasks missing content | CRITICAL | 4 |
| GAP-UI-CHAT-001 | No agent chat UI | CRITICAL | 4 |
| GAP-INFRA-004 | Infrastructure dashboard | HIGH | 4 |
| GAP-UI-037-042 | Agent dashboard features | HIGH | 4 |
| GAP-RD-001 | Kanren benefit assessment | MEDIUM | 4 |
| GAP-010 | CI/CD pipeline | LOW | 5 |

### R&D Priority Order

| # | Item | Phase | Status |
|---|------|-------|--------|
| 1 | Agent Orchestration (ORCH-001-007) | 4 | 🚧 IN_PROGRESS |
| 2 | Kanren Context Engineering (KAN-003-005) | 4 | 📋 TODO |
| 3 | Testing Strategy (TEST-001-006) | 4 | 🚧 IN_PROGRESS |
| 4 | Haskell MCP (RD-001-005) | 5 | ⏸️ FUTURE |

---

## Success Metrics

| Phase | Metric | Target | Actual |
|-------|--------|--------|--------|
| 1 | Services healthy | 100% | ✅ 100% |
| 2 | Docs inherited | 114+ | ✅ 53 high-value |
| 2 | Custom UI | Dashboard | ✅ 12 views |
| 3 | Integration clean | No hacks | ⏸️ Deferred |
| 4 | TypeDB working | Inference demo | ✅ 25 rules, inference |
| 4 | MCP tools | 20+ | ✅ 40+ tools |
| 4 | Test coverage | 500+ | ✅ 1,156 tests |
| 5 | Enterprise ready | First client | 📋 Future |

---

## Links

- **Tasks:** [`TODO.md`](TODO.md)
- **Rules:** [`docs/RULES-DIRECTIVES.md`](docs/RULES-DIRECTIVES.md)
- **Workflows:** [`.windsurf/workflows.md`](.windsurf/workflows.md)
- **Deployment:** [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)

---

*Updated: 2024-12-31*
