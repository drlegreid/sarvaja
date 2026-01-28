# GAP-TASK-DATA-QUALITY-001: Task Data Quality & Rule Compliance

**Priority:** HIGH | **Category:** data_integrity/compliance | **Status:** RESOLVED
**Discovered:** 2026-01-20 | **Source:** Task System Audit
**Resolution:** 2026-01-20 - Status migration + workspace_capture_tasks mapping complete

---

## Problem Statement

TypeDB contains 102 tasks with significant data quality issues and rule compliance violations. Task status values are inconsistent and many required fields are unpopulated.

---

## Audit Findings (2026-01-20)

### Issue 1: Status Value Inconsistency

**Actual values found:**
| Status | Casing | Count |
|--------|--------|-------|
| `TODO` | uppercase | many |
| `DONE` | uppercase | many |
| `completed` | lowercase | some |
| `in_progress` | lowercase | some |
| `pending` | lowercase | some |

**Required by TASK-LIFE-01-v1:**
| Status | Expected |
|--------|----------|
| `OPEN` | Not found |
| `IN_PROGRESS` | Found as lowercase |
| `CLOSED` | Not found |

**Violation:** TASK-LIFE-01-v1 defines status as OPEN/IN_PROGRESS/CLOSED, but TypeDB contains TODO/DONE/completed/pending.

---

### Issue 2: Missing Field Population

From 30-task sample:

| Field | Populated | Empty/Null | Coverage |
|-------|-----------|------------|----------|
| agent_id | 0 | 30 | 0% |
| linked_sessions | 6 | 24 | 20% |
| evidence | 0 | 30 | 0% |
| linked_commits | 1 | 29 | 3% |
| created_at | 0 | 30 | 0% |
| claimed_at | 0 | 30 | 0% |
| completed_at | 0 | 30 | 0% |
| business | 0 | 30 | 0% |
| design | 0 | 30 | 0% |
| architecture | 0 | 30 | 0% |
| test_section | 0 | 30 | 0% |

---

### Issue 3: Rule Compliance Violations

| Rule | Requirement | Compliance |
|------|-------------|------------|
| TASK-LIFE-01-v1 | Status: OPEN/IN_PROGRESS/CLOSED | ❌ Uses TODO/DONE/pending |
| TASK-LIFE-01-v1 | Resolution: NONE/DEFERRED/IMPLEMENTED/etc | ❌ All have NONE |
| TASK-TECH-01-v1 | Tech sections (business, design, arch, test) | ❌ 0% populated |
| TEST-FIX-01-v1 | Evidence required for completed tasks | ❌ 0% have evidence |

---

## Root Causes

1. **Backward Compatibility Debt**: System accepts old status values without migration
2. **No Validation on Insert**: `task_create` doesn't enforce TASK-LIFE-01-v1 statuses
3. **workspace_capture_tasks**: Parses TODO.md with old status values
4. **No Enforcement Hooks**: No pre-commit hook validates task data quality

---

## Proposed Solutions

| Component | Fix | Complexity |
|-----------|-----|------------|
| **1. Migration Script** | Convert TODO→OPEN, DONE→CLOSED with proper resolution | MEDIUM |
| **2. Validation Layer** | Add status validation to task_create/task_update | LOW |
| **3. workspace_capture_tasks** | Map parsed statuses to TASK-LIFE-01-v1 values | LOW |
| **4. Data Backfill** | Populate created_at from TypeDB insert timestamp | MEDIUM |

---

## Acceptance Criteria

1. [x] All 102 tasks migrated to OPEN/IN_PROGRESS/CLOSED status - **97 migrated, 5 already correct**
2. [ ] DONE tasks have resolution = IMPLEMENTED or VALIDATED (deferred - future enhancement)
3. [x] task_create defaults to OPEN status per TASK-LIFE-01-v1
4. [x] workspace_capture_tasks maps statuses correctly - **governance/task_parsers.py normalize_status()**
5. [ ] created_at populated for all tasks (deferred - future enhancement)

## Resolution (2026-01-20)

**Migration Script:** `scripts/migrate_task_statuses.py`

**Results:**
```
Found 102 tasks in TypeDB
Migrated: 97
Errors: 0
Already correct: 5

Status mapping:
- TODO/pending → OPEN (30 tasks)
- DONE/completed → CLOSED (64 tasks)
- in_progress → IN_PROGRESS (3 tasks)
```

**MCP Tool Update:** `task_create` default status changed from "pending" to "OPEN"

---

## Related

- TASK-LIFE-01-v1: Task Lifecycle Management
- TASK-TECH-01-v1: Technology Solution Documentation
- TEST-FIX-01-v1: Verification Before Completion
- GAP-UI-AUDIT-001: Dashboard traceability

---

*Per GOV-TRANSP-01-v1: Audit findings documented with full scope*
