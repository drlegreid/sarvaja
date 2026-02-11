# DATA-LAZY-01-v1: Session Detail Lazy Loading

| Field | Value |
|-------|-------|
| **Rule ID** | DATA-LAZY-01-v1 |
| **Category** | technical |
| **Priority** | MEDIUM |
| **Status** | ACTIVE |

## Statement

Session detail data MUST support zoom-level lazy loading to prevent OOM on large sessions.

## Rationale

CC sessions can contain thousands of tool calls and thinking blocks. Loading all data at once causes excessive memory usage and slow API responses. Zoom levels cap response size per SRE principles.

## Implementation

- Zoom 0: Summary only (tokens, tool count, duration)
- Zoom 1: + tool breakdown by type + thinking summary
- Zoom 2: + individual tool calls with inputs (paginated)
- Zoom 3: + full tool outputs (paginated)
- `governance/services/cc_session_ingestion.py:get_session_detail(zoom=)`
- `GET /api/sessions/{id}/detail?zoom=N`

## Verification

- zoom=0 response < 1KB for any session
- zoom=3 responses are paginated (max 50 items per page)
- Unit tests in `tests/unit/test_cc_session_ingestion.py`
