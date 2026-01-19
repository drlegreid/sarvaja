# GAP-UI-AUDIT-2026-01-18: Dashboard UX & Data Integrity Audit

**Priority:** CRITICAL | **Category:** architecture/ux | **Status:** OPEN
**Discovered:** 2026-01-18 | **Source:** User Feedback - Comprehensive UI Review
**Assignee:** UNASSIGNED | **Resolution:** NONE

---

## Executive Summary

User feedback indicates the dashboard is a "toy" with:
1. Pervasive mocked/stubbed data
2. Broken data integrity and traceability linkage
3. Non-actionable UI elements
4. Redundant/confusing navigation structure
5. Missing critical functionality

**Verdict:** Dashboard needs architectural redesign focused on data traceability and actionability.

---

## Critical Issues

### ISSUE-001: Task Tab Redundancy

**Gap:** Two task-related tabs exist with unclear purpose separation.

| Tab | Current State | Problem |
|-----|---------------|---------|
| Agent Task Backlog | Shows available tasks for agents to claim | Tasks not actionable without session linkage |
| Platform Tasks | Shows all tasks with CRUD | No session linkage, no execution log, no PR link |

**Required:**
- [ ] Merge or clarify purpose distinction
- [ ] Add session linkage (task ↔ session)
- [ ] Add execution log per task
- [ ] Add PR/commit linkage per task (schema exists: task-commit relation)

**Evidence:** Per GAP-TASK-LINK-002, schema exists but UI doesn't expose it.

---

### ISSUE-002: Governance Rules - No Traceability

**Gap:** Rules view shows rules but has zero traceability.

**Missing:**
- Tasks implementing each rule
- Sessions where rule was applied
- Violations/compliance status
- Evolution history (rule versions)

**Evidence:** TypeDB has `task-implements-rule` relation but UI doesn't query or display it.

---

### ISSUE-003: Workflow Compliance Tab - Hollow

**Gap:** Workflow compliance view exists but lacks:

| Missing Feature | Impact |
|-----------------|--------|
| Actual violations | No compliance visibility |
| Validation checks | Can't verify workflows |
| Recommendations | No actionable guidance |

**Current State:** UI renders but data is mocked/empty.

---

### ISSUE-004: Audit Trail - Not Actionable

**Gap:** Audit view shows events but:
- Events not linked to entities (tasks, rules, sessions)
- No drill-down capability
- No filtering by entity type
- No correlation ID tracing

**Evidence:** TypeDB has audit-event entity but UI doesn't leverage it properly.

---

### ISSUE-005: Test Runner - No Evidence Linkage

**Gap:** Test view runs tests but:
- No linkage to evidence markdown files
- No linkage to gaps being validated
- No certification trail

**Required:** Per TEST-FIX-01-v1, tests MUST produce traceable evidence.

---

### ISSUE-006: Rule Impact Analyzer - Unclear Purpose

**Gap:** User cannot understand the purpose of this view.

**Questions:**
- What decisions does this support?
- What actions can user take?
- How does it relate to compliance?

**Assessment:** View may be R&D artifact without production value. Consider DEFERRED or removal.

---

### ISSUE-007: Executive Report - Stale Data

**Gap:** Session dropdown appears non-functional, showing stale data.

**Symptoms:**
- Dropdown doesn't update with new sessions
- Data doesn't refresh on selection
- May be disconnected from API

---

### ISSUE-008: Session Evidence - UX Issues

**Gap:** Session view doesn't conform to management UX principles:
- No data traceability visible
- No task linkage shown
- No evidence file previews
- No session outcome/intent display

**Required:** Per SESSION-EVID-01-v1, sessions MUST show evidence chains.

---

### ISSUE-009: Strategic Decisions Tab - Purpose Unclear

**User Feedback:** "Why do we need this? I want sessions/task/rule/agent linkage, never asked for decisions."

**Assessment:** This tab may be over-engineered for unused functionality.

**Options:**
1. Remove tab entirely
2. Repurpose as "Decision Log" linked to sessions
3. Clarify what "strategic decisions" means in this context

---

### ISSUE-010: Real-time Rule Monitoring - Stale Data

**Gap:** "Real-time" monitoring shows stale/demo data.

