# UI-VUE-IMPL-01-v1: Vue.js / Trame UI Implementation Patterns

**Category:** `technical` | **Priority:** CRITICAL | **Status:** ACTIVE | **Type:** TECHNICAL

> **Tags:** `vue`, `trame`, `vuetify`, `ui`, `reactivity`

---

## Directive

All dashboard UI code MUST follow Trame-specific Vue.js/Vuetify 3 patterns. The dashboard uses Python-side Trame (NOT raw Vue SFCs). Failing to follow these patterns causes silent failures (events not firing, state not updating, blank pages).

---

## CRITICAL: Trame Event Binding

### Event Registration for Missing Events
VDataTable in trame-vuetify v3 does NOT register `click:row` in `_event_names`. You MUST use `__events` to register custom events:

```python
# CORRECT - registers event AND uses plain string handler
v3.VDataTable(
    click_row="($event, row) => { trigger('select_rule', [row.item.id]) }",
    __events=[("click_row", "click:row")],
)

# WRONG - tuple handler gets wrapped in extra trigger()
v3.VDataTable(
    click_row=("($event, row) => { trigger('select_rule', [row.item.id]) }",),
    __events=[("click_row", "click:row")],
)

# WRONG - without __events, click_row becomes a prop (:click-row), not an event (@click:row)
v3.VDataTable(
    click_row="($event, row) => { trigger('select_rule', [row.item.id]) }",
)
```

### Handler Value Types
| Syntax | Behavior | Use For |
|--------|----------|---------|
| `"js_code"` (string) | Raw JS expression passed to Vue | Event handlers |
| `("js_code",)` (tuple) | Trame wraps in `trigger('js_code')` | Props/state bindings |
| `("state_var", default)` | Reactive state binding | VDataTable items/headers |

---

## State Reactivity

### Reactive Bindings (Props)
```python
# CORRECT - tuple binds to trame state variable
v3.VDataTable(
    items=("rules",),
    headers=("rules_headers", [{"title": "ID", "key": "id"}]),
)

# WRONG - string is literal value, not reactive
v3.VDataTable(items="rules")
```

### State Updates from Python
```python
# Controller: use state directly
state.rules = new_data          # triggers Vue reactivity
state.dirty("rules")            # force dirty if nested mutation
```

---

## Controller Decorators

| Decorator | Callable From | Use For |
|-----------|--------------|---------|
| `@ctrl.trigger("name")` | Vue `trigger('name')` | Button clicks, row clicks, form submits |
| `@ctrl.set("name")` | Python only | Internal helpers called by other controllers |
| `@state.change("var")` | Automatic on state change | Reactive filters, auto-refresh |

---

## Vuetify 3 Component Patterns

### Import
```python
from trame.widgets import vuetify3 as v3, html
# Always prefix: v3.VCard, v3.VBtn, v3.VDataTable
# NEVER: from trame.widgets.vuetify3 import VCard  (not how trame works)
```

### Test Attributes
```python
# Always add data-testid for Robot Framework selectors
v3.VBtn(
    "Click Me",
    __properties=["data-testid"],
    **{"data-testid": "my-button"}
)
```

### Conditional Rendering
```python
# v_if for conditional display
v3.VCard(v_if="active_view === 'rules'")

# v_for for iteration
v3.VListItem(v_for="(item, idx) in items", **{":key": "idx"})
```

### Template Slots
```python
# Vuetify 3 slot syntax in Trame
with html.Template(v_slot_prepend=True):
    v3.VIcon("mdi-icon-name", size="small")
```

---

## Common Anti-Patterns (DO NOT)

1. **DO NOT** use tuples for event handler values (causes double-wrapping)
2. **DO NOT** omit `__events` for unregistered Vue events on Vuetify 3 components
3. **DO NOT** use `@ctrl.set()` for handlers triggered from Vue templates
4. **DO NOT** mutate props directly - use `trigger()` to call Python controller
5. **DO NOT** use bare string for reactive state bindings (use tuple)
6. **DO NOT** assign JS variables directly in click handlers for trame state updates (use `trigger()`)

---

## Vue.js Best Practices (from Vue 3 docs)

- **ref() over reactive()**: Destructuring reactive() breaks reactivity
- **v-if with v-for**: Never on same element - filter in computed/Python instead
- **Props read-only**: Child components must NOT modify props; emit events instead
- **Computed no side effects**: No API calls or mutations in computed getters
- **Key attribute**: Always provide `:key` in v-for loops

---

## References

- [Vue 3 Best Practices](https://skills.sh/hyf0/vue-skills/vue-best-practices)
- [Trame Documentation](https://trame.readthedocs.io/)
- [Vuetify 3 Components](https://vuetifyjs.com/en/components/all/)
- Prior fix: commit c8f9985 (VDataTable click:row event registration)

---

## Validation

- [ ] All VDataTable click handlers use plain strings + `__events`
- [ ] All controller handlers use `@ctrl.trigger()` for Vue-callable functions
- [ ] All reactive state bindings use tuple syntax
- [ ] All components have `data-testid` attributes
- [ ] No event handler uses tuple syntax (single-element tuple)

---

*Per PLAN-UI-OVERHAUL-001 Task R.2*
