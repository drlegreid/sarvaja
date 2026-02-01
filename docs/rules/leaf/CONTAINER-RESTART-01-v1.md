# CONTAINER-RESTART-01-v1: API Server Restart Protocol

**Category:** `testing` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Legacy ID:** RULE-027
> **Location:** [RULES-STANDARDS.md](../operational/RULES-STANDARDS.md)
> **Tags:** `api`, `testing`, `restart`, `podman`, `sfdc`

---

## Directive

ALWAYS restart API servers via **podman** after code changes BEFORE running tests. The dev profile volume mounts reflect code changes immediately — just restart the container, never rebuild.

---

## Protocol

| Step | Command | Purpose |
|------|---------|---------|
| 1. RESTART | `podman restart platform_governance-dashboard-dev_1` | Pick up code changes |
| 2. WAIT | `sleep 10` | Container startup time |
| 3. VERIFY | `curl -s http://localhost:8082/api/health` | Confirm responsive |
| 4. UNIT | `.venv/bin/python3 -m pytest tests/unit/ -v` | Run unit tests |
| 5. E2E | `.venv/bin/python3 -m pytest tests/e2e/ -v` | Run E2E API tests |
| 6. ROBOT | `robot tests/robot/` | Run Robot Framework tests (if UI changes) |
| 7. PLAYWRIGHT | `mcp__playwright__browser_navigate` + snapshot | Visual verification (if UI changes) |

**CRITICAL:** Steps 1-5 are MANDATORY for ALL code changes. Steps 6-7 are MANDATORY for UI/view changes. Skipping restart (step 1) before testing is a QUALITY VIOLATION.

### If Container is Stopped (Exited)

```bash
podman start platform_governance-dashboard-dev_1
sleep 10
curl -s http://localhost:8082/api/health
```

### If Container Doesn't Exist

```bash
podman compose --profile dev up -d
sleep 15
curl -s http://localhost:8082/api/health
```

---

## Anti-Patterns (PROHIBITED)

| Don't | Do Instead |
|-------|-----------|
| Run tests immediately after changes | Restart container first |
| Assume hot-reload caught changes | Explicitly restart container |
| Debug "404" without checking server | `podman compose --profile dev ps` first |
| `python -m governance.api --port 8082` | `podman restart platform_governance-dashboard-dev_1` |
| `kill` / `fuser -k` server processes | `podman stop` / `podman restart` |
| Run bare python for API server | Container serves both 8081 + 8082 |
| Skip E2E tests after UI changes | Run Robot + Playwright verification |
| Claim "done" without restart + test | Follow FULL protocol (all 7 steps) |

---

## Tool Bindings (GOV-BIND-01-v1)

| Verification | Tool | Example |
|-------------|------|---------|
| Health check | `mcp__rest-api__test_request` | `GET http://localhost:8082/api/health` |
| Container status | Bash | `podman compose --profile dev ps` |
| UI render | `mcp__playwright__browser_navigate` | `http://localhost:8081` |

---

## Validation

- [ ] Container restarted via `podman restart` (not bare python)
- [ ] Health endpoint verified: `{"status":"ok"}`
- [ ] Tests run on fresh container instance
- [ ] No bare python processes running on ports 8081/8082

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
*Per CONTAINER-DEV-01-v1: Podman dev profile mandatory*
*Per GOV-BIND-01-v1: Tool bindings specified*
