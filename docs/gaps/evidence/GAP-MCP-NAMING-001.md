# GAP-MCP-NAMING-001: MCP Tool Naming Standardization

| Field | Value |
|-------|-------|
| **ID** | GAP-MCP-NAMING-001 |
| **Priority** | HIGH |
| **Status** | RESOLVED |
| **Created** | 2026-01-17 |
| **Resolved** | 2026-01-19 |
| **Category** | Architecture |

## Problem Statement

MCP tools had inconsistent naming patterns causing confusion:
- `governance_update_task` vs `governance_task_link_session`
- 84 tools with mixed naming conventions

## Resolution Summary

**Reduced MCP tools from 84 to 26 (69% reduction)**

| Metric | Before | After |
|--------|--------|-------|
| Tool count | 84 | 26 |
| Naming pattern | Mixed | Consistent `entity_action` |
| Deprecated functions | 42 | 0 |

## Final Tool Inventory

### Agents (6): `agent_create`, `agent_get`, `agents_list`, `agent_trust_update`, `agents_dashboard`, `agent_activity`

### Rules (10): `rule_create`, `rule_update`, `rule_deprecate`, `rule_delete`, `rules_query`, `rules_query_by_tags`, `rule_get`, `rule_get_deps`, `rules_find_conflicts`, `rules_list_archived`

### Tasks (6): `task_create`, `task_get`, `task_update`, `task_delete`, `tasks_list`, `task_verify`

### Other (4): `proposal_create`, `handoff_create`, `audit_query`, `backlog_get`

## Implementation Details

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Add aliases | ✅ 2026-01-17 |
| Phase 2 | Deprecation docs | ✅ 2026-01-18 |
| Phase 3 | Remove deprecated | ✅ 2026-01-19 |
| Phase 4 | Update tests | ✅ 2026-01-19 |

## Files Modified (2026-01-19)

- `governance/mcp_tools/agents.py` - 12→6 tools
- `governance/mcp_tools/rules_query.py` - 12→6 tools
- `governance/mcp_tools/rules_crud.py` - 8→4 tools
- `governance/mcp_tools/tasks_crud.py` - 12→6 tools
- `governance/mcp_tools/tasks_linking.py` - 16→8 tools
- `governance/mcp_tools/proposals.py` - 10→5 tools
- `governance/mcp_tools/handoff.py` - 10→5 tools
- `governance/mcp_tools/gaps.py` - 8→4 tools
- `governance/mcp_tools/audit.py` - 8→4 tools
- `governance/mcp_tools/rules_archive.py` - 6→3 tools
- `governance/compat.py` - Created for backward compatibility in tests
- `tests/test_rules_crud.py` - Updated function names

## Verification

```bash
scripts/check_mcp_duplicates.sh
# Output: Tools: 26, No duplicates
```

## Related

- MCP-NAMING-01-v1 (ACTIVE)
- ARCH-MCP-02-v1 (MCP Architecture)
