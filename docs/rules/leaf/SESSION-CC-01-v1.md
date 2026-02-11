# SESSION-CC-01-v1: Claude Code Session Metadata

| Field | Value |
|-------|-------|
| **Rule ID** | SESSION-CC-01-v1 |
| **Category** | governance |
| **Priority** | HIGH |
| **Status** | ACTIVE |

## Statement

Claude Code sessions ingested into governance MUST include `cc_session_uuid` and `cc_project_slug` for traceability back to the original CC session.

## Rationale

CC sessions are the primary work unit. Without the UUID link, governance sessions cannot be correlated with raw JSONL logs for audit, replay, or debugging.

## Implementation

- TypeDB schema: `cc-session-uuid`, `cc-project-slug`, `cc-git-branch`, `cc-tool-count`, `cc-thinking-chars`, `cc-compaction-count` attributes on `work-session`
- `governance/services/cc_session_ingestion.py` extracts metadata from JSONL files
- `governance/routes/sessions/detail.py` exposes zoom-level lazy loading

## Verification

- Ingested CC sessions have non-null `cc_session_uuid`
- `GET /api/sessions/{id}/detail?zoom=1` returns tool breakdown
- Unit tests in `tests/unit/test_cc_session_ingestion.py`
