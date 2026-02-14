# TEST-DISCOVERY-01-v1: Test Discovery Bug Tracking

| Field | Value |
|-------|-------|
| **Category** | Testing |
| **Priority** | HIGH |
| **Applicability** | MANDATORY |
| **Status** | ACTIVE |
| **Created** | 2026-02-14 |
| **Related** | TEST-E2E-01-v1, GAP-DOC-01-v1, GOV-MCP-FIRST-01-v1 |

## Directive

When executing E2E or integration tests and discovering a bug, gap, or unexpected behavior, the agent MUST immediately create a tracked task of type BUG via `mcp__gov-tasks__task_create()`.

## Required Fields

Each bug task MUST include:

1. **Business Intent** — What the user expects to happen (user-facing impact)
2. **Technical Symptoms** — Actual error, missing behavior, or wrong data observed
3. **Affected Component** — File paths and UI view involved
4. **Discovery Context** — Which test scenario and tier revealed the issue

## Task Format

- **ID**: `BUG-{DOMAIN}-{SEQ}` (e.g., `BUG-UI-RULES-001`)
- **Priority**: Match severity:
  - CRITICAL = blocks user workflow
  - HIGH = degrades UX significantly
  - MEDIUM = cosmetic / workaround exists
  - LOW = minor inconvenience
- **Phase**: `BUG` (or link to relevant phase)
- **Session**: Link to active session via `session_id` parameter

## Rationale

Gaps discovered during E2E testing are often lost between:
- Context compactions (amnesia events)
- Session boundaries (new conversation starts)
- Task switches (focus moves to next scenario)

By creating TypeDB-persisted tasks immediately on discovery, bugs survive all three boundaries and appear in the backlog for prioritized resolution.

## Example

```
mcp__gov-tasks__task_create(
    task_id="BUG-UI-RULES-001",
    name="Rules status/category filter dropdowns not wired to actual filtering",
    description="""
    Business Intent: User selects 'ACTIVE' from Status dropdown → expects only ACTIVE rules shown.
    Technical Symptoms: VDataTable has no custom-filter prop; dropdown sets state but no @state.change handler triggers re-fetch or client-side filter.
    Affected Component: agent/governance_ui/views/rules_view.py (VSelect), agent/governance_ui/controllers/rules.py (handlers)
    Discovery Context: E2E-T3-RULES Scenario 3 (Filter by status), Tier 3 Playwright
    """,
    priority="HIGH",
    phase="BUG"
)
```
