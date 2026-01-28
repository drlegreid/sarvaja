# GOV-NOEST-01-v1: No Time Estimates

**Status:** ACTIVE | **Priority:** HIGH | **Category:** GOVERNANCE
**Created:** 2026-01-20 | **Author:** User Directive

---

## Directive

**Never provide time estimates. No one can control time - especially when bugs happen.**

---

## Prohibited Phrases

- "~30 minutes"
- "2-3 hours"
- "should take about..."
- "estimated effort: X hours"
- "quick fix"
- "this will be fast"
- Any duration prediction

---

## Correct Behavior

Instead of time estimates, describe:
- **Scope**: Number of files, functions, or points to address
- **Complexity**: Simple/Medium/Complex
- **Dependencies**: What must happen first
- **Risk**: What could go wrong

### Example

**WRONG:**
```
This task will take ~2 hours
```

**CORRECT:**
```
Scope: 3 files, 5 functions to modify
Complexity: Medium - requires understanding mock setup
Dependencies: None
Risk: May uncover additional test issues
```

---

## Rationale

1. **Unpredictability**: Bugs, edge cases, and discoveries invalidate estimates
2. **False Precision**: Estimates create false expectations
3. **Pressure**: Time pressure leads to shortcuts and lower quality
4. **Focus**: Focus on scope and quality, not speed

---

## Related Rules

- GOV-CONSULT-01-v1: User consultation
- GOV-TRANSP-01-v1: Transparent decision-making
- TEST-QUAL-01-v1: Quality over speed

---

*Per user directive 2026-01-20: "stop providing estimates in hours - no one can control time"*
