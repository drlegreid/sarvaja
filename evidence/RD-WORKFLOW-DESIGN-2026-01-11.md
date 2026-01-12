# RD-WORKFLOW: Agentic Workflow Integrity Design

**Date:** 2026-01-11
**Status:** DESIGN
**Priority:** HIGH
**Related:** RD-INTENT, RULE-020, RULE-023, GAP-WORKFLOW-*

---

## Executive Summary

RD-WORKFLOW defines a gap-based workflow validation system that ensures Claude sessions follow governance rules and properly track work items through the gap/task lifecycle.

---

## Problem Statement

Current gaps in workflow integrity:

| Issue | Impact | Evidence |
|-------|--------|----------|
| Workflow rule violations undetected | RULE-020 (test before claim) violations | GAP-WORKFLOW-004 |
| Gap lifecycle not enforced | Gaps left in incorrect states | Manual audits required |
| Task-Gap linking broken | Work done without gap tracking | Orphaned changes |
| No workflow metrics | Can't measure governance compliance | No dashboard data |

---

## Goals

1. **Validate workflow compliance** - Ensure rules like RULE-020, RULE-023 are followed
2. **Track gap lifecycle** - Validate state transitions (OPEN -> IN_PROGRESS -> RESOLVED)
3. **Link work to gaps** - Every code change tied to gap/task
4. **Report violations** - Alert on workflow integrity issues

---

## Design: 4-Phase Implementation

### Phase 1: Workflow Validation Model

**Data Structures:**

```python
@dataclass
class WorkflowValidation:
    """Represents a workflow validation check."""
    rule_id: str           # e.g., "RULE-020"
    check_name: str        # e.g., "test_before_claim"
    status: str            # PASS | FAIL | SKIP
    evidence: str          # Path to evidence file or test result
    timestamp: datetime

@dataclass
class GapLifecycle:
    """Tracks gap state transitions."""
    gap_id: str
    current_state: str     # OPEN | IN_PROGRESS | RESOLVED
    transitions: List[Dict]  # [{from, to, timestamp, evidence}]
    linked_tasks: List[str]
    linked_commits: List[str]
```

**Validation Rules Matrix:**

| Rule | Check | Trigger | Evidence |
|------|-------|---------|----------|
| RULE-020 | Tests pass before fix claim | `gap_update(RESOLVED)` | Test results |
| RULE-023 | E2E tests for UI claims | `gap_update(RESOLVED, category=UI)` | Playwright report |
| RULE-001 | Session evidence logged | `session_end()` | Evidence file exists |
| RULE-024 | Context recovery on start | `session_start()` | CLAUDE.md read |

---

### Phase 2: Validation Implementation

**Core Functions:**

```python
def validate_gap_transition(gap_id: str, from_state: str, to_state: str) -> ValidationResult:
    """
    Validate a gap state transition is allowed and has required evidence.

    Args:
        gap_id: Gap being transitioned
        from_state: Current state
        to_state: Target state

    Returns:
        ValidationResult with status and any violations
    """

def validate_workflow_rule(rule_id: str, context: Dict) -> ValidationResult:
    """
    Check if a workflow rule is being followed.

    Args:
        rule_id: Rule to validate (e.g., RULE-020)
        context: Current context (files modified, tests run, etc.)
    """

def link_work_to_gap(gap_id: str, work_type: str, reference: str) -> bool:
    """
    Link work artifact (commit, task, file) to a gap.
    """
```

---

### Phase 3: Integration Points

**Healthcheck Integration:**
- Add workflow validation to detailed healthcheck output
- Show recent violations as warnings
- Track compliance score over time

**Session Lifecycle:**
- Validate at session start (RULE-024 compliance)
- Validate at session end (evidence logging)
- Validate gap transitions during session

**MCP Tool Integration:**
- `governance_update_gap()` triggers validation
- `session_end()` checks evidence requirements
- `governance_health()` includes workflow metrics

---

### Phase 4: Reporting & Alerts

**Compliance Dashboard:**
- Rule compliance % per session
- Gap lifecycle violations
- Missing evidence alerts
- Trend over time

**Alert Levels:**

| Level | Condition | Action |
|-------|-----------|--------|
| INFO | Rule followed correctly | Log for metrics |
| WARNING | Minor deviation (missing link) | Show in healthcheck |
| ALERT | Major violation (no tests) | Block transition |
| CRITICAL | Governance bypass attempt | Halt + escalate |

---

## Implementation Plan

| Phase | Tasks | Effort | Dependencies |
|-------|-------|--------|--------------|
| Phase 1 | Data models, validation matrix | 1 session | None |
| Phase 2 | Core validation functions | 2 sessions | Phase 1 |
| Phase 3 | Healthcheck + MCP integration | 1 session | Phase 2 |
| Phase 4 | Reporting, alerts, dashboard | 1 session | Phase 3 |

---

## Success Criteria

- [ ] Gap state transitions validated with evidence
- [ ] RULE-020 violations detected before gap closure
- [ ] RULE-023 requires E2E test evidence for UI gaps
- [ ] Workflow compliance visible in healthcheck
- [ ] Dashboard shows compliance metrics

---

## Related

- [RD-INTENT-DESIGN-2026-01-10.md](RD-INTENT-DESIGN-2026-01-10.md) - Session intent tracking
- [RULES-OPERATIONAL.md](../docs/rules/RULES-OPERATIONAL.md) - Workflow rules
- [GAP-INDEX.md](../docs/gaps/GAP-INDEX.md) - Gap tracking

---

*Per RULE-015: R&D Task Protocol*
*Per RULE-010: Evidence-Based Wisdom*
