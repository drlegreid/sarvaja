# GAP-UI-EXP-004: Tasks View Missing Search/Filter/Pagination

**Status:** RESOLVED
**Priority:** HIGH
**Category:** ux
**Discovered:** 2026-01-14 via Playwright exploratory testing

## Problem Statement

Tasks view displays 50 tasks in one long scrolling list without:
- Search functionality
- Status filter (TODO/DONE/IN_PROGRESS)
- Phase filter (R&D/P10/P11/P12)
- Pagination

Rules view has search - Tasks should have similar UX.

## Technical Details

### Affected Files

| File | Current | Required |
|------|---------|----------|
| `agent/governance_ui/views/tasks_view.py` | Basic list | Add search/filter/pagination |

### Reference Implementation (Rules View)

```python
# agent/governance_ui/views/rules/list.py:47-53
v3.VTextField(
    v_model=("rule_search_query", ""),
    label="Search rules...",
    prepend_icon="mdi-magnify",
    clearable=True,
    hide_details=True,
)
```

### Required Components

1. **Search TextField**
```python
v3.VTextField(
    v_model=("task_search_query", ""),
    label="Search tasks...",
    prepend_icon="mdi-magnify",
    clearable=True,
)
```

2. **Status Filter**
```python
v3.VSelect(
    v_model=("task_status_filter", ""),
    items=["", "TODO", "DONE", "IN_PROGRESS", "BLOCKED"],
    label="Status",
    clearable=True,
)
```

3. **Phase Filter**
```python
v3.VSelect(
    v_model=("task_phase_filter", ""),
    items=["", "R&D", "P10", "P11", "P12", "TEST"],
    label="Phase",
    clearable=True,
)
```

4. **Pagination**
```python
v3.VPagination(
    v_model=("task_page", 1),
    length=("Math.ceil(filtered_tasks.length / tasks_per_page)", 1),
    total_visible=7,
)
```

### State Variables Needed

Add to `agent/governance_ui/state/initial.py`:
```python
"task_search_query": "",
"task_status_filter": "",
"task_phase_filter": "",
"task_page": 1,
"tasks_per_page": 20,
```

### Computed Property for Filtering

```python
# In controller or state transforms
filtered_tasks = [
    t for t in tasks
    if (not search_query or search_query.lower() in t["description"].lower())
    and (not status_filter or t["status"] == status_filter)
    and (not phase_filter or t["phase"] == phase_filter)
]
```

## Current UX Issues

1. **50 tasks in one list** - User must scroll to find specific task
2. **No search** - Cannot quickly find task by ID or description
3. **No status filter** - Cannot see only TODO or only DONE tasks
4. **No phase filter** - Cannot focus on specific project phase
5. **Inconsistent with Rules** - Rules has search, Tasks doesn't

## Resolution (2026-01-14)

**Root Cause:** UI components existed but filter dropdown options (`task_status_options`, `task_phase_options`) were never added to state.

**Fix Applied:** Added to `agent/governance_ui/state/initial.py`:
```python
'task_status_options': ['TODO', 'IN_PROGRESS', 'DONE', 'BLOCKED'],
'task_phase_options': ['P10', 'P11', 'P12', 'R&D', 'FH', 'KAN', 'ORCH', 'DOCVIEW'],
```

**Verification:** State loads correctly with both options lists.

## Related

- Rule: UI-LOADER-01-v1 (consistent UX)
- GAP-UI-EXP-003: Task list shows only DONE at top (related sorting issue)
