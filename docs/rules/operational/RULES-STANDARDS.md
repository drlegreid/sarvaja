# Standards Rules - Sim.ai

Rules governing development standards, DevOps, and documentation.

> **Parent:** [RULES-OPERATIONAL.md](../RULES-OPERATIONAL.md)
> **Rules:** RULE-027, RULE-030, RULE-032, RULE-033, RULE-034, RULE-035

---

## RULE-027: API Server Restart Protocol

**Category:** `testing` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** REQUIRED

### Directive

ALWAYS restart API servers after making code changes BEFORE running tests.

### Protocol

1. STOP existing server process
2. START fresh server instance
3. VERIFY server is responsive (/api/health)
4. RUN tests

### Anti-Patterns

| Don't | Do Instead |
|-------|-----------|
| Run tests immediately after changes | Restart server first |
| Assume hot-reload caught changes | Explicitly restart |
| Debug "404" without checking server | Check if server has latest code |

---

## RULE-030: Docker Dev Container Workflow

**Category:** `development` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** REQUIRED

### Directive

For UI/API development, agents MUST use Docker dev containers with volume mounts instead of local Python processes.

### When to Use Docker

| Scenario | Docker Dev | Local Python |
|----------|-----------|--------------|
| UI validation | ✅ Yes | ❌ No |
| API testing | ✅ Yes | ❌ No |
| Code fix validation | ✅ Yes | ❌ No |
| Unit tests only | Optional | ✅ Yes |

### Available Dev Containers

| Container | Port | Profile | Mounts |
|-----------|------|---------|--------|
| `governance-dashboard-dev` | 8081 | `dev` | agent, governance, docs |
| `governance-api` | 8082 | `cpu` | governance |

---

## RULE-032: File Size & OOP Standards

**Category:** `architecture` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** REQUIRED

### Directive

All source files MUST stay under 300 lines. When exceeded, IMMEDIATELY refactor using OOP/modular design.

### Hard Limits

| Lines | Status | Action |
|-------|--------|--------|
| ≤200 | HEALTHY | No action |
| 201-300 | WARNING | Consider splitting |
| >300 | **VIOLATION** | MUST split immediately |

### Decomposition Heuristics

| Signal | Action |
|--------|--------|
| File >300 lines | Split by entity |
| Class >200 lines | Extract concerns |
| Function >50 lines | Compose smaller functions |
| Mixed concerns | Separate layers |

---

## RULE-033: PARTIAL Task Handling

**Category:** `workflow` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** REQUIRED

### Directive

When a gap requires breakdown, mark as PARTIAL and create linked subtasks. Each subtask must be <2 hours.

### Status Meanings

| Status | Meaning | Next Action |
|--------|---------|-------------|
| OPEN | Not started | Begin or break down |
| PARTIAL | Needs breakdown | Create subtasks |
| IN_PROGRESS | Being worked | Continue |
| RESOLVED | Done | No action |

### Naming Conventions

```
GAP-UI-001       ← PARTIAL (parent)
GAP-UI-001.1     ← RESOLVED (subtask A)
GAP-UI-001.2     ← OPEN (subtask B)
```

---

## RULE-034: Relative Document Linking

**Category:** `documentation` | **Priority:** CRITICAL | **Status:** ACTIVE | **Type:** REQUIRED

### Directive

ALL document references MUST use relative markdown links: `[text](relative/path)`

### Link Formats

| Type | Format | Example |
|------|--------|---------|
| Evidence | `[ID](evidence/FILE.md)` | `[SESSION-2026](evidence/SESSION-2026.md)` |
| Gaps | `[GAP-X](docs/gaps/GAP-INDEX.md#gap-x)` | `[GAP-003](docs/gaps/GAP-INDEX.md#gap-003)` |
| Rules | `[RULE-X](docs/rules/FILE.md#rule-x)` | `[RULE-034](#rule-034)` |
| Source | `[file:line](path#Lline)` | `[api.py:42](governance/api.py#L42)` |

### Anti-Patterns

| Don't | Do Instead |
|-------|-----------|
| `sim-ai-session` (plain text) | `[sim-ai-session](evidence/...)` |
| `See GAP-INDEX.md` | `See [GAP-INDEX.md](docs/gaps/GAP-INDEX.md)` |

---

## RULE-035: Shell Command Environment Selection

**Category:** `devops` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** REQUIRED

### Directive

Agents MUST use the correct shell environment and prefer MCP tools over shell commands. Bash tool runs in Linux; Windows-specific requires PowerShell MCP.

### Environment Matrix

