# MCP-RESTART-AUTO-01-v1: Autonomous MCP Server Restart

**Category:** `operational` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Legacy ID:** RULE-051
> **Location:** [RULES-OPERATIONAL.md](../RULES-OPERATIONAL.md)
> **Tags:** `mcp`, `restart`, `automation`, `testing`, `safety`

---

## Directive

Agents MAY autonomously restart MCP servers when ALL of the following conditions are met:
1. Changes are **low-risk** (code modifications only, no schema changes)
2. Changes are **proven** with multilayered tests (unit + integration)
3. No **destructive** operations pending (per SAFETY-DESTR-01-v1)

---

## Low-Risk Change Criteria

| Change Type | Risk Level | Auto-Restart? |
|-------------|------------|---------------|
| MCP tool implementation update | LOW | YES |
| Query function modification | LOW | YES |
| New attribute addition | LOW | YES |
| TypeDB schema change | HIGH | NO - manual only |
| TypeDB data migration | HIGH | NO - manual only |
| Infrastructure changes | HIGH | NO - manual only |

---

## Required Test Layers

Before automatic restart, verify:

| Layer | What to Test | Tool |
|-------|--------------|------|
| 1. Syntax | No import/syntax errors | `python -m py_compile <file>` |
| 2. Unit | Function logic correct | `pytest tests/unit/` |
| 3. Integration | MCP tools work end-to-end | `governance_health()` after restart |

---

## Restart Protocol

```
1. PRE-CHECK: Verify all test layers pass
2. NOTIFY: Log restart intent (session_thought or output)
3. EXECUTE: Issue restart command
4. VERIFY: Call governance_health() within 30s
5. ROLLBACK: If health fails, alert user immediately
```

---

## Anti-Patterns (PROHIBITED)

| Don't | Do Instead |
|-------|-----------|
| Restart without testing | Run all test layers first |
| Restart during schema migration | Wait for manual approval |
| Silent restart | Log intent before restart |
| Skip health verification | Always verify post-restart |

---

## Validation

- [ ] All changes are low-risk (no schema/infra)
- [ ] Syntax check passed
- [ ] Unit tests passed
- [ ] Integration ready for post-restart check

---

*Per WORKFLOW-AUTO-02-v1: Autonomous Task Continuation*
*Per SAFETY-DESTR-01-v1: Destructive Action Protection*
