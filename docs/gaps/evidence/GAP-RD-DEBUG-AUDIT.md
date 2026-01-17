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

### Phase 1: Audit Log Schema (TODO)
- Add `audit-entry` entity to TypeDB schema
- Create audit log table/collection
- Define retention policy

### Phase 2: Correlation ID Propagation (PARTIAL)
- Generate correlation_id at request entry
- Pass through all service layers
- Include in all log messages

### Phase 3: Rule Application Tracking (TODO)
- Capture which rules influenced each decision
- Store rule IDs with audit entries
- Enable "why was this decision made?" queries

### Phase 4: Query Interface (TODO)
- MCP tool: `governance_query_audit_trail(entity_id)`
- API endpoint: `GET /api/audit/{entity_id}`
- Dashboard view: Audit trail tab on entity detail

## Acceptance Criteria

- [ ] All task state changes logged with correlation_id
- [ ] Applied rules captured for each decision
- [ ] Audit trail queryable by entity_id
- [ ] Dashboard shows audit history
- [ ] 7-day retention for audit entries

## Related

- WORKFLOW-SEQ-01-v1: Verification hierarchy (source of audit data)
- GOV-RULE-01-v1: Governance rule framework
- GAP-DATA-INTEGRITY-001: Data quality tracking

---

*Per GAP-DOC-01-v1: Evidence file for gap documentation*
