# SAFETY-HEALTH-01-v1: MCP Healthcheck Protocol

**Category:** `stability` | **Priority:** CRITICAL | **Status:** ACTIVE | **Type:** TECHNICAL

> **Legacy ID:** RULE-021
> **Location:** [RULES-STABILITY.md](../operational/RULES-STABILITY.md)
> **Tags:** `health`, `mcp`, `recovery`, `monitoring`

---

## Directive

Every MCP-dependent operation MUST verify health before execution. Failures must be logged and recovery attempted **automatically**.

**CRITICAL:** At session start, healthcheck hook auto-verifies container services and triggers recovery if DOWN.

---

## Healthcheck Hierarchy

```mermaid
flowchart TD
    L1["L1: Pre-Operation<br/>Verify MCP responding"] --> L2
    L2["L2: Session Start<br/>healthcheck.py hook"] --> L2D{Healthy?}
    L2D -->|No| RECOVER[ContainerRecovery.start_containers]
    L2D -->|Yes| L3
    RECOVER --> AUDIT[Audit Trail Log]
    L3["L3: MCP Tools<br/>health_check"] --> L4
    L4["L4: Frankel Hash<br/>State tracking"]
```

---

## MCP Server Tiers

| Tier | Servers | Failure Impact |
|------|---------|----------------|
| **CRITICAL** | filesystem, git, powershell | Session blocked |
| **HIGH** | claude-mem, desktop-commander | Degraded |
| **MEDIUM** | playwright, octocode, llm-sandbox | Feature unavailable |
| **CONDITIONAL** | godot-mcp | Skip if not needed |

---

## Allowed Failures

- `godot-mcp` - Requires Godot Editor
- `llm-sandbox` - Requires Docker/Podman
- `octocode` - Requires GitHub PAT
- `context7` - May be disabled

---

## Auto-Recovery Actions

| State | Action |
|-------|--------|
| `PODMAN: DOWN` | Start podman socket |
| `typedb: DOWN` | `ContainerRecovery.start_containers(["typedb"])` |
| `chromadb: DOWN` | `ContainerRecovery.start_containers(["chromadb"])` |

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Skip health check at session start | Always call `health_check` first |
| Assume services are running | Verify with healthcheck hook |
| Ignore DOWN status | Follow recovery actions table |
| Proceed without critical MCPs | Wait for recovery or notify user |

## Test Coverage

**4 robot test file(s)** validate this rule:

| File | Scope |
|------|-------|
| `tests/robot/e2e/platform_health.robot` | e2e |
| `tests/robot/unit/health.robot` | unit |
| `tests/robot/unit/health_modes.robot` | unit |
| `tests/robot/unit/mcp_status_display.robot` | unit |

```bash
# Run all tests validating this rule
robot --include SAFETY-HEALTH-01-v1 tests/robot/
```

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
