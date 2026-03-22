# EDS: EPIC-GOV-TASKS-V2 Heuristic Gap Analysis — 2026-03-21

Per TEST-EXPLSPEC-01-v1 and EPIC-GOV-TASKS-V2 Phase 9e.

## Root Cause Analysis

EPIC-GOV-TASKS-V2 ran **3 EDS gates** (Phase 6, 6c, 9b) which successfully caught:
- BUG-WS-CREATE-001: workspace_id silent failure (CRITICAL)
- BUG-WS-API-001: Pydantic model missing workspace_id (HIGH)
- BUG-STATUS-CASE-001: mixed-case statuses (MEDIUM)
- BUG-TASK-POPUP-001: execution log blocking popup (MEDIUM)

However, **8 additional concerns** (#0-#7) were discovered during manual review (2026-03-21) that EDS gates did NOT catch:

| # | Concern | Phase Fixed | Category Missed |
|---|---------|-------------|-----------------|
| 0 | MCP tasks not visible in Dashboard (BUG-TASK-UI-001) | P9b | DATA_MODEL |
| 1 | No `specification` task type | P9c | DATA_MODEL |
| 2 | Summary field missing — description overloaded | P9c | FIELD_INTEGRITY |
| 3 | No default sort (random order) | P9c | UX_DEFAULTS |
| 4 | Priority embedded as `[Priority: X]` in description | P9c | FIELD_INTEGRITY |
| 5 | No cross-entity navigation (task→session clicks) | P9d | CROSS_NAV |
| 6 | Client-side search (page-local only) | P9d | SEARCH |
| 7 | No session column/filter in task list | P9d | CROSS_NAV |

## Why EDS Missed These

EDS gates validated **CRUD mechanics** (create/read/update/delete operations work correctly) but did NOT validate:

| Gap Category | What EDS Tested | What EDS Missed |
|---|---|---|
| **DATA_MODEL** | Fields present in API response | New field propagation (summary), missing enum values (specification), layer consistency |
| **UX_DEFAULTS** | Table renders with data | Sort order defaults, filter dropdown population, column mapping to new fields |
| **CROSS_NAV** | Detail view shows linked entities | Clickable navigation between entities, bidirectional traversal, back-button context |
| **SEARCH** | Search input exists in UI | Server-side vs client-side execution, structured prefix syntax, pagination interaction |
| **FIELD_INTEGRITY** | Values returned by API | Null fields needing defaults, embedded metadata tags, timestamp ordering, status normalization |

## Expanded Heuristic Checklist

### DATA_MODEL (5 checks)
- [ ] All schema attributes present in API response
- [ ] New fields propagate through all layers (TypeDB → service → route → UI)
- [ ] Optional fields have sensible defaults
- [ ] Enum/Literal values consistent across layers (Pydantic, constants, TypeDB, MCP)
- [ ] Auto-generated fields populate correctly (summary, created_at, task_id)

### UX_DEFAULTS (4 checks)
- [ ] Default sort order is user-friendly (newest first)
- [ ] Filter dropdowns match API-accepted values
- [ ] Empty states have meaningful messages
- [ ] Column widths appropriate for data content

### CROSS_NAV (4 checks)
- [ ] Linked entities are clickable (not just displayed as text)
- [ ] Navigation preserves back-button context
- [ ] Bidirectional navigation works (task→session AND session→task)
- [ ] Navigation to missing/deleted entities shows clear error

### SEARCH (3 checks)
- [ ] Search is server-side (not client-side page filter)
- [ ] Search respects pagination (correct total count after filter)
- [ ] Structured search syntax works for power users (type:bug priority:HIGH)

### FIELD_INTEGRITY (4 checks)
- [ ] No null fields that should have defaults (priority, task_type, summary)
- [ ] No embedded metadata in wrong fields ([Priority: X] in description)
- [ ] Timestamp ordering valid (completed_at >= created_at)
- [ ] Status values normalized (uppercase, no mixed case)

## Recommendation

**TEST-EDS-HEURISTIC-01-v1**: All future EDS specs MUST include at least one scenario per heuristic category. CRUD-only EDS is necessary but NOT sufficient.

## Implementation

Heuristic category definitions: `governance/eds/heuristic_categories.py`
Coverage analysis function: `analyze_eds_coverage(scenario) → missing categories`
Tests: `tests/unit/test_eds_heuristic_categories.py` (10 tests)
