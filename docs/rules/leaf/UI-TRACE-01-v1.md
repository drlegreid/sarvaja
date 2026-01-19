# UI-TRACE-01-v1: Bottom Bar with Technical Traces

**Category:** `technical` | **Priority:** LOW | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Location:** [RULES-TECHNICAL.md](../RULES-TECHNICAL.md)
> **Tags:** `ui`, `trace`, `debug`, `observability`

---

## Directive

UI MUST include a bottom bar displaying technical traces for developer visibility. Traces include API calls, UI actions, and errors with timing information.

---

## Trace Event Types

| Type | Description | Example |
|------|-------------|---------|
| `api_call` | HTTP API request | `GET /api/rules - 200 OK - 150ms` |
| `ui_action` | User interface action | `click on rules_table` |
| `error` | Error occurrence | `ERROR: Connection timeout` |
| `mcp_call` | MCP tool invocation | `rules_query - OK - 85ms` |

---

## TraceEvent Structure

```python
@dataclass
class TraceEvent:
    event_type: TraceType
    message: str
    timestamp: datetime
    event_id: str

    # API call fields
    endpoint: Optional[str] = None
    method: str = "GET"
    status_code: Optional[int] = None
    duration_ms: int = 0

    # UI action fields
    action: Optional[str] = None
    component: Optional[str] = None
    target: Optional[str] = None
```

---

## Trace Bar State

```python
{
    "trace_bar_visible": True,    # Bar visibility
    "trace_bar_expanded": False,  # Collapsed/expanded
    "trace_events": [],           # Event list (max 100)
    "trace_events_count": 0,
    "trace_error_count": 0,
    "trace_filter": None,         # Filter by type
}
```

---

## UI Behavior

### Collapsed View
- Show status summary: "5 traces | 1 error | last: GET /api/rules"
- Click to expand

### Expanded View
- Show scrollable list of trace events
- Filter by type (API, UI, Error)
- Clear traces button
- Color-code errors (red)

---

## Transform Functions

```python
from agent.governance_ui.trace_bar import (
    add_api_trace,
    add_ui_action_trace,
    add_error_trace,
    clear_traces,
    toggle_trace_bar,
)

# Log API call
add_api_trace(state, "/api/rules", "GET", 200, 150)

# Log UI action
add_ui_action_trace(state, "click", "rules_table", "row_1")

# Clear all traces
clear_traces(state)
```

---

## Enforcement

**Location**: `agent/governance_ui/trace_bar/`

**Gap Trigger**: Missing trace integration triggers GAP-UI-TRACE-*

---

*Per GAP-UI-048: Bottom bar with technical traces*
