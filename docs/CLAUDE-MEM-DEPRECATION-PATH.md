# Claude-Mem Deprecation Path

**Date:** 2024-12-27
**Status:** PLANNED
**Related:** DECISION-003 (TypeDB-First), P11.4 (Session Integration)

---

## Summary

This document outlines the deprecation path for claude-mem (ChromaDB-based memory MCP) as we transition to the Docker agent platform with TypeDB as the primary data store.

**Trigger:** Deprecation begins when Docker agent platform is operational.

---

## Current State

### Claude-Mem Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Current: Claude-Mem (ChromaDB)                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Claude Code (Claude Agent) ←──── MCP ────→ Claude-Mem (ChromaDB:8001)  │
│       │                                           │                      │
│       └── Session memory ──────────────────────→  │                      │
│       └── Project memories ────────────────────→  │                      │
│       └── Semantic search ─────────────────────→  │                      │
│                                                                          │
│  Files: ~/.claude-mem/                                                   │
│  Collection: claude_memories                                             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Claude-Mem Usage Patterns

| Pattern | Frequency | Purpose |
|---------|-----------|---------|
| Session evidence | HIGH | Store session summaries, decisions |
| Project context | HIGH | Store project-specific knowledge |
| Semantic search | MEDIUM | Query past memories |
| Recovery (RULE-024) | HIGH | AMNESIA protocol context recovery |

### Current Integration Points

| File | Usage |
|------|-------|
| `governance/session_memory.py` | SessionMemoryManager with claude-mem |
| `agent/sync_agent.py` | Agent task context |
| `.claude/CLAUDE.md` | Memory query patterns |

---

## Target State

### Governance UI + TypeDB Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Target: Governance UI + TypeDB                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Docker Agent Platform                                                   │
│       │                                                                  │
│       ├── Governance Dashboard (Trame:8081)                             │
│       │       └── Session Viewer                                        │
│       │       └── Evidence Browser                                      │
│       │       └── Task Management                                       │
│       │                                                                  │
│       ├── REST API (FastAPI:8082)                                       │
│       │       └── Session CRUD                                          │
│       │       └── Evidence CRUD                                         │
│       │       └── Task/Rule/Decision CRUD                               │
│       │                                                                  │
│       └── TypeDB (1729)                                                 │
│               └── work-session entity                                   │
│               └── evidence-file entity                                  │
│               └── Vector embeddings (P7.1)                              │
│               └── Inference rules                                       │
│                                                                          │
│  Semantic Search: TypeDB vector store (governance/vector_store.py)      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Replacement Mapping

| Claude-Mem Feature | Replacement | Status |
|-------------------|-------------|--------|
| Session storage | TypeDB work-session entity | ✅ Ready |
| Evidence storage | TypeDB evidence-file entity | ✅ Ready |
| Semantic search | TypeDB vector_store.py | ✅ Ready |
| Project memories | TypeDB + governance_evidence_search MCP | ✅ Ready |
| AMNESIA recovery | governance_list_sessions, governance_get_session | ✅ Ready |

---

## Migration Steps

### Phase 1: Parallel Operation (Current)

Both systems operational:
- Claude-mem: Active for Claude Code sessions
- TypeDB: Active for governance data

**Status:** IN PROGRESS

### Phase 2: Data Migration

1. **Extract claude-mem data**
   ```python
   # Query all memories
   memories = chroma_query_documents(
       collection_name="claude_memories",
       query_texts=["sim-ai"],
       n_results=1000
   )
   ```

2. **Transform to TypeDB format**
   ```python
   # For each memory, create work-session + evidence
   for memory in memories:
       session = {
           "session_id": f"MIGRATED-{memory['id']}",
           "session_name": memory.get('metadata', {}).get('title', 'Migrated'),
           "description": memory['document']
       }
       # Insert into TypeDB
       client.insert_session(session)
   ```

3. **Verify data integrity**
   ```python
   # Use data_integrity.py
   from governance.data_integrity import validate_edge_to_edge
   report = validate_edge_to_edge()
   assert report["summary"]["integrity_score"] >= 95
   ```

### Phase 3: Claude-Mem Read-Only

1. **Update CLAUDE.md**
   - Remove claude-mem quick reference
   - Add governance MCP quick reference

2. **Update session_memory.py**
   - Switch SessionMemoryManager to TypeDB-only mode
   - Keep claude-mem query as fallback for historical data

3. **Update recovery protocol (RULE-024)**
   - Primary: governance_list_sessions, governance_get_session
   - Fallback: claude-mem for pre-migration memories

### Phase 4: Deprecation

**Trigger:** Docker agent platform stable + all memories migrated

1. **Remove claude-mem MCP from config**
2. **Archive ~/.claude-mem/ data**
3. **Update documentation**
4. **Remove claude-mem code references**

---

## Timeline

| Phase | Trigger | Duration |
|-------|---------|----------|
| Parallel | Now | Until Docker agent platform stable |
| Migration | Docker agents operational | 1-2 hours |
| Read-Only | Migration verified | 1 week observation |
| Deprecation | No issues in read-only | Permanent |

---

## Deprecation Checklist

### Pre-Deprecation

- [ ] Docker agent platform operational
- [ ] All claude-mem data migrated to TypeDB
- [ ] Data integrity validation passes (95%+ score)
- [ ] Governance UI can display all session/evidence data
- [ ] AMNESIA recovery works with governance MCP
- [ ] 1 week in read-only mode without issues

### Deprecation Actions

- [ ] Remove `claude-mem` from MCP server config
- [ ] Archive `~/.claude-mem/` to backup location
- [ ] Remove claude-mem references from CLAUDE.md
- [ ] Update session_memory.py to remove claude-mem code
- [ ] Update sync_agent.py to use governance MCP only
- [ ] Run full test suite to verify no regressions

### Post-Deprecation

- [ ] Document migration completion
- [ ] Update R&D-BACKLOG.md to mark complete
- [ ] Close related gaps (GAP-PROC-001, GAP-ARCH-011)

---

## Rollback Plan

If issues arise during deprecation:

1. **Restore claude-mem MCP config**
2. **Re-enable claude-mem in session_memory.py**
3. **Document issues for resolution**
4. **Retry deprecation after fixes**

---

## Evidence

- TypeDB session schema: governance/schema.tql (lines 77-88)
- Vector store: governance/vector_store.py
- Session memory: governance/session_memory.py
- Data integrity: governance/data_integrity.py (30 tests)

**Per RULE-012 DSP:** Claude-mem deprecation path documented.
