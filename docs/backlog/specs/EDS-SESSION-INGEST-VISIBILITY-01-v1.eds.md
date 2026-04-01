# EDS-SESSION-INGEST-VISIBILITY-01-v1

## DSE: Session Ingestion Visibility

**Bug:** SRVJ-BUG-SESSION-INGEST-01
**Priority:** HIGH
**Type:** Exploratory Design Specification
**Created:** 2026-03-31

---

## Problem Statement

CC JSONL sessions are ingested into TypeDB but invisible via MCP `session_list` tool.
Root cause: `session_list` filtered to ACTIVE-only; CC-ingested sessions are marked COMPLETED.

## Exploration Axes

### Axis 1: MCP session_list status filtering
**Goal:** Verify session_list returns sessions for all status values.

| Scenario | Input | Expected |
|----------|-------|----------|
| E1.1 Default (no status) | `session_list()` | Returns ACTIVE + COMPLETED sessions |
| E1.2 ACTIVE filter | `session_list(status="ACTIVE")` | Returns only ACTIVE sessions |
| E1.3 COMPLETED filter | `session_list(status="COMPLETED")` | Returns COMPLETED sessions, includes CC-ingested |
| E1.4 CC sessions present | `session_list(status="COMPLETED")` | At least 1 session_id contains "-CC-" |

### Axis 2: MCP session_list limit enforcement
**Goal:** Verify limit parameter caps result count.

| Scenario | Input | Expected |
|----------|-------|----------|
| E2.1 Limit=3 | `session_list(limit=3)` | count <= 3 |
| E2.2 Limit=1 | `session_list(limit=1)` | count == 1 |
| E2.3 Default limit | `session_list()` | count <= 50 |

### Axis 3: REST API session endpoint consistency
**Goal:** Verify REST API and MCP return consistent CC session data.

| Scenario | Input | Expected |
|----------|-------|----------|
| E3.1 API returns CC | `GET /api/sessions?limit=50` | items contain sessions with "-CC-" in ID |
| E3.2 API has COMPLETED | `GET /api/sessions` | statuses include "COMPLETED" |
| E3.3 API+MCP agreement | Both endpoints | CC session IDs overlap between API and MCP |

### Axis 4: Response key backward compatibility
**Goal:** Verify response keys match the status filter used.

| Scenario | Input | Expected Key |
|----------|-------|-------------|
| E4.1 No status | `session_list()` | `"sessions"` |
| E4.2 ACTIVE | `session_list(status="ACTIVE")` | `"active_sessions"` |
| E4.3 COMPLETED | `session_list(status="COMPLETED")` | `"completed_sessions"` |

### Axis 5: Session data sources
**Goal:** Verify all 3 sources contribute to session_list results.

| Scenario | Check | Expected |
|----------|-------|----------|
| E5.1 TypeDB source | sources field | At least 1 source == "typedb" |
| E5.2 Memory source | ACTIVE filter with running session | At least 1 source == "memory" (if MCP session active) |
| E5.3 CC JSONL source | ACTIVE filter with recent JSONL | source == "cc_jsonl" for recently-modified files |

## Out of Scope
- L3 Playwright UI tests (dashboard rendering) — separate spec
- JSONL parsing correctness — covered by existing scanner unit tests
- TypeDB schema validation — covered by schema migration tests

## Risks
- Stale ACTIVE sessions (207 from weeks ago) may inflate ACTIVE counts
- TypeDB query is slow (~750ms) — may affect limit enforcement timing