| Environment | Tool | Use For |
|-------------|------|---------|
| **Linux Bash** | Built-in Bash | curl, git, sleep, system commands |
| **Windows PowerShell** | `mcp__powershell__run_powershell` | Invoke-WebRequest, Get-ChildItem |
| **Containers** | `mcp__podman__*` | Container operations (PREFERRED) |

### Container Runtime (2026-01-12)

**USE PODMAN MCP, NOT SHELL COMMANDS** for container operations:

| Task | Preferred (MCP) | Fallback (Shell) |
|------|-----------------|------------------|
| List containers | `mcp__podman__container_list` | `podman ps` |
| Start container | `mcp__podman__container_run` | `podman compose up -d` |
| View logs | `mcp__podman__container_logs` | `podman logs` |
| Stop container | `mcp__podman__container_stop` | `podman stop` |

**Runtime Abstraction:** [`.claude/hooks/recovery/containers.py`](../../../.claude/hooks/recovery/containers.py)

```python
# Auto-detects podman or docker at runtime
ContainerRecovery()  # Uses podman on Linux, docker on Windows/Mac
```

### Command Equivalents

| Task | Bash (Linux) | PowerShell (Windows) |
|------|--------------|---------------------|
| Wait N seconds | `sleep N` | `Start-Sleep -Seconds N` |
| HTTP request | `curl http://...` | `Invoke-WebRequest -Uri ...` |
| First N lines | `head -n N` | `Select-Object -First N` |

### Anti-Patterns (PROHIBITED)

| Don't | Do Instead |
|-------|-----------|
| `Start-Sleep` in Bash | Use `sleep N` |
| `Select-Object` in Bash | Use `head -n N` |
| `Invoke-WebRequest` in Bash | Use `curl` |
| `docker` commands | Use `podman` or Podman MCP |
| Shell for container ops | Use `mcp__podman__*` tools |

---

## RULE-037: Fix Validation Protocol

**Category:** `quality` | **Priority:** CRITICAL | **Status:** ACTIVE | **Type:** REQUIRED

### Directive

When marking a fix as DONE/RESOLVED, agent MUST run verification test and include evidence. "Done but broken" is a CRITICAL violation.

### Validation Steps (REQUIRED)

1. **RUN verification test** - Execute test that proves fix works
2. **INCLUDE evidence** - Screenshot, log output, or test result
3. **LINK to fix** - Reference the commit/file changed
4. **SAVE session context** - `chroma_save_session_context()` with fix details

### Evidence Requirements

| Fix Type | Verification | Evidence |
|----------|-------------|----------|
| Container fix | `podman ps` shows running | Terminal output |
| MCP fix | `governance_health()` OK | Health check output |
| API fix | Curl/test passing | Test result |
| UI fix | Playwright screenshot | Screenshot file |

### Anti-Patterns (PROHIBITED)

| Don't | Do Instead |
|-------|-----------|
| Mark DONE without testing | Run verification first |
| "Fixed, should work now" | "Fixed, verified with [test]" |
| Skip evidence for "simple" fixes | ALL fixes need evidence |
| Trust previous session claims | RE-verify in current session |

### GAP Trigger

Per GAP-VERIFY-001: Failure to verify results in gap reopening.

---

## RULE-042: Destructive Command Prevention

**Category:** `safety` | **Priority:** CRITICAL | **Status:** ACTIVE | **Type:** PROHIBITED

### Directive

Agents MUST NEVER execute destructive commands without explicit user confirmation. Destructive means data loss or irreversible state change.

### Prohibited Commands (ALWAYS REQUIRE CONFIRMATION)

| Command Pattern | Risk | Alternative |
|----------------|------|-------------|
| `rm -rf /path` | Data loss | `rm -i` or explicit file list |
| `podman system reset` | Wipes all images | Restart specific containers |
| `git reset --hard` | Loses uncommitted work | `git stash` first |
| `DROP TABLE` / `DELETE FROM` | Database loss | Backup first |
| `--force` on any destructive op | Bypasses safety | Remove --force |

### Before ANY Destructive Action

1. **CHECK actual state** - `podman ps`, `ls`, `git status`
2. **QUERY memory** - `chroma_query_documents(["recent infrastructure changes"])`
3. **READ DEVOPS.md** - Correct commands for environment
4. **ASK user** - If uncertain, use `AskUserQuestion`

### Recovery First Principle

| Symptom | DON'T | DO Instead |
|---------|-------|-----------|
| Container not responding | Reset everything | Restart specific service |
| MCP failing | Wipe and rebuild | Check logs, fix config |
| TypeDB errors | Delete data | Query for specific issue |

### GAP Trigger

Per GAP-DESTRUCT-001: Executing destructive commands without verification creates CRITICAL gap.

---

*Per RULE-012: DSP Semantic Code Structure*
