# Session Log: Strategic Decisions Day

**Date:** 2024-12-24
**Duration:** ~6 hours (multi-session)
**Focus:** Strategic platform architecture decisions

---

## Session Summary

This session made 4 critical strategic decisions that shape the sim-ai platform direction:

| Decision | Summary | Impact |
|----------|---------|--------|
| DECISION-001 | Remove Opik | -8 containers, simpler stack |
| DECISION-002 | Mem0 + Ollama | Validated but superseded |
| DECISION-003 | TypeDB Priority | Inference > vector storage |
| DECISION-004 | No Enterprise Lockdown | Build incrementally on own stack |

---

## Key Outcomes

### 1. Stack Simplification
- Removed Opik (8 containers, ~3GB RAM)
- Focused on core: Agents, LiteLLM, ChromaDB, Ollama

### 2. Strategic Direction: TypeDB
- Vector stores (ChromaDB, Mem0) = storage only
- TypeDB = inference + type safety + reasoning
- Hybrid architecture planned (ChromaDB for search, TypeDB for inference)

### 3. Platform Vision Defined
```
┌─────────────────────────────────────────────────────────────┐
│              Private Cluster AI Platform                    │
├─────────────────────────────────────────────────────────────┤
│  Pillars: Agents | Tasks | Evidence | Rules                │
│  Governance: Workflows | Observability | Conflict Detection│
│  Memory: Short-term (vectors) | Long-term (TypeDB)         │
│  Strategy: Cloud→Local transfer via TypeDB inference       │
└─────────────────────────────────────────────────────────────┘
```

### 4. Independence from Enterprise Lock-in
- No Claude Enterprise dependency
- Cherry-pick patterns from open-source (Minion Skills, SuperClaude)
- RULE-008 ensures rewrite warranty for all strategic tech

---

## Rules Created

| Rule | Purpose |
|------|---------|
| RULE-006 | Decision logging in evidence/ |
| RULE-007 | MCP usage protocol |
| RULE-008 | In-house rewrite principle (technology scorecard) |

---

## Migration Strategy

### Principle: Don't Break What Works

```
Phase 0 (Current):
  - Agents (7777) ✅ Working
  - LiteLLM (4000) ✅ Working
  - ChromaDB (8001) ✅ Working (53 docs)
  - Ollama (11434) ✅ Working

Phase 1 (Add TypeDB):
  - Add TypeDB container (port 1729)
  - Create rules schema
  - Test inference
  - NO CHANGES to existing services

Phase 2 (Hybrid Layer):
  - Create query router
  - Route: semantic → ChromaDB, inference → TypeDB
  - Migrate rules to TypeDB
  - ChromaDB continues for document search

Phase 3 (Integration):
  - Agents use hybrid layer
  - Performance benchmarks
  - v1.0 release
```

### Safety Guarantees

1. **Additive changes only** - TypeDB runs alongside, not replacing
2. **Rollback path** - If TypeDB fails, continue with ChromaDB-only
3. **Test coverage** - Health checks validate each service independently
4. **Incremental migration** - Rules first, then decisions, then tasks

---

## Commits Made

| Commit | Description |
|--------|-------------|
| `b108f42` | DECISION-003 + RULE-008 + test fixes |
| `a98d43e` | Strategic vision with platform pillars |

---

## GitHub Issue

- **Issue #1**: Strategic Decisions Log (DECISION-001 to DECISION-004)
- **URL**: https://github.com/drlegreid/platform-gai/issues/1

---

## Next Steps

1. [ ] Add TypeDB to docker-compose.yml (P1.1)
2. [ ] Create TypeDB schema for 8 rules (P1.2)
3. [ ] Write Python TypeDB client wrapper (P1.3)
4. [ ] Test inference rule: "blocked-by-dependency" (P1.4)
5. [ ] Validate hybrid query works (P2.1)

---

*Session evidence: [evidence/SESSION-DECISIONS-2024-12-24.md](../evidence/SESSION-DECISIONS-2024-12-24.md)*
