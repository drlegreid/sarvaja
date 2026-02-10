# ARCH-BACKFILL-01-v1: Backfill Tool Registration

**Category:** `technical` | **Priority:** MEDIUM | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Tags:** `architecture`, `backfill`, `mcp`, `evidence`

---

## Directive

Evidence backfill tools (backfill_scan_*, backfill_execute_*) MUST be registered in the appropriate MCP server (gov-sessions or gov-tasks). Backfill operations MUST default to dry_run=True to prevent accidental data modification. Audit trail MUST record all backfill executions.

---

## Validation

- [ ] Backfill tools registered in gov-sessions or gov-tasks MCP server
- [ ] `dry_run=True` is the default for all backfill operations
- [ ] Audit trail records backfill executions with entity counts
- [ ] Backfill scan produces preview before execution

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Execute backfill without dry run | Always `dry_run=True` first, review output |
| Skip audit trail for backfill | Record BACKFILL action in audit store |
| Register backfill in wrong MCP | Use gov-sessions for session backfill, gov-tasks for tasks |
| Allow backfill to overwrite live data | Backfill only fills gaps, never overwrites |

---

*Per ARCH-MCP-02-v1: MCP Server Split Architecture*
