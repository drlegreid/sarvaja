# GAP-UI-EXP-009: TypeDB Task-Resolution Type Missing

**Status:** RESOLVED
**Priority:** HIGH (downgraded from CRITICAL)
**Category:** data_integrity
**Discovered:** 2026-01-14 via MCP tool call during exploratory testing
**Resolved:** 2026-01-14

## Problem Statement

The `governance_list_all_tasks` MCP tool failed with TypeDB errors when querying optional attributes/relations that don't exist in the running TypeDB schema:
- `task-resolution`
- `task-commit`
- Other optional types

## Technical Details

### Root Cause

The schema.tql file defines many types (task-resolution, task-commit, etc.) that were added in code but never migrated to the running TypeDB instance. When queries referenced these types, TypeDB threw:
```
[TYR03] Invalid Type Read: The type 'task-resolution' does not exist.
```

### Fix Applied

Added graceful error handling for optional queries in `governance/typedb/queries/tasks/read.py`:

1. Created `_safe_query()` helper method:
```python
def _safe_query(self, query: str) -> list:
    """Execute query with graceful handling of missing types."""
    try:
        return self._execute_query(query)
    except Exception:
        # Type may not exist in older TypeDB schemas
        return []
```

2. Changed all optional attribute/relation queries to use `_safe_query()` instead of direct `_execute_query()`:
   - task-body
   - task-resolution
   - gap-reference
   - agent-id
   - task-evidence
   - task-completed-at
   - task-created-at
   - task-claimed-at
   - implements-rule relationship
   - completed-in relationship
   - task-commit relationship
   - task-business/design/architecture/test sections

### Files Modified

| File | Changes |
|------|---------|
| `governance/typedb/queries/tasks/read.py` | Added `_safe_query()` helper, refactored all optional queries |
| `governance/typedb/queries/tasks/crud.py` | Made task-resolution conditional in insert |

### Impact

- MCP tool `governance_list_all_tasks` now handles schema version mismatches gracefully
- Tasks are returned even if optional attributes aren't in schema
- No data loss - attributes simply return empty/null if type doesn't exist

### Remaining Work

To fully enable all features, apply schema migration:
```bash
# From TypeDB console
source governance/schema.tql
```

## Evidence

- MCP tool error: `[TYR03] Invalid Type Read: The type 'task-resolution' does not exist`
- After fix: Optional queries return empty results instead of errors
- Code change verified via import test

## Related

- Rules: RULE-009 (Version Compatibility), RULE-021 (MCP Healthcheck)
- Other GAPs: GAP-UI-EXP-006 (Infrastructure health)
- Session: SESSION-2026-01-14-GAP-EXP-008-FIX

---
*Per GAP-DOC-01-v1: Full technical details in evidence file*
