---
description: Quick bug report with auto-generated ID (META-TAXON-01-v1)
allowed-tools: mcp__gov-tasks__task_create, mcp__gov-tasks__taxonomy_get, mcp__gov-sessions__session_start
---

# Quick Bug Report

Create a bug task with auto-generated ID (e.g. BUG-042).

## Steps

1. Ask user for:
   - **Description**: What's broken? (required)
   - **Priority**: CRITICAL / HIGH / MEDIUM / LOW (default: HIGH)
   - **Phase**: Which phase? (default: current)
   - **Component**: Affected file/module (optional, goes into body)

2. Call `task_create` with:
   - `name`: User's description
   - `task_type`: "bug"
   - `priority`: User's choice or HIGH
   - `task_id`: "" (auto-generates BUG-{NNN})
   - `description`: Component/context details if provided

3. Report back with the auto-generated ID and next steps.

## Example

```
User: /bug
You: What's the bug?
User: Session duration shows negative values
You: Priority? (default: HIGH)
User: CRITICAL
→ task_create(name="Session duration shows negative values", task_type="bug", priority="CRITICAL")
→ Created BUG-043 successfully
```
