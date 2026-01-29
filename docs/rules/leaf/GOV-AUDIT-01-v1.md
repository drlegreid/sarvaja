# GOV-AUDIT-01-v1: Governance Sync Protocol

**Category:** `governance` | **Priority:** HIGH | **Status:** DRAFT | **Type:** OPERATIONAL

> **Tags:** `governance`, `sync`, `sessions`, `skills`

---

## Directive

Agents MUST synchronize governance artifacts (skills, sessions, decisions) between local workspace and TypeDB using the sync protocol. Divergence between workspace files and TypeDB state MUST be detected and resolved.

---

## Sync Protocol

| Source | Target | Tool | Frequency |
|--------|--------|------|-----------|
| `TODO.md` | TypeDB tasks | `workspace_capture_tasks` | On session start |
| `docs/rules/**/*.md` | TypeDB rules | `workspace_scan_rule_documents` | On rule changes |
| `evidence/*.md` | TypeDB sessions | `session_link_evidence` | On evidence creation |
| TypeDB state | Workspace files | `governance_sync_status` | Periodic check |

---

## Divergence Detection

Use `governance_sync_status` to detect:
- Rules in files but not in TypeDB
- Rules in TypeDB but missing files
- Task status mismatches between files and TypeDB
- Session-evidence file linkage gaps

---

## Tool Bindings (GOV-BIND-01-v1)

| Verification | Tool | Example |
|-------------|------|---------|
| Sync status | `mcp__gov-tasks__governance_sync_status` | Check divergence |
| Task sync | `mcp__gov-tasks__workspace_capture_tasks` | Sync tasks to TypeDB |
| Rule scan | `mcp__gov-tasks__workspace_scan_rule_documents` | Scan rule docs |

---

## Validation

- [ ] `governance_sync_status` called at session start
- [ ] Divergence items reviewed and resolved
- [ ] No critical rules missing from TypeDB
- [ ] Task statuses aligned between workspace and TypeDB

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
*Per GOV-BIND-01-v1: Tool bindings specified*
