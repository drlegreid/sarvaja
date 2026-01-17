# GAP-API-PERF-001: API Response Times Unacceptable

**Priority:** HIGH | **Category:** performance | **Status:** FIX APPLIED (pending validation)
**Discovered:** 2026-01-16 | **Session:** SESSION-2026-01-16-PLATFORM-AUDIT

---

## Summary

API endpoints take 7-9 seconds for simple list queries. This is unacceptable for production use.

## Evidence

### Response Times (MCP REST Testing)

| Endpoint | Records | Time | Assessment |
|----------|---------|------|------------|
| GET /api/tasks?limit=10 | 10 | **7510ms** | CRITICAL |
| GET /api/tasks?limit=5&offset=5 | 5 | **7603ms** | CRITICAL |
| GET /api/agents | 8 | **9090ms** | CRITICAL |
| GET /api/sessions?limit=5 | 5 | **1631ms** | Poor |
| GET /api/rules | 50 | **666ms** | Acceptable |
| POST /api/tasks | 1 | **908ms** | Poor |
| DELETE /api/tasks/{id} | 1 | **114ms** | Good |

### Analysis

- Tasks/Agents queries are **10-50x slower** than expected
- Fetching 5 records takes same time as 10 → query overhead, not data size
- Likely cause: TypeDB query inefficiency or connection overhead

## Impact

- **User experience degraded** - 7 second load times drive users away
- **UI feels broken** - Trace bar shows long wait times
- **Scalability blocked** - Can't add more data if simple queries take 7s

## Proposed Investigation

1. **Profile TypeDB queries**
   ```python
   # Add timing to governance/client.py
   with timer("typedb_query"):
       results = tx.query.get(query)
   ```

2. **Check indexing**
   - Are task-id, agent-id indexed in TypeDB?

3. **Connection pooling**
   - Is connection being reopened for each request?

4. **Cache layer**
   - Rules are fast (666ms) - are they cached?
   - Apply same pattern to tasks/agents

## Acceptance Criteria

| Endpoint | Target | Current | Gap |
|----------|--------|---------|-----|
| GET /api/tasks?limit=10 | <500ms | 7510ms | **15x** |
| GET /api/agents | <500ms | 9090ms | **18x** |
| GET /api/sessions | <500ms | 1631ms | **3x** |

---

## Fix Applied (2026-01-16)

### Root Cause: N+1 Query Problem

Each entity (task/session) was fetched individually with 10-16 separate TypeDB queries.

| Entity | Before | After | Improvement |
|--------|--------|-------|-------------|
| Tasks (50) | 800 queries (16 × 50) | 16 queries (batched) | **50x fewer queries** |
| Sessions (100) | 1000 queries (10 × 100) | 11 queries (batched) | **90x fewer queries** |
| Agents | Called tasks + sessions | Benefits from above | **Cascading improvement** |

### Files Modified

| File | Change |
|------|--------|
| `governance/typedb/queries/tasks/read.py` | Batch fetch attributes + relationships |
| `governance/typedb/queries/sessions/read.py` | Batch fetch attributes + relationships |

### New Methods Added

- `_batch_fetch_task_attributes()` - 12 optional attrs in 12 queries (not 12 × N)
- `_batch_fetch_task_relationships()` - 3 relationship queries (not 3 × N)
- `_batch_fetch_session_attributes()` - 6 attrs + status handling
- `_batch_fetch_session_relationships()` - 4 relationships + task counts

### Expected Performance Improvement

| Endpoint | Before | Target | Method |
|----------|--------|--------|--------|
| GET /api/tasks | 7510ms | <500ms | Batch queries |
| GET /api/agents | 9090ms | <1000ms | Benefits from tasks/sessions fix |
| GET /api/sessions | 1631ms | <500ms | Batch queries |

**Note:** Performance improvement requires container rebuild to pick up code changes.

---

## Validation Results (2026-01-16)

**Status: VALIDATED ✓**

Container rebuilt and API performance tested:

| Endpoint | Before | After | Improvement | Target Met |
|----------|--------|-------|-------------|------------|
| GET /api/tasks?limit=10 | 7510ms | **203ms** | 37x faster | ✓ (<500ms) |
| GET /api/sessions?limit=5 | 1631ms | **244ms** | 7x faster | ✓ (<500ms) |
| GET /api/agents | 9090ms | **404ms** | 22x faster | ✓ (<500ms) |
| GET /api/rules | 666ms | 1008ms | baseline | ✓ (acceptable) |

### Root Cause Confirmed
N+1 query pattern was causing 800+ TypeDB queries for 50 tasks. Batch query optimization reduced this to ~16 queries.

---

*Per GAP-DOC-01-v1: Evidence file for gap documentation*
