# GAP-UI-LINKED-SESSIONS-001: Task UI Missing Linked Sessions Display

**Priority:** HIGH | **Category:** ui | **Status:** RESOLVED
**Discovered:** 2026-01-16 | **Session:** SESSION-2026-01-16-PLATFORM-AUDIT
**Resolved:** 2026-01-17 | **Session:** SESSION-2026-01-17-WORKFLOW-GUARDRAILS

---

## Summary

The task detail view in the UI doesn't display the `linked_sessions` field, even though:
1. The TypeDB schema supports it
2. The API returns it
3. EPIC-DR-006 added session linking to workflow endpoints

## Evidence

### API Response (Working)
```json
{
  "task_id": "TASK-TEST-LINK-1768601069",
  "status": "DONE",
  "resolution": "VALIDATED",
  "linked_sessions": ["SESSION-TEST-LINK-1768601069"]
}
```

### UI Display (Missing)
- Task list shows: task name, phase, status chips
- Task detail shows: description, body, linked_rules
- **Missing**: linked_sessions, resolution not displayed anywhere

## Impact

- EPIC-DR-006 (session→task traceability) is **incomplete** without UI display
- Users can't see which sessions worked on a task
- GAP-DATA-INTEGRITY-001 goal of "bidirectional traceability" not achievable in UI

## Proposed Fix

1. Add `linked_sessions` to task detail view
2. Display as clickable chips linking to session detail
3. Show count in task list item subtitle
4. **NEW**: Display `resolution` field (IMPLEMENTED/VALIDATED/CERTIFIED)

### Files to Modify

- `agent/governance_ui/views/tasks/list.py` - Add linked_sessions count, resolution badge
- `agent/governance_ui/views/tasks/detail.py` - Add linked_sessions section

## Related

- EPIC-DR-006: Session→task linking (backend complete)
- GAP-DATA-INTEGRITY-001: Dashboard data traceability

---

## Progress (2026-01-17)

### Backend Guardrails Implemented

Per user's 3 Directives, implemented workflow guardrails:

1. **Evidence linking on state transitions** (Directive 1)
   - `PUT /tasks/{id}/complete` now accepts `verification_level` (L1/L2/L3)
   - Evidence enriched with verification metadata
   - Resolution auto-determined based on verification level

2. **Verification subtasks** (Directive 2)
   - `POST /tasks/{id}/create-verification-subtasks` - Creates L1/L2/L3 child tasks
   - `GET /tasks/{id}/verification-status` - Shows verification completion
   - `PUT /tasks/{id}/promote-resolution` - Promotes IMPLEMENTED→VALIDATED→CERTIFIED

3. **Consolidated rules** (Directive 3)
   - Updated WORKFLOW-SEQ-01-v1 with API guardrails documentation
   - Added resolution mapping table

### UI Work Completed (2026-01-17)

All UI components now implemented:

1. **Task List View** ([list.py](../../../../agent/governance_ui/views/tasks/list.py))
   - ✅ Resolution badge with color-coding (IMPLEMENTED=warning, VALIDATED=info, CERTIFIED=success)
   - ✅ Icons per resolution level (code-tags, test-tube, check-decagram)
   - ✅ linked_sessions count already displayed

2. **Task Detail View** ([detail.py](../../../../agent/governance_ui/views/tasks/detail.py))
   - ✅ Resolution chip in metadata section
   - ✅ linked_sessions display (already existed in forms.py)
   - ✅ Evidence display with verification metadata

### Test Evidence

```bash
# Task created, completed with L2, promoted to CERTIFIED
PUT /api/tasks/UI-TEST-RES-001/complete?verification_level=L2
→ resolution: "VALIDATED"
→ evidence: "[Verification: L2] E2E functionality verified..."

PUT /api/tasks/UI-TEST-RES-001/promote-resolution?target_resolution=CERTIFIED
→ resolution: "CERTIFIED"
→ evidence includes audit trail with timestamps
```

---

*Per GAP-DOC-01-v1: Evidence file for gap documentation*
