# WORKFLOW-HOTRELOAD-01-v1: Dashboard Hot-Reload via Watcher

**Category:** `workflow` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Location:** [RULES-OPERATIONAL.md](../operational/RULES-OPERATIONAL.md)
> **Tags:** `dashboard`, `hot-reload`, `trame`, `watcher`, `podman`

---

## Directive

The Trame dashboard MUST use a file watcher process to auto-restart on Python code changes. Direct `python -m agent.governance_dashboard` entrypoints are prohibited in container configurations.

---

## Problem Statement

Trame caches Python modules at startup. Unlike uvicorn's `--reload` flag for FastAPI, Trame has no built-in hot-reload capability. Code changes to `agent/` or `governance/` directories require a full process restart to take effect.

Without auto-restart:
- Developers must manually restart the container after every code change
- The dashboard watcher was introduced (GAP-WORKFLOW-RELOAD-001) but has platform-specific requirements

---

## Required Patterns

### Container Entrypoint

The dashboard Dockerfile MUST use the watcher as entrypoint:

```dockerfile
# CORRECT - watcher auto-restarts on .py changes
CMD ["python", "-m", "agent.dashboard_watcher"]

# WRONG - no auto-restart capability
CMD ["python", "-m", "agent.governance_dashboard", "--port", "8081"]
```

### Watcher Configuration

| Setting | Value | Rationale |
|---------|-------|-----------|
| Observer | `PollingObserver` | Podman bind mounts don't propagate inotify events |
| Poll interval | 3 seconds | Balance between responsiveness and CPU usage |
| Debounce | 2 seconds | Prevent restart storms during multi-file edits |
| Watch dirs | `/app/agent`, `/app/governance` | Both UI and backend code |
| File filter | `*.py` only | Ignore non-Python changes |

### Vuetify 3 Event Handling in Trame

Vuetify 3 VSelect/VBtnToggle do NOT emit `change` events. Use `@state.change()` handlers:

```python
# WRONG - Vuetify 3 VSelect ignores `change` in Trame
v3.VSelect(
    v_model="my_filter",
    change="trigger('apply_filter')",  # Never fires
)

# CORRECT - Use @state.change() in the controller
@state.change("my_filter")
def _on_filter_change(my_filter, **kwargs):
    load_data()  # Reactive handler
```

---

## Anti-Patterns (NEVER DO)

1. Using `watchdog.observers.Observer` (inotify) in containers with bind mounts
2. Setting `CMD` directly to `governance_dashboard` without the watcher
3. Using Vuetify 3 `change` event prop for VSelect/VBtnToggle/VSelect triggers
4. Relying on container restart for code changes during development

---

## Implementation Reference

- **Watcher**: `agent/dashboard_watcher.py` (~110 lines)
- **Dockerfile**: `agent/Dockerfile.dashboard` (uses `dashboard_watcher` as CMD)
- **Dependencies**: `watchdog` package in `requirements.txt`

---

## Related

- CONTAINER-DEV-01-v1: Container-first development
- ARCH-INFRA-02-v1: Infrastructure patterns
- GAP-WORKFLOW-RELOAD-001: Original gap that motivated the watcher

---

*Per META-TAXON-01-v1: Semantic rule naming*
*Created: 2026-02-09 after discovering Trame has no hot-reload and Vuetify 3 event incompatibility*
