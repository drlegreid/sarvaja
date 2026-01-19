# GAP-MCP-VALIDATE-001: MCP Server Validation Gap

**Status:** MITIGATED (Partial)
**Priority:** HIGH
**Category:** testing
**Created:** 2026-01-19
**Updated:** 2026-01-19
**Phase:** Monitoring

## Summary

Claude Code intermittently shows "failed" status for MCP servers despite servers working correctly.

## Root Cause Analysis

### GitHub Issue Status
- **#12449**: Closed as duplicate of #3071
- **#3071**: Closed as **NOT_PLANNED** (unfixed by Anthropic)

### Technical Root Cause
Race condition in Claude Code's MCP initialization:
1. Connection succeeds but closes within 1ms
2. Server identity tracking failure (shows as "undefined")
3. State mismatch between establishment and usage

**Key Finding**: This is a Claude Code bug, not our code. Anthropic has not fixed it.

## Mitigation Effectiveness

| Mitigation | Status | Effectiveness |
|------------|--------|---------------|
| **mcp-runner.sh optimization** | ✓ Done | **Helps** - faster startup reduces race window |
| **Validation script** | ✓ Done | Detection only - confirms servers work |
| **SessionStart hook** | ✓ Done | Detection only - runs after connect attempt |
| **Manual /mcp reconnect** | Workaround | **Always works** |

### What We Changed (2026-01-19)

**1. Optimized mcp-runner.sh** ✓
```bash
# Before: source activation (~100ms overhead)
source "$HOME/.venv/sarvaja/bin/activate"
python -m "$1"

# After: direct path (minimal overhead)
PYTHON="$PROJECT_DIR/.venv/bin/python3"
exec "$PYTHON" -m "$1"
```
Result: ~600ms startup (well under timeout)

**2. Validation Script** ✓
```bash
./scripts/validate-mcp.sh
# Tests MCP protocol handshake - confirms servers work
```

**3. SessionStart Hook** ✓
```python
# .claude/hooks/checkers/mcp_connection.py
# Validates venv exists, suggests /mcp recovery on failure
```

## Manual Recovery (Reliable)

When servers show "failed":
1. **Use /mcp menu** → Select server → "Reconnect" ← **Always works**
2. If all fail: Restart IDE
3. Debug: `./scripts/validate-mcp.sh`

## Test Gap Analysis

| Area | Current | Needed |
|------|---------|--------|
| MCP Server Import | Yes | - |
| MCP Protocol Handshake | No | Add |
| MCP Tool Registration | Partial | Complete |
| MCP Startup Timing | No | Add |
| Pre-deploy Validation | No | Add |

## Related

- [MCP-HEALTH-01-v1](../../rules/leaf/MCP-HEALTH-01-v1.md): MCP health check rule
- [TEST-FIX-01-v1](../../rules/leaf/TEST-FIX-01-v1.md): Test before fix
- [SAFETY-HEALTH-01-v1](../../rules/leaf/SAFETY-HEALTH-01-v1.md): Health checks

## Notes

This incident revealed that we need validation of MCP server startup as part of pre-restart workflow. The code changes (item_type, document_path in TypeDB CRUD) were NOT the cause - the servers work correctly.
