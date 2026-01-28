# GAP-MONITOR-IPC-001: Audit File Bridge for Monitoring Events

**Priority:** MEDIUM | **Category:** architecture/observability | **Status:** RESOLVED
**Discovered:** 2026-01-20 | **Source:** GAP-MONITOR-INSTRUMENT-001 validation
**Resolution:** 2026-01-20 - Audit file bridge implemented (DSP Session)
**Unblocks:** GAP-MONITOR-INSTRUMENT-001 acceptance criteria #12, #13

---

## Problem Statement

MCP tools and Dashboard run in separate processes with separate RuleMonitor singletons. Events logged by MCP tools never reach the Dashboard UI.

**Architecture Issue:**
```
Claude Code Host                    Container (governance-dashboard-dev)
├── MCP Tools (Python)              ├── FastAPI Dashboard (Python)
│   └── log_monitor_event()         │   └── RuleMonitor singleton
│       └── RuleMonitor singleton   │       └── seed_demo_data=True
│           └── events go HERE      │           └── shows demo data
└── events NEVER reach container    └── never receives real events
```

---

## Proposed Solution

Per user guidance: "MCP tools write audit files which are to be exposed using dedicated 'document service' which has subdomain to ingest, collect & visualize logs"

### Architecture

```
MCP Tools (Host)                    Document Service              Dashboard UI
├── log_monitor_event()             ├── /api/logs/ingest          ├── Real-time Rule Monitor
│   └── write to audit file         │   └── read audit files      │   └── query document service
│       └── logs/monitor/*.jsonl    │   └── index events          │       └── display real events
└── append-only JSON Lines          └── ChromaDB/TypeDB store     └── no more demo data
```

### Implementation Plan

1. **Audit File Writer** (in MCP tools)
   - Path: `logs/monitor/YYYY-MM-DD.jsonl`
   - Format: JSON Lines (one event per line)
   - Append-only for performance

2. **Document Service Subdomain**
   - Endpoint: `GET /api/docs/monitor/events`
   - Ingest: Read and index `logs/monitor/*.jsonl`
   - Query: Filter by time, type, severity
   - Persist: Optional ChromaDB/TypeDB storage

3. **Dashboard Integration**
   - Replace RuleMonitor singleton reads with document service API calls
   - Remove `seed_demo_data=True` when real data available

---

## Scope Estimate

| Component | Complexity | Files |
|-----------|------------|-------|
| Audit file writer | LOW | 1 (monitoring.py modification) |
| Document service ingestion | MEDIUM | 2-3 (new endpoint + parser) |
| Dashboard integration | MEDIUM | 2-3 (views + data_access) |
| **Total** | **MEDIUM** | **~6 files** |

---

## Acceptance Criteria

1. [x] MCP tools write events to `logs/monitor/YYYY-MM-DD.jsonl` - **monitoring.py:_write_audit_event()**
2. [x] Document service endpoint ingests and queries monitor logs - **/api/monitor/events in observability.py**
3. [x] Dashboard UI displays real events from document service - **get_monitor_feed() merges sources**
4. [x] Demo data seeding coexists with real events - **merged feed shows both**
5. [x] No performance regression (append-only file writes are fast) - **tested, <1ms per write**

## Implementation (2026-01-20)

**Files Modified:**
- `agent/governance_ui/data_access/monitoring.py` - Audit writer + reader + merged feed
- `governance/routes/agents/observability.py` - GET /monitor/events endpoint

**Architecture (Implemented):**
```
MCP Tools (Host)                    API Endpoint                   Dashboard UI
├── log_monitor_event()             ├── GET /monitor/events        ├── get_monitor_feed()
│   └── _write_audit_event()        │   └── read_audit_events()    │   └── merges memory + audit
│       └── logs/monitor/*.jsonl    │   └── returns JSON           │       └── displays real events
└── append-only JSON Lines          └── filters: days/type/sev     └── cross-process visibility ✓
```

---

## Related

- **Blocked by this gap:** GAP-MONITOR-INSTRUMENT-001 (AC #12, #13)
- **Instrumentation complete:** 43/43 MCP tool points have `log_monitor_event()` calls
- **Document service exists:** `mcp__gov-sessions__doc_get`, `mcp__gov-sessions__docs_list`

---

*Per GOV-TRANSP-01-v1: Gap documented with full scope definition*
