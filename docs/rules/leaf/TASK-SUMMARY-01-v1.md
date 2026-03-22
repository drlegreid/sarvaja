# TASK-SUMMARY-01-v1: Task Summary Field Requirements

| Field | Value |
|-------|-------|
| **Category** | Governance |
| **Priority** | MEDIUM |
| **Applicability** | MANDATORY |
| **Status** | ACTIVE |
| **Created** | 2026-03-21 |

## Directive

Every task MUST have a structured `summary` field (<=80 chars) that captures the task's intent in the format `domain > action`.

## Requirements

### 1. Summary Field
- Summary is a separate field from description/body
- Maximum 80 characters
- Format: concise intent statement (e.g., "governance > fix task-document linking relation")
- If not provided at creation time, auto-generated from description

### 2. Auto-Generation
- `_generate_summary()` in service layer creates summary from first sentence of description
- Truncated to 80 chars with "..." suffix if longer
- Does not overwrite explicitly provided summaries

### 3. Layer Propagation
- TypeDB: `task-summary` attribute on `task` entity
- Pydantic: `summary: Optional[str]` on TaskCreate/Update/Response
- MCP: `summary` parameter on `task_create` and `task_update`
- Dashboard: Summary column in task list table (replaces raw description)

## Rationale

Description fields were being overloaded — used as both detailed body and display label. Summary provides a concise, scannable label while description retains full detail.

## Related Rules
- TASK-LIFE-01-v1 (task lifecycle)
- META-TAXON-01-v1 (task taxonomy)
