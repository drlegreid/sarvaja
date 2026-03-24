# MCP-PERSIST-01-v1: MCP Write Persistence Requirement

| Field | Value |
|-------|-------|
| **Rule ID** | MCP-PERSIST-01-v1 |
| **Category** | OPERATIONAL |
| **Priority** | HIGH |
| **Status** | ACTIVE |
| **Applicability** | MANDATORY |
| **Created** | 2026-03-24 |

## Directive

MCP write operations (create, update, delete) MUST persist to TypeDB through the service layer. In-memory stores are cache only — TypeDB is the single source of truth. Entities created via MCP but not persisted to TypeDB are invisible to the REST API and dashboard.

---

## Required Pattern

```python
# CORRECT: MCP session_start persists through service layer
@mcp_tool("session_start")
def session_start(topic: str, session_type: str = "general"):
    session_id = f"SESSION-{date}-{topic}"
    # MUST call service layer which writes to TypeDB
    service.create_session(session_id, topic, session_type)
    # In-memory collector is supplementary cache only
    collector.track_session(session_id)
    return {"session_id": session_id}
```

## Persistence Rules

1. `session_start` MUST call `create_session()` service layer (writes to TypeDB)
2. `task_create` / `task_update` MUST go through service layer (already compliant)
3. In-memory stores (`_sessions_store`, `SessionCollector`) are cache — NOT source of truth
4. On persistence failure: log at WARNING level, do NOT block MCP response
5. REST API reads from TypeDB first, in-memory fallback only

---

## Verification

```bash
# After MCP session_start, verify TypeDB persistence
curl http://localhost:8082/api/sessions/{session_id}
# Should return 200, not 404
```

---

## Anti-Patterns (PROHIBITED)

| Don't | Do Instead |
|-------|-----------|
| Store only in SessionCollector | Call `create_session()` for TypeDB persistence |
| Assume in-memory = persisted | Verify via REST API after MCP write |
| Block MCP response on TypeDB failure | Log WARNING, return success with caveat |
| Skip service layer for "quick" writes | ALL writes go through service layer |

---

## Root Cause (P12 Incident, 2026-03-22)

MCP `session_start()` created sessions in `SessionCollector` (in-memory) but never called `create_session()` service layer. Sessions were invisible to `GET /api/sessions/{id}` which queries TypeDB. Session chip navigation returned 404 for MCP-created sessions.

---

## Related

- GOV-MCP-FIRST-01-v1 (TypeDB via MCP = single source of truth)
- DATA-PERSIST-01-v1 (Data persistence patterns)
- SESSION-EVID-01-v1 (Session evidence collection)

---

*Per EPIC-TASK-QUALITY-V3 P12: Session Navigation Fix*
