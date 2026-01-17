# GAP-DATA-INTEGRITY-001: Dashboard Data Quality & Traceability

**Priority:** CRITICAL | **Category:** data-integrity | **Status:** PARTIAL FIX
**Discovered:** 2026-01-16 | **Session:** SESSION-2026-01-16-PLATFORM-AUDIT

---

## Summary

Dashboard shows counts but lacks actionable context. Entity relationships exist in schema but data not populated. No traceability from session → task → evidence → rules.

## Evidence

### Task Entity Quality (Sample: 10)

| Field | Populated | Empty | Quality |
|-------|-----------|-------|---------|
| `linked_rules` | 5 | 5 | **50%** |
| `linked_sessions` | 9 | 1 | 90% |
| `agent_id` | **0** | **10** | **0%** |
| `evidence` | **0** | **10** | **0%** |
| `gap_id` | **0** | **10** | **0%** |

### Session Entity Quality (Sample: 5)

| Field | Populated | Empty | Quality |
|-------|-----------|-------|---------|
| `tasks_completed` | **0** | 5 | **0%** |
| `evidence_files` | **0** | 5 | **0%** |
| `linked_rules_applied` | **0** | 5 | **0%** |
| `linked_decisions` | **0** | 5 | **0%** |
| `file_path` | **0** | 5 | **0%** |

### Test Data Pollution

4 of 5 sessions are `TEST-SESSION-*` garbage data from integration tests.

## Impact

- **Dashboard not useful** - Shows "50 Rules | 4 Decisions" but can't navigate relationships
- **No audit trail** - Can't trace session work to outcomes
- **Agent execution blind** - 0% agent_id populated means no visibility into who did what

## Root Cause

1. TypeDB schema supports relationships, but seeding/API doesn't populate them
2. Integration tests create garbage data without cleanup
3. No entity linking on task creation

## Proposed Fix

### Phase 1: Data Cleanup
```bash
# Remove TEST-SESSION-* entries from TypeDB
# Add test cleanup in conftest.py fixtures
```

### Phase 2: API Enhancement
- POST /api/tasks should accept and persist `linked_rules`, `linked_sessions`
- POST /api/sessions should link to evidence files
- Add relationship population in seed_data.py

### Phase 3: UI Context
- Click on rule → show linked tasks
- Click on session → show completed tasks + evidence
- Click on agent → show task history

---

## Fix Applied (2026-01-16): EPIC-DR-006

### Session→Task Linking via Workflow Endpoints

**Files Modified:**
- `governance/routes/tasks/workflow.py` - Added `session_id` parameter to `claim_task` and `complete_task`

**Changes:**
```python
# claim_task now accepts session_id
async def claim_task(task_id, agent_id, session_id=None):
    # When session_id provided, links task to session

# complete_task now accepts session_id
async def complete_task(task_id, evidence=None, session_id=None):
    # When session_id provided, calls link_task_to_session()
```

**Validation:**
```
Task: TASK-TEST-LINK-1768601069
  Status: DONE
  Linked Sessions: ['SESSION-TEST-LINK-1768601069'] ✓
```

**Remaining Work:**
- EPIC-DR-007: agent_id population on claim (still 0%)
- EPIC-DR-008: evidence field population (still 0%)
- Phase 3: UI navigation for relationships

---

## Fix Applied (2026-01-17): TypeDB Relations Sync

### linked_sessions → completed-in Relations

**Problem:** Tasks had `linked_sessions` attribute populated but TypeDB `completed-in` relations were missing. This caused `tasks_completed` to show 0 in session data.

**Solution:** Created sync script to populate TypeDB relations from existing task attributes.

**Files Created:**
- `governance/sync_task_session_relations.py` - REST API sync script

**Results:**
```
Found 81 tasks to check
Skipped (no sessions): 16
Already linked: 0
Newly synced: 65
Errors: 0

Verification:
  SESSION-2026-01-11-B2A608: tasks_completed = 62
```

**Validation:** Session→Task traceability now functional. GET returns correct counts.

**Bug Found:** LIST query returns wrong counts (GAP-BATCH-QUERY-001 opened).

---

## Data Quality Audit (2026-01-17) - Updated

### Current TypeDB State (Full Dataset)

**Tasks (82 total):**
| Field | Populated | Quality | Notes |
|-------|-----------|---------|-------|
| `agent_id` | **100%** | ✅ **FIXED** | EPIC-DR-007: Backfilled 76 tasks (2026-01-17) |
| `evidence` | 3% | **CRITICAL** | Only 2 tasks have evidence → EPIC-DR-008 |
| `linked_sessions` | 86% | Good | 65/76 have completed-in relations |

**Sessions (22 total):**
| Field | Populated | Quality | Notes |
|-------|-----------|---------|-------|
| `evidence_files` | **77%** | Good | 17/22 have has-evidence relations |
| `tasks_completed` | 18% | Improved | 4 sessions have completed tasks |
| `linked_rules_applied` | 23% | Fair | 5 sessions have rule links |

### Progress Since Original Audit

| Metric | 2026-01-16 | 2026-01-17 AM | 2026-01-17 PM | Change |
|--------|------------|---------------|---------------|--------|
| Task agent_id | 0% | 0% | **100%** | +100% ✅ |
| Task evidence | 0% | 3% | 3% | Pending |
| Session→Task relations | 0% | 18% | 18% | +18% |
| Session evidence_files | 0% | 77% | 77% | +77% |
| LIST query accuracy | Wrong | Fixed | Fixed | ✅ |

### Remaining Work

1. ~~**EPIC-DR-007:** agent_id backfill~~ ✅ DONE (2026-01-17)
2. **EPIC-DR-008:** evidence field population (3% → target 50%) - [GAP-EPIC-DR-008.md](GAP-EPIC-DR-008.md)
3. **Phase 3:** UI navigation for relationships

---

## Related Gaps

- GAP-BATCH-QUERY-001: ✅ RESOLVED (2026-01-17)
- GAP-API-PERF-001: API response times ✅ RESOLVED (37x faster)
- GAP-UI-PAGING-001: UI pagination for large datasets

---

*Per GAP-DOC-01-v1: Evidence file for gap documentation*
