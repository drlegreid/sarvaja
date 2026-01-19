# TEST-UI-VERIFY-01-v1: UI Feature Visual Verification

**Legacy ID:** RULE-052
**Category:** `testing`
**Priority:** HIGH
**Status:** ACTIVE
**Type:** OPERATIONAL
**Created:** 2026-01-14

## Directive

UI features MUST be visually verified before marking RESOLVED. Data layer tests alone are INSUFFICIENT.

## Verification Requirements

1. **Screenshot/Snapshot** - Playwright accessibility snapshot or PNG showing feature renders
2. **User Interaction** - Click, input, or other user action tested
3. **State Binding** - Verify Vue/Trame state binds to UI component

## Origin

Per GAP-UI-048 lesson: TDD for data models passed (35 tests) but UI trace bar never rendered to screen. Feature was marked RESOLVED but invisible to users.

## Anti-Pattern

```
# WRONG: Only test data layer
def test_trace_event_creation():
    event = TraceEvent(...)
    assert event.to_dict() == {...}
# Tests pass, UI never built
```

## Correct Pattern

```python
# RIGHT: Test data layer + visual verification
def test_trace_bar_renders():
    # 1. Data layer test
    event = TraceEvent(...)
    assert event.to_dict() == {...}

    # 2. Visual verification
    page.goto("http://localhost:8081")
    snapshot = page.accessibility.snapshot()
    assert "trace-bar" in str(snapshot)
```

## Related Rules

- TEST-COMP-01-v1: LLM-Driven E2E Test Generation
- SESSION-DSP-01-v1: Exploratory Test Automation
- WORKFLOW-VALID-01-v1: Fix-Then-Validate Protocol

## Evidence

- GAP-UI-048: Bottom bar feature - data layer done, UI missing
- Session 2026-01-14: Delivery audit revealed incomplete implementation
