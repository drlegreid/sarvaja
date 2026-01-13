# INTENT-CHECK-01-v1: Intent Verification Before Completion

**Category:** `governance` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Legacy ID:** RULE-045
> **Location:** [RULES-GOVERNANCE.md](../governance/RULES-GOVERNANCE.md)
> **Tags:** `intent`, `verification`, `completion`, `quality`

---

## Directive

Before marking any task complete, agent MUST verify output aligns with original user intent.

**Required Verification Steps:**
1. **Restate** - Echo user's original request
2. **Compare** - Match output against intent
3. **Flag** - Identify any divergence
4. **Clarify** - If ambiguous, ask before proceeding

---

## Enforcement Modes

Per hybrid architecture, this rule supports two enforcement modes:

### Single Agent Mode (Default)
```
CHECKPOINT before task completion:
1. Extract original user intent from conversation
2. List what was actually delivered
3. Compare: delivered vs requested
4. If mismatch detected:
   - Minor: Note divergence, proceed
   - Major: AskUserQuestion before marking complete
```

### Auditor Agent Mode (RD-WORKSPACE Phase 5)
```
HANDOFF to auditor:
1. Primary agent submits completion claim
2. Auditor extracts original intent
3. Auditor compares deliverables to intent
4. Auditor approves or returns with corrections
```

**Mode Switch:** Set via `agent_mode: single|auditor` in workspace config.

---

## Intent Extraction

| User Says | Extract As |
|-----------|------------|
| "session length" | TIME DURATION (not line count) |
| "fix the bug" | RESOLVE ROOT CAUSE (not workaround) |
| "add tests" | AUTOMATED TESTS (not manual checklist) |
| "summarize" | CONCISE OVERVIEW (not full details) |

**Ambiguity Signals:**
- Multiple valid interpretations
- Missing specifics (format, scope, target)
- Implied vs explicit requirements

---

## Verification Checklist

```markdown
## Intent Verification
**Original Request:** [quote user]
**Interpreted As:** [your understanding]
**Delivered:** [what you produced]
**Match:** YES / PARTIAL / NO
**Divergence:** [if any, explain]
```

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Assume interpretation is correct | Verify ambiguous terms |
| Deliver different format than asked | Match requested format |
| Add unrequested features | Deliver exactly what's asked |
| Skip verification on "simple" tasks | Verify ALL completions |

---

## Examples

### Good: Intent Verified
```
User: "Show me session lengths"
Agent: "You asked for session TIME DURATION.
        I found duration data in 4/19 sessions.
        Here's the duration table: [table]
        Note: 15 sessions lack duration tracking."
```

### Bad: Intent Misread
```
User: "Show me session lengths"
Agent: "Here are session line counts: [table]"
# VIOLATION: Interpreted "length" as size, not duration
```

---

## Integration with RD-INTENT

This rule complements session-level intent tracking (RD-INTENT):
- **RD-INTENT:** Session goals, outcomes, handoffs
- **INTENT-CHECK-01-v1:** Task-level intent verification

Both work together for full intent traceability.

---

## Validation

- [ ] Original intent restated before completion
- [ ] Output compared to intent
- [ ] Divergences flagged
- [ ] Ambiguities clarified with user

---

*Per SESSION-EVID-01-v1: Session Evidence Logging*
