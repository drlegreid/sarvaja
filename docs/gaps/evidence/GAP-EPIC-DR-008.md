# GAP-EPIC-DR-008: Task Evidence Field Population

**Priority:** HIGH | **Category:** data-integrity | **Status:** OPEN
**Discovered:** 2026-01-17 | **Session:** SESSION-2026-01-17-PLATFORM-GAPS
**Parent:** [GAP-DATA-INTEGRITY-001.md](GAP-DATA-INTEGRITY-001.md)

---

## Summary

Task entities have `evidence` field at 3% population (2/82 tasks). This field should contain completion notes, verification results, and work artifacts. Without evidence, tasks are "done" without audit trail.

## Current State

```
Tasks with evidence: 2/82 (3%)
Tasks without evidence: 80/82 (97%)
```

### Sample Tasks Without Evidence

```json
{
  "task_id": "KAN-001",
  "status": "DONE",
  "resolution": null,
  "evidence": null,  // Missing!
  "completed_at": "2026-01-14T..."
}
```

## Technical Analysis

### Schema Support
```typeql
# TypeDB schema (governance.tql)
task-evidence sub attribute, value string;
task owns task-evidence;
```
Schema supports evidence field. Issue is population, not schema.

### API Support
```python
# governance/routes/tasks/workflow.py:156-206
@router.put("/tasks/{task_id}/complete")
async def complete_task(
    task_id: str,
    evidence: Optional[str] = Query(None, ...)  # Already supported!
):
```
API accepts evidence parameter. Issue is callers not providing it.

### TypeDB Update Support
```python
# governance/typedb/queries/tasks/status.py:93-114
if evidence:
    evidence_escaped = evidence.replace('"', '\\"')
    insert_evidence_query = f"""
        match $t isa task, has task-id "{task_id}";
        insert $t has task-evidence "{evidence_escaped}";
    """
    tx.query.insert(insert_evidence_query)
```
TypeDB layer handles evidence persistence. Working correctly.

## Root Cause

1. **Historical tasks**: Completed before evidence workflow existed
2. **Manual completions**: Tasks marked DONE without using API
3. **No enforcement**: API doesn't require evidence for completion

## Proposed Solutions

### Option A: Backfill Script (Like EPIC-DR-007)
```python
# scripts/backfill_task_evidence.py
def backfill_evidence(dry_run=True):
    """
    Generate evidence for historical completed tasks.

    Strategy:
    - DONE tasks: "Marked complete during historical migration"
    - Tasks with linked_sessions: "Completed in session {session_id}"
    - Tasks with linked_rules: "Implements {rule_ids}"
    """
```

**Pros:** Quick fix, 100% coverage
**Cons:** Generic evidence, not meaningful

### Option B: Incremental Population
```python
# Require evidence for new completions
@router.put("/tasks/{task_id}/complete")
async def complete_task(
    task_id: str,
    evidence: str = Query(..., description="Required evidence")  # Make required
):
```

**Pros:** Meaningful evidence going forward
**Cons:** Doesn't fix historical tasks

### Option C: Hybrid (Recommended)
1. Backfill historical tasks with generic evidence
2. Make evidence required for new completions
3. Add verification_level to evidence quality

## Implementation Plan

### Phase 1: Backfill Script
```bash
# Create backfill script
scripts/backfill_task_evidence.py

# Run in dry-run mode first
python scripts/backfill_task_evidence.py --dry-run

# Execute backfill
python scripts/backfill_task_evidence.py
```

### Phase 2: API Enforcement
- Add `min_length=10` to evidence parameter
- Log warning for empty evidence
- Add evidence quality metrics to dashboard

### Phase 3: Evidence Quality Tiers
| Tier | Criteria | Example |
|------|----------|---------|
| L1 | Any text | "Done" |
| L2 | Includes session/commit | "Completed in SESSION-2026-01-17" |
| L3 | Includes verification | "[L2 Verified] Tests pass, E2E validated" |

## Acceptance Criteria

- [ ] Task evidence population >= 50%
- [ ] Backfill script created and tested
- [ ] Evidence includes session/commit references where available
- [ ] GAP-DATA-INTEGRITY-001 updated with new stats

## Related Files

- `governance/typedb/queries/tasks/status.py` - Evidence persistence
- `governance/routes/tasks/workflow.py` - Complete task endpoint
- `scripts/backfill_agent_id.py` - Reference for backfill pattern

---

*Per GAP-DOC-01-v1: Evidence file for gap documentation*
