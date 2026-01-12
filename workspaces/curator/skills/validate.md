# Skill: Evidence Validation

**ID:** SKILL-VALIDATE-002
**Tags:** curator, validation, evidence
**Requires:** governance_evidence_search, Read, governance_query_rules

## When to Use

- Validating research findings
- Checking evidence completeness
- Verifying gap resolutions
- Auditing session outcomes

## Procedure

1. **Load Evidence**
   ```python
   # Search relevant evidence
   governance_evidence_search("TASK-001")

   # Read session evidence
   Read("evidence/SESSION-*.md")
   ```

2. **Validation Criteria**
   | Criterion | Required | Check |
   |-----------|----------|-------|
   | Intent captured | Yes | session_capture_intent called |
   | Outcome documented | Yes | session_capture_outcome called |
   | Files referenced | Yes | Line numbers included |
   | Rules linked | Yes | RULE-XXX references |
   | Next steps clear | Yes | Handoff items listed |

3. **Cross-Reference**
   - Check task in GAP-INDEX.md
   - Verify rule compliance
   - Confirm evidence supports claims

4. **Document Findings**
   - Valid: Evidence meets standards
   - Incomplete: Missing elements
   - Invalid: Claims not supported

## Evidence Output

```markdown
## Validation: TASK-001 Evidence

### Evidence Files Reviewed
| File | Type | Status |
|------|------|--------|
| TASK-001-RESEARCH.md | Handoff | VALID |
| TASK-001-IMPLEMENTATION.md | Handoff | VALID |
| SESSION-2026-01-11-TASK-001.md | Session | VALID |

### Validation Results
| Criterion | Status | Notes |
|-----------|--------|-------|
| Intent | PASS | Goal and source documented |
| Outcome | PASS | Status COMPLETE |
| Files | PASS | dialogs.py:45 referenced |
| Rules | PASS | RULE-023, RULE-032 linked |
| Next Steps | PASS | "Merge to main" |

### Verdict
**VALID** - All evidence requirements met
```

## Related Skills

- SKILL-REVIEW-001 (Code Review)
- SKILL-APPROVE-003 (Change Approval)

---

*Per RULE-001: Evidence-First Development*
