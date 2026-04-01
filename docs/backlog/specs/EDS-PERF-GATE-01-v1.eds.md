# EDS: Performance Regression Gate — 2026-03-26

> Per TEST-EXPLSPEC-01-v1: Exploratory Dynamic Specification
> EPIC: EPIC-PERF-TELEM-V1 Phase 8

## Discovery Context
- URL: http://localhost:8081
- Browser: chromium (headless)
- Tool: MCP Playwright
- Scope: Dashboard performance thresholds as permanent safety net
- Date: 2026-03-26
- Deps: Phase 4 (parallel loading), Phase 5 (tracing)

---

## Purpose

This EDS defines the **permanent performance regression gate** for the Sarvaja dashboard.
All thresholds were established after P1-P7 optimizations (query consolidation, parallel loading,
traced HTTP, JSONL caching). Any future change that causes a threshold breach must be
investigated and fixed — thresholds MUST NOT be relaxed to pass.

---

## Layer 1: Business Scenarios

### Feature: Dashboard Performance Gate

```gherkin
Feature: Dashboard Performance Gate
  As a governance operator
  I want the dashboard to respond within defined time limits
  So that I can efficiently manage tasks and sessions without delays

  Scenario: S1 — Task detail loads within 3 seconds
    Given dashboard at http://localhost:8081
    And I navigate to the Tasks tab
    When I click a DONE task row
    Then the task detail panel appears within 3 seconds
    And execution log section is visible
    And evidence section is visible

  Scenario: S2 — Session detail loads within 5 seconds
    Given I navigate to the Sessions tab
    When I click a CC session row
    Then the session detail panel appears within 5 seconds
    And tool calls section or empty indicator is visible

  Scenario: S3 — Session page navigation within 2 seconds
    Given I am on the Sessions tab with multiple pages
    When I click the next page button
    Then new session rows appear within 2 seconds

  Scenario: S4 — Trace bar shows API calls after task click
    Given a task detail has been loaded (from S1)
    When I inspect the trace bar / API trace section
    Then at least 3 API call entries are visible
    And each entry includes a duration_ms value

  Scenario: S5 — Rapid task switching no hang
    Given I am on the Tasks tab with multiple task rows
    When I click 5 different tasks in rapid succession (<500ms apart)
    Then the dashboard remains responsive throughout
    And the final task's detail panel is displayed correctly
    And no stale data from earlier clicks is shown
```

---

## Layer 2: Technical Acceptance Criteria

| Scenario | Metric | Threshold | Measurement Method |
|----------|--------|-----------|-------------------|
| S1 | Time from click to detail panel visible | < 3000ms | `performance.now()` before click, wait for detail element |
| S2 | Time from click to detail panel visible | < 5000ms | `performance.now()` before click, wait for detail element |
| S3 | Time from click to new rows rendered | < 2000ms | `performance.now()` before click, wait for row count change |
| S4 | API trace entry count | >= 3 | Count elements in trace bar after task click |
| S5 | Dashboard responsiveness after 5 rapid clicks | No hang, correct final state | Sequential clicks with 400ms delay, verify final detail |

### Failure Policy

- **Threshold breach**: FAIL the scenario — do NOT adjust thresholds
- **Investigation required**: Document root cause if threshold exceeded
- **Flaky allowance**: None — if intermittently slow, the root cause must be fixed

---

## Layer 3: Evidence Requirements

| Scenario | Evidence |
|----------|----------|
| S1 | Screenshot of task detail panel with execution + evidence sections visible |
| S2 | Screenshot of session detail panel with tool calls or empty indicator |
| S3 | Screenshot of sessions list after page navigation |
| S4 | Screenshot of trace bar showing >= 3 API call entries with duration_ms |
| S5 | Screenshot of final task detail after rapid switching |

---

## Execution Log

| Scenario | Status | Duration | Notes |
|----------|--------|----------|-------|
| S1 | PASS | 160ms | FEAT-008 detail: Execution Log + Evidence + Task Information all visible. Screenshot: EDS-PERF-GATE-S1-task-detail-160ms.png |
| S2 | PASS | 368ms | CC session detail: Tool Calls + Session Information + Activity Timeline visible. Screenshot: EDS-PERF-GATE-S2-session-detail-368ms.png |
| S3 | PASS | 1950ms | Page 1→2 of 58, new session rows appeared. Close to threshold. Screenshot: EDS-PERF-GATE-S3-page-nav-1950ms.png |
| S4 | PASS | 5 new API calls | BUG-013: timeline(82ms), execution(81ms), comments(80ms), evidence/rendered(80ms), detail(8ms). Screenshot: EDS-PERF-GATE-S4-trace-bar-5-api-calls.png |
| S5 | PASS | 5 tasks in 1.6s | SRVJ-FEAT-016→015→BUG-013→BUG-012→FEAT-008 at 400ms intervals. Dashboard responsive, 67 API calls fired, valid detail displayed. Screenshot: EDS-PERF-GATE-S5-rapid-switch-5-tasks.png |

**Executed**: 2026-03-26 by Claude Code via Playwright MCP
**All 5 scenarios PASS** — no threshold breaches.
