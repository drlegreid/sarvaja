# Gap Index - Sarvaja

**Last Updated:** 2026-03-20 | **Source of Truth:** TypeDB via `backlog_get()`

| Status | Count |
|--------|-------|
| OPEN | 2 |
| PARTIAL | 0 |
| DEFERRED | 2 |
| MITIGATED | 1 |
| RESOLVED | 262+ |

> **Test Traceability:** Run `robot --include GAP-*` to execute all 60 gap regression tests.

> Use `mcp__gov-tasks__backlog_get()` for current backlog.
> Detailed evidence in [evidence/](evidence/) per GAP-META-001.
> Archived gaps: [GAP-INDEX-ARCHIVE.md](GAP-INDEX-ARCHIVE.md)

---

## Active Gaps

| ID | Priority | Status | Category | Evidence | Tests |
|----|----------|--------|----------|----------|-------|
| GAP-SESSION-METRICS-CORRELATION | HIGH | RESOLVED | analytics | Per SESSION-METRICS-01-v1 | 19 pytest + 7 Robot |
| GAP-SESSION-METRICS-CONTENT | HIGH | RESOLVED | analytics | Per SESSION-METRICS-01-v1 | 19 pytest + 6 Robot |
| GAP-SESSION-METRICS-ERRORS | MEDIUM | RESOLVED | analytics | Per SESSION-METRICS-01-v1 | 7 pytest + 4 Robot |
| GAP-SESSION-METRICS-PLATFORM | MEDIUM | RESOLVED | analytics | Per SESSION-METRICS-01-v1 | 18 pytest + 4 Robot |
| GAP-SESSION-METRICS-TEMPORAL | LOW | RESOLVED | analytics | Per SESSION-METRICS-01-v1 | 15 pytest + 5 Robot |
| GAP-SESSION-METRICS-UI | HIGH | RESOLVED | analytics | Per SESSION-METRICS-01-v1 | 14 pytest + 6 pytest |
| GAP-GOVSESS-CAPTURE-001 | CRITICAL | RESOLVED | gov-sessions | [evidence](evidence/GAP-GOVSESS-CAPTURE-001.md) | 19+13 pytest |
| GAP-GOVSESS-TIMESTAMP-001 | HIGH | RESOLVED | gov-sessions | [evidence](evidence/GAP-GOVSESS-CAPTURE-001.md) | 15 pytest |
| GAP-GOVSESS-AGENT-001 | HIGH | RESOLVED | gov-sessions | [evidence](evidence/GAP-GOVSESS-CAPTURE-001.md) | 15 pytest |
| GAP-GOVSESS-DURATION-001 | MEDIUM | RESOLVED | gov-sessions | [evidence](evidence/GAP-GOVSESS-CAPTURE-001.md) | 15 pytest |
| GAP-LANGGRAPH-QUALITY-001 | MEDIUM | DEFERRED | enhancement | [evidence](evidence/GAP-LANGGRAPH-QUALITY-001.md) | - |
| GAP-MCP-PAGING-001 | MEDIUM | MITIGATED | tooling | [evidence](evidence/GAP-MCP-PAGING-001.md) | - |
| GAP-STALE-TOOL-COUNT | MEDIUM | OPEN | data-integrity | Watcher doesn't update tool_count on re-scan | 1 xfail E2E |
| GAP-TASK-SESSION-LINK | MEDIUM | OPEN | data-integrity | update_task() lacks auto-linking on status transition | H-TASK-005 |
| GAP-SESSION-DISCOVERY | HIGH | DEFERRED | ingestion | Only 78/1911 JSONL files discovered; content indexer non-functional | H-INGESTION-001 |

> **Notes:**
> - GAP-GOVSESS-CAPTURE-001: RESOLVED (2026-02-11) - MCP auto-session tracker (`auto_session.py`) captures non-chat tool calls. Chat bridge + MCP tracker = full coverage. 13 new tests.
> - GAP-GOVSESS-TIMESTAMP-001: RESOLVED (2026-02-11) - `session_repair.py` parses dates from session IDs, generates reasonable timestamps. Repair script: `scripts/repair_backfill_sessions.py`. 15 tests.
> - GAP-GOVSESS-AGENT-001: RESOLVED (2026-02-11) - `session_repair.py` assigns "code-agent" to backfilled sessions lacking agent_id. 15 tests.
> - GAP-GOVSESS-DURATION-001: RESOLVED (2026-02-11) - `session_repair.py` detects and caps unrealistic durations (>24h). 15 tests.
> - GAP-SESSION-METRICS-CORRELATION: RESOLVED (2026-01-29) - correlation.py with 19 pytest + 7 Robot tests
> - GAP-SESSION-METRICS-CONTENT: RESOLVED (2026-01-29) - search.py + parse_log_file_extended with 19 pytest + 6 Robot tests
> - GAP-SESSION-METRICS-ERRORS: RESOLVED (2026-01-29) - is_api_error detection, error_rate calculation with 7 pytest + 4 Robot tests
> - GAP-SESSION-METRICS-PLATFORM: RESOLVED (2026-01-29) - evidence.py + typedb_queries.py with 18 pytest + 4 Robot tests
> - GAP-SESSION-METRICS-TEMPORAL: RESOLVED (2026-01-29) - temporal.py with query_at_time, query_date_range, activity_timeline with 15 pytest + 5 Robot tests
> - GAP-SESSION-METRICS-UI: RESOLVED (2026-01-29) - REST API routes + dashboard view + navigation + controller with 14 route + 6 data access tests
> - GAP-MCP-PAGING-001: MITIGATED - External MCP tools, workarounds documented
> - GAP-LANGGRAPH-QUALITY-001: DEFERRED (2026-01-26) - Option C selected, revisit when multi-agent active
> - GAP-STALE-TOOL-COUNT: OPEN (2026-03-20) - Watcher updates end_time/cc_external_name but NOT cc_tool_count. Fix: add tool_count to update_kwargs in claude_watcher.py
> - GAP-TASK-SESSION-LINK: OPEN (2026-03-20) - create_task() auto-links correctly, but update_task() does NOT auto-link on status transition. 49/59 worked tasks unlinked, mostly pre-2026-02-09. Fix: add auto-linking to update_task() for IN_PROGRESS/DONE transitions
> - GAP-SESSION-DISCOVERY: DEFERRED (2026-03-20) - ChromaDB at 2.4% capacity (614 docs, 26MB/1GB). Capacity concern DISMISSED. Real blockers: (a) auto-discovery only found 78 of 1911 JSONL files, (b) sim_ai_session_content collection never created, (c) scheduler ran 39 scans but only 1 session ingested. Revisit when discovery pipeline fixed

## Recently Resolved (2026-02-11)

| ID | Resolution |
|----|------------|
| GAP-GOVSESS-CAPTURE-001 | RESOLVED - MCP auto-session tracker for non-chat tool calls + chat bridge |
| GAP-GOVSESS-TIMESTAMP-001 | RESOLVED - Session repair service parses dates from session IDs |
| GAP-GOVSESS-AGENT-001 | RESOLVED - Session repair assigns "code-agent" to backfilled sessions |
| GAP-GOVSESS-DURATION-001 | RESOLVED - Duration capping and detection in session repair service |

## Previously Resolved (2026-01-27)

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
