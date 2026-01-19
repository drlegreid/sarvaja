# GAP-EXPLOR-UI-001: UI Pagination/Data Display Gaps

**Priority:** MEDIUM | **Category:** ux | **Status:** RESOLVED
**Discovered:** 2026-01-18 | **Session:** Exploratory Testing with Playwright MCP
**Resolved:** 2026-01-18 | **Fixed Issues:** 3/3 (All issues resolved)

---

## Summary

Exploratory UI testing with Playwright MCP revealed inconsistencies between API data counts and UI display, plus missing pagination controls.

## Evidence

### Issue 1: Backlog - No Visible Pagination for 65 Tasks

**Observed:**
- Backlog page shows "65 Available Tasks"
- All 65 tasks rendered in scrollable list
- No pagination controls visible (no page numbers, no "Load More" button)

**Screenshot:** `.playwright-mcp/exploratory-backlog-no-pagination.png`

**Impact:** Large task lists may cause performance issues. UX inconsistency with Tasks view.

---

### Issue 2: Sessions - Shows 10 When API Has 16

**API Response:**
```
GET /api/sessions - Returns 16 sessions
```

**UI Display:**
```
Sessions page shows: "10 sessions loaded"
```

**Impact:** Data mismatch. Users cannot see all sessions. Likely hardcoded limit without UI controls.

---

### Issue 3: Claim Buttons Disabled Without Feedback

**Observed:**
- All "Claim" buttons in Backlog are disabled
- No tooltip or feedback explaining why (Agent ID required)

**Expected:** Tooltip: "Enter Agent ID to claim tasks"

---

## Working UI Elements (Verified)

| Element | Status | Notes |
|---------|--------|-------|
| Navigation tabs | OK | All 15 tabs clickable, correct routing |
| Rules search | OK | Filter textbox works |
| Rules category/status dropdowns | OK | Filtering works |
| Rules list | OK | 60 rules display with badges |
| Trace panel | OK | Expands, shows API calls with timing |
| Header refresh button | OK | Triggers data reload |
| Task detail view | OK | Shows task info, edit/delete buttons |

## Heuristic Coverage

| Heuristic | Coverage | Notes |
|-----------|----------|-------|
| Vertical Navigation | PARTIAL | Task→detail works, Rules→detail missing |
| Horizontal Navigation | GOOD | All tabs accessible |
| Data Integrity | PARTIAL | Counts mismatch (sessions) |
| Loaders | GOOD | Initial loading state visible |
| Pagination | GOOD | Backlog pagination implemented, Sessions limit increased |

## Action Items

1. [x] Add pagination controls to Backlog view - Implemented client-side pagination with nav buttons
2. [x] Fix Sessions view to show all sessions - Changed limit from 10 to 100 in get_sessions()
3. [x] Add tooltip feedback to disabled Claim buttons - Added title attribute to Claim button

## Resolution Details (2026-01-18)

**Issue 1 Fix:** Added client-side pagination controls to Backlog view:
- `agent/governance_ui/state/initial.py` - Added pagination state: `backlog_page`, `backlog_per_page`, `backlog_per_page_options`
- `agent/governance_ui/views/backlog_view.py` - Added:
  - Client-side slicing: `available_tasks.slice((backlog_page - 1) * backlog_per_page, backlog_page * backlog_per_page)`
  - Per-page selector dropdown (10, 25, 50 options)
  - Page info display with v_text for reactivity
  - Previous/Next navigation buttons
- `governance/routes/tasks/__init__.py` - Fixed route ordering (static before dynamic routes)

**Screenshot Evidence:** `.playwright-mcp/backlog-pagination-page2.png`

**Issue 2 Fix:** Changed `get_sessions(limit=10)` to `get_sessions(limit=100)` in:
- `agent/governance_ui/data_access/core.py` - Default parameter
- `agent/governance_dashboard.py` - Initial load call

**Issue 3 Fix:** Added tooltip to disabled Claim button in `agent/governance_ui/views/backlog_view.py`:
```python
title=("backlog_agent_id ? '' : 'Enter Agent ID above to claim tasks'",)
```

**Container Fix:** Added `COPY shared /app/shared` to `agent/Dockerfile.dashboard` for shared constants module.

## Related

- GAP-UI-PAGING-001: Previous pagination work
- UI-LOADER-01-v1: Reactive loaders rule
- MCP-OUTPUT-01-v1: Output size limits

---

*Per GAP-DOC-01-v1: Evidence file format*
