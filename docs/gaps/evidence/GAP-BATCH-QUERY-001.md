# GAP-BATCH-QUERY-001: Session Batch Query Returns Wrong tasks_completed

**Priority:** HIGH | **Category:** data_integrity | **Status:** RESOLVED
**Discovered:** 2026-01-17 | **Session:** SESSION-2026-01-17-AUDIT

---

## Summary

The `get_sessions` batch query returns incorrect `tasks_completed` counts.
Individual `get_session(id)` returns correct counts, but list query shows wrong values.

**Example:**
- LIST /api/sessions → SESSION-2026-01-11-B2A608 shows `tasks_completed: 1`
- GET /api/sessions/SESSION-2026-01-11-B2A608 → shows `tasks_completed: 62`

## Root Cause Analysis

### Batch Query (WRONG)
Location: [governance/typedb/queries/sessions/read.py:156-170](../../../../governance/typedb/queries/sessions/read.py#L156)

```python
# This query returns ALL completed-in relations, not grouped by session
tasks_results = self._execute_query("""
    match
        $s isa work-session, has session-id $sid;
        (completed-task: $t, hosting-session: $s) isa completed-in;
    get $sid;
""")
```

**Problem:** The query returns one row per task-session relation, but Python side counts occurrences of `sid`. If query ordering or result set differs from expectation, counts are wrong.

### Individual Query (CORRECT)
Uses `_build_session_from_id()` which explicitly counts tasks for one session.

## Hypothesis: NOT TypeDB Version Bug

- Running TypeDB 2.x Core (docker.io/vaticle/typedb:latest)
- Issue is query logic, not TypeDB behavior
- TypeDB 3.x migration is tracked in GAP-TYPEDB-UPGRADE-001 (separate concern)

## Proposed Fix

Option A: Use TypeQL aggregate count per session
```typeql
match
    $s isa work-session, has session-id $sid;
    (completed-task: $t, hosting-session: $s) isa completed-in;
get $sid; count;
group $sid;
```

Option B: Post-process in Python with explicit grouping
```python
from collections import Counter
task_counts = Counter(r.get("sid") for r in tasks_results)
```

## Impact

- Dashboard sessions view shows incorrect task counts
- Data integrity appearance degraded
- Users see "1 task" when 62 tasks actually completed

---

## Resolution (2026-01-17)

**Root Cause:** TypeDB 2.x deduplicates query results when the `get` clause only includes variables with non-unique values across rows. When querying `get $sid;` only, TypeDB returns 4 distinct session IDs instead of 65 individual relation rows.

**Fix Applied:** Added `$t` to the get clause in [governance/typedb/queries/sessions/read.py:162](../../../../governance/typedb/queries/sessions/read.py#L162)

```python
# Before (WRONG - TypeDB deduplicates to 4 rows)
get $sid;

# After (CORRECT - returns all 65 relation rows)
get $sid, $t;
```

**Verification:**
```
LIST SESSION-2026-01-11-B2A608: 62 tasks ✓
GET  SESSION-2026-01-11-B2A608: 62 tasks ✓
```

---

*Per GAP-DOC-01-v1: Evidence file for gap documentation*
