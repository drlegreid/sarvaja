# SRVJ-FEAT-AUDIT-TRAIL-01 — P1 Design: Task Activity Audit Trail

**Date**: 2026-03-28
**Status**: DESIGN (no production code)
**Parent EPIC**: SRVJ-FEAT-AUDIT-TRAIL-01

---

## 1. Current State Map

### 1.1 File Inventory — What Writes Audit/Activity Data

| File | Lines | What It Captures | Where It Writes |
|------|-------|------------------|-----------------|
| `governance/stores/audit.py` | 270 | AuditEntry (actor, action, entity, old/new, rules, metadata) | `data/audit_trail.json` (7-day retention, 50K cap) |
| `governance/routes/audit.py` | 107 | REST interface to audit store | Reads from audit store |
| `governance/mcp_tools/audit.py` | 192 | MCP interface to audit store (4 tools) | Reads from audit store |
| `agent/governance_ui/data_access/monitoring.py` | 294 | Monitor events (event_type, source, severity) | `logs/monitor/YYYY-MM-DD.jsonl` + RuleMonitor (in-memory) |
| `governance/middleware/event_log.py` | ~30 | Business events (entity, action, details) | `governance.events` logger (container stdout) |
| `governance/middleware/access_log.py` | ~120 | HTTP requests (method, path, status, duration) | `logs/access.jsonl` (rotating 50MB) |
| `governance/mcp_logging.py` | ~300 | MCP tool calls (name, args, duration, errors) | `logs/mcp.jsonl` + `logs/mcp-metrics.jsonl` |
| `governance/routes/tasks/execution.py` | ~140 | Task execution events (claimed, started, completed...) | In-memory dict (100/task cap) |
| `governance/services/task_timeline.py` | 153 | Multi-session timeline (tool_calls, thoughts) | Derived from session data (no own storage) |
| `governance/services/task_comments.py` | 126 | Task comments (author, body) | In-memory + TypeDB best-effort |
| `agent/governance_ui/views/audit_view.py` | 286 | Audit dashboard UI | Reads from REST API |

### 1.2 Service-Level _monitor() Call Sites

`_monitor()` is defined in 10+ service files, all following the same pattern:
```
_monitor(action, entity_id, source) → log_monitor_event() → JSONL + RuleMonitor
```

**Task-specific call sites** (in `governance/services/`):

| File | Actions Captured |
|------|-----------------|
| `tasks.py` | CREATE, update_details |
| `tasks_mutations.py` | update (status), delete |
| `tasks_mutations_linking.py` | link_rule, link_session, link_document, unlink_document, link_evidence, link_commit, link_workspace |

### 1.3 record_audit() Call Sites (Task-Specific)

| File | Actions | Captures old/new? |
|------|---------|-------------------|
| `governance/services/tasks.py:276,329` | CREATE | No (both null) |
| `governance/services/tasks_mutations.py:339` | UPDATE | Yes (status only) |
| `governance/services/tasks_mutations.py:374` | DELETE | No |
| `governance/routes/tasks/execution.py:136` | Event type (CLAIMED, COMPLETED...) | No |
| `governance/routes/tasks/helpers.py:148` | Route-level audit | Varies |

**CRITICAL GAP**: `tasks_mutations_linking.py` does NOT call `record_audit()`.
Linking operations (link_rule, link_session, link_document, link_evidence, link_commit)
are captured by `_monitor()` only — they reach JSONL files but NOT the queryable audit store.

---

## 2. Data Flow Map

```
                          SERVICE LAYER
                              │
              ┌───────────────┼───────────────┐
              │               │               │
         _monitor()     record_audit()    log_event()
              │               │               │
              ▼               ▼               ▼
     log_monitor_event()  _audit_store    logger.info()
              │               │               │
       ┌──────┴──────┐       │               │
       │              │       ▼               ▼
       ▼              ▼   audit_trail.json  container
  RuleMonitor    JSONL files  │              stdout
  (in-memory)   (logs/monitor)│              (lost)
       │              │       │
       ▼              ▼       ▼
  Dashboard      Dashboard  REST API ──→ Dashboard (audit view)
  monitor feed   monitor    MCP tools ──→ Claude Code
                 feed
```

**Key observation**: Two parallel paths (`_monitor` → JSONL, `record_audit` → JSON) that never merge.
The audit store is the only queryable path, but it misses linking operations.

---

