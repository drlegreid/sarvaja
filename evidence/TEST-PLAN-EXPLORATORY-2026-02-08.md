# Dynamic Exploratory Test Plan

**Generated**: 2026-02-08T21:25:00 | **Session**: Dynamic Orthogonal Test
**Tool Chain**: Playwright MCP + REST API MCP + Heuristic Runner
**Dashboard**: http://localhost:8081 | **API**: http://localhost:8082

---

## 1. Horizontal Sweep: Navigation Coverage (15/15 tabs)

| # | Tab | Nav ID | Renders | Data Count | Key Elements |
|---|-----|--------|---------|------------|--------------|
| 1 | Chat | nav-chat | PASS | N/A | Agent selector, message input, 5 quick commands |
| 2 | Rules | nav-rules | PASS | 48 rules | Data table (8 cols), search, status/category filters, detail view |
| 3 | Agents | nav-agents | PASS | 9 agents | Summary stats, register button, all PAUSED |
| 4 | Tasks | nav-tasks | PASS | 117 tasks | Data table (8 cols), search, status/phase filters, 4 filter tabs |
| 5 | Sessions | nav-sessions | PASS | 18 sessions | Summary stats (4 cards), search, evidence search (disabled) |
| 6 | Executive | nav-executive | PASS | 1 report | 88% compliance, expandable sections |
| 7 | Decisions | nav-decisions | PASS | 4 decisions | Session filter, Record Decision button |
| 8 | Impact | nav-impact | PASS | 0 analyses | Rule selector, graph/list toggle |
| 9 | Trust | nav-trust | PASS | 9 agents | Leaderboard, proposals section (empty) |
| 10 | Workflow | nav-workflow | PASS | 0 proposals | Proposal form (6 fields), compliance (5 pass/1 issue) |
| 11 | Audit | nav-audit | PASS | 0 entries | Data table (7 cols), 4 filters, charts (empty) |
| 12 | Monitor | nav-monitor | PASS | 15 events | Event feed table, 3 active alerts, Most Active Rules |
| 13 | Infrastructure | nav-infra | PASS | 5 services | Service cards, system stats, container logs, recovery actions |
| 14 | Metrics | nav-metrics | PASS | 6 sessions | Summary stats, per-day breakdown, tool usage (37 tools) |
| 15 | Tests | nav-tests | PASS | 10 runs | 3-phase regression, 6 test categories, Robot Framework |

---

## 2. Vertical CRUD: Per-Domain Operations

### 2.1 Tasks CRUD

| Operation | Method | Endpoint | UI Path | Status | Notes |
|-----------|--------|----------|---------|--------|-------|
| CREATE | POST /api/tasks | Add Task dialog | API:PASS, UI:FAIL | UI dialog doesn't close on submit; console error |
| READ | GET /api/tasks/{id} | Click task row | PASS | Detail shows all fields |
| UPDATE | PUT /api/tasks/{id} | Edit button | API:PASS | status/description/agent_id updated correctly |
| DELETE | DELETE /api/tasks/{id} | Delete button | API:PASS (204) | Cleanup successful |
| LIST | GET /api/tasks?limit=N&offset=N | Tasks tab | PASS | Pagination: 117 total, 6 pages |
| FILTER | GET /api/tasks?status=X&phase=Y | Status/Phase dropdowns | PASS | Filters wired to API |

### 2.2 Rules CRUD

| Operation | Method | Endpoint | UI Path | Status | Notes |
|-----------|--------|----------|---------|--------|-------|
| CREATE | POST /api/rules | Add Rule button | API:PASS (201) | Validates category enum (governance/technical/operational) |
| READ | GET /api/rules/{id} | Click rule row | PASS | Shows Name, Category, Priority, Directive |
| UPDATE | PUT /api/rules/{id} | Edit button | API:PASS | **GAP**: UI edit form doesn't pre-populate current values |
| DELETE | DELETE /api/rules/{id} | Delete button | API:PASS (204) | |
| LIST | GET /api/rules | Rules tab | PASS | 48 rules, 25 per page |

### 2.3 Sessions CRUD

| Operation | Method | Endpoint | UI Path | Status | Notes |
|-----------|--------|----------|---------|--------|-------|
| CREATE | POST /api/sessions | Add Session button | Not tested via UI | API endpoint exists |
| READ | GET /api/sessions/{id} | Click session row | PASS | Shows Session Info, Evidence, Tasks, Tool Calls |
| LIST | GET /api/sessions | Sessions tab | PASS | 18 total, summary stats |
| EDIT | N/A | Edit button | Present in UI | |
| DELETE | N/A | Delete button | Present in UI | |

### 2.4 Decisions CRUD

