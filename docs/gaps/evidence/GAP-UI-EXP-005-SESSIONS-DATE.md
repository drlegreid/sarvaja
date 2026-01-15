# GAP-UI-EXP-005: Sessions View Shows "No date" - UI Bug

**Status:** OPEN
**Priority:** HIGH
**Category:** data_integrity
**Discovered:** 2026-01-14 via Playwright exploratory testing

## Problem Statement

Sessions view displays "No date" for all 22 sessions, despite the API returning valid `start_time` values.

## Root Cause

UI templates use wrong field name `session.date` but API returns `start_time`.

## Technical Details

### Affected Files

| File | Line | Bug | Fix |
|------|------|-----|-----|
| `agent/governance_ui/views/sessions/list.py` | 70 | `session.date \|\| 'No date'` | Change to `session.start_time` |
| `agent/governance_ui/views/sessions/content.py` | 16 | `selected_session.date \|\| 'No date'` | Change to `selected_session.start_time` |
| `agent/governance_ui/views/sessions/content.py` | 47 | `selected_session.date \|\| 'N/A'` | Change to `selected_session.start_time` |

### API Response (Correct)

```json
{
  "session_id": "SESSION-2026-01-13-0AED98",
  "start_time": "2026-01-13T09:49:50",
  "end_time": "2026-01-13T09:49:50",
  "status": "COMPLETED",
  "description": "Session to end in E2E test"
}
```

### UI Template (Bug)

```python
# list.py:70 - WRONG
v3.VCardSubtitle("{{ session.date || 'No date' }}")

# content.py:16 - WRONG
v3.VChip(v_text="selected_session.date || 'No date'", ...)

# content.py:47 - WRONG
v3.VListItem(title="Date", subtitle=("selected_session.date || 'N/A'",), ...)
```

## Fix

Change all occurrences of `.date` to `.start_time`:

```python
# list.py:70 - FIXED
v3.VCardSubtitle("{{ session.start_time || 'No date' }}")

# content.py:16 - FIXED
v3.VChip(v_text="selected_session.start_time || 'No date'", ...)

# content.py:47 - FIXED
v3.VListItem(title="Date", subtitle=("selected_session.start_time || 'N/A'",), ...)
```

## TDD Test

Failing test written: `tests/test_sessions_date_bug.py`

## Evidence

- Screenshot: `.playwright-mcp/sessions_no_date.png` (if captured)
- API response verified via `GET /api/sessions` returns `start_time`

## Related

- Similar bug was GAP-UI-EXP-001 (Decisions date) - already fixed
- Rule: SESSION-EVID-01-v1