## 3. Existing MCP Audit Tools — Live Probe Results

### 3.1 audit_summary (no params)
```
total_entries: 1427
by_action_type: CREATE=428, UPDATE=945, BOOTSTRAP=41, DELETE=13
by_entity_type: task=85, session=1297, system=41, agent=4
by_actor: system=1066, code-agent=315, agent-1=32, agent-curator=8
retention_days: 7
```
**Assessment**: Functional. Shows cross-entity stats. Useful for system-level view.

### 3.2 audit_entity_trail (entity_id=SRVJ-FEAT-AUDIT-TRAIL-01)
```
count: 1
timeline_summary: actions=[CREATE], actors=[system], rules_applied=[]
entries: [{ audit_id, correlation_id, timestamp, actor_id=system,
            action_type=CREATE, entity_id, old_value=null, new_value=null,
            applied_rules=[], metadata={phase:P10, status:OPEN, source:rest-api} }]
```
**Assessment**: Functional but sparse. Only 1 entry for a task that was just created.
For mature tasks with updates/links, this would show more — but NOT linking operations (gap).

### 3.3 audit_query (entity_type=task, action_type=UPDATE, limit=5)
```
count: 5
entries: [
  { entity_id=BUG-002, old_value=OPEN, new_value=IN_PROGRESS, actor_id=code-agent },
  { entity_id=T-DONE-TEST-002, old_value=TODO, new_value=IN_PROGRESS, actor_id=code-agent },
  { entity_id=T-DONE-TEST-001, old_value=IN_PROGRESS, new_value=DONE, actor_id=system },
  { entity_id=P9-DETERM-011, old_value=OPEN, new_value=null, actor_id=system },  ← BUG
  { entity_id=P9-DETERM-003, old_value=OPEN, new_value=IN_PROGRESS, actor_id=code-agent }
]
```
**Assessment**: Functional. Captures status transitions with old→new. BUT:
- `new_value=null` on some UPDATEs (inconsistent recording bug)
- Only status changes tracked — no field-level diffs
- `applied_rules` always empty

### 3.4 audit_trace (correlation_id=CORR-20260327-162356-BA5381)
```
count: 1
affected_entities: { SRVJ-FEAT-AUDIT-TRAIL-01: [CREATE] }
```
**Assessment**: Functional but limited. Correlation IDs are per-request, so multi-entity
traces are rare unless a single operation touches multiple entities. More useful for
debugging than for activity feeds.

### 3.5 Tool Assessment Summary

| Tool | Functional? | Useful for Activity Feed? | Needs Redesign? |
|------|------------|--------------------------|-----------------|
| audit_query | Yes | Partial — missing linking ops | Extend, don't replace |
| audit_summary | Yes | No — system-level, not per-task | Keep as-is |
| audit_entity_trail | Yes | Yes — this IS the per-task feed | Extend with linking ops |
| audit_trace | Yes | No — correlation-based, not entity | Keep as-is |

---

## 4. Activity Types — What Exists vs What's Missing

### 4.1 Activity Types Captured Today

| Activity | Captured By | In Audit Store? | Queryable per Task? |
|----------|------------|-----------------|---------------------|
| Task CREATE | `record_audit` | Yes | Yes |
| Task UPDATE (status) | `record_audit` | Yes (with old/new) | Yes |
| Task DELETE | `record_audit` | Yes | Yes |
| Execution event (claim, start, complete, fail) | `record_audit` + execution store | Yes | Yes |
| Link rule | `_monitor` only | **NO** | No (JSONL only) |
| Link session | `_monitor` only | **NO** | No |
| Link document | `_monitor` only | **NO** | No |
| Unlink document | `_monitor` only | **NO** | No |
| Link evidence | `_monitor` only | **NO** | No |
| Link commit | `_monitor` only | **NO** | No |
| Link workspace | `_monitor` only | **NO** | No |
| Comment add | Not captured | **NO** | No |
| Comment delete | Not captured | **NO** | No |

### 4.2 What's Missing

