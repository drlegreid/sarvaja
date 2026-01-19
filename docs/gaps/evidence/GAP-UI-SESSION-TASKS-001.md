# GAP-UI-SESSION-TASKS-001: Session Detail Not Loading Completed Tasks

**Priority:** HIGH | **Category:** ui | **Status:** RESOLVED
**Discovered:** 2026-01-18 | **Source:** GAP-UI-AUDIT-2026-01-18 Phase Validation
**Assignee:** AGENT | **Resolution:** IMPLEMENTED

---

## Summary

Session detail view shows "Completed Tasks: 0" and "No tasks linked to this session" even when API returns 7 tasks for `SESSION-2024-12-25-DSP-CYCLES`.

## Root Cause Analysis

### API Layer - WORKING

```bash
$ curl -s http://localhost:8082/api/sessions/SESSION-2024-12-25-DSP-CYCLES/tasks
{"session_id":"SESSION-2024-12-25-DSP-CYCLES","task_count":7,"tasks":[...]}
```

The `/api/sessions/{session_id}/tasks` endpoint correctly returns 7 tasks.

### UI Layer - NOT WORKING

**Issue:** Click handler in `views/sessions/list.py` was:
```python
click="selected_session = session; show_session_detail = true"
```

This directly sets state but never calls the `select_session` handler that loads tasks.

**Attempted Fix 1:** Changed to:
```python
click="select_session(session.session_id || session.id)"
```
Result: JavaScript error - function not found in Vue context.

**Attempted Fix 2:** Changed to use Trame trigger pattern:
```python
@ctrl.trigger("select_session")  # Changed from @ctrl.set
...
click="trigger('select_session', [session.session_id || session.id])"
```
Result: Click does nothing - state not updated.

## Technical Details

### Files Modified

| File | Change | Status |
|------|--------|--------|
| [handlers/session_handlers.py](agent/governance_ui/handlers/session_handlers.py) | Added `load_session_tasks()` function, changed `@ctrl.set` to `@ctrl.trigger` | Modified |
| [views/sessions/list.py](agent/governance_ui/views/sessions/list.py) | Changed click handler to use `trigger()` | Modified |
| [controllers/tasks.py](agent/governance_ui/controllers/tasks.py) | Added API call for full task details | Completed |

### Trame Event Handling Investigation

Per Trame documentation and codebase patterns:
- `@ctrl.set()`: Synchronous state setters, called directly from Vue
- `@ctrl.trigger()`: Async operations, called via `trigger('name', [args])`

Looking at working examples in `views/tasks/list.py:288`:
```python
click="trigger('tasks_prev_page')"
```

This works for no-argument triggers. The issue may be with passing arguments via `trigger('name', [args])`.

## Resolution (2026-01-18)

### Root Cause Found

There were **TWO separate handler files** defining `select_session`:

1. **`handlers/session_handlers.py`** - Used `@ctrl.trigger`, HAD task loading, but **NOT REGISTERED**
2. **`controllers/sessions.py`** - Used `@ctrl.set`, NO task loading, **WAS REGISTERED**

The `handlers/session_handlers.py` was never called by `register_all_controllers()`.

### Fix Applied

Modified `controllers/sessions.py` (the active file):

1. Changed `@ctrl.set("select_session")` to `@ctrl.trigger("select_session")`
2. Added `load_session_tasks(session_id)` function with API call
3. Call `load_session_tasks()` inside `select_session()` handler

### Verification

**Verified with valid 2026 session data:**

- **Session:** `SESSION-2026-01-10-INTENT-TEST`
- **API Response:** 3 tasks (P12.3, P12.4, P12.5)
- **UI Display:** "Completed Tasks: 3" with all task names and DONE status chips
- **Screenshot:** `.playwright-mcp/session-tasks-verified.png`

**Tasks Displayed:**
1. P12.3: Agent Chat Backend: DelegationProtocol wired in chat.py:31-145 - DONE
2. P12.4: Execution Logging: 26/26 tests, UI timeline viewer, API endpoints - DONE
3. P12.5: Delegation Protocol: DelegationProtocol in agent/orchestrator/delegation.py - DONE

## Screenshots

| Screenshot | Description |
|------------|-------------|
| `.playwright-mcp/session-detail-still-zero.png` | BEFORE: Session showing 0 tasks despite API returning tasks |
| `.playwright-mcp/session-tasks-verified.png` | AFTER: Session showing 3 tasks correctly (2026 data) |

## Cleanup Required

The `handlers/session_handlers.py` file is now redundant - its `select_session` and `load_session_tasks` logic has been moved to the active `controllers/sessions.py`. Consider removing the duplicate handler file to prevent confusion.

## Related

- [GAP-UI-AUDIT-2026-01-18](GAP-UI-AUDIT-2026-01-18.md) - Parent audit
- [GAP-UI-TASK-SESSION-001](GAP-UI-TASK-SESSION-001.md) - Task linked_sessions display (COMPLETED)
- RULE-019: UI/UX Standards

---

*Per GAP-DOC-01-v1: Evidence file format*
