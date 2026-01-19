# GAP-GAPS-TASKS-001: Gaps/Tasks Entity Merge Architecture

| Field | Value |
|-------|-------|
| **ID** | GAP-GAPS-TASKS-001 |
| **Priority** | HIGH |
| **Status** | OPEN |
| **Created** | 2026-01-19 |
| **Category** | Architecture |

## Problem Statement

Current architecture has gaps and tasks as separate entities:
- **Gaps**: Parsed from GAP-INDEX.md (filesystem)
- **Tasks**: Stored in TypeDB

This creates:
1. Data duplication (same work tracked in two places)
2. Sync complexity (keeping INDEX and TypeDB aligned)
3. Different APIs/tools for related concepts

**User requirement:** "Gaps ARE tasks. Each task should have a markdown document linked. INDEX file is just backup when TypeDB is down."

## Current Architecture

```
GAP-INDEX.md (filesystem)     TypeDB (database)
├── GAP-001                   ├── TASK-001
├── GAP-002                   ├── P11.1
└── EPIC-001                  └── RD-001
       ↓                            ↓
   GapParser                   TypeDBClient
       ↓                            ↓
   WorkItem <──── backlog_unified ────> WorkItem
```

**Issue:** Two sources of truth, combined only at runtime via `backlog_unified()`.

## Proposed Architecture

```
TypeDB (single source of truth)
├── work-item (entity)
│   ├── id: "GAP-001" | "TASK-001" | "P11.1"
│   ├── item_type: "gap" | "task" | "rd"
│   ├── document_path: "docs/gaps/evidence/GAP-001.md"
│   └── ... other fields
│
GAP-INDEX.md (backup/sync target)
├── Generated from TypeDB query
└── Fallback when TypeDB unavailable
```

## Implementation Plan

### Phase 1: Schema Enhancement (TypeDB)
- Add `document_path` owns attribute to task entity
- Add `item_type` owns attribute (gap, task, rd)
- Support GAP-xxx style IDs alongside existing

### Phase 2: Sync Tool
- `workspace_sync_gaps_to_typedb()` - Import gaps as tasks
- Auto-generate document_path from ID: `GAP-xxx` → `docs/gaps/evidence/GAP-xxx.md`
- Preserve existing task data

### Phase 3: Bi-directional Sync
- TypeDB → GAP-INDEX.md: `generate_gap_index()` for backup
- GAP-INDEX.md → TypeDB: `sync_gaps_from_index()` for recovery
- Divergence detection in `workspace_sync_status()`

### Phase 4: Tool Unification
- Deprecate `backlog_get` (gap-only)
- Enhance `backlog_unified` as primary tool
- Add filters: `backlog_unified(item_type="gap", limit=20)`

## Schema Changes

```tql
# Add to task entity
task owns document-path;
task owns item-type;

# New attributes
attribute document-path value string;
attribute item-type value string;
```

## Migration Script

```python
def migrate_gaps_to_typedb():
    """Import GAP-INDEX.md gaps as tasks in TypeDB."""
    parser = GapParser()
    gaps = parser.get_all_gaps()

    for gap in gaps:
        client.create_task(
            task_id=gap.id,
            name=gap.description,
            item_type="gap",
            status="open" if not gap.is_resolved else "resolved",
            priority=gap.priority.upper(),
            document_path=f"docs/gaps/evidence/{gap.id}.md"
        )
```

## Backward Compatibility

| Tool | Behavior |
|------|----------|
| `backlog_get()` | Returns gaps from TypeDB (query `item_type="gap"`) |
| `backlog_unified()` | Returns all work items (unchanged) |
| `GapParser` | Fallback when TypeDB unavailable |
| `GAP-INDEX.md` | Generated backup, not edited manually |

## Benefits

1. **Single source of truth** - TypeDB holds all work items
2. **Unified API** - Same tools for gaps and tasks
3. **Referential integrity** - Links enforced by schema
4. **Better queries** - TypeDB inference for related items
5. **Offline resilience** - INDEX.md as recoverable backup

## Risks

| Risk | Mitigation |
|------|------------|
| Data loss during migration | Backup GAP-INDEX.md first |
| TypeDB downtime | Keep GapParser as fallback |
| Breaking existing workflows | Phased rollout, backward compat |

## Acceptance Criteria

- [ ] Schema supports document_path and item_type attributes
- [ ] All gaps from GAP-INDEX.md exist in TypeDB as tasks
- [ ] `backlog_unified` returns both gaps and tasks
- [ ] `workspace_sync_status` detects divergence
- [ ] GAP-INDEX.md can be regenerated from TypeDB

## Related

- WorkItem abstraction: [governance/utils/work_item.py](../../../governance/utils/work_item.py)
- Gap parser: [governance/utils/gap_parser.py](../../../governance/utils/gap_parser.py)
- Backlog tools: [governance/mcp_tools/gaps.py](../../../governance/mcp_tools/gaps.py)
