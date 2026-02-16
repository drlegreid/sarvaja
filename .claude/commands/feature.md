---
description: Quick feature request with auto-generated ID (META-TAXON-01-v1)
allowed-tools: mcp__gov-tasks__task_create, mcp__gov-tasks__taxonomy_get, mcp__gov-sessions__session_start
---

# Quick Feature Request

Create a feature task with auto-generated ID (e.g. FEAT-012).

## Steps

1. Ask user for:
   - **Description**: What feature is needed? (required)
   - **Priority**: CRITICAL / HIGH / MEDIUM / LOW (default: MEDIUM)
   - **Phase**: Which phase? (default: current)
   - **Acceptance criteria**: How do we know it's done? (optional, goes into body)

2. Call `task_create` with:
   - `name`: User's description
   - `task_type`: "feature"
   - `priority`: User's choice or MEDIUM
   - `task_id`: "" (auto-generates FEAT-{NNN})
   - `description`: Acceptance criteria if provided

3. Report back with the auto-generated ID and next steps.

## Example

```
User: /feature
You: What feature do you need?
User: Add histogram date filtering for sessions table
You: Priority? (default: MEDIUM)
User: HIGH
-> task_create(name="Add histogram date filtering for sessions table", task_type="feature", priority="HIGH")
-> Created FEAT-013 successfully
```
