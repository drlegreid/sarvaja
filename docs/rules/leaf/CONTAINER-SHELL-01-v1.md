# CONTAINER-SHELL-01-v1: Shell Command Environment Selection

**Category:** `devops` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Legacy ID:** RULE-035
> **Location:** [RULES-STANDARDS.md](../operational/RULES-STANDARDS.md)
> **Tags:** `devops`, `shell`, `podman`, `containers`

---

## Directive

Agents MUST use the correct shell environment. **ALWAYS use Podman MCP tools for container operations.** Fallback to shell commands ONLY when Podman MCP is unavailable.

---

## Environment Matrix

| Environment | Tool | Use For |
|-------------|------|---------|
| **Containers** | `mcp__podman__*` | **ALWAYS USE FIRST** for container ops |
| **Linux Bash** | Built-in Bash | curl, git, sleep, system commands |
| **Windows PowerShell** | `mcp__powershell__run_powershell` | Invoke-WebRequest, Get-ChildItem |

---

## Container Runtime (2026-01-13)

**MANDATORY: USE PODMAN MCP FOR ALL CONTAINER OPERATIONS**

| Task | REQUIRED (MCP) | Fallback (Only if MCP unavailable) |
|------|----------------|-----------------------------------|
| List containers | `mcp__podman__container_list` | `podman ps` |
| Start container | `mcp__podman__container_run` | `podman compose up -d` |
| View logs | `mcp__podman__container_logs` | `podman logs` |
| Stop container | `mcp__podman__container_stop` | `podman stop` |
| Build image | `mcp__podman__image_build` | `podman build` |
| List images | `mcp__podman__image_list` | `podman images` |

---

## When to Use Fallback

Shell commands are permitted ONLY when:
1. Podman MCP server is not running/available
2. Complex compose operations (e.g., `--profile cpu`)
3. Pipe/redirect operations not supported by MCP

---

## Runtime Abstraction

```python
# Auto-detects podman or docker at runtime
from hooks.recovery.containers import ContainerRecovery
ContainerRecovery()  # Uses podman on Linux, docker on Windows/Mac
```

---

## Anti-Patterns (PROHIBITED)

| Don't | Do Instead |
|-------|-----------|
| `Start-Sleep` in Bash | Use `sleep N` |
| `Select-Object` in Bash | Use `head -n N` |
| `Invoke-WebRequest` in Bash | Use `curl` |
| `docker` commands | Use `podman` or Podman MCP |
| Shell for container ops | Use `mcp__podman__*` tools |

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
