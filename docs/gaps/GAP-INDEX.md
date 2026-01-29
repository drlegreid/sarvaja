# Gap Index - Sarvaja

**Last Updated:** 2026-01-29 | **Source of Truth:** TypeDB via `backlog_get()`

| Status | Count |
|--------|-------|
| OPEN | 1 |
| PARTIAL | 0 |
| DEFERRED | 1 |
| MITIGATED | 1 |
| RESOLVED | 256+ |

> **Test Traceability:** Run `robot --include GAP-*` to execute all 60 gap regression tests.

> Use `mcp__gov-tasks__backlog_get()` for current backlog.
> Detailed evidence in [evidence/](evidence/) per GAP-META-001.
> Archived gaps: [GAP-INDEX-ARCHIVE.md](GAP-INDEX-ARCHIVE.md)

---

## Active Gaps

| ID | Priority | Status | Category | Evidence | Tests |
|----|----------|--------|----------|----------|-------|
| GAP-SESSION-METRICS-CORRELATION | HIGH | RESOLVED | analytics | Per SESSION-METRICS-01-v1 | 19 pytest + 7 Robot |
| GAP-SESSION-METRICS-CONTENT | HIGH | OPEN | analytics | Per SESSION-METRICS-01-v1 | - |
| GAP-LANGGRAPH-QUALITY-001 | MEDIUM | DEFERRED | enhancement | [evidence](evidence/GAP-LANGGRAPH-QUALITY-001.md) | - |
| GAP-MCP-PAGING-001 | MEDIUM | MITIGATED | tooling | [evidence](evidence/GAP-MCP-PAGING-001.md) | - |

> **Notes:**
> - GAP-SESSION-METRICS-CORRELATION: RESOLVED (2026-01-29) - correlation.py with 19 pytest + 7 Robot tests
> - GAP-SESSION-METRICS-CONTENT: Deliberate content/decision search + session ID + git branch filtering
> - GAP-MCP-PAGING-001: MITIGATED - External MCP tools, workarounds documented
> - GAP-LANGGRAPH-QUALITY-001: DEFERRED (2026-01-26) - Option C selected, revisit when multi-agent active

## Recently Resolved (2026-01-27)

| ID | Resolution |
|----|------------|
| GAP-RULE-DATA-QUALITY-001 | RESOLVED - Rule metadata fixes, 18+ null values corrected |
| GAP-API-500-001 | CLOSED (2026-01-25) - 3rd party dependency, mitigations in place |

## Previously Resolved (2026-01-21)

| ID | Resolution |
|----|------------|
| GAP-TEST-EVIDENCE-001 | BDD evidence module with rule traceability (TEST-EVID-01-v1) |
| GAP-TEST-EVIDENCE-002 | session_test_result MCP tool + pytest --session-report integration |
| GAP-TEST-EVIDENCE-003 | TEST-TDD-01-v1 + TEST-BDD-01/EVID-01 updates for TDD/BDD governance |
| GAP-UI-TRACE-001 | Query params parsing + headers/params display in trace bar |
| GAP-SYNC-AUTO-001 | File watcher module with debounced queue + category sync callbacks |
| GAP-SESSION-THOUGHT-001 | PostToolUse hook + state file persistence (SESSION-HOOK-01-v1) |
| GAP-UI-SEARCH-001 | Server-side search param + filter module (governance/routes/rules/search.py) |
| GAP-UI-AUDIT-002 | Option C: Client-side sessionStorage for window-isolated nav state |
| GAP-MONITOR-IPC-001 | Audit file bridge: MCP→file→API→Dashboard cross-process events |
| GAP-TASK-DATA-QUALITY-001 | 3/3 core: status migration, task_create defaults, workspace_capture_tasks mapping |
| GAP-DSP-NOTIFY-001 | 5/5 criteria: session blocking, dashboard alert, rule, /deep-sleep command |
| GAP-UI-AUDIT-001 | All 12 P1-P3 tasks implemented |
| GAP-UI-AUDIT-004 | Audit trail filtering implemented |

---

## Quick Commands

```bash
# Get current backlog (TypeDB source)
mcp__gov-tasks__backlog_get(limit=20)

# Get critical gaps only
mcp__gov-tasks__gaps_critical()

# Get gap summary stats
mcp__gov-tasks__gaps_summary()

# Sync gaps to TypeDB (dry run)
mcp__gov-tasks__workspace_sync_gaps_to_typedb(dry_run=True)
```

---

## Data Architecture

```
TypeDB (Source of Truth)
    └── task entities with item_type="gap"
         └── document_path → evidence/*.md

GAP-INDEX.md (View)
    └── Auto-regeneratable from TypeDB
    └── Human-readable summary

evidence/*.md (Immutable)
    └── Detailed analysis per gap
    └── Write-once, archive on resolution
```

---

*Per DOC-GAP-ARCHIVE-01-v1: RESOLVED gaps move to archive.*
*Per DATA-ARCH-CLEANUP DSM: TypeDB = source of truth.*
