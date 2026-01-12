# RD-INTENT: Session Intent Reconciliation Design

**Date:** 2026-01-10
**Status:** DESIGN
**Related:** RULE-024 (AMNESIA Protocol), RULE-001 (Session Evidence)

---

## Problem Statement

Claude sessions lose context continuity. Current evidence captures:
- What was **completed** (tasks, gaps resolved)
- What the **outcome** was (health status, screenshots)

Missing:
- What was **intended** (starting goals, planned tasks)
- Whether **intent was achieved** (completion vs. abandonment)
- **Intent drift** detection across sessions

---

## Proposed Solution: Session Intent Tracking

### 1. Session Start Intent Capture

At session start, before any work begins:

```markdown
## Session Intent (Captured at Start)

**Started:** 2026-01-10T16:30:00
**Primary Goal:** {extracted from user request or TODO.md top item}
**Planned Tasks:**
- [ ] Task 1 (from backlog)
- [ ] Task 2 (from gaps)
- [ ] Task 3 (user requested)

**Continuity Check:**
- Last session: SESSION-2026-01-10-WORKSPACE-VALIDATION
- Last session outcome: COMPLETE
- Unfinished from last: None
```

### 2. Session End Outcome Capture

At session end (via `/save` or context limit):

```markdown
## Session Outcome (Captured at End)

**Ended:** 2026-01-10T18:00:00
**Primary Goal:** [ACHIEVED | PARTIAL | ABANDONED | DEFERRED]
**Tasks Completed:**
- [x] Task 1 - completed
- [ ] Task 2 - deferred (reason)
- [x] Task 3 - completed

**Handoff Items:**
- Unfinished: Task 2 (blocked by X)
- New discoveries: GAP-NEW-001, RD-NEXT
```

### 3. Intent Reconciliation Algorithm

```python
def reconcile_intent(current_session_id: str, previous_session_id: str) -> dict:
    """
    Compare session intents to detect drift.

    Returns:
        {
            "status": "ALIGNED" | "DRIFT" | "AMNESIA",
            "alignment_score": 0.0 - 1.0,
            "missing_handoffs": [...],
            "unexpected_work": [...]
        }
    """
    prev_outcome = get_session_outcome(previous_session_id)
    curr_intent = get_session_intent(current_session_id)

    # Check handoff items were picked up
    missing = []
    for item in prev_outcome.get("handoff_items", []):
        if item not in curr_intent.get("planned_tasks", []):
            missing.append(item)

    # Check for unexpected work (not from handoff or backlog)
    unexpected = []
    for task in curr_intent.get("planned_tasks", []):
        if task not in prev_outcome.get("handoff_items", []) + get_backlog_items():
            unexpected.append(task)

    # Calculate alignment
    total = len(prev_outcome.get("handoff_items", [])) + len(curr_intent.get("planned_tasks", []))
    aligned = total - len(missing) - len(unexpected)
    score = aligned / total if total > 0 else 1.0

    # Determine status
    if len(missing) > 0 and score < 0.5:
        status = "AMNESIA"  # Forgot previous work
    elif len(unexpected) > len(missing):
        status = "DRIFT"    # Doing unplanned work
    else:
        status = "ALIGNED"

    return {
        "status": status,
        "alignment_score": score,
        "missing_handoffs": missing,
        "unexpected_work": unexpected
    }
```

---

## Implementation Plan

### Phase 1: Evidence Format Extension

Add to session evidence template:

```markdown
## Intent Tracking

### Start Intent
- **Goal:** {primary goal}
- **Source:** {TODO.md | User request | Handoff from SESSION-XXX}
- **Planned:** {list of planned tasks}

### End Outcome
- **Status:** {COMPLETE | PARTIAL | ABANDONED}
- **Achieved:** {list of completed}
- **Handoff:** {list for next session}
```

### Phase 2: MCP Tool Enhancement

New governance-sessions tools:

| Tool | Purpose |
|------|---------|
| `session_capture_intent(goal, tasks)` | Record starting intent |
| `session_capture_outcome(status, completed, handoff)` | Record ending outcome |
| `session_reconcile(current, previous)` | Compare intents |

### Phase 3: Healthcheck Integration

Add to healthcheck output:

```
[SESSION] Last: SESSION-2026-01-10-WORKSPACE-VALIDATION
[SESSION] Status: COMPLETE | Handoff: 0 items
[SESSION] Continuity: ALIGNED (score: 1.0)
```

### Phase 4: AMNESIA Detection

If `reconcile_intent().status == "AMNESIA"`:

```
⚠️ AMNESIA DETECTED
Missing handoffs from SESSION-2026-01-10-XXX:
  - Task 1: Not in current plan
  - Task 2: Not in current plan

Recommended: Review previous session evidence
```

---

## Success Criteria

- [ ] Session evidence captures both intent AND outcome
- [ ] Intent reconciliation detects missing handoffs
- [ ] AMNESIA indicator triggers on significant drift
- [ ] Healthcheck shows continuity status
- [ ] Cross-session task tracking works

---

## Integration Points

| System | Integration |
|--------|-------------|
| **healthcheck.py** | Add continuity check |
| **session_start hook** | Auto-capture intent |
| **session_end hook** | Auto-capture outcome |
| **governance-sessions MCP** | New reconciliation tools |
| **ChromaDB** | Store intent vectors for semantic search |

---

## Example Workflow

```
Session A (2026-01-10 14:00)
├── Intent: Fix GAP-UI-005
├── Outcome: PARTIAL
└── Handoff: Loading state needs testing

Session B (2026-01-10 16:00)
├── Intent: Continue GAP-UI-005 testing ← Reconciled from handoff
├── Outcome: COMPLETE
└── Handoff: None

Session C (2026-01-10 18:00)
├── Intent: Work on RD-INTENT ← New goal (aligned with backlog)
├── Outcome: DESIGN COMPLETE
└── Handoff: Implement Phase 1
```

**Reconciliation:**
- A→B: ALIGNED (handoff picked up)
- B→C: ALIGNED (new work from backlog)

---

*Per RULE-024: AMNESIA Protocol*
*Per RULE-001: Session Evidence Logging*
