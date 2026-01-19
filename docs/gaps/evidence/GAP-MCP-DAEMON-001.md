# GAP-MCP-DAEMON-001: MCP Daemon Architecture

**Status:** ON_HOLD
**Priority:** MEDIUM
**Category:** architecture
**Created:** 2026-01-19
**Blocked By:** VSCode SSE limitation (GitHub #9522)

## Summary

Design persistent MCP server architecture to eliminate zombie processes and connection conflicts between Claude Code IDE and CLI.

## Problem Statement

Current architecture spawns new MCP processes per session/client:
```
IDE Extension  ──spawns──▶  MCP Processes (set A)
CLI "claude"   ──spawns──▶  MCP Processes (set B) ← Conflict!
```

Results in:
- Zombie process accumulation
- Connection conflicts
- Race conditions (GitHub #12449, #3071)
- Stale UI state in IDE panel

## Proposed Architecture

```
┌─────────────┐
│  IDE        │──┐
└─────────────┘  │   ┌────────────────────────┐
                 ├──▶│  MCP Container         │
┌─────────────┐  │   │  (Podman, always on)   │
│  CLI        │──┘   │  HTTP/SSE transport    │
└─────────────┘      │  Port: 8090            │
                     └────────────────────────┘
```

Benefits:
- Single process pool shared by all clients
- No zombie accumulation
- Faster connections (already running)
- Proper service management via Podman

## Technical Findings

### Transport Support Matrix

| Transport | CLI | VSCode Extension | Desktop |
|-----------|-----|------------------|---------|
| stdio | ✅ | ✅ | ✅ |
| HTTP | ✅ | ❌ (#9522) | ✅ |
| SSE | ✅ | ❌ (#9522) | ✅ |

**Blocker:** VSCode extension does NOT support HTTP/SSE transport.

### Official Documentation

Per [code.claude.com/docs/en/mcp](https://code.claude.com/docs/en/mcp):

```bash
# HTTP transport (NOT supported in VSCode)
claude mcp add --transport http <name> <url>

# SSE transport (deprecated, NOT supported in VSCode)
claude mcp add --transport sse <name> <url>

# stdio transport (ONLY option for VSCode)
claude mcp add --transport stdio <name> -- <command>
```

### GitHub Issues

- **#9522**: VSCode SSE support request - OPEN, no timeline
- **#12449**: Race condition - Closed as duplicate
- **#3071**: Connection closed error - Closed as NOT_PLANNED

### Workaround Options Evaluated

| Approach | Feasibility | Notes |
|----------|-------------|-------|
| HTTP container | ❌ Blocked | VSCode doesn't support HTTP |
| stdio-to-HTTP bridge | Possible | Complex, needs wrapper |
| Unix domain socket | Possible | Linux only, complex |
| Process lock/singleton | Possible | Fragile coordination |
| mcp-remote wrapper | Partial | "Tools not discovered" bug |

## Recommended Path Forward

### Short-term (Current)

Use workarounds:
1. **mcp-runner.sh** optimization (done)
2. **Zombie cleanup** via SessionStart hook (done)
3. **/mcp → Reconnect** for failed servers (manual)
4. **scripts/mcp-cleanup.sh** before IDE start

### Medium-term (When VSCode supports HTTP)

1. Create MCP HTTP server container
2. Configure .mcp.json with HTTP transport
3. Integrate with existing Podman stack

### Long-term (Agentic Platform)

1. Full daemon architecture with proper IPC
2. MCP servers as Kubernetes/Podman services
3. Unified agent workspace management

## Implementation Sketch (ON HOLD)

### Container Dockerfile

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY governance/ governance/
COPY claude_mem/ claude_mem/

# HTTP server mode
EXPOSE 8090
CMD ["python", "-m", "uvicorn", "mcp_http_server:app", "--host", "0.0.0.0", "--port", "8090"]
```

### .mcp.json (when HTTP supported)

```json
{
  "mcpServers": {
    "gov-core": {
      "type": "http",
      "url": "http://localhost:8090/gov-core"
    }
  }
}
```

### stdio-to-HTTP Bridge (alternative)

```bash
#!/bin/bash
# mcp-bridge.sh - Converts stdio to HTTP
exec socat - TCP:localhost:8090,forever
```

## Related

- [GAP-MCP-VALIDATE-001](GAP-MCP-VALIDATE-001.md): Current mitigations
- [MCP-HEALTH-01-v1](../../rules/leaf/MCP-HEALTH-01-v1.md): Health checks
- [DOC-SOURCE-01-v1](../../rules/leaf/DOC-SOURCE-01-v1.md): Official docs first

## Decision

**ON HOLD** - Wait for either:
1. Anthropic to fix VSCode HTTP/SSE support (#9522)
2. Team decision to implement stdio-to-HTTP bridge complexity

Current workarounds are sufficient for development workflow.

---

*Per DOC-SOURCE-01-v1: Research based on official Claude Code documentation*