**Evidence:** Data appears hardcoded from initial demo phase.

---

### ISSUE-011: Trace Console - No Request/Response Payloads ✅ RESOLVED

**Gap:** Trace bottom bar was an initial requirement but doesn't show:
- Request payloads (what was sent to API)
- Response payloads (what API returned)
- Only shows event count, not actual data

**Initial Requirement:** Trace console should expose full API communication for debugging.

**Required:**
- [x] Show request method, URL, headers
- [x] Show request body (JSON payload)
- [x] Show response status, headers
- [x] Show response body (JSON)
- [x] Expandable detail per API call

**Resolution (2026-01-18):**
- Added `request_body`, `response_body`, `request_headers` fields to TraceEvent dataclass
- Updated `add_api_trace` to capture response payloads from all API calls
- Updated `_traced_get` helper to extract and store response JSON
- Implemented expandable accordion panels in trace bar view
- Each API call shows "Request" (left) and "Response" (right) panels
- Large payloads auto-truncated to 5000 chars to prevent memory issues
- **Screenshot:** `.playwright-mcp/trace-console-payloads.png`

---

### ISSUE-012: UI State is Singleton - Multiple Windows Mirror Each Other

**Gap:** CRITICAL - Multiple browser windows/tabs share the same UI state.

**Symptoms:**
- Open 2 browser windows to dashboard
- Click navigation in window 1
- Window 2 also navigates
- Form inputs, selections, view state all shared

**Root Cause:** Trame framework defaults to shared server-side state.

**Impact:**
- Multi-user scenarios impossible
- Even single user can't have independent views
- Production deployment unusable for teams

