---
description: Check MCP dependency chain health and detect AMNESIA indicators
allowed-tools: mcp__governance__governance_health, mcp__claude-mem__chroma_query_documents, Read
---

# Health Check Protocol (RULE-021)

Run comprehensive health check including:

1. **MCP Dependency Chain**: Call `governance_health` to verify TypeDB + ChromaDB
2. **Memory Continuity**: Query claude-mem for recent sim-ai sessions
3. **Frankel Hash**: Read `.claude/hooks/.healthcheck_state.json` for service hash

## AMNESIA Detection Indicators

Check for memory loss by querying: `mcp__claude-mem__chroma_query_documents` with:
- Query: `["sim-ai session {today's date}"]`
- If 0 results for today → AMNESIA LIKELY
- If results exist but no context about current task → PARTIAL AMNESIA

## Output Format

```
=== HEALTH CHECK ===
Governance: [healthy/unhealthy]
TypeDB: [OK/DOWN] (26 rules)
ChromaDB: [OK/DOWN]
Frankel Hash: [XXXXXXXX]
Memory Status: [CONTINUOUS/AMNESIA DETECTED]
Last Session: [date/time]
```

## Recovery Actions (if unhealthy)

1. If services down: `.\deploy.ps1 -Action up -Profile cpu`
2. If AMNESIA: Run `/remember sim-ai` to restore context
3. If hash changed: Services restarted, context may need refresh
