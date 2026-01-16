---
description: Check MCP dependency chain health and detect AMNESIA indicators
allowed-tools: mcp__governance__governance_health, mcp__claude-mem__chroma_query_documents, Read
---

# Health Check Protocol (RULE-021)

Run comprehensive health check including:

1. **MCP Dependency Chain**: Call `governance_health` to verify TypeDB + ChromaDB
2. **Memory Continuity**: Query claude-mem for recent sarvaja sessions
3. **Frankel Hash**: Read `.claude/hooks/.healthcheck_state.json` for service hash

## AMNESIA Detection Indicators

Check for memory loss by querying: `mcp__claude-mem__chroma_query_documents` with:
- Query: `["sarvaja session {today's date}"]`
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
