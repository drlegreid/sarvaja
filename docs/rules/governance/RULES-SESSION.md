# Session & Reporting Rules - Sim.ai

Rules governing session evidence, decision logging, and reporting.

> **Parent:** [RULES-GOVERNANCE.md](../RULES-GOVERNANCE.md)
> **Rules:** RULE-001, RULE-003, RULE-006, RULE-018, RULE-026, RULE-029

---

## RULE-001: Session Evidence Logging

**Category:** `governance` | **Priority:** CRITICAL | **Status:** ACTIVE | **Type:** REQUIRED

### Directive

All agent sessions MUST produce evidence logs including:
1. **Thought Chain** - Decisions, rationale, alternatives
2. **Artifact Tracking** - Files modified with timestamps
3. **Session Metadata** - IDs, models, tools, tokens
4. **Export** - `./docs/SESSION-{date}-{topic}.md`

### Schema

```python
session_log = {
    "session_id": str,
    "thought_chain": [{"step": int, "decision": str, "rationale": str}],
    "artifacts": [{"path": str, "action": "create|modify|delete"}],
    "metadata": {"models": dict, "tools": dict, "tokens": int}
}
```

### Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| End session without evidence | Export session log before closing |
| Skip thought chain logging | Document decisions with rationale |
| Omit file modification tracking | List all artifacts with actions |
| Forget session metadata | Include tokens, models, tools used |

---

## RULE-003: Sync Protocol for Skills & Sessions

**Category:** `governance` | **Priority:** HIGH | **Status:** DRAFT | **Type:** RECOMMENDED

### Directive

Local skills and sessions MUST be syncable to:
- Remote storage (optional cloud backup)
- Team shared repositories
- Cross-device continuity

See `docs/SYNC-AGENT-DESIGN.md` for implementation.

---

## RULE-006: Decision Logging

**Category:** `governance` | **Priority:** MEDIUM | **Status:** ACTIVE | **Type:** RECOMMENDED

### Directive

All strategic decisions MUST be logged in task system, not just chat.

### Format

```markdown
## DECISION-XXX: [Title]
**Date:** YYYY-MM-DD
**Context:** [Why needed]
**Options:** 1. A [pros/cons] 2. B [pros/cons]
**Decision:** [What was decided]
**Rationale:** [Why this option]
**Status:** IMPLEMENTED | PENDING | DEFERRED
```

### Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Log decisions only in chat | Record in task system with DECISION-XXX |
| Skip context/rationale | Include why, not just what |
| Omit alternatives considered | Document options evaluated |
| Use vague status | Use IMPLEMENTED/PENDING/DEFERRED |

---

## RULE-018: Objective Reporting

**Category:** `reporting` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** REQUIRED

### Directive

All comparisons and recommendations MUST use **functional feature comparison** rather than subjective ratings.

### Prohibited Patterns

| Pattern | Problem |
|---------|---------|
| Star ratings | Non-measurable |
| Superlatives | Unfounded |
| Flattery | Non-technical bias |

### Required Patterns

| Pattern | Purpose |
|---------|---------|
| Feature matrix | Objective capability list |
| Technical constraints | Measurable limits |
| Integration requirements | Concrete dependencies |
| Build effort | Countable work items |

---

## RULE-026: Decision Context Communication

**Category:** `governance` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** REQUIRED

### Directive

When presenting decisions or recommendations, agents MUST provide full context including:
- Problem statement
- Constraints considered
- Options evaluated
- Rationale for choice
- Trade-offs acknowledged

Never present a decision without context.

### Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Present conclusions without context | Start with problem statement |
| Skip trade-off analysis | Acknowledge what was sacrificed |
| Hide constraints | List limitations openly |
| Present single option | Show alternatives considered |

---

## RULE-029: Executive Reporting Pattern

**Category:** `governance` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** REQUIRED

### Directive

Enterprise sessions MUST produce executive summaries including:
- Session scope and objectives
- Key decisions made
- Tasks completed/pending
- Metrics summary
- Next steps

### Format

```markdown
# Executive Report: {Session Topic}
**Date:** YYYY-MM-DD | **Phase:** P{X}

## Summary
[2-3 sentence overview]

## Key Decisions
| ID | Decision | Rationale |

## Metrics
| Metric | Value |

## Next Steps
1. [Action item]
```

### Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Skip executive summary | Include 2-3 sentence overview |
| List tasks without status | Mark completed/pending clearly |
| Omit metrics | Include quantitative measures |
| End without next steps | List concrete action items |

---

*Per RULE-012: DSP Semantic Code Structure*
