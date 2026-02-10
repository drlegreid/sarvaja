# DATA-LINK-01-v1: Task-Session Auto-Linking

**Category:** `governance` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** GOVERNANCE

> **Tags:** `data-integrity`, `tasks`, `sessions`, `auto-linking`

---

## Directive

Tasks created during a session MUST be automatically linked to that session via the completed-in relation. The MCP task_create tool MUST accept an optional session_id parameter and link tasks to the active session when available. Orphan tasks (no linked sessions) indicate a workflow violation.

---

## Implementation

Auto-linking is implemented in `governance/services/tasks.py:create_task()`:
1. If `linked_sessions` is not provided, `_get_active_session_id()` finds the most recent ACTIVE session
2. Task is linked to that session automatically
3. Links are persisted to TypeDB via `client.link_task_to_session()`

---

## Validation

- [ ] H-TASK-005: Worked tasks (IN_PROGRESS/DONE) have linked_sessions
- [ ] `create_task()` auto-links to active session when available
- [ ] TypeDB relations persist across container restarts
- [ ] Explicit linked_sessions param is preserved (not overwritten)

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Create tasks without session context | Auto-link via `_get_active_session_id()` |
| Store linked_sessions only in memory | Persist to TypeDB via relations |
| Overwrite explicit session links | Only auto-link when `linked_sessions` is None |
| Check all tasks for linkage | Only check worked tasks (IN_PROGRESS/DONE) |

---

*Per SESSION-EVID-01-v1: Evidence-Based Governance*
