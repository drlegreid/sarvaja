# TODO Index - Sarvaja

**Last Updated:** 2026-01-20 | **Source of Truth:** TypeDB via MCP tools

---

## Quick Commands

```bash
# Get current backlog (TypeDB source)
mcp__gov-tasks__backlog_get(limit=20)

# Get task by ID
mcp__gov-tasks__task_get(task_id="P12.1")

# List all tasks
mcp__gov-tasks__tasks_list()

# R&D items
mcp__gov-sessions__governance_list_tasks(phase="RD")
```

---

## Data Sources

| Need | Tool/File |
|------|-----------|
| **Backlog** | `backlog_get()` |
| **Gaps** | [GAP-INDEX.md](docs/gaps/GAP-INDEX.md) |
| **R&D** | [R&D-BACKLOG.md](docs/backlog/R&D-BACKLOG.md) |
| **Rules** | `rules_query(status="ACTIVE")` |

---

## Session Start Protocol

```
1. health_check()         → Verify TypeDB + ChromaDB
2. backlog_get(limit=10)  → Load prioritized gaps
3. Load to todo list      → Track progress
```

---

## Data Architecture

```
TypeDB (Source of Truth)
    └── task entities (102 total)
         └── linked to sessions, rules, evidence

TODO.md (View)
    └── Index pointing to MCP tools
    └── Human-readable quick reference

evidence/*.md (Immutable)
    └── Implementation details per R&D item
```

---

*Per DATA-ARCH-CLEANUP DSM: TypeDB = source of truth.*
*Per RULE-024: AMNESIA Protocol - recovery-friendly documents.*

## Provisional Tasks (2026-01-23)

- [x] GAP-CONTEXT-ROT-002: ✅ RESOLVED - Added entropy reset to SessionStart hooks
- [x] GAP-HOOK-RECOVERY-001: ✅ RESOLVED - Implemented `podman start` before `compose up` pattern
- [x] GAP-CONTEXT-ROT-CHECK: ✅ RESOLVED - Added previous session audit + warning on reset
- [x] GAP-API-500-001: ✅ RESOLVED - Documented as external tracking gap
- [x] DOC-CLAUDE-MD-FALLBACK: ✅ RESOLVED - Added to CLAUDE.md § "Provisional Tasks"

**Fixes Applied (2026-01-23):**
- `settings.local.json`: Added `entropy_cli.py --reset` to SessionStart
- `containers.py`: Added `_try_start_existing()` for resume-first recovery
- `entropy_cli.py`: Enhanced reset with previous session audit trail
