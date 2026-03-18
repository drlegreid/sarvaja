# Platform Reliability Plan — RELIABILITY-PLAN-01-v1

**Goal**: Platform fully auditable, configurable, scalable & resilient by 2026-02-21 11:00 GMT+2
**Created**: 2026-02-20
**Status**: COMPLETE

---

## Priority Stack (ordered by user impact)

### P0: Session Histogram — No Data Visible
**Gap**: Metrics view has per-day TABLE but no chart/histogram visualization.
**Root Cause**: `metrics_view.py` builds `build_per_day_table()` only. No Plotly chart.
**Fix**: Add `build_metrics_histogram()` using Plotly pattern from `sessions/timeline.py`.
**Files**: `agent/governance_ui/views/metrics_view.py`
**TDD**: `tests/unit/test_metrics_view.py` — add test for histogram builder function
**Effort**: 30 min

### P1: Full-Data Session View (thoughts, MCP calls, tool pairing)
**Gap**: User cannot see a session with full data set in UI. Validation API exists (`/sessions/{id}/validate`) but results not surfaced in detail view.
**Fix**: Add "Content Validation" card in session detail showing:
- Thinking blocks count + total chars
- MCP server distribution (pie/bar or chip list)
- Tool call pairing stats (total, orphaned, errors)
- Parse error count
**Files**: `agent/governance_ui/views/sessions/detail.py`, `agent/governance_ui/controllers/sessions.py`
**TDD**: `tests/unit/test_session_detail_validation.py`
**Effort**: 45 min

### P2: Cross-Entity Navigation — Projects > Sessions
**Gap**: 107 chat sessions have no project_id. No visible project > session linkage in UI.
**Status**: Projects exist in TypeDB. Sessions exist. Link field (`cc_project_slug`) exists but only populated for CC-ingested sessions.
**Fix**:
  a. Session detail shows project link (clickable chip)
  b. Project detail shows session count + list link
  c. Ensure CC-ingested sessions have project linkage (H-SESSION-CC-002 already checks this)
**Files**: `agent/governance_ui/views/sessions/detail.py`, session controller
**Effort**: 30 min

### P3: Synthetic TDD Suite (entity graph validation)
**Gap**: No test seeds a full entity graph (Project > Task > Rule > Session) and validates relationships.
**Fix**: Create `tests/unit/test_entity_graph_tdd.py` that:
  a. Seeds Project + Task + Rule + Session via service layer mocks
  b. Validates cross-references (task.linked_sessions, session.cc_project_slug)
  c. Validates heuristic checks pass on well-formed data
**TDD**: The test IS the deliverable
**Effort**: 40 min

### P4: Real-Data TDD Suite (CC JSONL validation)
**Gap**: SessionContentValidator works but no test runs against actual CC session files on disk.
**Fix**: Create `tests/unit/test_real_data_validation.py` that:
  a. Discovers real CC JSONL files from `~/.claude/projects/`
  b. Runs `validate_session_content()` on each
  c. Asserts basic sanity: entry_count > 0, has_user_messages, has_assistant_messages
  d. Skips gracefully if no CC sessions on machine
**Files**: `tests/unit/test_real_data_validation.py`
**Effort**: 30 min

### P5: Critical UI Bugs (auditability blockers)
**Known bugs from E2E**:
- BUG-UI-SESSIONS-001: Pivot toggle non-functional
- BUG-UI-TASKS-001: Create form validation
- BUG-UI-AGENTS-001: Pause/resume returns 404
**Fix**: Triage and fix top 2 highest-impact bugs
**Effort**: 45 min

### P6: MCP Task/Rule Integration Check
**Gap**: MCP tools (gov-tasks, gov-core) may not be reliable for project management workflows.
**Fix**: Write integration smoke test: create task, update status, link to session, verify chain.
**Effort**: 20 min

---

## Execution Order

1. P0 (Histogram) — immediate visual win
2. P1 (Full-data session) — auditability
3. P4 (Real-data TDD) — validates real data quality
4. P3 (Synthetic TDD) — validates entity relationships
5. P2 (Cross-entity nav) — navigability
6. P5 (UI bugs) — polish
7. P6 (MCP integration) — future workflow readiness

---

## Success Criteria

- [x] Session histogram shows bar chart with per-day session counts (VSparkline in metrics_view.py)
- [x] At least one session detail shows thinking blocks, MCP distribution, tool pairing (validation_card.py)
- [x] Real-data TDD suite runs against actual CC JSONL and reports validation metrics (15 tests, 246K entries)
- [x] Synthetic TDD suite validates entity graph relationships (24 tests)
- [x] All unit tests pass — **10,515 passed** (baseline was 10,447)
- [x] No new test failures introduced
- [x] Cross-entity navigation: clickable project slug + agent link in session detail
- [x] MCP integration chain test: task CRUD + session lifecycle + rule linkage (4 integration tests)
- [x] Dashboard container restarted with all UI changes
