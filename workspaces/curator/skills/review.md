# Skill: Code Review

**ID:** SKILL-REVIEW-001
**Tags:** curator, review, quality
**Requires:** Read, Grep, governance_query_rules

## When to Use

- Reviewing implementation handoffs from CODING agent
- Validating changes meet requirements
- Checking rule compliance
- Approving for merge

## Procedure

1. **Load Review Context**
   ```python
   # Read implementation evidence
   Read("evidence/TASK-{id}-IMPLEMENTATION.md")

   # Get applicable rules
   governance_query_rules(priority="CRITICAL")
   ```

2. **Review Checklist**
   | Check | Rule | Pass? |
   |-------|------|-------|
   | File size < 300 lines | RULE-032 | |
   | Tests included | RULE-023 | |
   | No hardcoded secrets | Security | |
   | Follows existing patterns | RULE-008 | |
   | Documentation updated | RULE-001 | |

3. **Verify Tests**
   ```bash
   # Run affected tests
   pytest tests/test_affected.py -v

   # Run E2E if UI change
   python -m robot tests/e2e/
   ```

4. **Document Decision**
   - APPROVED: Ready for merge
   - CHANGES_REQUESTED: Issues to fix
   - BLOCKED: Major issues, escalate

## Evidence Output

```markdown
## Review: TASK-001 Implementation

### Summary
Error dialog fix reviewed and approved.

### Checklist
| Check | Rule | Status |
|-------|------|--------|
| File size | RULE-032 | PASS (245 lines) |
| Tests | RULE-023 | PASS (3 new tests) |
| Patterns | RULE-008 | PASS |
| Docs | RULE-001 | N/A |

### Test Results
- pytest: 3 passed
- E2E: 1 passed

### Decision
**APPROVED** - Ready for merge

### Notes
Clean implementation, follows existing patterns.
```

## Related Skills

- SKILL-VALIDATE-002 (Evidence Validation)
- SKILL-APPROVE-003 (Change Approval)

---

*Per RULE-011: Multi-Agent Governance*
