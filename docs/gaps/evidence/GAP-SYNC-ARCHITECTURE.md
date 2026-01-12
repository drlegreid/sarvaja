# Sync Architecture Requirements

> **Gaps:** GAP-SYNC-001, GAP-SYNC-002, GAP-SYNC-003
> **Rule:** DECISION-003 (TypeDB-First)
> **Date:** 2026-01-02
> **Updated:** 2026-01-04

---

## GAP-SYNC-001: Bidirectional Sync

**Status:** PARTIAL (Detection complete, sync tools pending)

**Problem:** TypeDB rules/tasks may diverge from workspace files

**Issues:**
- Rules in TypeDB (36) vs rules in docs/rules/*.md may diverge
- Tasks in TypeDB vs workspace TODO.md may diverge
- Sessions in TypeDB vs evidence/*.md files may diverge

**Current State (2026-01-04):**
- ✅ `governance_sync_status()` detects divergence (GAP-SYNC-002)
- ✅ `workspace_capture_tasks()` syncs TODO.md → TypeDB (one-way)
- ✅ `workspace_link_rules_to_documents()` links rules → markdown
- ✅ Rules 033-036 synced to TypeDB (GAP-CTX-006)
- ⏳ `governance_sync_rules()` - Not implemented
- ⏳ `governance_sync_tasks()` - Not implemented

**Required (Remaining):**
1. ~~`governance_sync_status()`~~ ✅ DONE
2. `governance_sync_rules()` - Bidirectional rule sync with conflict detection
3. `governance_sync_tasks()` - Bidirectional task sync with status tracking

---

## GAP-SYNC-002: Divergence Validation Workflow

**Status:** RESOLVED (2026-01-04)

**Solution:** `governance_sync_status()` MCP tool implemented in `governance/mcp_tools/workspace.py`

**Features:**
- Compares TypeDB rules vs docs/rules/*.md
- Compares TypeDB tasks vs TODO.md
- Counts TypeDB sessions vs evidence/*.md files
- Returns `sync_needed: boolean` for quick status check
- 4 tests in `tests/test_sync_status.py`

---

## Safe/Quality-Driven Approach for MCP Refactoring

```
┌─────────────────────────────────────────────────────────────────────────┐
│               MCP REFACTORING PRIORITY ORDER (SAFE PATH)                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  STEP 1: STABILIZE (Before any refactoring)                             │
│  ─────────────────────────────────────────────                          │
│  □ Run full test suite: pytest tests/ -v                                │
│  □ Document baseline: 1160 tests passing                                │
│  □ Commit current state as checkpoint                                   │
│                                                                          │
│  STEP 2: SYNC VALIDATION (GAP-SYNC-002)                                 │
│  ─────────────────────────────────────────                              │
│  □ Add governance_sync_status() MCP tool                                │
│  □ Compare TypeDB rules vs docs/rules/*.md                              │
│  □ Compare TypeDB tasks vs TODO.md                                      │
│  □ Generate divergence report                                           │
│                                                                          │
│  STEP 3: MCP CONSOLIDATION (TOOL-007)                                   │
│  ────────────────────────────────────                                   │
│  □ Evaluate: Should governance MCP be split into smaller MCPs?          │
│  □ Current: 40+ tools in single governance MCP                          │
│  □ Consider: rules-mcp, tasks-mcp, sessions-mcp, evidence-mcp           │
│                                                                          │
│  STEP 4: BIDIRECTIONAL SYNC (GAP-SYNC-001)                              │
│  ─────────────────────────────────────────                              │
│  □ Implement with conflict detection                                    │
│  □ Last-write-wins vs merge strategy                                    │
│  □ Audit trail for sync operations                                      │
│                                                                          │
│  STEP 5: CONTAINERIZATION (TOOL-006)                                    │
│  ───────────────────────────────────                                    │
│  □ Only after sync is stable                                            │
│  □ Docker container for MCP services                                    │
│  □ Eliminates NPX cold-start issues                                     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

*Per DECISION-003: TypeDB-First Architecture*
