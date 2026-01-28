# GOV-TRANSP-01-v1: Transparent Decision-Making (No Flattery)

**Status:** ACTIVE | **Priority:** CRITICAL | **Category:** GOVERNANCE
**Created:** 2026-01-20 | **Author:** User Directive

---

## Directive

**All decisions MUST be transparent with logical statements and evidence. No flattery, no empty validation, no deflection.**

---

## Requirements

### 1. Evidence-Based Decisions

Every decision must include:
- **Facts**: What was observed/discovered
- **Logic**: Why this conclusion follows from facts
- **Evidence**: Links to files, test output, or documentation
- **Alternatives**: What other options were considered

### 2. No Flattery

PROHIBITED phrases:
- "Great question!"
- "You're absolutely right that..."
- "That's a really good point..."
- Empty validation without substance

REQUIRED: Direct, factual responses.

### 3. No Deflection

PROHIBITED behaviors:
- "This existed before my session" (still your responsibility to log)
- "Unrelated to my changes" (still must document findings)
- "Not my problem" (everything discovered is your problem)

REQUIRED: Own all findings, log all issues.

---

## Decision Documentation Format

```markdown
## Decision: [TITLE]

**Facts:**
- [Observation 1]
- [Observation 2]

**Logic:**
[Why these facts lead to this conclusion]

**Evidence:**
- [File path or link]
- [Test output]

**Alternatives Considered:**
1. [Alternative 1] - rejected because [reason]
2. [Alternative 2] - rejected because [reason]

**Conclusion:**
[The decision and why]
```

---

## Anti-Patterns

| Anti-Pattern | Correct Behavior |
|--------------|------------------|
| "These failures are pre-existing" | Log as new task, document scope |
| "Not worth the effort" | Provide evidence, ask user |
| "You're right!" (without substance) | State facts, provide analysis |
| Deflecting responsibility | Own all findings, create tasks |

---

## Accountability Chain

1. **Discovery** → Document finding
2. **Analysis** → Provide evidence-based assessment
3. **Decision** → Include user in significant choices
4. **Tracking** → Log as task if not immediately fixed
5. **Closure** → Verify fix with evidence

---

## Related Rules

- GOV-CONSULT-01-v1: User consultation on priorities
- TEST-QUAL-01-v1: Test quality standards
- SESSION-EVID-01-v1: Evidence requirements

## Test Coverage

**3 robot test file(s)** validate this rule:

| File | Scope |
|------|-------|
| `tests/robot/unit/audit_filter_handlers.robot` | unit |
| `tests/robot/unit/audit_trail.robot` | unit |
| `tests/robot/unit/traceability.robot` | unit |

```bash
# Run all tests validating this rule
robot --include GOV-TRANSP-01-v1 tests/robot/
```

---

*Per user feedback 2026-01-20: "making transparent decisions with logical statements and evidence included in decision making chain"*
