# UI-NAV-01-v1: Entity Navigation Context

**Category:** `ui` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** TECHNICAL

> **Location:** [RULES-TECHNICAL.md](../technical/RULES-TECHNICAL.md)
> **Tags:** `ux`, `navigation`, `entity`, `context`

---

## Directive

When navigating between related entities (e.g., session→task, rule→task), preserve navigation source context to enable contextual back navigation.

---

## Rationale

Users often explore relationships between entities (sessions, tasks, rules). Without navigation context, the back button simply closes the detail view rather than returning to the source entity. This creates a poor UX where users lose their place in the workflow.

---

## Implementation Pattern

### State Variables

```python
# Entity Navigation Context (UI-NAV-01-v1)
'nav_source_view': None,       # 'sessions', 'rules', etc.
'nav_source_id': None,         # session_id, rule_id, etc.
'nav_source_label': None,      # Human-readable label for back button
```

### Navigation Trigger (with source)

```javascript
// When navigating from session to task
trigger('navigate_to_task', [
    task.task_id,
    'sessions',                                    // source_view
    selected_session.session_id,                   // source_id
    'Session: ' + selected_session.session_id      // source_label
])
```

### Back Button (context-aware)

```python
# Show "Back to Source" when nav_source_view is set
v3.VBtn(
    v_if="nav_source_view",
    prepend_icon="mdi-arrow-left",
    click="trigger('navigate_back_to_source')"
):
    html.Span("{{ nav_source_label }}")

# Show simple back when no source
v3.VBtn(
    v_if="!nav_source_view",
    icon="mdi-arrow-left",
    click="show_detail = false; selected = null"
)
```

---

## Entity Navigation Matrix

| Source Entity | Target Entity | Back Label Pattern |
|---------------|---------------|-------------------|
| Session | Task | "Session: SESSION-ID" |
| Rule | Task | "Rule: RULE-ID" |
| Task | Session | "Task: TASK-ID" |
| Rule | Decision | "Rule: RULE-ID" |

---

## Validation Checklist

- [ ] Navigation trigger passes source context
- [ ] Target detail view shows contextual back button
- [ ] Back handler restores source entity selection
- [ ] Simple back button clears navigation context

---

## Test Coverage

**4 robot test file(s)** validate this rule:

| File | Scope |
|------|-------|
| `tests/robot/unit/executive_dropdown.robot` | unit |
| `tests/robot/unit/ui_constants.robot` | unit |
| `tests/robot/unit/ui_nav_context.robot` | unit |
| `tests/robot/unit/ui_navigation.robot` | unit |

```bash
# Run all tests validating this rule
robot --include UI-NAV-01-v1 tests/robot/
```
---

*Per GAP-UX-NAV-001: Entity navigation context preservation*
