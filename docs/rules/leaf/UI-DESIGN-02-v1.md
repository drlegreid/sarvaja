# UI-DESIGN-02-v1: UI/UX Design Standards

**Category:** `reporting` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** TECHNICAL

> **Location:** [RULES-STRATEGY.md](../technical/RULES-STRATEGY.md)
> **Tags:** `ui`, `ux`, `accessibility`, `design`, `wcag`

---

## Directive

All UI components MUST follow:

1. **Accessibility (WCAG)** - Meet WCAG 2.1 AA standards
2. **Responsive Design** - Support desktop, tablet, mobile viewports
3. **Consistent Components** - Reuse component patterns across views
4. **Dark Mode Support** - Provide dark theme option

---

## Validation

- [ ] Color contrast meets WCAG AA (4.5:1 minimum)
- [ ] All interactive elements keyboard accessible
- [ ] Layout adapts to viewport size
- [ ] Dark mode toggle functional

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Use fixed pixel widths | Use responsive units (rem, %) |
| Low contrast text | Ensure 4.5:1 contrast ratio |
| Mouse-only interactions | Support keyboard navigation |
| Hardcoded light theme | Provide theme toggle |

## Test Coverage

**6 robot test file(s)** validate this rule:

| File | Scope |
|------|-------|
| `tests/robot/unit/file_viewer.robot` | unit |
| `tests/robot/unit/ui_data_access.robot` | unit |
| `tests/robot/unit/ui_factory.robot` | unit |
| `tests/robot/unit/ui_filters.robot` | unit |
| `tests/robot/unit/ui_helpers.robot` | unit |
| `tests/robot/unit/ui_module.robot` | unit |

```bash
# Run all tests validating this rule
robot --include UI-DESIGN-02-v1 tests/robot/
```

---

*Per UI-TRAME-01-v1: Trame UI Patterns*
