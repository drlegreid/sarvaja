---
name: Certification Request
about: Request E2E certification run for a feature or milestone
title: '[CERT] '
labels: certification, e2e
assignees: ''
---

## Certification Request

### Feature/Milestone
<!-- What feature or milestone needs certification? -->


### Capability Journeys to Verify

<!-- Check all that apply -->
- [ ] J1: Rules Governance Data
- [ ] J2: Agent Trust Data
- [ ] J3: Session/Evidence Data
- [ ] J4: Task Data
- [ ] J5: Monitoring Data
- [ ] J6: Journey Patterns

### Pre-Certification Checklist

<!-- Must be completed before certification -->
- [ ] All unit tests pass (`pytest tests/ -v`)
- [ ] Phase 7 tests pass (data router, migration, readonly)
- [ ] No critical GAPs blocking
- [ ] Documentation updated (TODO.md, R&D-BACKLOG.md)

### Test Coverage

| Suite | Tests | Status |
|-------|-------|--------|
| data_router | 22 | |
| chroma_migration | 19 | |
| chroma_readonly | 17 | |
| governance_ui | 36 | |
| rule_monitor | 20 | |
| journey_analyzer | 24 | |

### Expected Outcomes

<!-- What should the certification prove? -->
1.
2.
3.

### Evidence Requirements

<!-- Per RULE-001: Session Evidence Logging -->
- [ ] Screenshots captured for each journey step
- [ ] Certification report generated
- [ ] Results uploaded to `results/e2e/`

### Related Rules

- RULE-004: Exploratory Testing with Evidence Capture
- RULE-020: LLM-Driven E2E Test Generation
- RULE-024: AMNESIA Protocol

---

### Certification Result

<!-- Filled by automation or reviewer -->

**Status:** [ ] PASSED | [ ] FAILED | [ ] PARTIAL

**Run Date:**

**Evidence Location:** `results/e2e/`

**Notes:**


---
*Per P9.8: Capability Journey Certification*
