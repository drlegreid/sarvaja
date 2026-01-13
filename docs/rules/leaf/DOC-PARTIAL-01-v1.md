# DOC-PARTIAL-01-v1: PARTIAL Task Handling

**Category:** `workflow` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Legacy ID:** RULE-033
> **Location:** [RULES-STANDARDS.md](../operational/RULES-STANDARDS.md)
> **Tags:** `workflow`, `tasks`, `partial`, `breakdown`

---

## Directive

When a gap requires breakdown, mark as PARTIAL and create linked subtasks. Each subtask must be <2 hours.

---

## Status Meanings

| Status | Meaning | Next Action |
|--------|---------|-------------|
| OPEN | Not started | Begin or break down |
| PARTIAL | Needs breakdown | Create subtasks |
| IN_PROGRESS | Being worked | Continue |
| RESOLVED | Done | No action |

---

## Naming Conventions

```
GAP-UI-001       <- PARTIAL (parent)
GAP-UI-001.1     <- RESOLVED (subtask A)
GAP-UI-001.2     <- OPEN (subtask B)
```

---

## Validation

- [ ] Large tasks marked PARTIAL
- [ ] Subtasks created and linked
- [ ] Each subtask < 2 hours

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
