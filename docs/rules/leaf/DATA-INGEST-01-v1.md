# DATA-INGEST-01-v1: JSONL Ingestion Service

| Field | Value |
|-------|-------|
| **Rule ID** | DATA-INGEST-01-v1 |
| **Category** | technical |
| **Priority** | MEDIUM |
| **Status** | ACTIVE |

## Statement

JSONL session backfill MUST use CCSessionIngestionService, not raw REST calls.

## Rationale

Direct REST calls bypass metadata extraction, project linking, and deduplication logic. The ingestion service ensures consistent data quality across all CC session imports.

## Implementation

- `governance/services/cc_session_ingestion.py` provides `ingest_session()` and `ingest_all()`
- Extracts CC UUID, project slug, git branch, tool counts from JSONL
- Auto-creates project entity if needed
- Links session to project via TypeDB relation

### Event-Driven Ingestion (P2-10a/c)

- `governance/services/claude_watcher.py` — watchdog-based JSONL file monitor
- `governance/services/ingestion_scheduler.py` — periodic fallback (5 min default)
- `ingest_single_session()` creates OR updates session entities (idempotent)

### Timestamp Passthrough (P2-10c)

- `insert_session()` accepts `start_time`, `end_time`, `status` parameters
- `create_session()` service layer forwards all timestamps to TypeDB
- CC sessions get real timestamps from JSONL (not `datetime.now()`)
- Existing sessions updated on re-ingestion if `end_time` changed

### Session Name Extraction (P2-10c)

- Scanner extracts `customTitle` from JSONL `custom-title` entry type
- Stored as `cc_external_name` on session entity (TypeDB + API)
- Watcher auto-syncs name changes on JSONL file modification

## Verification

- `ingest_session()` returns session_id + stats dict
- `ingest_all()` processes directory of JSONL files with dedup
- `tests/unit/test_cc_session_ingestion.py` — batch ingestion
- `tests/unit/test_claude_watcher.py` — watcher + single-session ingestion
- `tests/unit/test_session_endtime_fix.py` — timestamp + name passthrough (26 tests)
