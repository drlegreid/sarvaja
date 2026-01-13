# CONTAINER-DEV-02-v1: Docker Dev Container Workflow

**Category:** `development` | **Priority:** HIGH | **Status:** DISABLED | **Type:** LEAF

> **Legacy ID:** RULE-030
> **Location:** [RULES-STANDARDS.md](../operational/RULES-STANDARDS.md)
> **Tags:** `docker`, `containers`, `development`, `deprecated`

---

## Status: DISABLED (2026-01-13)

This rule has been superseded by Podman-based workflows. See [RULE-035](RULE-035.md) for current container operations.

When Docker support is needed, create a gap and implement accordingly.

---

## Original Directive (Historical)

For UI/API development, agents MUST use Docker dev containers with volume mounts instead of local Python processes.

---

## Migration Path

| Docker Command | Podman Equivalent | MCP Tool |
|----------------|-------------------|----------|
| `docker ps` | `podman ps` | `mcp__podman__container_list` |
| `docker-compose up` | `podman compose up` | `mcp__podman__container_run` |
| `docker logs` | `podman logs` | `mcp__podman__container_logs` |

---

## Backward Compatibility

Per DECISION-003: ContainerRecovery class auto-detects runtime:

```python
from hooks.recovery.containers import ContainerRecovery
recovery = ContainerRecovery()  # Auto-detects podman/docker
```

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