| Operation | Method | Endpoint | UI Path | Status | Notes |
|-----------|--------|----------|---------|--------|-------|
| CREATE | POST /api/decisions | Record Decision btn | API:PASS (201) | **GAP**: rules_applied not linked in response |
| READ | GET /api/decisions | Decisions tab | PASS | 4 decisions with linked_rules |
| DELETE | DELETE /api/decisions/{id} | N/A | API:PASS (204) | |

### 2.5 Agents CRUD

| Operation | Method | Endpoint | UI Path | Status | Notes |
|-----------|--------|----------|---------|--------|-------|
| READ | GET /api/agents/{id} | Click agent card | PASS | Shows capabilities, trust_score |
| TOGGLE | PUT /api/agents/{id}/status/toggle | Pause/Resume btn | PASS | PAUSED↔ACTIVE toggle works |
| SESSIONS | GET /api/agents/{id}/sessions | Agent detail | PASS | Returns linked sessions (empty for now) |

### 2.6 Chat Operations

| Operation | UI Path | Status | Notes |
|-----------|---------|--------|-------|
| Send /status | Chat input + Enter | PASS | Returns system stats |
| Quick Commands | Click chip | PASS | /help, /status, /tasks, /rules, /agents |

---

## 3. Data Integrity: Heuristic Check Results

**Run ID**: HEUR-20260208-212450 | **Duration**: 1.63s | **Total**: 21 checks

### 3.1 PASSING Checks (11)

| ID | Domain | Name | Message |
|----|--------|------|---------|
| H-TASK-001 | TASK | Task descriptions | All tasks have descriptions |
| H-TASK-003 | TASK | DONE completion timestamps | All DONE tasks have timestamps |
| H-TASK-004 | TASK | No TEST-* artifacts | No TEST-* task artifacts |
| H-SESSION-001 | SESSION | Active session agent_id | All active sessions have agents |
| H-SESSION-003 | SESSION | Stale active sessions | No active sessions |
| H-SESSION-004 | SESSION | No TEST-* artifacts | No TEST-* session artifacts |
| H-RULE-003 | RULE | Rule directive content | All rules have directives |
| H-RULE-004 | RULE | No TEST-* artifacts | No TEST-* rule artifacts |
| H-AGENT-001 | AGENT | Agent trust scores | All agents have trust scores |
| H-AGENT-002 | AGENT | Agent last_active recency | All agents recently active or new |
| H-UI-003 | UI | data-testid coverage | Key views have data-testid attributes |

### 3.2 FAILING Checks (5)

| ID | Domain | Severity | Violations | Root Cause |
|----|--------|----------|------------|------------|
| H-TASK-002 | TASK | MEDIUM | 3 tasks (EPIC-UI-VALUE-001, GAP-AGENT-PAUSE-001, RD-005) | IN_PROGRESS tasks missing agent_id |
| H-TASK-005 | TASK | HIGH | 84/117 tasks orphaned | Tasks not linked to sessions (DATA-LINK-01) |
| H-SESSION-002 | SESSION | MEDIUM | 4 sessions missing evidence | SESSION-2026-01-30-45A2EB + 3 others |
| H-SESSION-005 | SESSION | LOW | 1 live session | SESSION-2026-01-30-45A2EB lacks tool calls |
| H-SESSION-006 | SESSION | LOW | 1 live session | SESSION-2026-01-30-45A2EB lacks thoughts |

### 3.3 SKIPPED Checks (5) — Self-Referential

| ID | Domain | Name | Reason |
|----|--------|------|--------|
| H-CROSS-001 | CROSS-ENTITY | Service layer coverage | Run from host with REST MCP |
| H-CROSS-003 | CROSS-ENTITY | Decisions link to rules | Run from host with REST MCP |
| H-RULE-001 | RULE | Active rules have document_path | Run from host with REST MCP |
| H-API-001 | API | Endpoint health | Run from host with REST MCP |
| H-API-002 | API | Pagination contract | Run from host with REST MCP |

### 3.4 External Cross-Checks (run via REST MCP from host)

| Check | Result | Details |
|-------|--------|---------|
| H-CROSS-003 (Decisions→Rules) | PASS | All 4 decisions link to rules |
| H-API-001 (Endpoint health) | PASS | 9/10 endpoints 200 OK (only /api/tests/runs is 404) |
| H-API-002 (Pagination) | PASS | All 4 domain endpoints have consistent {items, pagination} |

---

## 4. Gaps Discovered

### 4.1 UI Gaps

