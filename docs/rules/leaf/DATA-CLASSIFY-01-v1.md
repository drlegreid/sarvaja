# DATA-CLASSIFY-01-v1: Tool Call Classification

| Field | Value |
|-------|-------|
| **Rule ID** | DATA-CLASSIFY-01-v1 |
| **Category** | governance |
| **Priority** | HIGH |
| **Status** | ACTIVE |

## Statement

Tool calls recorded in session data MUST include a `tool_category` field classifying the tool as one of: `mcp_governance`, `mcp_other`, `cc_builtin`, `chat_command`, or `unknown`. Slash commands (`/status`, `/tasks`) MUST be classified as `chat_command` and distinguishable from MCP tool calls.

## Rationale

Without classification, session analytics cannot distinguish between local Claude Code skills (Read, Write, Bash), MCP governance tools, and chat commands. This causes confusion in session data and inflated tool call counts.

## Categories

| Category | Pattern | Examples |
|----------|---------|----------|
| `mcp_governance` | `mcp__gov-*__` prefix | mcp__gov-core__rules_query |
| `mcp_other` | `mcp__` prefix (non-gov) | mcp__claude-mem__chroma_query |
| `cc_builtin` | _CC_BUILTIN_TOOLS set | Read, Write, Edit, Bash, Glob |
| `chat_command` | starts with `/` | /status, /tasks, /help |
| `unknown` | none of the above | custom tools |

## Implementation

- `classify_tool()` in `governance/routes/chat/session_bridge.py`
- `is_chat_command()` for slash command detection
- `_CC_BUILTIN_TOOLS` frozenset (16 tools)
- `_GOV_MCP_PREFIXES` tuple for governance MCP servers
- All `_sessions_store` tool_calls include `tool_category` field

## Verification

- Every tool call in _sessions_store has tool_category
- /status classified as chat_command, not tool call
- mcp__gov-core__rules_query classified as mcp_governance
- Read classified as cc_builtin
- Unit tests in `tests/unit/test_skills_visibility.py`
