# Technical Discoveries - 2026-01-14

Per user request: Document key tech discoveries with resolution and symptom details.

## TECH-DISC-001: Container Networking - Compose Service Names

**Symptom:** Infrastructure health view showing ALL services as DOWN despite being accessible via browser/curl.

**Root Cause:** Using `localhost` for port checks inside containers. When running in a container, `localhost` refers to the container itself, not other containers on the same network or the host machine.

**Resolution:** Use Docker/Podman compose service names for inter-container communication:
- `typedb:1729` (not `localhost:1729`)
- `chromadb:8000` (internal port, not external 8001)
- `litellm:4000`
- `ollama:11434`

**Detection Pattern:**
```python
# Detect if running in container
in_container = os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv")

# Service config: (container_host, container_port, host_port)
service_config = {
    "typedb": ("typedb", 1729, 1729),
    "chromadb": ("chromadb", 8000, 8001),  # internal 8000, mapped to 8001
}

for name, (container_host, container_port, host_port) in service_config.items():
    if in_container:
        ok = check_port(container_host, container_port)
    else:
        ok = check_port("localhost", host_port)
```

**Related:** GAP-UI-EXP-006 | File: `agent/governance_ui/controllers/data_loaders.py`

---

## TECH-DISC-002: Volume Mount - Hooks Directory Access

**Symptom:** `FileNotFoundError` for `/app/.claude/hooks/checkers/workflow_checker.py` in Workflow Compliance view.

**Root Cause:** The `.claude` directory was not mounted as a volume in `docker-compose.yml`. Only explicitly mounted directories are accessible inside containers.

**Resolution:** Add volume mount to docker-compose.yml:
```yaml
volumes:
  - ./.claude:/app/.claude:ro  # GAP-UI-EXP-011: Mount hooks/checkers for workflow compliance
```

**Pattern:** When code references local filesystem paths in container:
1. Verify path exists locally
2. Check if parent directory is in volume mounts
3. Add mount with appropriate permissions (`:ro` for read-only, `:rw` for read-write)

**Related:** GAP-UI-EXP-011 | File: `docker-compose.yml`

---

## TECH-DISC-003: MCP vs REST API Parity Testing

**Symptom:** Bottom-up unit tests pass, but data discrepancies exist between MCP tools and REST API endpoints. Example: MCP returning `0.8` trust score for all agents while REST API returns calculated values.

**Root Cause:** MCP tools and REST API routes may:
- Use different data sources (in-memory vs TypeDB)
- Apply different calculations or defaults
- Have different caching behavior

**Resolution:** Add cross-source parity tests comparing MCP and REST outputs:
```python
class TestMCPRestAPIParity:
    @data("Agent counts match between MCP and REST", api=True, entity="Agent")
    def test_agent_count_parity(self, client):
        # REST API
        rest_response = client.get("/api/agents")
        rest_count = len(rest_response.json().get("agents", []))

        # MCP
        from governance.mcp_tools.agents import list_agents
        mcp_count = len(list_agents().get("agents", []))

        assert rest_count == mcp_count, f"Mismatch: REST={rest_count}, MCP={mcp_count}"
```

**Key Insight:** Per RULE-025/GOV-PROP-03-v1 - Tests passing with empty data are invalid. Always verify API returns actual data before making assertions.

**Related:** GAP-UI-EXP-008 | File: `tests/heuristics/test_data_integrity.py`

---

## Summary

| ID | Discovery | Impact |
|----|-----------|--------|
| TECH-DISC-001 | Container networking via service names | CRITICAL - Health checks |
| TECH-DISC-002 | Volume mounts for local file access | HIGH - Feature availability |
| TECH-DISC-003 | MCP/REST parity testing | HIGH - Data consistency |

---
*Per SESSION-EVID-01-v1: Technical discoveries documented with full context*
