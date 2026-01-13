# GOV-PROP-02-v1: UI/UX Design Standards

**Category:** `reporting` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** TECHNICAL

> **Legacy ID:** RULE-019
> **Location:** [RULES-MULTI-AGENT.md](../governance/RULES-MULTI-AGENT.md)
> **Tags:** `ui`, `ux`, `design`, `accessibility`

---

## Directive

All UI components MUST follow established design patterns:
1. Use Vuetify components (Trame environment)
2. Consistent spacing and typography
3. Accessible color contrast (WCAG AA)
4. Responsive layouts

---

## Component Patterns

| Component | Use Case | Pattern |
|-----------|----------|---------|
| VDataTable | Lists | Sortable, filterable |
| VCard | Details | Grouped information |
| VDialog | Modals | Confirmation, forms |
| VBtn | Actions | Primary/secondary variants |

---

## State Management

```python
# Use Trame state, NOT Vue refs
from trame.widgets import vuetify

with state:
    state.rules = []
    state.loading = False
```

---

## Validation

- [ ] Vuetify components used
- [ ] Color contrast >= 4.5:1
- [ ] Responsive breakpoints tested
- [ ] Loading states implemented

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Use raw HTML elements | Use Vuetify components (VBtn, VCard) |
| Use Vue refs for state | Use Trame `state` object |
| Skip loading states | Show VProgressLinear during fetch |
| Ignore accessibility | Maintain WCAG AA contrast >= 4.5:1 |

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
