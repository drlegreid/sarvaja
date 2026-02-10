# WORKFLOW-DSP-01-v1: DSP Workflow Stability Requirements

**Category:** `operational` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Tags:** `workflow`, `dsp`, `stability`, `langgraph`

---

## Directive

DSP (Deep Sleep Protocol) workflows MUST: (1) Use thread-safe state management (no global singletons without locks), (2) Implement atomic file writes for state persistence, (3) Auto-detect and cleanup abandoned cycles older than 24 hours, (4) Handle state load failures gracefully with rollback. Consider LangGraph for complex multi-phase workflows.

---

## Implementation

- DSM Tracker: `governance/dsm/tracker.py` (state management, cycle lifecycle)
- LangGraph DSP: `governance/dsm/langgraph/` (multi-phase workflow with loop-back)
- Evidence: `governance/dsm/evidence.py` (evidence file generation)
- Retention: `completed_cycles` capped at 50 entries to prevent unbounded growth

---

## Validation

- [ ] State file `.dsm_state.json` uses atomic writes
- [ ] Completed cycles list is capped (max 50)
- [ ] LangGraph workflow has loop-back (validate -> hypothesize when retry < 3)
- [ ] 24/25 DSM tests pass (1 skipped for missing LangGraph)

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Use global mutable state without locks | Thread-safe state management |
| Grow `completed_cycles` unbounded | Cap to 50 entries, prune oldest |
| Leave abandoned cycles active | Auto-cleanup cycles >24h old |
| Fail on corrupted state file | Graceful fallback with fresh state |

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
