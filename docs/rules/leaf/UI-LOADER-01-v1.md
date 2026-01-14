# UI-LOADER-01-v1: Reactive Loaders with Trace Status

**Category:** `technical` | **Priority:** MEDIUM | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Location:** [RULES-TECHNICAL.md](../RULES-TECHNICAL.md)
> **Tags:** `ui`, `loading`, `trace`, `observability`

---

## Directive

UI components MUST display reactive loading indicators with trace status for all async data operations. Loading states should include API call metadata for debugging and monitoring.

---

## Loader State Requirements

### 1. LoaderState Structure

Each component loading state MUST include:

| Field | Type | Description |
|-------|------|-------------|
| `is_loading` | boolean | Whether loading is in progress |
| `has_error` | boolean | Whether an error occurred |
| `error_message` | string | Error description (if any) |
| `trace` | APITrace | API call metadata |
| `items_count` | int | Number of items loaded |
| `last_loaded` | datetime | When data was last refreshed |

### 2. APITrace Structure

Each API call trace MUST capture:

| Field | Type | Description |
|-------|------|-------------|
| `endpoint` | string | API endpoint called |
| `method` | string | HTTP method (GET, POST, etc.) |
| `status` | string | pending, loading, success, error |
| `status_code` | int | HTTP response code |
| `start_time` | datetime | When request started |
| `duration_ms` | int | Total request duration |
| `request_id` | string | Unique request identifier |

---

## Component Loading States

Per-component loading states (not global):

```python
# Initial state includes loader states for each component
{
    'rules_loading': False,
    'rules_loader': {
        'is_loading': False,
        'trace': {...},
        'items_count': 0,
    },
    'sessions_loading': False,
    'sessions_loader': {...},
    # ... other components
}
```

---

## Transform Functions

Use transform functions to update loading state:

```python
from agent.governance_ui.loaders import (
    set_loading_start,
    set_loading_complete,
    set_loading_error,
)

# Start loading
set_loading_start(state, "rules", "/api/rules")

# Complete loading
set_loading_complete(state, "rules", status_code=200, items_count=10)

# Handle error
set_loading_error(state, "rules", "Connection timeout", status_code=504)
```

---

## UI Display Requirements

1. **Skeleton Loaders**: Show placeholder content matching expected layout
2. **Progress Indicators**: Linear progress bar for indeterminate loads
3. **Trace Status**: Display endpoint and timing in developer mode
4. **Error States**: Show error message with retry option

---

## Enforcement

**MCP Tool**: `governance_dashboard.py` uses loader state from `get_initial_state()`

**Gap Trigger**: Missing loading states trigger GAP-UI-LOADER-*

---

*Per GAP-UI-047: Reactive loaders with trace status*
