# DATA-PERSIST-01-v1: Session Persistence Integrity

**Category:** `governance` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** GOVERNANCE

> **Tags:** `data-integrity`, `sessions`, `persistence`, `typedb`

---

## Directive

Sessions MUST be visible in the dashboard regardless of TypeDB persistence outcome. When TypeDB insert fails, the session MUST remain in `_sessions_store` with `persistence_status="memory_only"` and be included in `get_all_sessions_from_typedb()` results via orphan merge. Persistence failures MUST be logged at ERROR level, not WARNING.

---

## Implementation

Orphan merge is implemented in `governance/stores/typedb_access.py:get_all_sessions_from_typedb()`:
1. TypeDB sessions tagged `persistence_status="persisted"`
2. `_sessions_store` sessions not in TypeDB tagged `persistence_status="memory_only"`
3. Both sets returned in combined result when `allow_fallback=True`

Retry is via `governance/services/sessions.py:sync_pending_sessions()`:
- Iterates `_sessions_store`, checks each against TypeDB
- Inserts missing sessions, counts synced/failed/already_persisted

---

## Validation

- [ ] `persistence_status` present on every session returned by list_sessions()
- [ ] Orphan sessions (memory-only) visible in dashboard
- [ ] `sync_pending_sessions()` retries failed inserts
- [ ] Persistence failures logged at ERROR level

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Log persistence failures at WARNING | Log at ERROR level for visibility |
| Return only TypeDB sessions from list | Merge orphan sessions from _sessions_store |
| Silently lose sessions on TypeDB failure | Tag as memory_only and retry later |
| Assume TypeDB is always available | Design for graceful degradation |

---

*Per SESSION-EVID-01-v1: Evidence-Based Governance*
