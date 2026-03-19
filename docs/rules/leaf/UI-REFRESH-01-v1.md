# UI-REFRESH-01-v1: Smart Dashboard Auto-Refresh

| Field | Value |
|-------|-------|
| **Rule ID** | UI-REFRESH-01-v1 |
| **Category** | UI / Data Sync |
| **Priority** | HIGH |
| **Status** | ACTIVE |
| **Applicability** | MANDATORY |
| **Created** | 2026-03-19 |

## Directive

Dashboard data views MUST support smart auto-refresh polling that:

1. **Only polls when the relevant tab is active** — no background API calls for invisible views
2. **Pauses when user is viewing a detail record** — never interrupt detail reading with list refresh
3. **Uses configurable interval** (minimum 5 seconds) — default 10s for sessions, 5s for backlog
4. **Provides a visible toggle** — user can enable/disable auto-refresh per view
5. **Calls `state.flush()`** after update to force Trame UI sync

## Pattern (Reference Implementation)

```python
# Module-level task reference
_polling_task: Optional[asyncio.Task] = None

@ctrl.trigger("toggle_{view}_auto_refresh")
def toggle_auto_refresh():
    nonlocal _polling_task
    state.{view}_auto_refresh = not state.{view}_auto_refresh

    if state.{view}_auto_refresh:
        async def polling_loop():
            while state.{view}_auto_refresh:
                await asyncio.sleep(state.{view}_refresh_interval)
                if getattr(state, 'active_view', '') != '{view}':
                    continue  # Skip — user on another tab
                if getattr(state, 'show_{view}_detail', False):
                    continue  # Skip — user viewing detail
                load_{view}_page()
                state.flush()
        loop = asyncio.get_event_loop()
        if _polling_task and not _polling_task.done():
            _polling_task.cancel()
        _polling_task = loop.create_task(polling_loop())
    else:
        if _polling_task and not _polling_task.done():
            _polling_task.cancel()
            _polling_task = None
```

## State Variables Required

Each view implementing auto-refresh needs:
- `{view}_auto_refresh: bool = False` — toggle state
- `{view}_refresh_interval: int` — seconds between polls (min 5)

## Guards (DO NOT refresh when)

- `active_view != '{view}'` — user is on another tab
- `show_{view}_detail == True` — user is reading a detail record
- User is actively typing in a filter/search field (debounce)

## Rationale

Without auto-refresh, users must manually switch tabs or click filters to see
new data from the watcher daemon or ingestion scheduler. This creates a
disconnect between the event-driven backend (watchdog JSONL monitoring) and
the dashboard UI.

## Related Rules

- WORKFLOW-HOTRELOAD-01-v1: File watcher hot-reload (code changes, not data)
- DATA-INGEST-01-v1: JSONL ingestion service
- DATA-PERSIST-01-v1: Session persistence integrity
