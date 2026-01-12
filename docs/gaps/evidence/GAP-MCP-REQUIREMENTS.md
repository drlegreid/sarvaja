# MCP Health Requirements

> **Gaps:** GAP-MCP-002, GAP-MCP-004
> **Rule:** RULE-021 (MCP Healthcheck Protocol)
> **Date:** 2024-12-31

---

## GAP-MCP-002: Dependency Health Check Protocol

**Status:** PARTIAL - Tool implemented but not auto-called

**Problem:** MCP governance service should check if dependencies (TypeDB, ChromaDB) are healthy before operations. If dependencies fail, Claude Code should be notified to stop and attempt to resolve the issue automatically.

**Related:**
- RULE-021: MCP Healthcheck Protocol (Level 3: Recovery Protocol)
- R&D-BACKLOG: "Docker Wrapper" pattern for MCP dependency auto-start
- GAP-INFRA-004: Infrastructure health dashboard

**Required Capabilities:**

### 1. Pre-Operation Health Check (RULE-021 Level 1)
- Before MCP tool calls, verify TypeDB (port 1729) and ChromaDB (port 8001) are responding
- If unhealthy, return structured error with dependency status

### 2. Session Start Health Check (RULE-021 Level 2)
- At MCP server initialization, run full dependency audit
- Log health status to session evidence

### 3. Recovery Protocol (RULE-021 Level 3)
- On dependency failure:
  - Attempt 1: Wait 5s, retry connection
  - Attempt 2: Restart dependent service via Docker CLI
  - Attempt 3: Return actionable error to Claude Code
- Claude Code should interpret error and:
  - Run `docker compose up -d <service>` for failed dependencies
  - Wait for health check to pass
  - Retry original operation

### Implementation Path:
```python
# governance/mcp_tools/healthcheck.py
@tool
def governance_health_check() -> dict:
    """Check all governance dependencies."""
    status = {
        "typedb": check_typedb_health(),
        "chromadb": check_chromadb_health(),
        "overall": "healthy" | "degraded" | "unhealthy"
    }
    if status["overall"] == "unhealthy":
        return {
            "error": "DEPENDENCY_FAILURE",
            "action_required": "START_SERVICES",
            "services": [s for s, v in status.items() if v == "unhealthy"]
        }
    return status
```

### Claude Code Integration (via CLAUDE.md or MCP response):
- When MCP returns `action_required: START_SERVICES`, Claude Code should:
  - Stop current operation
  - Run `docker compose up -d <services>`
  - Re-run health check
  - Resume original operation

---

## GAP-MCP-004: Rule Fallback to Markdown

**Status:** RESOLVED 2026-01-02

**Issue:** When TypeDB is unavailable, agents cannot access rule content

**Current:** hybrid_router.py has TypeDB→ChromaDB fallback for *queries*, not rule content

**Current:** rule_linker.py has static mapping fallback for scanning, not reading

**Needed:** Implement `get_rule_from_markdown(rule_id)` function that reads from:
- `docs/rules/RULES-GOVERNANCE.md` (RULE-001,003,006,011,013)
- `docs/rules/RULES-TECHNICAL.md` (RULE-002,007,008,009,010)
- `docs/rules/RULES-OPERATIONAL.md` (RULE-004,005,012,014+)

**Resolution:** governance/mcp_tools/rule_fallback.py implemented with 14 tests passing

---

*Per RULE-021: MCP Healthcheck Protocol*
