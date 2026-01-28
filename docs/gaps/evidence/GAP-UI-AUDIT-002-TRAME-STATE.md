# GAP-UI-AUDIT-002: Trame State Singleton - Multiple Windows Mirror Each Other

**Priority:** CRITICAL | **Category:** architecture | **Status:** RESOLVED
**Discovered:** 2026-01-18 | **Source:** User Feedback
**Resolution:** 2026-01-20 - Option C implemented (client-side state via sessionStorage)

---

## Summary

Multiple browser windows/tabs opening the dashboard mirror each other because Trame uses a **singleton state pattern** by default. This is by design, not a bug.

## Root Cause

Trame's `get_server()` creates a **single server instance** with **shared state**:

```python
# governance_dashboard.py:232-241
self._server = get_server(client_type="vue3", name="governance-dashboard")
self._state = self._server.state  # Singleton - shared across ALL clients
```

**Result:**
- Client 1 clicks navigation -> `active_view` state changes
- Server broadcasts state to ALL clients via WebSocket
- Client 2's UI updates automatically (unwanted)

## What Gets Shared (Unintentionally)

| State Type | Shared? | Impact |
|------------|---------|--------|
| Navigation (active_view) | YES | All windows switch tabs together |
| Selection (selected_task) | YES | Selecting task in Window 1 shows in Window 2 |
| Forms (form_*) | YES | Form inputs appear in all windows |
| Filters (search, sort) | YES | Filter changes affect all windows |
| Data (rules, tasks) | YES | Intentional - this is fine |

## Resolution Options

### Option A: ParaViewWeb-style Launcher (Infrastructure)
- **Requires:** `wslink-launcher` service + Apache/nginx proxy
- **How:** Each client gets own Trame process on different port
- **Pro:** True isolation, production-ready pattern
- **Con:** Significant infrastructure overhead

### Option B: Kubernetes/Docker per-user (Scalable)
- **Requires:** K8s/Swarm orchestration + session manager
- **How:** Deploy Trame as stateless service, external routing
- **Pro:** Horizontally scalable, cloud-ready
- **Con:** Complex deployment

### Option C: Client-side State Management (Code Change)
- **Requires:** Refactor state management
- **How:** Move navigation/filter state to Vue (browser-side)
- **Pro:** Lowest infrastructure change
- **Con:** Highest code refactoring effort

## Decision Required

**User Clarification Needed:**

1. **Multi-user support required?**
   - Multiple different users accessing dashboard simultaneously
   - If YES: Options A or B recommended

2. **Multi-window support required?**
   - Single user opening multiple tabs/windows
   - If YES: Option C may suffice (cheaper)

3. **Is this a demo/MVP or production system?**
   - Demo: Can defer to BACKLOG
   - Production: Must resolve before deployment

## Evidence

- Trame GitHub: [Multi-User Discussion #32](https://github.com/Kitware/trame/discussions/32)
- Files affected:
  - `agent/governance_dashboard.py:232-241` (server init)
  - `agent/governance_ui/state/initial.py` (state factory - not leveraged per-client)
  - `agent/governance_ui/controllers/**/*.py` (all controllers share state)

## Immediate Mitigation (Not Full Fix)

If user wants quick partial fix for multi-window in single browser:
1. Use `sessionStorage` for navigation state (Vue-side)
2. Leave data state server-side (rules, tasks, sessions)

This requires code changes but less than full Option C.

---

## Resolution (2026-01-20 DSP Session)

**User Decision:** Option C - Client-side State Management

**Implementation:**

1. **New file:** `agent/governance_ui/components/window_state.py`
   - `inject_window_state_isolator()` function
   - Generates unique window ID per browser tab
   - Saves navigation state keys to sessionStorage
   - Restores on page load, prevents server broadcasts from overwriting

2. **Modified:** `agent/governance_dashboard.py`
   - Added `inject_window_state_isolator()` call in layout

**State Keys Made Window-Local:**
- `active_view` (navigation)
- `show_*_detail` (detail panels)
- `selected_*` (selections)

**State Keys Remain Server-Shared:**
- `rules`, `tasks`, `sessions`, `decisions` (data)
- All form state (intentional for demo)

---

*Per GAP-DOC-01-v1: Evidence file format*
