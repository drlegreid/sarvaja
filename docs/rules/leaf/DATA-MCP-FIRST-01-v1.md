# DATA-MCP-FIRST-01-v1: MCP-First Data Retrieval

| Field | Value |
|-------|-------|
| **Category** | workflow |
| **Priority** | HIGH |
| **Applicability** | MANDATORY |
| **Status** | ACTIVE |
| **Created** | 2026-03-22 |

## Directive

When MCP tools exist for a data domain, they are the EXCLUSIVE retrieval interface. Raw file reading (JSONL, JSON, disk stores) is FORBIDDEN when the corresponding MCP server is healthy.

## Requirements

### 1. Session Data
- Use `gov-sessions` MCP tools: `session_search`, `session_list`, `memory_recall`, `governance_get_session`
- NEVER read raw JSONL files from `~/.claude/projects/` directly
- NEVER spawn agents that `cat`, `grep`, or parse JSONL session logs
- Fallback to raw JSONL ONLY when `gov-sessions` health check fails

### 2. Task Data
- Use `gov-tasks` MCP tools: `task_get`, `tasks_list`, `task_search`
- NEVER read `TODO.md` or `_tasks_store` JSON as primary source
- Per GOV-MCP-FIRST-01-v1: TypeDB via MCP = single source of truth

### 3. Rule Data
- Use `gov-core` MCP tools: `rules_query`, `rule_get`
- NEVER parse `docs/rules/` files as primary source when MCP is healthy

### 4. Agent Subprocesses
- Subagents (Agent tool) MUST follow the same MCP-first principle
- A subagent that reads raw JSONL instead of calling session MCP is non-compliant
- Prompt subagents with explicit MCP tool names, not "search the session files"

## Anti-Patterns
- Spawning an Explore agent to `grep` through 83K-line JSONL files
- Reading `_sessions_store` disk JSON when `session_list` MCP works
- Parsing `.tql` schema files when `rules_query` can return the same data
- Using `cat` or `head` on session logs instead of `session_search(query=...)`

## Rationale

Raw JSONL session files can be 80,000+ lines. Reading them wastes context window, is slow, and bypasses the optimized indexes that MCP servers maintain. The MCP tools exist precisely to provide structured, filtered, efficient access to this data. Using raw files when MCP is available is like querying a database by reading WAL logs.

## Related Rules
- GOV-MCP-FIRST-01-v1 (task MCP as primary interface)
- RECOVER-AMNES-01-v1 (context recovery via MCP, not raw files)
- CONTEXT-SAVE-01-v1 (context efficiency)