| Gap ID | Tab | Severity | Description |
|--------|-----|----------|-------------|
| GAP-UI-TS-001 | Tasks, Sessions | LOW | Raw ISO timestamps displayed (e.g., `2026-01-19T04:06:50.000000000`) instead of human-readable format |
| GAP-UI-PAGN-001 | Sessions | LOW | Dual pagination controls: VDataTable built-in + custom footer both visible |
| GAP-TASK-CREATE-UI-001 | Tasks | MEDIUM | Add Task dialog submit triggers console error, dialog stays open |
| GAP-RULE-EDIT-001 | Rules | MEDIUM | Edit form defaults to governance/HIGH instead of pre-populating actual rule values |
| GAP-SESSION-DETAIL-001 | Sessions | LOW | Session detail view doesn't show agent_id field despite data having it |
| GAP-AUDIT-EMPTY-001 | Audit | HIGH | Audit trail has 0 entries - no audit events being captured |
| GAP-MONITOR-COUNT-001 | Monitor | LOW | Total Events counter shows "9" but event table has 15 rows |
| GAP-INFRA-MCP-001 | Infrastructure | MEDIUM | MCP Server Status shows "not available" despite services running |
| GAP-INFRA-PROCS-002 | Infrastructure | LOW | Python Process Details expansion shows "0 processes" while system stats show "2" |
| GAP-CHAT-COUNT-001 | Chat | LOW | /status reports "20 active sessions" but Sessions tab shows 18 total, 0 active |

### 4.2 API Gaps

| Gap ID | Endpoint | Severity | Description |
|--------|----------|----------|-------------|
| GAP-DECISION-RULES-001 | POST /api/decisions | MEDIUM | `rules_applied` in request body not stored as `linked_rules` in response |
| GAP-API-TESTS-RUNS-001 | GET /api/tests/runs | LOW | Endpoint returns 404 (not implemented) |
| GAP-RULE-DOC-PATH-001 | GET /api/rules | MEDIUM | Active rules have null `document_path` (42/42 checked) |

### 4.3 Data Integrity Gaps (from Heuristic Checks)

| Gap ID | Check | Severity | Impact |
|--------|-------|----------|--------|
| GAP-TASK-ORPHAN-001 | H-TASK-005 | HIGH | 84/117 tasks (72%) not linked to any session |
| GAP-TASK-AGENT-001 | H-TASK-002 | MEDIUM | 3 IN_PROGRESS tasks have no agent assigned |
| GAP-SESSION-EVIDENCE-001 | H-SESSION-002 | MEDIUM | 4 completed sessions lack evidence files |
| GAP-MCP-READINESS-001 | /api/mcp/readiness | MEDIUM | Reports all backends unreachable but API works fine |

---

## 5. E2E Test Specifications (for static test conversion)

### 5.1 Navigation Tests

```
TEST-NAV-001: All 15 tabs render without error
  FOR EACH tab IN [chat, rules, agents, tasks, sessions, executive,
                    decisions, impact, trust, workflow, audit, monitor,
                    infra, metrics, tests]:
    CLICK nav-{tab}
    ASSERT main content area is not empty
    ASSERT no JS console errors (TypeError, ReferenceError)

TEST-NAV-002: Header shows correct counts
  ASSERT header shows "48 Rules" chip
  ASSERT header shows "4 Decisions" chip
  ASSERT health hash is displayed
```

### 5.2 Rules Tests

```
TEST-RULES-001: Rules list loads with data
  NAVIGATE to rules tab
  ASSERT table has > 0 rows
  ASSERT pagination shows "X of 48"

TEST-RULES-002: Rule detail view opens on row click
  CLICK first rule row
  ASSERT detail view shows Name, Category, Priority, Directive
  ASSERT back button returns to list

TEST-RULES-003: Rule search filters list
  TYPE "MCP" in search field
  ASSERT table rows contain "MCP" in name or ID

TEST-RULES-004: Rule CRUD via API
  POST /api/rules with valid body → 201
  GET /api/rules/{id} → 200
  PUT /api/rules/{id} with updates → 200
  DELETE /api/rules/{id} → 204
  GET /api/rules/{id} → 404

TEST-RULES-005: Rule category validation
  POST /api/rules with category="invalid" → 422
  ASSERT error mentions "governance, technical, operational"
```

### 5.3 Tasks Tests

```
TEST-TASKS-001: Tasks list loads with pagination
  NAVIGATE to tasks tab
  ASSERT table shows 20 rows
  ASSERT pagination shows "Page 1 of 6 (117 total)"

TEST-TASKS-002: Task filter tabs work
  CLICK "Completed" tab
  ASSERT all visible tasks have status DONE or completed

TEST-TASKS-003: Task CRUD via API
  POST /api/tasks → 201
  GET /api/tasks/{id} → 200
  PUT /api/tasks/{id} → 200 (verify description/status changed)
  DELETE /api/tasks/{id} → 204

TEST-TASKS-004: Task create dialog (UI) [KNOWN GAP]
  CLICK "Add Task"
  ASSERT dialog opens with fields: Task ID, Description, Phase, Agent
  FILL fields and CLICK Create
  ASSERT dialog closes and task appears in list (CURRENTLY FAILING)
```

