# GOV-PROP-01-v1: Rules Applicability Convention

**Category:** `governance` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** META

> **Legacy ID:** RULE-013
> **Location:** [RULES-MULTI-AGENT.md](../governance/RULES-MULTI-AGENT.md)
> **Tags:** `traceability`, `convention`, `gaps`, `todo`

---

## Directive

All code comments, gaps, and TODOs MUST reference applicable rules:

```
{TYPE}({RULE-ID}): {Description}
```

---

## Examples

```python
# Good
# TODO(RULE-002): Extract to separate module
# GAP-020(RULE-005): Memory threshold exceeded

# Bad
# TODO: Fix this later
```

---

## Gap Format

```markdown
| ID | Gap | Priority | Rule |
|----|-----|----------|------|
| GAP-020 | Memory monitoring | HIGH | RULE-005 |
```

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| `# TODO: Fix later` | `# TODO(RULE-XXX): Fix X` |
| `# FIXME` without rule | `# FIXME(RULE-002): Circular import` |
| Gap without rule reference | Link gaps to applicable rules |
| Orphan comments | Always reference governance rule |

---

## Validation

- [ ] All TODOs reference rules
- [ ] All gaps linked to rules
- [ ] Comments follow convention

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