| Gap | Impact | Difficulty to Fix |
|-----|--------|-------------------|
| **Linking ops not in audit store** | Can't answer "when was this rule linked?" | LOW — add `record_audit` calls to `tasks_mutations_linking.py` |
| **No field-level diffs** | Can't answer "what changed besides status?" | MEDIUM — need to diff task state before/after |
| **`applied_rules` always empty** | Can't answer "which rules influenced this?" | MEDIUM — need to wire rule engine output |
| **`new_value` sometimes null** | Inconsistent UPDATEs | LOW — fix `record_audit` call in mutations |
| **Comments not audited** | Can't see comment add/delete in trail | LOW — add `record_audit` to `task_comments.py` |
| **No session correlation** | Can't answer "which session made this change?" | MEDIUM — pass active session_id to `record_audit` |
| **7-day retention, no archive** | Historical trail lost | MEDIUM — add JSONL archive before retention purge |
| **Execution events ephemeral** | Lost on restart | MEDIUM — persist to TypeDB or file |

---

## 5. Design Proposal: Unified TaskActivity Model

### 5.1 Recommendation: Extend audit_store, Don't Replace It

The existing `AuditEntry` model in `governance/stores/audit.py` is **already 80% of what's needed**.
The right approach is to:
1. Fix the gaps (add `record_audit` to linking operations)
2. Enrich the data (session correlation, field-level diffs)
3. Surface it per-task in the detail view

**NOT recommended**: Creating a new `TaskActivity` model. This would duplicate data,
create sync problems, and waste the existing 270-line audit store + 4 MCP tools + REST API + dashboard.

### 5.2 Enriched AuditEntry (Backward-Compatible Extensions)

Proposed additions to `metadata` dict (no schema break):

```python
metadata = {
    # Existing fields (keep)
    "phase": "P10",
    "status": "OPEN",
    "source": "rest",

    # New fields (Phase 2)
    "session_id": "SESSION-2026-03-28-AUDIT-WORK",   # Which session triggered this
    "field_changes": {                                 # Field-level diffs
        "priority": {"from": "MEDIUM", "to": "HIGH"},
        "summary": {"from": "old title", "to": "new title"}
    },
    "linked_entity": {                                 # For link/unlink ops
        "type": "rule",
        "id": "TEST-GUARD-01",
        "action": "link"                               # or "unlink"
    }
}
```

### 5.3 New Action Types

Add to existing set (CREATE, UPDATE, DELETE, CLAIM, COMPLETE, VERIFY):

| New Action | When | Example |
|------------|------|---------|
| LINK | Entity linked to task | rule, session, document, evidence, commit |
| UNLINK | Entity unlinked from task | document unlinked |
| COMMENT | Comment added/deleted | resolution comment |
| TRANSITION | Status change (more specific than UPDATE) | OPEN → IN_PROGRESS |

---

## 6. Design Proposal: Storage Decision

### 6.1 Options Evaluated

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **A. Extend audit_store (JSON file)** | Already built, 4 MCP tools, REST API, dashboard, tested | 7-day retention, no TypeDB | **RECOMMENDED** |
| B. TypeDB relation | Permanent, queryable, linked to entity graph | Complex schema change, slow writes, no existing infra | Overkill for P2 |
| C. New append-only JSONL | Fast writes, unlimited history | Another storage system to maintain | Consider for archive |
| D. Hybrid A+C | Best of both | Two systems | **RECOMMENDED for archive** |

### 6.2 Recommended Architecture

```
record_audit() [existing]
    │
    ├──→ _audit_store (in-memory, queryable)     ← HOT (7-day, fast queries)
    ├──→ data/audit_trail.json (persist)          ← WARM (survives restart)
    └──→ logs/audit/YYYY-MM-DD.jsonl [NEW]        ← COLD (unlimited archive)
```

- **Hot path**: Existing audit store — no changes needed
- **Cold archive**: New JSONL append before `_apply_retention()` purges entries
- **TypeDB**: Defer to Phase 4+ if needed for graph queries

### 6.3 Overlap with task_health_check (P8)

P8's health check validates task data integrity (required fields, TypeDB sync).
The audit trail tracks **what changed and when**. They serve different purposes.
However, health check violations SHOULD be audit events (action_type=VERIFY).
This is already partially done in `execution.py:136` — just needs consistency.

---

## 7. Design Proposal: Surface Layer

### 7.1 Per-Task Audit Timeline (Dashboard)

Add a 4th tab in the task detail view alongside Execution/Timeline/Comments:

```
[ Execution Log ] [ Session Timeline ] [ Audit Trail ] [ Comments ]
```

