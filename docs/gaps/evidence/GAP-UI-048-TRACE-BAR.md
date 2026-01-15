# GAP-UI-048: Trace Bar UI Component

**Status:** RESOLVED
**Priority:** MEDIUM
**Category:** UI
**Created:** 2026-01-14
**Resolved:** 2026-01-14

## Summary

Trace bar UI component now captures and displays API call events.

## Resolution (2026-01-14)

### Root Cause
The trace transforms were being called and state was updating server-side, but Vue wasn't reflecting the changes. The issue was using `state.update({...})` instead of direct attribute assignment.

### Fix Applied
Changed `_add_trace_event()` in `transforms.py` to use direct attribute assignment:

```python
# Before (doesn't trigger Vue reactivity):
state.update({
    'trace_events': events,
    'trace_events_count': len(events),
    ...
})

# After (triggers Vue reactivity properly):
state.trace_events = events
state.trace_events_count = len(events)
...
```

### Key Learning
In Trame with Vue 3, `state.update()` (dict-style update) doesn't trigger Vue reactivity the same way direct attribute assignment does. Use `state.attr = value` for proper reactivity.

## Playwright Verification (2026-01-14)

### All Working
- [x] Trace bar visible at bottom of screen
- [x] Collapsed view shows summary (5 events, 5 API after refresh)
- [x] Click to expand works
- [x] Filter buttons render (ALL, API, UI, ERRORS)
- [x] Clear button renders
- [x] Events captured on API calls (Refresh button)
- [x] Last event preview shows in collapsed view

## Screenshots

- `.playwright-mcp/GAP-UI-048-trace-bar-working.png` - Final working state

## Files Modified

- `agent/governance_ui/trace_bar/transforms.py` - Direct assignment for Vue reactivity
- `agent/governance_ui/views/trace_bar_view.py` - Use `trace_events.length` for counts
- `agent/governance_ui/controllers/data_loaders.py` - API trace calls (already wired)

## Related

- GAP-UI-047: Reactive loader states (completed)
- Initial state in `agent/governance_ui/state/initial.py`
