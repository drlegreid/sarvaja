# Sim.ai Platform Roadmap

**Created:** 2024-12-24  
**Status:** Active R&D  
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

## Phase 1: Foundation ✅ (Current)

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

## Phase 2: Knowledge + Custom UI 📋

**Status:** 50% Complete  
**Timeline:** Dec 2024 - Jan 2025  
**Priority:** #1

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
- [ ] Import governance docs as agent knowledge
- [ ] Migrate scripts (dsm_tracker, memory_audit)
- [ ] Update agent instructions with inherited patterns
- [ ] Build custom session/memory UI

---

## Phase 3: Simplification 📋

**Status:** Not Started  
**Timeline:** Jan 2025 (1-2 days)  
**Priority:** #2

### Objective
Replace hacky Agno ChromaDb integration with proven memory MCP.

### Why?
| Aspect | Agno ChromaDb | Memory MCP |
|--------|---------------|------------|
| Maturity | New, undocumented | Proven (114 docs) |
| Integration | Hacky (_client injection) | Clean MCP protocol |
| Features | Basic vector search | Knowledge graph |

### Deliverables
- [ ] Keep Agno for agent orchestration only
- [ ] Replace `create_chromadb_knowledge()` with memory MCP
- [ ] Preserve bicameral governance model
- [ ] Test agent knowledge queries

---

## Phase 4: Differentiation (TypeDB) 📋

**Status:** R&D Planning  
**Timeline:** Q1 2025 (weeks)  
**Priority:** #3  
**Business Value:** Enterprise upsell

### Objective
Build in-house TypeDB-based rules engine for enterprise clients.

### Features
| Feature | Benefit |
|---------|---------|
| Type System | Compile-time safety (Haskell) |
| Rule Inference | Auto-derive facts |
| Symbolic Reasoning | Logic-based queries |
| Audit Trail | Compliance ready |

### Phases
1. Prototype TypeDB rules schema
2. Build inference rules for governance
3. Haskell client integration (type-safe)
4. Migration path from ChromaDB
5. Enterprise packaging

### Upsell Potential
- Enterprise compliance
- Complex rule chains
- On-premise deployment
- Type-safe integrations

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
| GAP-003 | Ollama model | High | 1 |
| GAP-011 | OctoCode MCP | High | 2 |
| GAP-013 | MCP workflow | High | 2 |
| GAP-004 | Grok API key | Medium | 1 |
| GAP-005 | Task backlog UI | Medium | 3 |
| GAP-006 | Sync agent | Medium | 3 |

### R&D Priority Order

| # | Item | Phase | Effort |
|---|------|-------|--------|
| 1 | Inherit Data Lakes | 2 | 1-2 days |
| 2 | TypeDB Solution | 4 | Weeks |
| 3 | Replace Agno ChromaDb | 3 | 1-2 days |
| 4 | OctoCode MCP | 2 | 30 min |

---

## Success Metrics

| Phase | Metric | Target |
|-------|--------|--------|
| 1 | Services healthy | 100% |
| 2 | Docs inherited | 114+ |
| 3 | Integration clean | No hacks |
| 4 | TypeDB working | Inference demo |
| 5 | Enterprise ready | First client |

---

## Links

- **Tasks:** [`TODO.md`](TODO.md)
- **Rules:** [`docs/RULES-DIRECTIVES.md`](docs/RULES-DIRECTIVES.md)
- **Workflows:** [`.windsurf/workflows.md`](.windsurf/workflows.md)
- **Deployment:** [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)

---

*Updated: 2024-12-24*