**Data source**: `GET /api/audit/{task_id}` (already exists!)
**UI pattern**: Reuse VTimeline from `views/tasks/execution.py`
**Icon mapping**:
- CREATE → mdi-plus-circle (success)
- UPDATE/TRANSITION → mdi-swap-horizontal (warning)
- LINK → mdi-link-variant (info)
- UNLINK → mdi-link-variant-off (grey)
- DELETE → mdi-delete (error)
- COMMENT → mdi-comment (primary)

### 7.2 MCP Tool Enhancement

`audit_entity_trail` already returns the right data. Enhancements:
- Include linking operations (once they're in audit store)
- Add `activity_summary` field: "Created → 3 rules linked → status changed to IN_PROGRESS → 2 sessions linked → DONE"

### 7.3 REST Endpoint

No new endpoints needed. `GET /api/audit/{entity_id}` already exists and works.
Just need to ensure linking operations produce audit entries.

---

## 8. Phase 2-4 Scope Estimates

### Phase 2: Wire Missing Audit Points (SMALL — ~4 files, ~80 lines)

| Task | File | Estimate |
|------|------|----------|
| Add `record_audit` to all linking ops | `governance/services/tasks_mutations_linking.py` | +7 calls (~35 lines) |
| Add `record_audit` to comment add/delete | `governance/services/task_comments.py` | +2 calls (~10 lines) |
| Fix `new_value=null` bug in UPDATE | `governance/services/tasks_mutations.py` | ~5 lines |
| Add session_id to audit metadata | `governance/services/tasks_mutations.py` | ~10 lines |
| Add field-level diff capture | `governance/services/tasks_mutations.py` | ~20 lines |
| Tests for new audit points | `tests/unit/test_tasks_mutations_audit.py` (new) | ~150 lines |

### Phase 3: Audit Timeline in Task Detail (MEDIUM — ~6 files, ~200 lines)

| Task | File | Estimate |
|------|------|----------|
| Audit timeline UI component | `agent/governance_ui/views/tasks/audit_trail.py` (new) | ~120 lines |
| Add to task detail view | `agent/governance_ui/views/tasks/detail.py` | ~5 lines |
| Controller fetch function | `agent/governance_ui/controllers/tasks_crud.py` | ~20 lines |
| State variables | `agent/governance_ui/state/initial.py` | ~5 lines |
| Wire into parallel loader | `agent/governance_ui/controllers/tasks_crud.py` | ~10 lines |
| Tests | `tests/unit/test_task_audit_timeline.py` (new) | ~100 lines |

### Phase 4: Archive + Retention Enhancement (SMALL — ~2 files, ~50 lines)

| Task | File | Estimate |
|------|------|----------|
| JSONL archive before retention purge | `governance/stores/audit.py` | ~30 lines |
| Archive query function | `governance/stores/audit.py` | ~20 lines |
| Archive MCP tool | `governance/mcp_tools/audit.py` | ~30 lines |
| Tests | `tests/unit/test_audit_archive.py` (new) | ~80 lines |

### Optional Phase 5: TypeDB Persistence (LARGE — separate EPIC)

Would require new TypeDB schema (audit-entry entity, performed-audit relation),
migration script, dual-write from `record_audit()`, and query layer changes.
Recommend deferring unless graph-based audit queries become a requirement.

---

## 9. Summary: NIH Assessment

**The existing audit infrastructure provides ~80% of what's needed.**

The critical fix is surgical: add `record_audit()` calls to `tasks_mutations_linking.py`
(~35 lines of production code) to close the biggest gap. Everything else — the store,
the MCP tools, the REST API, the dashboard — already works.

Do NOT build a new system. Extend what exists.

| Component | Status | Action Needed |
|-----------|--------|---------------|
| AuditEntry model | 80% complete | Add LINK/UNLINK/COMMENT action types, enrich metadata |
| audit_store.py | Production-ready | Add JSONL archive (Phase 4) |
| 4 MCP audit tools | Fully functional | Enhance `audit_entity_trail` summary (Phase 3) |
| REST API (3 endpoints) | Fully functional | No changes needed |
| Audit dashboard view | Fully functional | No changes needed |
| Task detail audit tab | **Missing** | New VTimeline component (Phase 3) |
| Linking operations audit | **Missing** | Add `record_audit` calls (Phase 2) |
| Field-level diffs | **Missing** | Enrich UPDATE metadata (Phase 2) |
| Session correlation | **Missing** | Pass session_id in metadata (Phase 2) |
| Cold archive | **Missing** | JSONL append before retention purge (Phase 4) |
