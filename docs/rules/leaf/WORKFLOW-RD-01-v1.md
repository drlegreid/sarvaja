# WORKFLOW-RD-01-v1: R&D Workflow with Human Approval

**Category:** `autonomy` | **Priority:** CRITICAL | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Legacy ID:** RULE-015
> **Location:** [RULES-WORKFLOW.md](../operational/RULES-WORKFLOW.md)
> **Tags:** `rd`, `autonomy`, `approval`, `budget`

---

## Directive

R&D tasks impacting budget, architecture, or strategy MUST require human approval unless DEEP autonomy is mandated.

---

## Autonomy Levels

| Level | Trigger | Approval |
|-------|---------|----------|
| **ROUTINE** | Default task | None |
| **STRATEGIC** | P1 milestone | Post-hoc review |
| **R&D** | Research needed | **Human required** |
| **DEEP** | Explicit mandate | Pre-approved |

---

## R&D Triggers

- New technology evaluation
- Architecture changes
- External dependency additions
- Budget-impacting decisions
- Infrastructure changes

---

## Autonomous Cleanup Exception (Amendment A - 2026-01-21)

Agents MAY autonomously delete/clean entities WITHOUT human approval when ALL conditions are met:

| Condition | Requirement |
|-----------|-------------|
| **Pattern Match** | Entity ID matches test artifact pattern: `TEST-*`, `TEMP-*`, `_test_*`, `*-TEST-*` |
| **No Production Refs** | Entity has no inbound relations from non-test entities |
| **Recency** | Created within current session OR last 7 days |
| **No Preserve Tag** | Entity lacks explicit `PRESERVE` or `KEEP` tag |

**Rationale:** Test artifacts are ephemeral by design. Blocking cleanup wastes human attention on obvious decisions while polluting production data.

**Evidence:** SESSION-2026-01-21-QA-REVIEW - 342 TEST-* entities cleaned autonomously after pattern validation.

---

## Validation

- [ ] R&D tasks flagged correctly
- [ ] Human approval obtained when required
- [ ] Autonomy level documented
- [ ] Cleanup exceptions validated against pattern rules

## Test Coverage

**1 robot test file(s)** validate this rule:

| File | Scope |
|------|-------|
| `tests/robot/unit/delegation.robot` | unit |

```bash
# Run all tests validating this rule
robot --include WORKFLOW-RD-01-v1 tests/robot/
```

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
*Amendment A: Per SESSION-2026-01-21-QA-REVIEW*
