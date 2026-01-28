# RECOVER-AMNES-02-v1: AMNESIA Hierarchical Recovery

**Category:** `maintenance` | **Priority:** CRITICAL | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Location:** [RULES-STABILITY.md](../operational/RULES-STABILITY.md)
> **Tags:** `recovery`, `amnesia`, `context`, `hierarchy`

---

## Directive

Context recovery MUST use hierarchical sources in order:

1. **TODO.md** - Current sprint tasks and immediate context
2. **R&D-BACKLOG.md** - Active R&D items and phase information
3. **Session Summary** - Most recent session evidence
4. **claude-mem (ChromaDB)** - Semantic memory search
5. **GAP-INDEX.md** - Open gaps and known issues

---

## Recovery Protocol

```
1. Read TODO.md for current tasks
2. Read R&D-BACKLOG.md for project phase
3. Query recent session evidence
4. Search claude-mem for relevant context
5. Check GAP-INDEX.md for blockers
6. NEVER ask user "what were we doing?"
```

---

## Validation

- [ ] Hierarchical sources checked in order
- [ ] Context recovered autonomously
- [ ] No user queries for context
- [ ] Recovery evidence logged

---

*Per RECOVER-AMNES-01-v1: AMNESIA Protocol*
