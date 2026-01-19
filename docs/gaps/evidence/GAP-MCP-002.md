# GAP-MCP-002: gov-tasks MCP Integration

**Status**: RESOLVED
**Priority**: MEDIUM
**Category**: Integration
**Created**: 2026-01-17
**Resolved**: 2026-01-17

## Problem Statement

The gov-tasks MCP server is configured in `.mcp.json` and starts successfully, but its tools are not exposed to Claude Code sessions. This is the same issue as GAP-MCP-001 (gov-sessions).

## Analysis

### MCP Server Status
- **Config**: `.mcp.json` includes gov-tasks with correct paths
- **Server**: Starts successfully (`governance.mcp_server_tasks`)
- **Output**: "Tools: Tasks, Workspace, Gaps" - confirms tool registration

### Tools Registered (Not Available to Claude Code)

```
# Task CRUD
governance_create_task, governance_get_task, governance_update_task
governance_delete_task, governance_list_all_tasks

# Task Linking
governance_task_link_session, governance_task_link_rule, governance_task_link_evidence
governance_task_get_evidence

# Workspace Operations
workspace_scan_tasks, workspace_capture_tasks, workspace_list_sources
workspace_scan_rule_documents, workspace_link_rules_to_documents

# Backlog & Gaps
governance_get_backlog, governance_gap_summary, governance_get_critical_gaps
governance_unified_backlog

# Handoffs
governance_create_handoff, governance_get_pending_handoffs
governance_complete_handoff, governance_get_handoff
governance_route_task_to_agent

# Audit
governance_query_audit, governance_audit_summary, governance_entity_audit_trail
governance_trace_correlation
```

### Available vs Missing MCP Tools

| MCP Server | Status | Tools Available in Claude Code |
|------------|--------|-------------------------------|
| gov-core | ✅ Working | governance_query_rules, governance_health, etc. |
| gov-agents | ✅ Working | governance_create_agent, governance_vote, etc. |
| gov-sessions | ❌ Not exposed | (see GAP-MCP-001) |
| gov-tasks | ❌ Not exposed | All workspace/backlog tools missing |

## Root Cause (FOUND 2026-01-17)

**Same as GAP-MCP-001: Print statements corrupting MCP JSON-RPC protocol.**

The server's startup print statements were going to stdout instead of stderr, corrupting the JSON-RPC handshake that Claude Code uses to connect.

**Fix Applied:** Changed all `print()` calls in `mcp_server_tasks.py` to use `file=sys.stderr`.

```python
# BEFORE (broken):
print("Starting Governance Tasks MCP Server...")

# AFTER (fixed):
print("Starting Governance Tasks MCP Server...", file=sys.stderr)
```

## Root Cause Hypothesis (OBSOLETE)

## Workaround

Use REST API via rest-api MCP for task operations:
- GET /api/tasks - List tasks
- POST /api/tasks - Create task
- PUT /api/tasks/{id} - Update task
- GET /api/gaps - Get gap summary

## Impact

Without gov-tasks tools:
- No `governance_get_backlog()` for session start protocol
- No `workspace_scan_tasks()` for task discovery
- No `governance_unified_backlog()` for prioritized work list
- Manual workaround via REST API required

## Related

- GAP-MCP-001: Same issue with gov-sessions server
- `.mcp.json`: MCP configuration file
- `governance/mcp_server_tasks.py`: Server implementation

---
*Per GAP-DOC-01-v1: Evidence file for gap documentation*
