# TASK-HANDOVER-01-v1: Task ID Reference for LLM Handover

| Field | Value |
|-------|-------|
| **Rule ID** | TASK-HANDOVER-01-v1 |
| **Category** | operational |
| **Priority** | HIGH |
| **Applicability** | MANDATORY |
| **Status** | ACTIVE |
| **Created** | 2026-03-21 |

## Directive

Sessions and prompts MUST reference tasks by ID only (e.g., `FEAT-042`, `BUG-003`).
Task descriptions, bodies, and details MUST NOT be repeated in session prompts or handover context.

## Rationale

Repeating full task descriptions in every session prompt wastes context tokens and
creates divergence when the canonical description is updated in TypeDB but stale
copies persist in prompts. Task IDs are stable, short, and queryable.

## Rules

1. **ID-only references**: When referencing a task in a session prompt, plan file,
   or agent handover, use the task ID. Example: `Work on FEAT-042` not
   `Work on "Add OAuth2 authentication flow with PKCE support"`.

2. **On-demand resolution**: The receiving agent queries TypeDB for the full
   description, body, and linked documents when it needs context:
   - `task_get(task_id)` for description + status
   - `task_get_details(task_id)` for business/design/architecture/test sections
   - `task_get_documents(task_id)` for linked document paths

3. **Attached documents provide depth**: Plans, specs, and evidence files linked
   via `task_link_document()` provide deep context without bloating prompts.

4. **Summary field**: The `summary` field (max 80 chars) provides a structured
   one-line intent for quick scanning without full description lookup.

## Examples

### Good
```
EPIC-GOV-TASKS-V2 Phase 9c. Plan: gleaming-drifting-pearl.md.
Work on FEAT-042, BUG-003, SPEC-001.
```

### Bad
```
Work on the task to add OAuth2 authentication flow with PKCE support
for the governance API, ensuring backward compatibility with existing
session tokens and implementing refresh token rotation...
```

## Linked Rules
- GOV-MCP-FIRST-01-v1 (TypeDB as source of truth)
- META-TAXON-01-v1 (task ID auto-generation)
