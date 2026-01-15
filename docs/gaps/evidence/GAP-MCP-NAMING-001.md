# GAP-MCP-NAMING-001: MCP Tool Names Too Long

**Status:** RESOLVED
**Priority:** MEDIUM
**Category:** architecture
**Discovered:** 2026-01-14 via user feedback
**Resolved:** 2026-01-14

## Problem Statement

MCP tool names were verbose due to server naming:
```
mcp__governance-sessions__session_capture_intent  (47 chars)
mcp__governance-tasks__governance_create_task     (45 chars)
mcp__governance-core__governance_health           (39 chars)
```

## Resolution

Shortened server names in `.mcp.json`:
- `governance-core` → `gov-core`
- `governance-agents` → `gov-agents`
- `governance-sessions` → `gov-sessions`
- `governance-tasks` → `gov-tasks`

New tool names (-6 chars each):
```
mcp__gov-sessions__session_capture_intent  (41 chars)
mcp__gov-tasks__governance_create_task     (39 chars)
mcp__gov-core__governance_health           (33 chars)
```

## Validation Evidence (2026-01-14)

All 4 servers validated after IDE restart:
```
mcp__gov-core__governance_health()     ✅ Returns healthy status
mcp__gov-sessions__session_list()      ✅ Returns 0 active sessions
mcp__gov-tasks__governance_get_backlog() ✅ Returns 226 gaps
mcp__gov-agents__governance_list_agents() ✅ Returns 8 agents
```

## Current Architecture

4 governance MCP servers:
| Server | Tools | Pattern |
|--------|-------|---------|
| governance-core | 20+ | `governance_*`, `mcp__governance-core__*` |
| governance-agents | 15+ | `governance_*`, `mcp__governance-agents__*` |
| governance-sessions | 25+ | `session_*`, `dsm_*`, `mcp__governance-sessions__*` |
| governance-tasks | 30+ | `governance_*`, `workspace_*`, `mcp__governance-tasks__*` |

## Proposed Solutions

### Option A: Merge Servers (Recommended)
Merge 4 governance servers → 1 `governance` server

**Pros:**
- Single namespace: `mcp__governance__session_start`
- Simpler MCP config
- Still 90+ tools but unique function names

**Cons:**
- Large refactor
- Breaking change for any callers

### Option B: Shorter Server Names
Rename: `governance-sessions` → `gov-sess`

**Pros:**
- Minimal code change
- Non-breaking (just config)

**Cons:**
- Still has `__` separators
- Partial fix

### Option C: Custom Tool Names
Use `@mcp.tool(name="gov_session_start")` decorator param

**Pros:**
- Full control over names
- No server merge needed

**Cons:**
- Must update every tool definition
- Disconnect between function name and tool name

## Implementation Plan (Option A)

1. Create `governance/mcp_server_unified.py`
2. Import all tool registration from 4 modules
3. Update `.mcp.json` to use single server
4. Deprecate old servers
5. Update documentation

## Related

- ARCH-MCP-02-v1: MCP 4-Server Split (original split decision)
- Per DECISION-003: TypeDB-First Architecture
