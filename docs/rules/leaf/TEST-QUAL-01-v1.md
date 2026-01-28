# TEST-QUAL-01-v1: Fix Failing Tests (Quality Over Speed)

**Status:** ACTIVE | **Priority:** CRITICAL | **Category:** TEST
**Created:** 2026-01-20 | **Author:** User Directive

---

## Directive

**Failing tests MUST be fixed. Quality is the top priority, not speed. Less errors = less context consumption.**

---

## Core Principles

1. **Quality > Speed**: Never dismiss failing tests to move faster
2. **Context Efficiency**: Failing tests consume context on every run
3. **Signal Clarity**: Noise failures hide real issues
4. **Zero Tolerance**: Every test failure is a task to be fixed

---

## Requirements

### On Test Failure Discovery

1. **Log as Task**: Create task with:
   - Test name(s)
   - Error message(s)
   - Root cause analysis (if known)
   - Proposed fix approach

2. **Do NOT Dismiss**: Phrases like "pre-existing" or "unrelated to my changes" are PROHIBITED without also logging a fix task

3. **Prioritize Fix**: Consider fixing immediately if:
   - Simple environment/config issue
   - Mock expectation mismatch
   - < 30 minutes estimated effort

### Task Format for Test Failures

```markdown
## Task: FIX-TEST-[DATE]-[NUMBER]

**Failing Tests:**
- `test_name_1` - [error summary]
- `test_name_2` - [error summary]

**Root Cause:**
[Analysis of why tests fail]

**Proposed Fix:**
[How to fix]

**Evidence:**
- Test output: [path to evidence file]
- Related code: [file:line]
```

---

## Noise Test Categories

| Category | Example | Fix Priority |
|----------|---------|--------------|
| Environment mismatch | Host `typedb` vs `localhost` | HIGH - affects all runs |
| Mock expectations | Called 3x instead of 1x | HIGH - test logic broken |
| Flaky timing | Intermittent timeout | MEDIUM - needs investigation |
| Missing fixtures | Setup not run | HIGH - blocks test suite |

---

## Evidence Requirements

Every test fix MUST produce:
1. Before: Evidence file showing failure
2. After: Evidence file showing all tests pass
3. Task linkage: Fix task linked to evidence

---

## Metrics

Track and reduce:
- **Noise failures per run**: Target = 0
- **Time to fix discovered failures**: Target < 1 session
- **Context burned on noise**: Minimize repeated failure output

---

## Related Rules

- TEST-FIX-01-v1: Test evidence production
- TEST-GUARD-01-v1: Test coverage requirements
- GOV-TRANSP-01-v1: Transparent decision-making

## Test Coverage

**1 robot test file(s)** validate this rule:

| File | Scope |
|------|-------|
| `tests/robot/unit/quality_analyzer_split.robot` | unit |

```bash
# Run all tests validating this rule
robot --include TEST-QUAL-01-v1 tests/robot/
```

---

*Per user feedback 2026-01-20: "noise failing tests should be fixed - because we have another rule about top QUALITY priority (not fucking speed). less errors - less context consumption."*
