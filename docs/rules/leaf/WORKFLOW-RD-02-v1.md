# WORKFLOW-RD-02-v1: R&D Workflow with Human Approval Gate

**Category:** `autonomy` | **Priority:** CRITICAL | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Location:** [RULES-WORKFLOW.md](../operational/RULES-WORKFLOW.md)
> **Tags:** `workflow`, `r&d`, `approval`, `autonomy`

---

## Directive

R&D tasks impacting budget, architecture, or strategy MUST require human approval unless DEEP autonomy is explicitly mandated.

1. **Budget Impact** - Tasks requiring new resources need approval
2. **Architecture Impact** - Structural changes need human sign-off
3. **Strategy Impact** - Direction changes need stakeholder approval
4. **DEEP Autonomy Override** - Only skip approval when explicitly authorized

---

## Approval Categories

| Category | Approval Required | Override |
|----------|------------------|----------|
| Budget changes | YES | DEEP autonomy only |
| New dependencies | YES | DEEP autonomy only |
| Architecture changes | YES | DEEP autonomy only |
| Strategy pivots | YES | Never |
| Routine maintenance | NO | N/A |

---

## Validation

- [ ] Impact category identified
- [ ] Approval obtained if required
- [ ] Rationale documented
- [ ] Evidence logged

---

*Per WORKFLOW-RD-01-v1: R&D Workflow with Human Approval*
