# CONTAINER-LIFECYCLE-01-v1: Container Lifecycle Management Protocol

**Category:** `devops` | **Priority:** HIGH | **Status:** DEPRECATED | **Type:** OPERATIONAL

> **DEPRECATED 2026-03-24**: Consolidated into CONTAINER-RESTART-01-v1 which is specific and actively enforced.

> **Created:** 2026-01-20 (Lesson learned from session)
> **Tags:** `devops`, `podman`, `lifecycle`, `containers`

---

## Directive

Use the CORRECT command for container state transitions:
- **Stopped container** → `podman start` (preserves state)
- **Config changed** → `podman compose up -d` (recreates)
- **Need refresh** → `podman restart` (restart in place)

**NEVER use `up -d` to start existing stopped containers** - it recreates them.

---

## Command Decision Matrix

| Current State | Goal | Command | Why |
|---------------|------|---------|-----|
| Stopped | Start | `podman start <name>` | Preserves runtime state |
| Running | Restart | `podman restart <name>` | Quick refresh |
| Running | Update config | `podman compose up -d` | Recreates with new config |
| Any | Fresh start | `podman compose up -d --force-recreate` | Explicit recreation |
| Running | Stop | `podman stop <name>` | Graceful shutdown |

---

## Profile Warning

```bash
# WRONG: Profile doesn't exist - SILENT FAILURE (no error, no containers)
podman compose --profile cpu up -d

# RIGHT: Use existing profile
podman compose --profile dev up -d
```

**Always verify profile exists in compose.yml before using.**

---

## Anti-Patterns (2026-01-20 Lessons)

| Don't | Do Instead | Consequence |
|-------|------------|-------------|
| `up -d` for stopped containers | `podman start` | May lose runtime state |
| Assume profile exists | Check compose.yml | Silent failure |
| `ps -a` with podman-compose | `podman ps -a` | Flag not supported |
| Start only DB services | Start full stack for testing | Can't validate UI |

---

## Validation Checklist

- [ ] Correct command for container state transition
- [ ] Profile verified in compose.yml
- [ ] All dependent services started for testing
- [ ] Health checks pass after operation

---

*Per SESSION-2026-01-20: DevOps lessons learned*
