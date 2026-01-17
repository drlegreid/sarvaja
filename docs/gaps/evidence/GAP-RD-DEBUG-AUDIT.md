# GAP-RD-DEBUG-AUDIT: Audit Trail Debugability

**Priority:** MEDIUM | **Category:** observability | **Status:** PARTIAL
**Discovered:** 2026-01-14 | **Session:** SESSION-2026-01-14-ORCHESTRATOR
**R&D Track:** RD-DEBUG-AUDIT

---

## Summary

Need comprehensive audit trail for debugging agent decisions, rule applications, and task state changes. Currently partial: correlation_id and applied_rules added, but not consistently used across all operations.

## Current State (2026-01-14)

### Implemented
- `correlation_id` field added to task operations
- `applied_rules` field tracks which rules influenced decisions
- Basic logging in workflow endpoints

### Missing
- Correlation ID not passed through all layers
- No unified audit log format
- Rule application reasons not captured
- Session→Task→Rule chain not queryable

## Technical Analysis

### Schema Support
```typeql
# Existing
task owns task-id;
task owns task-status;

# Needed for full audit
audit-entry sub entity,
    owns audit-id,
    owns correlation-id,
    owns timestamp,
    owns actor-id,        # agent or user
    owns action-type,     # CREATE, UPDATE, DELETE, CLAIM, COMPLETE
    owns entity-type,     # task, session, rule
    owns entity-id,
    owns old-value,
    owns new-value,
    owns applied-rules;   # JSON list of rule IDs
```

### API Gaps
```python
# Current (partial)
@router.put("/tasks/{task_id}/complete")
async def complete_task(task_id, evidence, verification_level):
    # Missing: correlation_id tracking
    # Missing: audit log entry
    pass

# Needed
@router.put("/tasks/{task_id}/complete")
async def complete_task(task_id, evidence, verification_level):
    correlation_id = generate_correlation_id()
    audit_log.record(
        correlation_id=correlation_id,
        action="COMPLETE",
        entity_type="task",
        entity_id=task_id,
        actor_id=current_agent,
        applied_rules=["WORKFLOW-SEQ-01-v1"],
        metadata={"verification_level": verification_level}
    )
```

## Implementation Plan

### Phase 1: Audit Log Schema (DONE - 2026-01-17)
- ✅ `governance/stores/audit.py` - In-memory store with JSON persistence
- ✅ `AuditEntry` dataclass with all fields
- ✅ 7-day retention policy implemented
- Note: Uses file persistence instead of TypeDB (Python 3.13 workaround)

### Phase 2: Correlation ID Propagation (DONE - 2026-01-17)
- ✅ `generate_correlation_id()` function
- ✅ Auto-generated if not provided to `record_audit()`
- ✅ Format: `CORR-YYYYMMDD-HHMMSS-XXXXXX`

### Phase 3: Rule Application Tracking (DONE - 2026-01-17)
- ✅ `applied_rules` field in AuditEntry
- ✅ Task completion records `WORKFLOW-SEQ-01-v1`
- ✅ Stored with each audit entry

### Phase 4: Query Interface (PARTIAL - 2026-01-17)
- ✅ REST API: `GET /api/audit` - List with filters
- ✅ REST API: `GET /api/audit/summary` - Statistics
- ✅ REST API: `GET /api/audit/{entity_id}` - Entity trail
- TODO: MCP tool for claude-mem integration
- TODO: Dashboard view for audit history

## Files Created

| File | Purpose |
|------|---------|
| `governance/stores/audit.py` | Audit store module |
| `governance/routes/audit.py` | REST API endpoints |
| `data/audit_trail.json` | Persisted audit entries |

## Acceptance Criteria

- [x] All task state changes logged with correlation_id
- [x] Applied rules captured for each decision
- [x] Audit trail queryable by entity_id (via REST API)
- [ ] Dashboard shows audit history
- [x] 7-day retention for audit entries

## Related

- WORKFLOW-SEQ-01-v1: Verification hierarchy (source of audit data)
- GOV-RULE-01-v1: Governance rule framework
- GAP-DATA-INTEGRITY-001: Data quality tracking

---

*Per GAP-DOC-01-v1: Evidence file for gap documentation*
