# MCP-HEALTH-01-v1: MCP Server Health Validation

**Status:** ACTIVE
**Priority:** HIGH
**Category:** infrastructure
**Created:** 2026-01-19
**Semantic ID:** MCP-HEALTH-01-v1

## Directive

**ALL MCP servers MUST be validated via protocol handshake before session work begins.**

## Rationale

Per GitHub Issue #12449: Claude Code has a known race condition where MCP connections can fail on startup.

## Implementation

### Pre-Session Validation
```bash
./scripts/validate-mcp.sh
```

### MCP_TIMEOUT Configuration
```bash
export MCP_TIMEOUT="${MCP_TIMEOUT:-15000}"  # 15 seconds (in scripts/mcp-runner.sh)
```

## Recovery

1. `/mcp` → Select failed server → "Reconnect"
2. If persists, restart Claude Code IDE
3. Debug: `./scripts/validate-mcp.sh`

## Related

- [GAP-MCP-VALIDATE-001](../../gaps/evidence/GAP-MCP-VALIDATE-001.md)
- [SAFETY-HEALTH-01-v1](SAFETY-HEALTH-01-v1.md)
