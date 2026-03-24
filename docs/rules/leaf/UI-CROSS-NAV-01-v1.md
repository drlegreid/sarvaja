# UI-CROSS-NAV-01-v1: Cross-View Navigation Guard Pattern

| Field | Value |
|-------|-------|
| **Rule ID** | UI-CROSS-NAV-01-v1 |
| **Category** | TECHNICAL |
| **Priority** | HIGH |
| **Status** | ACTIVE |
| **Applicability** | MANDATORY |
| **Created** | 2026-03-24 |

## Directive

Cross-view navigation (task->session, session->task) MUST use the guard flag pattern to prevent `on_view_change` from wiping target entity state. Load the target entity BEFORE changing `active_view`.

---

## Required Pattern (Load-First + Guard)

```python
# CORRECT: Load entity first, then switch view with guard
def navigate_to_session(session_id):
    # 1. Load entity BEFORE view change
    session = api_client.get(f"/api/sessions/{session_id}")
    state.selected_session = session

    # 2. Set guard flag
    state.cross_nav_in_progress = True

    # 3. Change view (triggers on_view_change)
    state.active_view = "sessions"

    # 4. Guard cleared by on_view_change after early return


def on_view_change(active_view, **kwargs):
    # Early return when cross-nav guard is set
    if state.cross_nav_in_progress:
        state.cross_nav_in_progress = False
        return  # Entity already loaded — don't wipe it
    # Normal view change: reset entity state
    state.selected_session = None
```

---

## Rules

1. **Load-first**: Fetch and set target entity in state BEFORE changing `active_view`
2. **Guard flag**: Set `cross_nav_in_progress = True` before `active_view` change
3. **Early return**: `on_view_change` early-returns when guard is set, skipping state reset
4. **NEVER `dirty('active_view')`**: Causes double `on_view_change` invocation (Trame flush race)
5. **Minimize state changes** inside `@state.change` callbacks (Trame batches state flushes)

---

## Anti-Patterns (PROHIBITED)

| Don't | Do Instead |
|-------|-----------|
| Change `active_view` then load entity | Load entity FIRST, then change view |
| Call `dirty('active_view')` | Set `active_view` directly (Trame auto-detects) |
| Multiple state writes in `@state.change` | Batch into single update or use guard |
| Ignore cross-nav context in `on_view_change` | Check guard flag before resetting state |

---

## Root Cause (P12 Incident, 2026-03-22)

`on_view_change` wiped `selected_session` state when `active_view` changed to "sessions", because the entity hadn't been loaded yet. `dirty('active_view')` caused double-fire, making the race condition intermittent.

---

## Related

- UI-NAV-01-v1 (Entity navigation context preservation)
- UI-TRAME-01-v1 (Trame state management patterns)

---

*Per EPIC-TASK-QUALITY-V3 P12: Session Navigation Fix*
