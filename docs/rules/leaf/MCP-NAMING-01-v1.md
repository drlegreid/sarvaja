# MCP-NAMING-01-v1: MCP Tool Naming Convention

| Field | Value |
|-------|-------|
| **Rule ID** | MCP-NAMING-01-v1 |
| **Legacy ID** | RULE-043 |
| **Category** | ARCHITECTURE |
| **Priority** | HIGH |
| **Status** | ACTIVE |
| **Created** | 2026-01-17 |
| **Implemented** | 2026-01-19 |

## Directive

All MCP tools MUST follow a consistent compact naming pattern:

```
<entity>_<action>[_<modifier>]
```

## Pattern Components

| Component | Description | Values |
|-----------|-------------|--------|
| `<entity>` | Entity type | task, agent, rule, session, proposal, handoff, audit, gap, doc |
| `<action>` | Operation type | create, get, list, update, delete, link, query, search, verify |
| `<modifier>` | Optional qualifier | evidence, session, commit, archived, pending, etc. |

## Final Tool Names (26 Total)

### Agent Tools (6)
- `agent_create`, `agent_get`, `agents_list`, `agent_trust_update`, `agents_dashboard`, `agent_activity`

### Task Tools (8)
- `task_create`, `task_get`, `task_update`, `task_delete`, `tasks_list`, `task_verify`
- `task_link_session`, `task_link_evidence`

### Rule Tools (10)
- `rule_create`, `rule_update`, `rule_deprecate`, `rule_delete`
- `rules_query`, `rules_query_by_tags`, `rule_get`, `rule_get_deps`, `rules_find_conflicts`
- `rules_list_archived`, `rule_get_archived`, `rule_restore`

### Session/DSM Tools
- `session_start`, `session_end`, `session_task`, `session_decision`
- `dsm_start`, `dsm_advance`, `dsm_checkpoint`

## Migration Completed

| Old Name | New Name | Status |
|----------|----------|--------|
| `governance_create_task` | `task_create` | DONE |
| `governance_get_agent` | `agent_get` | DONE |
| `governance_list_all_tasks` | `tasks_list` | DONE |
| `governance_update_agent_trust` | `agent_trust_update` | DONE |
| All 42 deprecated tools | Removed | 2026-01-19 |

## Verification

```bash
# Check tool count (should be ~26)
scripts/check_mcp_duplicates.sh
```

## Rationale

- Compact names reduce verbosity (84 → 26 tools)
- Entity-first ordering groups related tools
- No redundant prefix improves readability
- Matches common API patterns (`resource_action`)

## Dependencies

- ARCH-MCP-02-v1 (MCP Split Architecture)

## Related

- GAP-MCP-NAMING-001 (RESOLVED: 2026-01-19)
