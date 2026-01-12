# Skill: Change Approval

**ID:** SKILL-APPROVE-003
**Tags:** curator, approval, governance
**Requires:** governance_vote, governance_update_task, governance_update_rule

## When to Use

- Final approval of implementations
- Rule modification decisions
- Gap resolution sign-off
- Trust score updates

## Procedure

1. **Gather Approval Context**
   ```python
   # Get proposal if rule change
   governance_get_proposals(status="pending")

   # Get task status
   governance_get_task(task_id="TASK-001")
   ```

2. **Approval Criteria**
   | Type | Requires | Threshold |
   |------|----------|-----------|
   | Code merge | Review PASS | 1 curator |
   | Rule modify | Evidence + vote | Trust ≥ 0.7 |
   | Rule create | Proposal + vote | Trust ≥ 0.9 |
   | Gap resolve | Tests + evidence | 1 curator |

3. **Execute Approval**
   ```python
   # Vote on rule proposal
   governance_vote(
       proposal_id="PROP-001",
       agent_id="curator-001",
       vote="approve",
       reason="Evidence supports change"
   )

   # Update task status
   governance_update_task(
       task_id="TASK-001",
       status="completed"
   )

   # Update gap status
   # (in GAP-INDEX.md)
   ```

4. **Document Decision**
   - Approval rationale
   - Conditions (if any)
   - Follow-up actions

## Evidence Output

```markdown
## Approval: TASK-001

### Decision
**APPROVED** for merge

### Approval Type
Code change (1 curator required)

### Basis
- Review: PASSED
- Evidence: VALID
- Tests: 3 passed, 0 failed
- Rules: Compliant

### Actions Taken
1. Task marked completed
2. Gap marked RESOLVED in GAP-INDEX.md
3. Evidence linked to task

### Curator
- Agent: curator-001
- Trust: 0.85
- Timestamp: 2026-01-11T10:30:00Z
```

## Related Skills

- SKILL-REVIEW-001 (Code Review)
- SKILL-VALIDATE-002 (Evidence Validation)

---

*Per RULE-011: Multi-Agent Governance Protocol*
