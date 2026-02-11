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

## Verification

- `ingest_session()` returns session_id + stats dict
- `ingest_all()` processes directory of JSONL files with dedup
- Unit tests in `tests/unit/test_cc_session_ingestion.py`
