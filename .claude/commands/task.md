---
description: Rapid task creation with type selection and auto-ID (META-TAXON-01-v1)
allowed-tools: mcp__gov-tasks__task_create, mcp__gov-tasks__taxonomy_get
---

# Rapid Task Creation

Create a task with type selection and auto-generated ID.

## Steps

1. Call `taxonomy_get()` to show available types and prefixes.

2. Ask user for:
   - **Type**: bug / feature / chore / research / gap / epic / test
   - **Description**: What needs to be done? (required)
   - **Priority**: CRITICAL / HIGH / MEDIUM / LOW (default: MEDIUM)
   - **Phase**: P10, P11, P12, RD, etc. (default: P10)

3. Call `task_create` with:
   - `name`: User's description
   - `task_type`: Selected type
   - `priority`: User's choice
   - `task_id`: "" (auto-generates {PREFIX}-{NNN})
   - `phase`: User's choice

4. Report the auto-generated ID.

## Type → ID Prefix Mapping

| Type | Prefix | Example |
|------|--------|---------|
| bug | BUG | BUG-001 |
| feature | FEAT | FEAT-012 |
| chore | CHORE | CHORE-003 |
| research | RD | RD-007 |
| gap | GAP | GAP-015 |
| epic | EPIC | EPIC-004 |
| test | TEST | TEST-008 |
