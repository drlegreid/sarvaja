# GOV-MCP-FIRST-01-v1: MCP-First Data Management

**Category:** `governance` | **Priority:** LOW | **Status:** SUSPENDED | **Type:** OPERATIONAL
**Enforcement:** SUSPENDED (2026-03-23 — MCP task system unstable, reverted to TodoWrite)

> **Location:** [RULES-GOVERNANCE.md](../governance/RULES-GOVERNANCE.md)
> **Tags:** `mcp`, `governance`, `typedb`, `source-of-truth`, `enforcement`
> **Related:** ARCH-MCP-01-v1 (MCP Usage Protocol), DECISION-003 (TypeDB-First)
> **Absorbs:** MCP-002-A (TodoWrite persistence to TypeDB)

---

## Directive

TypeDB (via MCP tools) is the SINGLE SOURCE OF TRUTH for tasks, rules, and sessions.

1. Tasks MUST be created/updated via `mcp__gov-tasks__task_create/task_update`
2. Rules MUST be managed via `mcp__gov-core__rule_create/rule_update`
3. Sessions MUST be tracked via `mcp__gov-sessions__session_start/session_end`
4. `TodoWrite` is for progress DISPLAY only — auto-synced to TypeDB via hook
5. `TODO.md` is FALLBACK when MCP services are confirmed unavailable
6. Leaf docs on disk are reference/metadata — TypeDB is authoritative

---

## Source of Truth Hierarchy

```
LEVEL 1 (Authoritative): TypeDB via MCP tools
LEVEL 2 (Sync target):   ChromaDB (semantic search)
LEVEL 3 (Fallback):      TODO.md, evidence/*.md (emergency only)
LEVEL 4 (Reference):     docs/rules/leaf/*.md (metadata + samples)
```

---

## Enforcement Mechanisms

| Layer | Mechanism | Status |
|-------|-----------|--------|
| CLAUDE.md | "Task Management" section mandates MCP-first | ACTIVE |
| PostToolUse:TodoWrite | `todo_sync.py` auto-syncs to TypeDB API | ACTIVE |
| PostToolUse | `mcp_usage_check.py` health-aware enforcement | ACTIVE |
| SessionStart | Healthcheck includes MCP usage + health summary | ACTIVE |
| Service Layer | `governance/services/todo_sync.py` TypeDB → TODO.md sync | ACTIVE |

### Health-Aware Enforcement (Phase 8)

The `mcp_usage_checker.py` hook now checks MCP API health before issuing warnings:

- **MCP healthy** + TodoWrite without gov-tasks → **MANDATORY warning** with guidance
- **MCP down** → **Fallback mode** — TodoWrite is legitimate, no warnings
- Health check cached for 60s to avoid hook latency

### TypeDB → TODO.md Sync

`governance/services/todo_sync.py` provides one-way sync:

- `sync_typedb_to_todomd()` — fetches tasks from API, writes formatted TODO.md
- `sync_fallback_to_typedb()` — imports fallback tasks back on MCP recovery

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Edit TODO.md directly for task management | `mcp__gov-tasks__task_create()` |
| Edit docs/rules/*.md to create rules | `mcp__gov-core__rule_create()` |
| Create evidence files manually | `mcp__gov-sessions__session_start()` |
| Assume TodoWrite = persistent storage | MCP tools; TodoWrite is display only |
| Rely on todo_sync.py as primary sync | Use MCP directly; hook is best-effort backup |
| Ignore MCP-FIRST warnings | Switch to MCP tools when MCP is healthy |

---

## Validation

- [ ] Tasks created via MCP tools, not file edits
- [ ] TODO.md only updated as MCP fallback or via sync service
- [ ] mcp_usage_check.py warnings visible when MCP healthy but unused
- [ ] No warnings in fallback mode (MCP down)
- [ ] governance_sync_status() shows no divergence

---

*Per DECISION-003: TypeDB-First Architecture*
*Per ARCH-MCP-01-v1: MCP Usage Protocol*
*Updated: 2026-03-21 (EPIC-GOV-TASKS-V2 Phase 8 — MANDATORY enforcement)*
