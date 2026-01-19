# GAP-MCP-001: gov-sessions MCP Integration

**Status**: RESOLVED
**Priority**: HIGH
**Category**: Integration
**Created**: 2026-01-16
**Resolved**: 2026-01-17

## Problem Statement

The gov-sessions MCP server is configured in `.mcp.json` and starts successfully, but its tools are not exposed to Claude Code sessions. This prevents automation of session lifecycle management.

## Analysis (2026-01-17)

### MCP Server Status
- **Config**: `.mcp.json` includes gov-sessions with correct paths
- **Server**: Starts successfully (`governance.mcp_server_sessions`)
- **Output**: "Tools: Sessions, DSM, Evidence" - confirms tool registration

### Available vs Missing Tools

| MCP Server | Status | Tools Available |
|------------|--------|-----------------|
| gov-core | ✅ Working | governance_query_rules, governance_health, etc. |
| gov-agents | ✅ Working | governance_create_agent, governance_vote, etc. |
| gov-sessions | ❌ Not exposed | session_start, dsm_advance, etc. |
| gov-tasks | ❌ Not exposed | (see GAP-MCP-002) |

### Expected Tools (Not Available)

```
session_start, session_decision, session_task, session_end, session_list
session_get_tasks, session_link_rule, session_link_decision, session_link_evidence
dsm_start, dsm_advance, dsm_checkpoint, dsm_finding, dsm_status, dsm_complete
governance_list_sessions, governance_get_session, governance_evidence_search
```

## Root Cause (FOUND 2026-01-17)

**Print statements corrupting MCP JSON-RPC protocol.**

The MCP protocol requires clean JSON-RPC messages on stdout. The server's startup print statements (`print("Starting Governance Sessions MCP Server...")`) were going to stdout, corrupting the JSON-RPC handshake.

```python
# BEFORE (broken):
print("Starting...")  # Goes to stdout, corrupts JSON-RPC

# AFTER (fixed):
print("Starting...", file=sys.stderr)  # Goes to stderr, stdout clean
```

## Root Cause Hypothesis (OBSOLETE)

## Verification Commands

```bash
# Test if server starts
timeout 5 bash scripts/mcp-runner.sh governance.mcp_server_sessions

# Check for import errors
python3 -c "from governance.mcp_server_sessions import mcp; print(mcp.tools)"
```

## Proposed Fix

### Option A: Debug Tool Registration
1. Add logging to `register_session_tools()`
2. Check for import errors in tool modules
3. Verify TypeDB connection before tool registration

### Option B: Session Restart
1. Restart Claude Code session with fresh MCP initialization
2. Monitor MCP logs for startup errors

### Option C: Fallback to REST API
1. Use existing REST API endpoints for session operations
2. Create wrapper functions for session lifecycle
3. Integrate via skills/hooks rather than direct MCP

## Subtasks

| ID | Status | Description |
|----|--------|-------------|
| MCP-001-A | BLOCKED | session_start integration - tools not exposed |
| MCP-001-B | BLOCKED | session_end integration - tools not exposed |
| MCP-001-C | BLOCKED | DSM tracking - tools not exposed |
| MCP-001-D | BLOCKED | Evidence search - tools not exposed |

## Workaround

Use REST API via rest-api MCP for session operations:
- GET /api/sessions - List sessions
- POST /api/sessions - Create session
- PUT /api/sessions/{id}/complete - End session

## Related

- GAP-MCP-002: Same issue with gov-tasks server
- `.mcp.json`: MCP configuration file
- `governance/mcp_server_sessions.py`: Server implementation

---
*Per GAP-DOC-01-v1: Evidence file for gap documentation*
