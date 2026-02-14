# EPIC-TESTING-E2E: Data Flow Verification Pipeline

| Field | Value |
|-------|-------|
| **Status** | OPEN |
| **Priority** | HIGH |
| **Rule** | TEST-E2E-01-v1 |
| **Created** | 2026-02-14 |
| **Domain** | Testing (Tier 2 Integration + Tier 3 Visual) |

## Strategic Goal

Unit tests (Tier 1) cover 98% of governance modules with 9,731 tests. However, data flow changes lack **integration verification** (Tier 2: API curl assertions) and **visual verification** (Tier 3: Playwright screenshots). Per TEST-E2E-01-v1, all 3 tiers are MANDATORY for data flow changes.

## Scope

### In-Scope
- API integration tests for all governance endpoints
- Playwright visual verification for dashboard views
- Automation scripts for CI-ready execution

### Out-of-Scope
- Unit test expansion (already at 98%)
- Performance/load testing (separate EPIC)

## Task Breakdown

### Phase 1: API Integration Tests (Tier 2)

| Task | Status | Description | Domain | Priority |
|------|--------|-------------|--------|----------|
| E2E-T2-001 | OPEN | **Session Endpoints**: GET/PUT /sessions, /sessions/{id}, /sessions/{id}/tools, /sessions/{id}/thoughts | sessions | HIGH |
| E2E-T2-002 | OPEN | **Task Endpoints**: GET/POST/PUT /tasks, /tasks/{id}, task_create, task_update | tasks | HIGH |
| E2E-T2-003 | OPEN | **Rule Endpoints**: GET /rules, /rules/{id}, rule_create, rule_update, rule_deprecate | rules | HIGH |
| E2E-T2-004 | OPEN | **Agent Endpoints**: GET /agents, /agents/{id}, trust scores | agents | MEDIUM |
| E2E-T2-005 | OPEN | **Decision Endpoints**: GET/POST /decisions, decision linking | decisions | MEDIUM |
| E2E-T2-006 | OPEN | **Heuristic/CVP Endpoints**: POST /tests/cvp/sweep, GET /tests/cvp/status | testing | MEDIUM |
| E2E-T2-007 | OPEN | **Ingestion Endpoints**: POST /ingestion/status/{id} | ingestion | LOW |

### Phase 2: Visual Verification (Tier 3)

| Task | Status | Description | Domain | Priority |
|------|--------|-------------|--------|----------|
| E2E-T3-001 | OPEN | **Dashboard Overview**: Navigate + screenshot main dashboard | UI | HIGH |
| E2E-T3-002 | OPEN | **Sessions List**: Verify session table renders with data | UI/sessions | HIGH |
| E2E-T3-003 | OPEN | **Session Detail**: Verify tool/thought/evidence tabs render | UI/sessions | HIGH |
| E2E-T3-004 | OPEN | **Rules Tab**: Verify rules table with status badges | UI/rules | MEDIUM |
| E2E-T3-005 | OPEN | **Tasks Tab**: Verify task list with priority/status | UI/tasks | MEDIUM |
| E2E-T3-006 | OPEN | **Agents Tab**: Verify agent cards with trust scores | UI/agents | MEDIUM |
| E2E-T3-007 | OPEN | **File Viewer**: Verify markdown rendering for evidence files | UI/files | LOW |

## Dependencies

- Container stack running (podman compose --profile cpu up -d)
- TypeDB seeded with rules + test sessions
- Dashboard accessible on :8081, API on :8082

## Acceptance Criteria

- [ ] All Tier 2 tasks: curl endpoint + assert HTTP 200 + validate JSON schema
- [ ] All Tier 3 tasks: Playwright navigate + screenshot + visual confirmation
- [ ] Zero regression in Tier 1 (9,731 unit tests still passing)
- [ ] Evidence artifacts in `evidence/test-results/`

## Concerns

- **Container dependency**: Tier 2/3 require running infrastructure (not unit-testable)
- **Playwright MCP**: Use `mcp__playwright__*` tools for Tier 3 — no raw Playwright scripts
- **Flaky screenshots**: Dashboard Trame renders async; may need wait strategies

---

*Per TASK-EPIC-01-v1: EPIC-driven task comprehension.*
*Per TEST-E2E-01-v1: 3-tier verification mandatory for data flow changes.*
