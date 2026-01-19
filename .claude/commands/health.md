---
description: Check MCP dependency chain health and detect AMNESIA indicators
allowed-tools: mcp__gov-core__health_check, mcp__claude-mem__chroma_query_documents, Read, Bash
---

# Health Check Protocol (RULE-021, MCP-HEALTH-01-v1)

Run comprehensive health check including:

1. **MCP Server Status**: Validate by category (CORE → TECHNICAL → EXPERIMENTAL)
2. **MCP Dependency Chain**: Call `health_check` to verify TypeDB + ChromaDB
3. **Memory Continuity**: Query claude-mem for recent sarvaja sessions
4. **Frankel Hash**: Read `.claude/hooks/.healthcheck_state.json` for service hash

## MCP Service Categories (MCP-HEALTH-01-v1)

| Category | MCPs | On Failure |
|----------|------|------------|
| **CORE** | claude-mem, gov-core, gov-agents, gov-sessions, gov-tasks, rest-api | **STOP ALL WORK** - fix immediately |
| **TECHNICAL** | playwright | **STOP CURRENT** - fix before UI testing |
| **EXPERIMENTAL** | ubuntu-desktop-control, podman | Disabled - ignore |

## MCP Health Validation

```bash
# Test CORE MCPs (must all pass)
for srv in governance.mcp_server_core governance.mcp_server_agents governance.mcp_server_sessions governance.mcp_server_tasks; do
  timeout 3 bash scripts/mcp-runner.sh $srv 2>&1 | head -1
done

# Check orphan containers
podman ps -a --format "{{.Names}} {{.Status}}" | grep -v platform_
```

If MCP server shows "failed":
1. Check for orphan containers → `podman rm -f <name>`
2. Check for duplicate tools → grep for "Tool already exists" in test output
3. Rebuild if needed → `podman build -t sarvaja-mcp:latest -f Dockerfile.mcp .`

## AMNESIA Detection Indicators

Check for memory loss by querying: `mcp__claude-mem__chroma_query_documents` with:
- Query: `["sarvaja session {today's date}"]`
- If 0 results for today → AMNESIA LIKELY
- If results exist but no context about current task → PARTIAL AMNESIA

## Output Format

```
=== HEALTH CHECK ===
MCP Servers: [X/Y connected] (list any failed)
Governance: [healthy/unhealthy]
TypeDB: [OK/DOWN] (64 rules)
ChromaDB: [OK/DOWN]
Frankel Hash: [XXXXXXXX]
Memory Status: [CONTINUOUS/AMNESIA DETECTED]
Last Session: [date/time]
```

## Recovery Actions (if unhealthy)

1. If services down: `podman compose --profile cpu --profile dashboard-dev up -d`
2. If AMNESIA: Run `/remember sarvaja` to restore context
3. If hash changed: Services restarted, context may need refresh

## E2E Thin-Slice Health Test

For comprehensive verification, run the E2E platform health test:
```bash
python -m tests.e2e.test_platform_health_e2e
```

Or via pytest:
```bash
pytest tests/e2e/test_platform_health_e2e.py -v
```

This test verifies:
- TypeDB connectivity (port + optional driver)
- ChromaDB connectivity (heartbeat)
- Kanren constraint engine (trust, RAG filter, task assignment)
- Kanren benchmarks (performance <1ms)
- Dashboard HTTP response
- API endpoints (optional)
