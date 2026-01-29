# CONTAINER-DEV-01-v1: DevOps Version Compatibility Protocol

**Category:** `devops` | **Priority:** CRITICAL | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Legacy ID:** RULE-009
> **Location:** [RULES-TOOLING.md](../technical/RULES-TOOLING.md)
> **Tags:** `devops`, `podman`, `containers`, `volume-mounts`, `sfdc`

---

## Directive

ALL development MUST use **podman containers** with the **`dev` profile** and volume mounts. NEVER run services as bare `python` processes. The dev profile enables fast Software Development Feedback Cycle (SFDC) — code changes are reflected immediately without container rebuild.

---

## Container Runtime (CRITICAL)

**USE PODMAN, NOT DOCKER** — xubuntu migration 2026-01-09

| Wrong | Correct |
|-------|---------|
| `docker` | `podman` |
| `docker-compose` | `podman compose` |
| `docker ps` | `podman compose --profile dev ps` |
| `python -m governance.api` | `podman start platform_governance-dashboard-dev_1` |
| `python -m agent.governance_dashboard` | `podman restart platform_governance-dashboard-dev_1` |

---

## Dev Profile — Volume-Mounted SFDC

The `dev` profile mounts source directories into the container:

```yaml
# Volume mounts (from compose.yaml)
volumes:
  - ./agent:/app/agent:ro         # Dashboard UI code
  - ./governance:/app/governance:ro  # API + MCP tools
  - ./docs:/app/docs:ro           # Documentation
  - ./evidence:/app/evidence:rw   # Evidence output
```

### Key Benefit: No Image Rebuild

Code changes in `agent/`, `governance/`, or `docs/` are **immediately reflected**. Just restart the container.

### When to Rebuild (ONLY)

- `Dockerfile.dashboard` changes
- Python dependencies change (`requirements.txt`)
- System packages change

```bash
podman compose --profile dev up -d --build  # Only when Dockerfile changes
```

---

## Container Lifecycle Commands

| Action | Command | When |
|--------|---------|------|
| **Start stopped** | `podman start platform_governance-dashboard-dev_1` | Container exists, just stopped |
| **Restart running** | `podman restart platform_governance-dashboard-dev_1` | Code changed, need refresh |
| **Full recreate** | `podman compose --profile dev up -d` | Config/Dockerfile changed |
| **Check status** | `podman compose --profile dev ps` | Verify running state |
| **View logs** | `podman logs platform_governance-dashboard-dev_1 --tail 50` | Debug issues |

> **WARNING**: Only `--profile dev` exists. Using non-existent profiles (e.g., `cpu`) causes **silent failure**.

---

## Version Check Protocol

| Step | Command |
|------|---------|
| Container version | `podman logs <container> \| grep version` |
| Python deps | `podman exec <container> pip list` |
| Dependency check | `podman exec <container> pip check` |
| System version | `podman exec <container> cat /etc/os-release` |

---

## Anti-Patterns (PROHIBITED)

| Don't | Do Instead |
|-------|------------|
| `python -m governance.api --port 8082` | `podman start platform_governance-dashboard-dev_1` |
| `python -m agent.governance_dashboard` | `podman restart platform_governance-dashboard-dev_1` |
| `nohup .venv/bin/python -m ...` | `podman start` (containers run as daemons) |
| `fuser -k 8082/tcp` to free port | `podman stop` then `podman start` |
| `pip install <pkg>` without version | Check container Python version first |
| Install to global Python | Use venv or container |
| Use `--profile cpu` | Use `--profile dev` (only profile that exists) |

---

## Tool Bindings (GOV-BIND-01-v1)

| Verification | Tool | Example |
|-------------|------|---------|
| Container status | Bash | `podman compose --profile dev ps` |
| Service health | `mcp__rest-api__test_request` | `GET http://localhost:8082/api/health` |
| UI available | `mcp__playwright__browser_navigate` | `http://localhost:8081` |

---

## Validation

- [ ] All services run via podman containers, not bare python
- [ ] `dev` profile used with volume mounts
- [ ] No docker commands used
- [ ] Container restarted (not rebuilt) after code changes
- [ ] Health endpoint verified after restart

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
*Per GOV-BIND-01-v1: Tool bindings specified*
