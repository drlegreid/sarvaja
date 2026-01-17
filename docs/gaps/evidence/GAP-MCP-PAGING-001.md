# GAP-MCP-PAGING-001: MCP Tools Need Paging for Large Outputs

**Priority:** MEDIUM | **Category:** tooling | **Status:** OPEN
**Discovered:** 2026-01-16 | **Session:** SESSION-2026-01-16-PLATFORM-AUDIT

---

## Summary

MCP tools like `mcp__podman__container_logs` can return outputs exceeding context limits (791K+ characters), causing tool failures or truncation.

## Evidence

### Error Message
```
Error: result (791,603 characters) exceeds maximum allowed tokens.
Output has been saved to /home/oderid/.claude/projects/.../tool-results/mcp-podman-container_logs-*.txt
```

### Affected Tools
- `mcp__podman__container_logs` - Container logs can be very large
- Any MCP tool returning unbounded text output

## Impact

- **Tool failures** - Large outputs exceed limits
- **Context pollution** - Even truncated outputs waste tokens
- **Workarounds required** - Must use Bash with head/tail instead

## Workarounds

### Option 1: Use Bash with Limits
```bash
# Instead of MCP tool
podman logs platform_typedb_1 2>&1 | head -50

# Grep for specific content
podman logs platform_typedb_1 2>&1 | grep "version:"
```

### Option 2: Use tail Parameter (if available)
Some MCP tools may support tail/limit parameters - check tool schema.

### Option 3: Read from Saved File
When output is saved to file, use Read tool with offset/limit:
```
Read(file_path="/path/to/saved/output.txt", limit=100)
```

## Proposed Fix

MCP servers should implement:
1. **Default limits** - Cap output at reasonable size (e.g., 10KB)
2. **Pagination params** - `offset`, `limit`, `tail` parameters
3. **Streaming** - For very large outputs, stream chunks

## Affected MCP Servers

| Server | Tool | Needs Paging |
|--------|------|--------------|
| podman | container_logs | YES |
| rest-api | test_request | Has 10KB limit |

---

*Per GAP-DOC-01-v1: Evidence file for gap documentation*
