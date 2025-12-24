# SESSION: R&D TypeDB Memory MCP Migration Advice

**Date:** 2024-12-24
**Type:** R&D (RULE-015)
**Status:** ADVISORY

---

## Session Metadata

```yaml
session_id: RD-2024-12-24-TYPEDB-MIGRATION
type: rd_advisory
phase: HYPOTHESIZE
rules_applied: [RULE-004, RULE-008, RULE-010, RULE-015]
mcps_used: [claude-mem, filesystem]
budget_flag: LOW (advisory only)
```

---

## Questions Addressed

1. When to migrate to TypeDB memory MCP?
2. How to structure tests (integration/component/unit) for MCP?
3. Whether to dockerize MCPs for agent access?
4. TDD/BDD with heuristics per RULE-004?
5. Claude-mem/ChromaDB bridge for sync?

---

## Key Recommendations

### Migration Timeline

| Milestone | Status | Blocker |
|-----------|--------|---------|
| TypeDB running | ✅ Ready | None |
| Governance MCP | ✅ 11 tools | None |
| Hybrid Router (P3.1) | 📋 TODO | **BLOCKING** |
| Integration Tests (P3.2) | 📋 TODO | **BLOCKING** |
| ChromaDB Bridge | 📋 TODO | P3.1 |

**When to Migrate:** After P3.1 (Hybrid Query Router) complete.

### Test Structure

```
tests/
├── unit/           # TypeDB queries, MCP tools, inference
├── component/      # MCP + TypeDB together (5 pass currently)
├── integration/    # Agent → MCP → TypeDB full stack
└── bdd/            # Executable specs with Given-When-Then
```

### Dockerizing MCPs

**Recommendation:** Start with HTTP, upgrade to WebSocket later.

```yaml
# Target: docker-compose.mcp.yml
services:
  governance-mcp:
    ports: ["8002:8002"]
    depends_on: [typedb]

  memory-mcp:
    ports: ["8003:8003"]
    depends_on: [chromadb, typedb]
```

### ChromaDB Sync Bridge

```
claude-mem → ChromaDB ←→ TypeDB (bidirectional)
                ↓
         Hybrid Query Router
```

---

## Implementation Plan (R&D Flagged)

| Phase | Task | Effort | Budget |
|-------|------|--------|--------|
| P3.1 | Hybrid Query Router | 4h | LOW |
| P3.2 | Integration Tests | 2h | LOW |
| P3.3 | Memory Sync Bridge | 3h | LOW |
| P3.4 | Dockerize MCPs | 4h | MEDIUM |
| P3.5 | BDD Test Suite | 3h | LOW |

**Total:** ~20h across 4-5 sessions

---

## Next Steps

1. Complete P3.1 (Hybrid Router) - enables all other work
2. Add Integration Tests (P3.2) - safety net for sync
3. Build Sync Bridge (P3.3) - connects claude-mem ↔ TypeDB

---

*Per RULE-001: Session Evidence Logging*
*Per RULE-015: R&D Workflow with Human Approval Gate*