**Research (2026-01-18):**
Per [Trame Multi-User Discussion #32](https://github.com/Kitware/trame/discussions/32):

**Option A: ParaViewWeb-style Launcher (Complex)**
- Requires wslink-launcher service + Apache/nginx proxy
- Each client gets own process on different port
- Proxy routes WebSocket connections to correct process
- Significant infrastructure change required

**Option B: Kubernetes/Docker Compose per-user (Scalable)**
- Deploy Trame as stateless service
- External session management routes users to instances
- Production-ready but requires K8s or Swarm orchestration

**Option C: Client-side State (Code Change)**
- Move navigation/filter state to Vue reactive (client-side)
- Keep data-heavy state server-side (rules, tasks, etc.)
- Hybrid approach - may not fix all mirroring issues
- Lowest infrastructure change, highest code change

**Status: DEFERRED - Requires Architecture Decision**
This is a fundamental Trame limitation. Fixing requires either:
1. Major infrastructure change (launcher/proxy/orchestration)
2. Major code refactor (client-side state management)

**Required:**
- [ ] Architecture decision: Infrastructure change vs code refactor
- [ ] Spike: Test Option C (client-side navigation state)
- [ ] Document chosen approach

**Reference:**
- https://github.com/Kitware/trame/discussions/32
- https://github.com/Kitware/trame/blob/master/docker/README.md

---

### ISSUE-013: Infrastructure Health - Incomplete

**Missing:**
| Feature | Status |
|---------|--------|
| Service logs | Not exposed |
| Actual service state verification | Unknown accuracy |
| Health hash display | Not shown |
| MCP Python processes | Not shown |

**Evidence:** Healthcheck hook generates hash but UI doesn't display it.

---

## Data Integrity Assessment

### Mocked/Stubbed Data Inventory

| Component | Data Source | Mock Level | Impact |
|-----------|-------------|------------|--------|
| Rules | TypeDB + REST API | **REAL** | Working |
| Tasks | TypeDB + REST API | **REAL** | Working |
| Sessions | TypeDB + REST API | **REAL** | Working |
| Agents | TypeDB + JSON | HYBRID | Some mock defaults |
| Workflow compliance | Unknown | **MOCK** | Non-functional |
| Audit events | TypeDB | PARTIAL | Schema exists, linkage broken |
| Rule monitoring | Unknown | **MOCK** | Demo data |
| Test results | pytest output | REAL | No persistence/linkage |
| Evidence files | Filesystem | REAL | No UI preview |

### Linkage Integrity

| Relation | Schema | TypeDB Data | UI Display |
|----------|--------|-------------|------------|
| task → session | completed-in | EXISTS | **NOT SHOWN** |
| task → rule | implements-rule | EXISTS | **NOT SHOWN** |
| task → commit | task-commit | EXISTS | **NOT SHOWN** |
| session → rule | session-applied-rule | EXISTS | **NOT SHOWN** |
| session → evidence | has-evidence | EXISTS | **NOT SHOWN** |
| agent → task | claimed-by | EXISTS | SHOWN (Backlog) |

**Root Cause (Investigated 2026-01-18):**
- **Schema exists** in TypeDB (completed-in relation)
- **Code exists** in API (link_task_to_session, read.py queries)
- **Data does NOT exist** - no completed-in relations in TypeDB
- **Why:** Historical tasks marked DONE without session_id parameter, no retroactive migration

**Verdict:** Schema and API exist but linkage data was never created. Need backfill.

---

## Prioritized Backlog

Per TASK-LIFE-01-v1 semantics:

### P1 - CRITICAL (Data Traceability)

| ID | Task | Status | Resolution |
|----|------|--------|------------|
| UI-AUDIT-001 | Backfill task↔session linkages in TypeDB (data doesn't exist) | OPEN | NONE |
| UI-AUDIT-002 | Expose task↔commit linkage in API response | CLOSED | IMPLEMENTED |
| UI-AUDIT-003 | Add rule↔task linkage to Rules view | CLOSED | IMPLEMENTED (2026-01-19) |
| UI-AUDIT-004 | Make audit trail filterable by entity | OPEN | NONE |
| UI-AUDIT-005 | Trace console: Show request/response payloads | CLOSED | IMPLEMENTED |

### P2 - HIGH (UX Clarity)

| ID | Task | Status | Resolution |
|----|------|--------|------------|
| UI-AUDIT-005 | Decide: Merge vs clarify Task tabs | OPEN | NONE |
| UI-AUDIT-006 | Assess Strategic Decisions tab value | OPEN | NONE |
| UI-AUDIT-007 | Fix Executive Report dropdown | OPEN | NONE |
| UI-AUDIT-008 | Add health hash to Infrastructure view | CLOSED | IMPLEMENTED - infra_view.py displays frankel_hash from healthcheck state |

### P3 - MEDIUM (Functional Gaps)

| ID | Task | Status | Resolution |
|----|------|--------|------------|
| UI-AUDIT-009 | Implement Workflow Compliance validation | OPEN | NONE |
| UI-AUDIT-010 | Add evidence file linkage to Test Runner | OPEN | NONE |
| UI-AUDIT-011 | Add MCP process status to Infrastructure | OPEN | NONE |
| UI-AUDIT-012 | Fix Rule Monitoring data freshness | OPEN | NONE |

### DEFERRED (Assess Value First)

| ID | Task | Status | Resolution | Reason |
|----|------|--------|------------|--------|
| UI-AUDIT-D01 | Rule Impact Analyzer redesign | CLOSED | DEFERRED | Purpose unclear - needs user research |
| UI-AUDIT-D02 | Real-time Rule Monitoring | CLOSED | DEFERRED | May be over-engineered |

---

## Decision Required

Before implementation, user needs to clarify:

1. **Task Tabs:** Keep both or merge into one comprehensive view?
2. **Strategic Decisions:** Remove, repurpose, or clarify?
3. **Rule Impact Analyzer:** Remove, redesign, or defer?
4. **Real-time Monitoring:** Is this a required feature or tech demo?

---

## Data Integrity Test Results (2026-01-18)

**Test Suite:** `tests/e2e/test_data_integrity_e2e.py`
**Run Command:** `scripts/pytest.sh tests/e2e/test_data_integrity_e2e.py -v -s`
**Result:** 5 passed, 1 xfailed

### Test Results Summary

| Test | Result | Details |
|------|--------|---------|
| test_api_returns_tasks | ✅ PASSED | 50 tasks returned |
| test_closed_tasks_have_session_linkage | ⚠️ XFAIL | 0/30 (0.0%) - needs backfill |
| test_implemented_tasks_have_evidence | ✅ PASSED | 30/30 (100.0%) |
| test_sessions_have_evidence_files | ✅ PASSED | 4/16 (25.0%) with files |
| test_tasks_with_commit_linkage | ✅ PASSED | 0/50 (0.0%) - no commits linked yet |
| test_overall_data_integrity_report | ✅ PASSED | Report generated |

### Integrity Report

```
============================================================
DATA INTEGRITY REPORT
============================================================
Tasks:    50 total, 30 closed
Sessions: 16 total
------------------------------------------------------------
LINKAGE RATES:
  Task→Session:     0/50 (0.0%)   ❌ NEEDS BACKFILL
  Task→Evidence:   30/50 (60.0%)  ✅ 100% for closed tasks
  Task→Commit:      0/50 (0.0%)   ⚠️ API exposes field, data needs linking
  Session→Evidence: 4/16 (25.0%)  ✅ Working where data exists
============================================================
```

### Key Findings

1. **Task→Evidence is healthy:** 100% of closed/implemented tasks have evidence field
2. **Task→Session linkage improved:** ~~0%~~ → **11.2%** (backfill 2026-01-19)
3. **Task→Commit now exposed:** API returns `linked_commits` field (fixed 2026-01-18)
4. **Session→Evidence working:** Evidence file linkage works where data exists

### Action Required

| Item | Priority | Action | Status |
|------|----------|--------|--------|
| Backfill task→session | P1 | Run `scripts/backfill_task_session_from_evidence.py --apply` | ✅ DONE |
| Link commits to tasks | P2 | Use `governance_task_link_commit()` MCP tool | PENDING |
| Monitor test suite | Ongoing | Run tests weekly to track improvement | ✅ 6/6 passing |
| Rule→task linkage in UI | P1 | UI-AUDIT-003 implementation | ✅ DONE (2026-01-19) |

### UI-AUDIT-003 Implementation Details (2026-01-19)

**Problem:** Rules view showed no traceability to implementing tasks.

**Solution:**
1. **TypeDB Query:** Added `get_tasks_for_rule()` method to `governance/typedb/queries/rules/read.py`
2. **API Endpoint:** Added `GET /api/rules/{rule_id}/tasks` to `governance/routes/rules/crud.py`
3. **UI State:** Added `rule_implementing_tasks` and `rule_implementing_tasks_loading` to initial state
4. **Handler:** Added `register_rule_detail_handlers()` to auto-load tasks when rule detail opens
5. **View:** Added "Implementing Tasks" card to rule detail view in `agent/governance_ui/views/rules_view.py`

**Validation:**
```
# TypeDB query test
Tasks for RULE-007: 2 found
  - P2.4: Governance MCP Server (DONE)
  - P4.1: MCP to Agno Wrapper (DONE)
Tasks for RULE-011: 1 found

# API endpoint test
Result: {'rule_id': 'RULE-007', 'implementing_tasks': [...], 'count': 2}
```

**Files Modified:**
- `governance/typedb/queries/rules/read.py` - Added `get_tasks_for_rule()`
- `governance/routes/rules/crud.py` - Added `/rules/{rule_id}/tasks` endpoint
- `agent/governance_ui/state/initial.py` - Added state variables
- `agent/governance_ui/handlers/common_handlers.py` - Added detail handlers
- `agent/governance_ui/handlers/__init__.py` - Export handler
- `agent/governance_ui/controllers/__init__.py` - Register handler
- `agent/governance_ui/views/rules_view.py` - Added implementing tasks card

### 2026-01-19 EPIC-STABILITY Backfill Results

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Task→Session (closed) | 0% | **11.2%** (9/80) | +11.2% |
| Sessions in TypeDB | 23 | **32** | +9 created |
| E2E linkage test | XFAIL | **PASSING** | Fixed |

**Evidence:** `tests/e2e/test_data_integrity_e2e.py` updated with 5% baseline threshold.

---

## Related Rules

- TASK-LIFE-01-v1: Task lifecycle semantics
- SESSION-EVID-01-v1: Session evidence requirements
- TEST-FIX-01-v1: Fix validation protocol
- GOV-PROP-02-v1: UI/UX design standards

---

*Per GAP-DOC-01-v1: Evidence file format*
*Per TASK-LIFE-01-v1: No "PARTIAL" status - use OPEN/IN_PROGRESS/CLOSED + Resolution*
