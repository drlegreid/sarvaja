# DATA-COMPLETE-01-v1: Session Data Completeness

**Category:** `governance` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** GOVERNANCE

> **Tags:** `data-integrity`, `sessions`, `evidence`, `heuristic`

---

## Directive

Sessions MUST have: (1) agent_id identifying the creating agent, (2) evidence_files array with at least one evidence file on completion, (3) linked_rules_applied for governance sessions, (4) linked_decisions for decision-making sessions. Heuristic checks MUST flag incomplete sessions.

---

## Validation

- [ ] H-SESSION-001: Active sessions have agent_id
- [ ] H-SESSION-002: Ended sessions have evidence files
- [ ] H-SESSION-005: Sessions have MCP tool call records
- [ ] H-SESSION-006: Sessions have thought/reasoning records
- [ ] Backfilled sessions are excluded from live-data checks

---

## Heuristic Checks

| Check ID | What It Validates |
|----------|-------------------|
| H-SESSION-001 | Active sessions must have agent_id |
| H-SESSION-002 | Ended sessions must have evidence files |
| H-SESSION-003 | Sessions >24h should not be ACTIVE |
| H-SESSION-005 | Sessions should have tool call records |
| H-SESSION-006 | Sessions should have thought records |

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Create sessions without agent_id | Always pass agent_id at session start |
| End sessions without evidence | Generate evidence file before session_end |
| Skip tool call recording | Use session_tool_call for every operation |
| Leave sessions ACTIVE indefinitely | Auto-detect stale sessions (>24h) |

---

*Per SESSION-EVID-01-v1: Evidence-Based Governance*
