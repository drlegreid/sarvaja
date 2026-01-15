# GAP-UI-EXP-006: Infrastructure Health Check Shows Incorrect Status

**Status:** RESOLVED
**Priority:** CRITICAL (was)
**Category:** observability
**Discovered:** 2026-01-14 via Playwright exploratory testing
**Resolved:** 2026-01-14

## Problem Statement

Infrastructure view shows TypeDB, ChromaDB, and Podman as "DOWN" when services are actually running.

## Root Cause

The `load_infra_status()` function in `data_loaders.py` was using `localhost` for port checks. When running inside a container, `localhost` refers to the container itself, not the host machine or other containers.

Services (TypeDB, ChromaDB, etc.) are running in separate containers on the same Podman compose network. Inter-container communication requires using service names (e.g., `typedb`, `chromadb`) with internal ports.

## Fix Applied

Modified `agent/governance_ui/controllers/data_loaders.py`:

1. **Container detection**: Check for `/.dockerenv` or `/run/.containerenv` to detect container runtime
2. **Service configuration**: Map each service to (container_host, container_port, host_port)
3. **Dynamic hostname selection**:
   - In container: use compose service names (e.g., `typedb:1729`, `chromadb:8000`)
   - On host: use `localhost` with mapped ports (e.g., `localhost:8001`)
4. **Podman check**: In container, assume podman OK if container is running

### Code Change

```python
# Detect if running in container
in_container = os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv")

# Service config: (container_host, container_port, host_port)
service_config = {
    "typedb": ("typedb", 1729, 1729),
    "chromadb": ("chromadb", 8000, 8001),  # internal 8000, mapped to 8001
    "litellm": ("litellm", 4000, 4000),
    "ollama": ("ollama", 11434, 11434),
}

for name, (container_host, container_port, host_port) in service_config.items():
    if in_container:
        ok = check_port(container_host, container_port)
    else:
        ok = check_port("localhost", host_port)
```

## Verification

Playwright test confirmed all services now show "OK":
- Podman: OK
- TypeDB: OK (port 1729)
- ChromaDB: OK (port 8001)
- LiteLLM: OK (port 4000)
- Ollama: OK (port 11434)
- Memory: 47.2%

## Files Modified

| File | Changes |
|------|---------|
| `agent/governance_ui/controllers/data_loaders.py` | Container-aware port checking |

## Related

- Rule: SAFETY-HEALTH-01-v1
- GAP-UI-EXP-009: TypeDB schema mismatch (resolved same session)

---
*Per GAP-DOC-01-v1: Full technical details in evidence file*
