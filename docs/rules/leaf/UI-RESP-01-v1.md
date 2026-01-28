# UI-RESP-01-v1: Responsive UI Design Standard

**Category:** `ui` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Legacy ID:** N/A (new rule)
> **Location:** [RULES-TECHNICAL.md](../technical/RULES-TECHNICAL.md)
> **Tags:** `ui`, `responsive`, `accessibility`, `ux`

---

## Directive

All UI components MUST scale appropriately with window size. Use relative units, responsive breakpoints, and mobile-first design patterns.

---

## Core Principles

### 1. Mobile-First Design
Design for smallest screens first, then scale up.

```python
# WRONG: Fixed columns
v3.VCol(cols=3)  # Always 25% width

# CORRECT: Responsive breakpoints
v3.VCol(cols=12, sm=6, md=4, lg=3)  # Stacks on mobile
```

### 2. Relative Units Over Fixed Pixels

| Don't | Do |
|-------|-----|
| `max-width: 300px` | `max-width: 100%` or Vuetify sizing |
| `max-height: 500px` | `max-height: calc(100vh - var(--header))` |
| `height: 48px` | `min-height: 3rem` |

### 3. Touch-Friendly Targets
Interactive elements MUST be at least 44x44 pixels for touch accessibility.

```python
# Buttons, clickable items
v3.VBtn(size="default")  # Not "x-small" for primary actions
```

---

## Vuetify Responsive Breakpoints

| Breakpoint | Width | Cols Example |
|------------|-------|--------------|
| `xs` | <600px | `cols=12` (full width) |
| `sm` | 600-960px | `sm=6` (half width) |
| `md` | 960-1280px | `md=4` (third width) |
| `lg` | 1280-1920px | `lg=3` (quarter width) |
| `xl` | >1920px | `xl=2` (sixth width) |

### Grid Pattern

```python
# 4-card metrics row - CORRECT
with v3.VRow():
    for metric in metrics:
        with v3.VCol(cols=12, sm=6, md=3):  # Responsive!
            build_metric_card(metric)
```

---

## Container Patterns

### Scrollable Lists
```python
# Use viewport-relative height
v3.VSheet(
    style="max-height: calc(100vh - 200px); overflow-y: auto;",
    classes="fill-height"
)
```

### Filter Toolbars
```python
# Wrap on small screens
with v3.VRow(dense=True):
    with v3.VCol(cols=12, sm=6, md=4):
        v3.VTextField(...)  # Search
    with v3.VCol(cols=6, sm=3, md=2):
        v3.VSelect(...)  # Filter 1
    with v3.VCol(cols=6, sm=3, md=2):
        v3.VSelect(...)  # Filter 2
```

---

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| `cols=3` only | Breaks on mobile | Add `sm`, `md` breakpoints |
| `max-width: 300px` | Doesn't scale | Use `%` or responsive classes |
| `calc(100vh - 300px)` | Magic number | Use CSS variables or refs |
| Fixed toolbar rows | Overflow on mobile | Use responsive grid |

---

## Validation Checklist

- [ ] All VCol use responsive breakpoints (sm, md, lg)
- [ ] No hardcoded pixel widths for containers
- [ ] Touch targets ≥44px
- [ ] Tested at 320px, 768px, 1280px, 1920px widths
- [ ] Content scrolls within containers, not page

---

## Sources

- [Cursor UI/UX Best Practices](https://cursor.directory/ui-ux-design-best-practices)
- [Vuetify Grid System](https://vuetifyjs.com/en/components/grids/)
- [WCAG 2.1 AA](https://www.w3.org/WAI/WCAG21/quickref/)

## Test Coverage

**1 robot test file(s)** validate this rule:

| File | Scope |
|------|-------|
| `tests/robot/unit/ui_state.robot` | unit |

```bash
# Run all tests validating this rule
robot --include UI-RESP-01-v1 tests/robot/
```

---

*Per GAP-UI-RESPONSIVE-001: Window scaling issues*
