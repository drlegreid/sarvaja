# CONTAINER-SHELL-01-v1: Shell Command Environment Selection

**Category:** `devops` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Legacy ID:** RULE-035
> **Location:** [RULES-STANDARDS.md](../operational/RULES-STANDARDS.md)
> **Tags:** `devops`, `shell`, `podman`, `containers`

---

## Directive

Agents MUST use **podman** for all container operations. NEVER use `docker` commands. NEVER run containerized services as bare `python` processes.

---

## Environment Matrix

| Environment | Tool | Use For |
|-------------|------|---------|
| **Containers** | `podman` CLI | All container lifecycle operations |
| **Linux Bash** | Built-in Bash | curl, git, sleep, system commands |
| **Python** | `.venv/bin/python3` | Local scripts, pytest, one-off tools |

---

## Container Operations (CRITICAL)

**MANDATORY: USE PODMAN FOR ALL CONTAINER OPERATIONS**

| Task | Command |
|------|---------|
| List containers | `podman compose --profile dev ps` |
| Start stopped | `podman start <container_name>` |
| Restart running | `podman restart <container_name>` |
| Stop container | `podman stop <container_name>` |
| View logs | `podman logs <container_name> --tail 50` |
| Full stack up | `podman compose --profile dev up -d` |
| Full stack down | `podman compose --profile dev down` |
| Rebuild images | `podman compose --profile dev up -d --build` |
| Exec in container | `podman exec <container_name> <command>` |

### Key Container Names

| Container | Ports | Purpose |
|-----------|-------|---------|
| `platform_governance-dashboard-dev_1` | 8081 (UI), 8082 (API) | Dashboard + REST API |
| `platform_typedb_1` | 1729 | Rule inference engine |
| `platform_chromadb_1` | 8001 | Semantic search |

---

## Profile (CRITICAL)

**Only `--profile dev` exists.** Using other profiles causes **silent failure** — no error, no containers.

| Wrong | Correct |
|-------|---------|
| `podman compose --profile cpu ps` | `podman compose --profile dev ps` |
| `podman compose --profile test up` | `podman compose --profile dev up -d` |
| `podman compose ps` (no profile) | `podman compose --profile dev ps` |

---

## Anti-Patterns (PROHIBITED)

| Don't | Do Instead |
|-------|-----------|
| `docker` commands | `podman` commands |
| `python -m governance.api --port 8082` | `podman start platform_governance-dashboard-dev_1` |
| `python -m agent.governance_dashboard` | `podman restart platform_governance-dashboard-dev_1` |
| `nohup .venv/bin/python -m ...` | Containers run as daemons natively |
| `kill` / `fuser -k` to free ports | `podman stop` then `podman start` |
| `--profile cpu` | `--profile dev` |

---

## Tool Bindings (GOV-BIND-01-v1)

| Verification | Tool | Example |
|-------------|------|---------|
| Container status | Bash | `podman compose --profile dev ps` |
| API health | `mcp__rest-api__test_request` | `GET http://localhost:8082/api/health` |
| UI render | `mcp__playwright__browser_navigate` | `http://localhost:8081` |

---

## Validation

- [ ] All container ops use `podman`, never `docker`
- [ ] `--profile dev` used consistently
- [ ] No bare python processes for services (8081, 8082)
- [ ] Container names used for start/restart/stop

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
*Per CONTAINER-DEV-01-v1: Podman dev profile mandatory*
*Per GOV-BIND-01-v1: Tool bindings specified*
