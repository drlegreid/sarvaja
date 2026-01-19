# GAP-MCP-CONTAINER-TIMEOUT-001: MCP Container Startup Timeout

**Status**: RESOLVED
**Priority**: CRITICAL
**Discovered**: 2026-01-19
**Resolved**: 2026-01-19

## Summary

Claude Code MCP servers (gov-agents, gov-sessions, gov-tasks) failed to connect due to container startup timeout. The container mode added ~0.9s overhead per server, causing Claude Code to timeout before receiving JSON-RPC response.

## Symptoms

- `/mcp` showed gov-core connected but gov-agents/sessions/tasks failed
- Podman events showed many containers starting and dying rapidly
- Manual testing worked fine: `bash scripts/mcp-runner.sh governance.mcp_server_agents`

## Root Cause Analysis

### Evidence from `podman events`

```
01:02:11 - container start elastic_chatterjee
01:02:14 - container start goofy_diffie
01:02:15 - container start happy_wiles
...
01:02:26 - container died goofy_diffie (12 seconds after start)
01:02:26 - container died happy_wiles
01:02:26 - container died stoic_torvalds
... (many more die events)
```

### Timeline
1. Claude Code starts all MCP servers simultaneously
2. Each gov-* server spawns a NEW podman container
3. Container cold-start takes ~0.9-1.0 seconds
4. Claude Code has ~3-5 second timeout
5. With 4+ containers starting simultaneously, resource contention causes delays
6. Some containers don't respond in time → marked "failed"
7. gov-core often succeeds (first in queue or random luck)

### Startup Time Comparison

| Mode | Time | Notes |
|------|------|-------|
| Container | ~0.9s | Podman overhead, image layers, cgroups |
| Venv | ~0.6s | Direct Python, no container overhead |

## Solution

Changed default MCP_MODE from `container` to `venv` in [scripts/mcp-runner.sh](../../../scripts/mcp-runner.sh):

```bash
# Before
MCP_MODE="${MCP_MODE:-container}"

# After
MCP_MODE="${MCP_MODE:-venv}"  # Container startup too slow for Claude Code timeout
```

## Verification

After switching to venv mode:
- All 6 MCP servers connect successfully
- No orphan containers created
- Faster startup (~0.6s vs ~0.9s)

## Prevention

1. **MCP-HEALTH-01-v1**: Agent must autonomously diagnose MCP failures
2. **Default to venv mode**: Faster, no container overhead
3. **Container mode optional**: Use `MCP_MODE=container` for sandboxed testing

## Related

- [MCP-HEALTH-01-v1](../../rules/leaf/MCP-HEALTH-01-v1.md): Autonomous MCP Health Management
- [GAP-MCP-002](GAP-MCP-002.md): MCP dependency health checks

## Files Modified

| File | Change |
|------|--------|
| scripts/mcp-runner.sh | Changed default MCP_MODE from container to venv |
| governance/mcp_tools/trust.py | Removed duplicate `governance_list_agents` |
| governance/mcp_server_core.py | Removed duplicate `governance_health` |
