# GAP-UI-ORPHAN-HANDLERS-001: Orphaned Handler Files Not Registered

**Priority:** HIGH | **Category:** architecture | **Status:** RESOLVED
**Discovered:** 2026-01-18 | **Source:** GAP-UI-AUDIT-2026-01-18 Session Feedback
**Assignee:** AGENT | **Resolution:** IMPLEMENTED 2026-01-18

---

## Summary

The `handlers/` directory contains registration functions that are **never called**, creating orphaned dead code that causes confusion and potential bugs when developers add functionality to the wrong file.

## Root Cause Analysis

### Architecture Issue

Two parallel directory structures exist for UI handlers:

| Directory | Registration | Status |
|-----------|--------------|--------|
| `controllers/` | Called by `register_all_controllers()` | **ACTIVE** |
| `handlers/` | NOT called anywhere | **ORPHANED** |

### Orphaned Functions

From `handlers/__init__.py`:
```python
__all__ = [
    "register_rule_handlers",      # NOT CALLED
    "register_task_handlers",      # NOT CALLED
    "register_session_handlers",   # NOT CALLED
    "register_common_handlers",    # NOT CALLED
    "register_trace_bar_handlers", # ONLY ONE CALLED
]
```

### Evidence

```bash
# Only register_trace_bar_handlers is called from controllers/__init__.py
$ grep -r "register_.*_handlers" agent/governance_ui/controllers/
controllers/__init__.py:from ..handlers import register_trace_bar_handlers
controllers/__init__.py:    register_trace_bar_handlers(ctrl, state)
```

### Impact

1. **GAP-UI-SESSION-TASKS-001**: `select_session` handler with task loading existed in `handlers/session_handlers.py` but was never called. Fix required adding to `controllers/sessions.py`.

2. **Task navigation**: `navigate_to_task` handler existed in `handlers/task_handlers.py` but was never called. Fix required adding to `controllers/tasks.py`.

3. **Developer confusion**: New functionality might be added to wrong file, leading to "works on dev, fails in prod" scenarios.

## Files Analysis

| Handler File | Controllers Equivalent | Duplicated? |
|--------------|----------------------|-------------|
| `handlers/rule_handlers.py` | `controllers/rules.py` | 95% duplicate |
| `handlers/task_handlers.py` | `controllers/tasks.py` | 90% duplicate |
| `handlers/session_handlers.py` | `controllers/sessions.py` | 85% duplicate |
| `handlers/common_handlers.py` | `controllers/data_loaders.py` | 80% duplicate |

## Resolution Options

### Option A: Remove handlers/ directory (Recommended)
- Delete all orphaned handler files
- Keep only `register_trace_bar_handlers` (move to controllers if needed)
- Single source of truth in controllers/

### Option B: Integrate handlers via controllers/__init__.py
- Call all handler registration functions
- Risk: Duplicate handler registrations may conflict

## Resolution (2026-01-18)

**Option A implemented**: Removed orphaned handler files.

### Changes Made

1. ✅ Deleted `handlers/rule_handlers.py`
2. ✅ Deleted `handlers/task_handlers.py`
3. ✅ Deleted `handlers/session_handlers.py`
4. ✅ Updated `handlers/__init__.py` to only export `register_trace_bar_handlers`
5. ✅ Added `navigate_to_task()` to `controllers/tasks.py`
6. ✅ Added `load_session_tasks()` to `controllers/sessions.py`

### Files After Cleanup

```
handlers/
├── __init__.py           # Only exports register_trace_bar_handlers
└── common_handlers.py    # Contains trace bar handlers (USED)
```

### Verification

- Dashboard restarts successfully
- Session tasks load correctly (verified with SESSION-2026-01-10-INTENT-TEST)
- Task navigation from session detail works (P12.3 navigates to Tasks view)
- Screenshot: `.playwright-mcp/task-navigation-working.png`

## Related

- [GAP-UI-SESSION-TASKS-001](GAP-UI-SESSION-TASKS-001.md) - Direct impact of this issue
- [GAP-UI-AUDIT-2026-01-18](GAP-UI-AUDIT-2026-01-18.md) - Parent audit
- RULE-012: Single Responsibility
- DOC-SIZE-01-v1: File organization

---

*Per GAP-DOC-01-v1: Evidence file format*
