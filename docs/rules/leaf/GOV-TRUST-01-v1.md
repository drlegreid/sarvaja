# GOV-TRUST-01-v1: Decision Logging

**Category:** `governance` | **Priority:** MEDIUM | **Status:** ACTIVE | **Type:** FOUNDATIONAL

> **Legacy ID:** RULE-006
> **Location:** [RULES-SESSION.md](../governance/RULES-SESSION.md)
> **Tags:** `decisions`, `logging`, `governance`, `traceability`

---

## Directive

All strategic decisions MUST be logged in task system, not just chat.

---

## Format

```markdown
## DECISION-XXX: [Title]
**Date:** YYYY-MM-DD
**Context:** [Why needed]
**Options:** 1. A [pros/cons] 2. B [pros/cons]
**Decision:** [What was decided]
**Rationale:** [Why this option]
**Status:** IMPLEMENTED | PENDING | DEFERRED
```

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Log decisions only in chat | Record in task system with DECISION-XXX |
| Skip context/rationale | Include why, not just what |
| Omit alternatives considered | Document options evaluated |
| Use vague status | Use IMPLEMENTED/PENDING/DEFERRED |

---

## Validation

- [ ] Decision uses DECISION-XXX format
- [ ] Context and rationale documented
- [ ] Alternatives listed
- [ ] Status is explicit

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