### 5.4 Sessions Tests

```
TEST-SESSIONS-001: Sessions list with summary stats
  NAVIGATE to sessions tab
  ASSERT "Total Sessions" card shows 18
  ASSERT "Active" card shows 0
  ASSERT table has 18 rows

TEST-SESSIONS-002: Session detail shows all sections
  CLICK first session row
  ASSERT Session Information section visible
  ASSERT Evidence Files section visible
  ASSERT Completed Tasks section visible
  ASSERT Tool Calls section visible

TEST-SESSIONS-003: Session search filters
  TYPE "API test" in search
  ASSERT filtered results contain matching description
```

### 5.5 Chat Tests

```
TEST-CHAT-001: Chat /status command
  NAVIGATE to chat tab
  TYPE "/status" and press Enter
  ASSERT response contains "Rules:" and "Tasks:" and "Agents:"

TEST-CHAT-002: Quick command chips
  CLICK "/help" chip
  ASSERT response message appears
```

### 5.6 Agents Tests

```
TEST-AGENTS-001: Agent list shows all agents
  NAVIGATE to agents tab
  ASSERT 9 agent cards visible
  ASSERT all show "PAUSED" status

TEST-AGENTS-002: Agent toggle via API
  PUT /api/agents/{id}/status/toggle → 200 (ACTIVE)
  PUT /api/agents/{id}/status/toggle → 200 (PAUSED)

TEST-AGENTS-003: Agent sessions endpoint
  GET /api/agents/{id}/sessions → 200
  ASSERT response has {agent_id, sessions, pagination}
```

### 5.7 Infrastructure Tests

```
TEST-INFRA-001: All 5 services show OK
  NAVIGATE to infrastructure tab
  ASSERT Podman card shows "OK"
  ASSERT TypeDB card shows "OK" and port 1729
  ASSERT ChromaDB card shows "OK" and port 8001
  ASSERT LiteLLM card shows "OK" and port 4000
  ASSERT Ollama card shows "OK" and port 11434

TEST-INFRA-002: System stats visible
  ASSERT Memory Usage percentage is visible
  ASSERT Python Processes count is visible
  ASSERT Health Hash is displayed
```

### 5.8 Heuristic Integrity Tests

```
TEST-HEUR-001: Run heuristic checks
  POST /api/tests/heuristic/run → 200
  GET /api/tests/results → 200
  ASSERT latest run has 21 checks
  ASSERT passed >= 11
  ASSERT no errors

TEST-HEUR-002: Known passing checks remain stable
  ASSERT H-TASK-001 (descriptions) = PASS
  ASSERT H-TASK-003 (DONE timestamps) = PASS
  ASSERT H-TASK-004 (no TEST-* artifacts) = PASS
  ASSERT H-RULE-003 (directive content) = PASS
  ASSERT H-AGENT-001 (trust scores) = PASS
```

### 5.9 API Contract Tests

```
TEST-API-001: All core endpoints return 200
  FOR endpoint IN [/api/tasks, /api/sessions, /api/rules,
                   /api/agents, /api/decisions, /api/health]:
    GET {endpoint} → 200

TEST-API-002: Pagination contract consistent
  FOR endpoint IN [/api/tasks, /api/sessions, /api/rules, /api/agents]:
    GET {endpoint}?limit=1 → 200
    ASSERT response has "items" array
    ASSERT response has "pagination" with {total, offset, limit, has_more, returned}

TEST-API-003: Health endpoint contract
  GET /api/health → 200
  ASSERT body has status, typedb_connected, rules_count, version
```

---

## 6. Recommended Priority Fixes

1. **GAP-AUDIT-EMPTY-001** (HIGH): Wire audit event capture to CRUD operations
2. **GAP-TASK-ORPHAN-001** (HIGH): Implement task-session auto-linking per DATA-LINK-01
3. **GAP-TASK-CREATE-UI-001** (MEDIUM): Fix task create dialog submit handler
4. **GAP-RULE-EDIT-001** (MEDIUM): Pre-populate edit form with current rule values
5. **GAP-DECISION-RULES-001** (MEDIUM): Link rules_applied during decision creation
6. **GAP-UI-TS-001** (LOW): Format ISO timestamps as human-readable dates
7. **GAP-UI-PAGN-001** (LOW): Remove duplicate pagination on Sessions tab
