# TASK-NAV-01-v1: Bidirectional Cross-Entity Navigation

| Field | Value |
|-------|-------|
| **Category** | Technical |
| **Priority** | MEDIUM |
| **Applicability** | MANDATORY |
| **Status** | ACTIVE |
| **Created** | 2026-03-21 |

## Directive

Cross-entity navigation MUST be bidirectional: every linked entity displayed in a detail view MUST be clickable and navigate to that entity's detail view with a way to return.

## Requirements

### 1. Task to Session
- linked_sessions displayed as clickable chips in task detail
- Clicking a session chip navigates to Sessions view with that session selected
- Session detail shows linked tasks with click-to-navigate back

### 2. Task to Document
- linked_documents displayed with type icons (evidence=beaker, plan=map, spec=document)
- Document chips are clickable where applicable
- Document type auto-detected from path prefix

### 3. Task to Rule
- linked_rules displayed as clickable chips
- Clicking navigates to Rules view with that rule selected

### 4. Navigation Context
- Back-button or breadcrumb preserves navigation origin
- `tasks_navigation.py` handles `navigate_to_session` trigger
- View switch uses `state.active_view` + entity selection state

## Anti-Patterns
- Displaying linked entity IDs as plain text (not clickable)
- One-way navigation (task→session but not session→task)
- Navigation that loses the user's scroll position or filter state

## Rationale

Phase 9d revealed that linked entities were displayed as static text, requiring users to manually navigate and search for related entities.

## Related Rules
- TASK-LIFE-01-v1 (task lifecycle includes linked entities)
- TASK-SEARCH-01-v1 (search results are navigable)
