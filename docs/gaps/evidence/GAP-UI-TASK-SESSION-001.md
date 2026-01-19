# GAP-UI-TASK-SESSION-001: Task Detail Not Showing linked_sessions

**Priority:** HIGH | **Category:** ui | **Status:** RESOLVED
**Discovered:** 2026-01-18 | **Source:** GAP-UI-AUDIT-2026-01-18 Phase Validation
**Assignee:** AGENT | **Resolution:** IMPLEMENTED

---

## Summary

Task detail view (e.g., FH-006) was not displaying `linked_sessions` field despite API returning it.

## Root Cause

The `select_task()` function in `controllers/tasks.py` was using cached list data instead of fetching full task details from API. The cached list only contains basic fields, not relationship fields like `linked_sessions`, `linked_commits`, `linked_rules`.

## Fix Applied

Modified `controllers/tasks.py` line 28-43:

```python
@ctrl.set("select_task")
def select_task(task_id):
    """Handle task selection for detail view.

    Per GAP-UI-TASK-SESSION-001: Fetch full task details including
    linked_sessions, linked_commits, linked_rules from API.
    """
    # Fetch full task details from API to get linked fields
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{api_base_url}/api/tasks/{task_id}")
            if response.status_code == 200:
                state.selected_task = response.json()
                state.show_task_detail = True
                return
    except Exception:
        pass  # Fall back to cached data

    # Fallback to cached list data if API fails
    for task in state.tasks:
        if task.get('task_id') == task_id or task.get('id') == task_id:
            state.selected_task = task
            state.show_task_detail = True
            break
```

## Verification

**API Test:**
```bash
$ curl -s http://localhost:8082/api/tasks/FH-006 | jq '.linked_sessions'
["SESSION-2024-12-25-DSP-CYCLES"]
```

**UI Test:** Task detail now fetches full data from API including linked_sessions.

## Files Modified

| File | Change |
|------|--------|
| [controllers/tasks.py](agent/governance_ui/controllers/tasks.py:28-43) | Added API call for full task details with fallback |

## Related

- [GAP-UI-AUDIT-2026-01-18](GAP-UI-AUDIT-2026-01-18.md) - Parent audit ISSUE-001
- [GAP-UI-SESSION-TASKS-001](GAP-UI-SESSION-TASKS-001.md) - Inverse problem (session showing tasks)

---

*Per GAP-DOC-01-v1: Evidence file format*
*Per TEST-FIX-01-v1: Fix with verification evidence*
