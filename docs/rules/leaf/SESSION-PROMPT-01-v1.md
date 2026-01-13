# SESSION-PROMPT-01-v1: Initial Prompt Capture

**Category:** `governance` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Legacy ID:** RULE-050
> **Location:** [RULES-GOVERNANCE.md](../governance/RULES-GOVERNANCE.md)
> **Tags:** `session`, `evidence`, `prompt`, `intent`, `traceability`

---

## Directive

All session evidence MUST include the initial user prompt that started the session. This establishes:

1. **Original Intent** - What the user actually requested
2. **Scope Baseline** - Reference for intent verification (INTENT-CHECK-01-v1)
3. **Audit Trail** - Complete session traceability

---

## Evidence Format

### Session Evidence File

```markdown
## Session: {TOPIC}

**Date:** {YYYY-MM-DD}
**Session ID:** SESSION-{date}-{topic}

### Initial Prompt

> {Verbatim copy of user's first message that started the session}

### Interpreted Intent

{Agent's understanding of what was requested}

### Session Work

{Rest of session evidence...}
```

---

## Capture Points

| When | What | How |
|------|------|-----|
| Session Start | First user message | Copy verbatim to evidence |
| Context Compaction | Summarize prompt | Include in summary |
| AMNESIA Recovery | Reference prompt | Query from evidence file |

---

## Integration

### With SESSION-EVID-01-v1
Initial prompt is part of mandatory session evidence.

### With INTENT-CHECK-01-v1
Original prompt is the baseline for intent verification.

### With REPORT-ISSUE-01-v1
STATUS/CERT issues should reference the original prompt.

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Paraphrase initial prompt | Quote verbatim |
| Skip prompt in evidence | Always include as first section |
| Lose prompt after compaction | Preserve in summary |
| Assume intent without reference | Check against original prompt |

---

## Automation

### MCP Tool Enhancement

```python
# session_capture_intent now includes prompt field
session_capture_intent(
    goal="...",
    source="...",
    initial_prompt="User's verbatim first message"
)
```

### Evidence Template

```markdown
### Initial Prompt

> {prompt}

**Captured:** {timestamp}
**Word Count:** {count}
**Key Terms:** {extracted terms}
```

---

## Validation

- [ ] Initial prompt captured verbatim
- [ ] Prompt appears in evidence file
- [ ] Intent interpretation follows prompt
- [ ] Prompt preserved through compaction

---

*Per SESSION-EVID-01-v1: Session Evidence Logging*
*Per INTENT-CHECK-01-v1: Intent Verification*
