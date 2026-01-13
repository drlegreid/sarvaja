# SAFETY-DESTR-01-v1: Destructive Command Prevention

**Category:** `safety` | **Priority:** CRITICAL | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Legacy ID:** RULE-042
> **Location:** [RULES-STANDARDS.md](../operational/RULES-STANDARDS.md)
> **Tags:** `safety`, `destructive`, `prevention`, `confirmation`

---

## Directive

Agents MUST NEVER execute destructive commands without explicit user confirmation. Destructive means data loss or irreversible state change.

---

## Prohibited Commands (ALWAYS REQUIRE CONFIRMATION)

| Command Pattern | Risk | Alternative |
|----------------|------|-------------|
| `rm -rf /path` | Data loss | `rm -i` or explicit file list |
| `podman system reset` | Wipes all images | Restart specific containers |
| `git reset --hard` | Loses uncommitted work | `git stash` first |
| `DROP TABLE` / `DELETE FROM` | Database loss | Backup first |
| `--force` on any destructive op | Bypasses safety | Remove --force |

---

## Before ANY Destructive Action

1. **CHECK actual state** - `podman ps`, `ls`, `git status`
2. **QUERY memory** - `chroma_query_documents(["recent infrastructure changes"])`
3. **READ DEVOPS.md** - Correct commands for environment
4. **ASK user** - If uncertain, use `AskUserQuestion`

---

## Recovery First Principle

| Symptom | DON'T | DO Instead |
|---------|-------|-----------|
| Container not responding | Reset everything | Restart specific service |
| MCP failing | Wipe and rebuild | Check logs, fix config |
| TypeDB errors | Delete data | Query for specific issue |

---

## GAP Trigger

Per GAP-DESTRUCT-001: Executing destructive commands without verification creates CRITICAL gap.

---

## Enforcement

**PreToolUse Hook**: `.claude/hooks/pre_bash_check.py`

The hook automatically:
1. Checks all Bash commands for destructive patterns
2. **BLOCKS** catastrophic commands (rm -rf /, fork bombs)
3. **WARNS** about risky commands with safer alternatives
4. **LOGS** all destructive attempts to `.destructive_log/`

**Checker Module**: `.claude/hooks/checkers/destructive.py`

---

## Validation

- [x] Destructive commands require confirmation (PreToolUse hook)
- [x] Audit trail for destructive attempts (.destructive_log/)
- [ ] State checked before action
- [ ] Backups created when needed

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
