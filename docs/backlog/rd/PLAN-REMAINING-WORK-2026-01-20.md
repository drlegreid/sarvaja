# PLAN: Remaining Work Assessment - 2026-01-20

**Status:** COMPLETE | **Linked EPIC:** EPIC-CLEANUP-001
**Created:** 2026-01-20 | **Source:** DSP Session Assessment
**Completed:** 2026-01-21 (overnight autonomous session)

---

## Executive Summary

Current state: **253+ gaps resolved, 0 OPEN, 1 MITIGATED**

Infrastructure healthy (TypeDB + ChromaDB operational, 65 rules, 102 tasks tracked).

**Overnight Session Results (2026-01-20/21):**
- ✅ GAP-TOON-MIGRATION: 9 files migrated, 157 tests pass
- ✅ GAP-HEALTH-AUTORECOVERY: Consent-based toggle via SARVAJA_AUTO_RECOVERY
- ✅ Document MCP Investigation: Created RD-DOCUMENT-MCP-SERVICE.md (DEFERRED)
- ✅ ATEST-001 to ATEST-008: All agent testing tasks complete, 27 tests in test_agent_platform.py
- ✅ MULTI-007: Observability infrastructure verified complete (API + UI + controllers)
- ✅ Data Quality Fix: Gap parser excludes "Recently Resolved" section, 5 new tests
- **Test Suite:** 209 unit tests passing (post-session verification)

---

## Priority 1: HIGH IMPACT (Operational Quality)

### GAP-TOON-MIGRATION (✅ RESOLVED 2026-01-20)
- **Issue:** 9 MCP tool files use `json.dumps` instead of `format_mcp_result`
- **Resolution:** Migrated all 9 files, 157/157 unit tests pass
- **Files:** `governance/mcp_tools/evidence/*.py`

### GAP-HEALTH-AUTORECOVERY (✅ RESOLVED 2026-01-20)
- **Issue:** Health hook detects container failures but can't auto-recover
- **Resolution:** Added `SARVAJA_AUTO_RECOVERY` env var for consent-based control
- **Files:** `.claude/hooks/healthcheck.py`, `healthcheck_formatters.py`, `core/base.py`, `README.md`

---

## Priority 2: MEDIUM IMPACT (R&D - Testing)

### EPIC: Agent Testing (ATEST-001 → ATEST-008)

| Task | Description | Status |
|------|-------------|--------|
| ATEST-001 | Design test pyramid for agent platform | ✅ DONE |
| ATEST-002 | Implement E2E agent workflow test | ✅ DONE |
| ATEST-003 | Create multi-agent concurrency tests | ✅ DONE |
| ATEST-004 | Build delegation chain validator | ✅ DONE |
| ATEST-005 | Add trust evolution simulation | ✅ DONE |
| ATEST-006 | Integrate Kanren with agent tests | ✅ DONE |
| ATEST-007 | Performance benchmark suite | ✅ DONE |
| ATEST-008 | Agent recovery scenario tests | ✅ DONE |

**Outcome:** 8/8 tasks COMPLETE. 27 tests covering agent platform workflows.

### MULTI-007: Observability Infrastructure (✅ RESOLVED 2026-01-21)
- **Issue:** Dashboard observability components partially implemented
- **Resolution:** Verified all components complete: agent status API, conflict detection, monitor events, dashboard UI, controller bindings
- **Effort:** VERIFIED

---

## Priority 3: LOWER IMPACT (Feature Enhancement)

### EPIC: Document Viewer (DOCVIEW-001 → DOCVIEW-005)

| Task | Description | Status |
|------|-------------|--------|
| DOCVIEW-001 | Research document viewer libraries | OPEN |
| DOCVIEW-002 | Evaluate markdown-it, vue-pdf, csv-parser | OPEN |
| DOCVIEW-003 | Design fullscreen modal with lazy loading | OPEN |
| DOCVIEW-004 | PoC: Basic Markdown + CSV viewer | OPEN |
| DOCVIEW-005 | TDD: Document viewer test specs | OPEN |

### EPIC: Frankel Hash Visualization (FH-001 → FH-008)

| Task | Description | Status |
|------|-------------|--------|
| FH-001 | CLI zoom in/out on hash changes | ✅ CORE |
| FH-002 | Hash tree visualization (ASCII/terminal) | ✅ CORE |
| FH-003 | 5D visualization framework | OPEN |
| FH-004 | Holographic mapping of evidence world | OPEN |
| FH-005 | Game theory for hash convergence | FUTURE |
| FH-007 | Dashboard hash display on refresh | ✅ CORE |
| FH-008 | Test coverage effectiveness assessment | ✅ TDD |

---

## Priority 4: MITIGATED (External)

### GAP-MCP-PAGING-001
- **Status:** MITIGATED
- **Issue:** External MCP tools (e.g., Podman logs) return unbounded output
- **Workaround:** Use Bash with `head/tail` instead of MCP tools
- **Resolution:** Requires upstream PR to MCP server vendors

---

## Session Violations (2026-01-20)

| Rule | Violation | Resolution |
|------|-----------|------------|
| TEST-FIX-01-v1 | Marked GAP-MONITOR-IPC-001 resolved without testing API endpoint | Fixed: Added observability router to api.py |
| RULE-023 | Shipped code without full validation | Fixed: Added router registration, verified syntax |

---

## Recommended Execution Order

1. ~~**GAP-TOON-MIGRATION** - Finish in-progress work~~ ✅ DONE
2. ~~**GAP-HEALTH-AUTORECOVERY** - Operational stability~~ ✅ DONE
3. ~~**Document MCP Service Investigation** - User-requested analysis~~ ✅ DONE (DEFERRED)
4. ~~**ATEST-001** - Foundation for agent testing~~ ✅ DONE
5. ~~**FH-007** - Dashboard hash display on refresh~~ ✅ ALREADY DONE
6. ~~**ATEST-002 to ATEST-008** - Agent testing suite~~ ✅ DONE (27 tests)
7. ~~**MULTI-007** - Observability infrastructure~~ ✅ VERIFIED

---

## Data Quality Note

~~The `backlog_unified()` tool incorrectly reads "Recently Resolved" gaps from GAP-INDEX.md as open.~~

**Fixed (2026-01-21):** Updated `governance/utils/gap_parser.py` to track section headers and skip gaps in "Recently Resolved" sections. Added 5 unit tests in `tests/unit/test_gap_parser.py`.

---

*Per DATA-ARCH-CLEANUP DSM: Plans stored as documents, linked to EPICs*
