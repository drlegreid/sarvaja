# DATA-LAZY-01-v1: Session Detail Lazy Loading

| Field | Value |
|-------|-------|
| **Rule ID** | DATA-LAZY-01-v1 |
| **Category** | technical |
| **Priority** | MEDIUM |
| **Status** | ACTIVE |

## Statement

Session detail data MUST support zoom-level lazy loading to prevent OOM on large sessions. JSONL files MUST be parsed in a single pass regardless of zoom level. Chat-bridge sessions without JSONL MUST fall back to `_sessions_store` for tool calls and thoughts.

## Rationale

CC sessions can contain thousands of tool calls and thinking blocks. Loading all data at once causes excessive memory usage and slow API responses. Zoom levels cap response size per SRE principles.

## Zoom Levels

| Level | Data | Source |
|-------|------|--------|
| zoom=0 | Summary metadata only | TypeDB / _sessions_store |
| zoom=1 | + tool breakdown + thinking summary | JSONL single-pass |
| zoom=2 | + individual tool calls (paginated) | JSONL or _sessions_store |
| zoom=3 | + full thinking content (paginated) | JSONL or _sessions_store |

## Implementation

- Single-pass parsing in `governance/services/cc_session_ingestion.py:get_session_detail()`
- Accepts `page` and `per_page` for pagination (default: page=1, per_page=20)
- `GET /api/sessions/{id}/detail?zoom=N&page=1&per_page=20`
- `GET /api/sessions/{id}/tools?page=1&per_page=20`
- `GET /api/sessions/{id}/thoughts?page=1&per_page=20`
- `GET /api/sessions/{id}/evidence/rendered` (markdown to HTML)
- Chat-bridge fallback: uses `_sessions_store` when no JSONL available

## Verification

- zoom=0 response < 1KB for any session
- zoom=3 responses are paginated (max 100 items per page)
- Chat-bridge sessions use _sessions_store fallback
- JSONL parsed exactly once per request (no re-parsing)
- Unit tests in `tests/unit/test_session_detail_lazy.py`
