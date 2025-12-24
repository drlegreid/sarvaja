# Governance Rules - Sim.ai

Rules governing process, documentation, and agent collaboration.

---

## RULE-001: Session Evidence Logging

**Category:** `governance` | **Priority:** CRITICAL | **Status:** ACTIVE

### Directive

All agent sessions MUST produce evidence logs that include:

1. **Thought Chain Documentation**
   - Every decision point with rationale
   - Alternatives considered and why rejected
   - Assumptions made and their basis

2. **Artifact Tracking**
   - Files created/modified with timestamps
   - Dependencies introduced
   - Configuration changes

3. **Session Metadata**
   - Session ID, start/end times
   - Models invoked with token counts
   - Tools used with invocation counts

4. **Export Requirements**
   - Session logs exported to `./docs/SESSION-{date}-{topic}.md`
   - Machine-readable YAML metadata block
   - Human-readable narrative

### Implementation

```python
session_log = {
    "session_id": str,
    "timestamp": datetime,
    "thought_chain": [
        {"step": int, "decision": str, "rationale": str, "alternatives": list[str], "confidence": float}
    ],
    "artifacts": [
        {"path": str, "action": "create|modify|delete", "timestamp": datetime}
    ],
    "metadata": {"models": dict, "tools": dict, "tokens": int}
}
```

### Validation
- [ ] Session log exists in `./docs/`
- [ ] Contains thought chain with ≥3 decision points
- [ ] Metadata block is valid YAML
- [ ] All artifacts are tracked

---

## RULE-003: Sync Protocol for Skills & Sessions

**Category:** `governance` | **Priority:** HIGH | **Status:** DRAFT

### Directive

Local skills and sessions MUST be syncable to:
- Remote storage (optional cloud backup)
- Team shared repositories
- Cross-device continuity

See `./docs/SYNC-AGENT-DESIGN.md` for implementation.

---

## RULE-006: Decision Logging

**Category:** `governance` | **Priority:** MEDIUM | **Status:** ACTIVE

### Directive

All strategic decisions MUST be logged in task system, not just chat.

### Decision Log Format

```markdown
## DECISION-XXX: [Title]

**Date:** YYYY-MM-DD
**Context:** [Why this decision was needed]
**Options Considered:**
1. Option A - [pros/cons]
2. Option B - [pros/cons]

**Decision:** [What was decided]
**Rationale:** [Why this option]
**Action:** [What was done / to be done]
**Status:** IMPLEMENTED | PENDING | DEFERRED
```

### Validation
- [ ] Session ends with decision audit
- [ ] Major decisions have DECISION-XXX entry
- [ ] evidence/SESSION-DECISIONS-*.md exists

---

## RULE-011: Multi-Agent Governance Protocol

**Category:** `governance` | **Priority:** CRITICAL | **Status:** ACTIVE

### Directive

Multi-agent systems MUST implement structured governance with human oversight, consensus mechanisms, and evidence-based conflict resolution.

### Governance Layers (Bicameral Model)

```
┌─────────────────────────────────────────────────────────────────────┐
│ UPPER CHAMBER (Human Oversight)                                      │
│ - Veto authority on rule changes                                    │
│ - Strategic steering and prioritization                             │
│ - Ambiguity resolution when AI cannot decide                        │
├─────────────────────────────────────────────────────────────────────┤
│ LOWER CHAMBER (AI Execution)                                         │
│ - Task execution from TypeDB queue                                  │
│ - Evidence collection and hypothesis testing                        │
│ - Peer review and consensus voting                                  │
└─────────────────────────────────────────────────────────────────────┘
```

### Governance MCP Tools

| Tool | Responsibility |
|------|----------------|
| `governance_propose_rule` | Submit rule changes with evidence |
| `governance_vote` | Peer review voting on proposals |
| `governance_dispute` | Raise conflicts for resolution |
| `governance_get_trust_score` | Agent reliability scoring |
| `governance_escalate_to_human` | Trigger human oversight |

### Trust Score Algorithm

```python
Trust = (Compliance × 0.4) + (Accuracy × 0.3) + (Consistency × 0.2) + (Tenure × 0.1)
```

### Validation
- [ ] Governance MCP server implemented
- [ ] TypeDB schema extended
- [ ] Trust scoring operational
- [ ] Human escalation workflow tested

---

## RULE-013: Rules Applicability Convention

**Category:** `governance` | **Priority:** HIGH | **Status:** ACTIVE

### Directive

All code comments, gaps, and TODOs MUST reference applicable governance rules using format:

```
{TYPE}({RULE-ID}): {Description}
```

### Examples

```python
# Good
# TODO(RULE-002): Extract to separate module
# FIXME(RULE-009): Version mismatch - check container version
# GAP-020(RULE-005): Memory threshold exceeded

# Bad
# TODO: Fix this later
# FIXME: This is broken
```

### Gap Format in TODO.md

```markdown
| ID | Gap | Priority | Category | Rule |
|----|-----|----------|----------|------|
| GAP-020 | Memory monitoring | HIGH | stability | RULE-005 |
```

### Validation
- [ ] All TODO comments have RULE-XXX reference
- [ ] Gaps in TODO.md have Rule column populated
- [ ] No orphan gaps in codebase

---

*Per RULE-001: Session Evidence Logging*
