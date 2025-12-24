# R&D Backlog - Sim.ai PoC

**Last Updated:** 2024-12-24
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
| **Rules** | RULE-001 to RULE-014 | ✅ TypeDB + Markdown | TypeDB inference |

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
│       │   └── Documents (53)  │  └── Rules (14) + Decisions    │
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
| P3.4 | 📋 TODO | Update agents to use hybrid layer |
| P3.5 | 📋 TODO | Performance benchmarks |
| P3.6 | 📋 TODO | v1.0 release |

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

## Strategic R&D: TypeDB 3.x Frontrun

**Context:** TypeDB 3.x is ALPHA. We use stable 2.29.1.

**Opportunity:** Build in-house inference engine:
- Study TypeDB 3.x alpha features
- Build lightweight Rust/Python engine
- Maintain 2.x data format compatibility

**Why:** Strategic independence + performance optimization.

---

*R&D tracking per RULE-010: Evidence-Based Wisdom*
