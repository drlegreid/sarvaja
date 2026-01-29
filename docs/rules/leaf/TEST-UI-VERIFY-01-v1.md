# TEST-UI-VERIFY-01-v1: UI Feature Visual Verification

**Legacy ID:** RULE-052
**Category:** `testing`
**Priority:** HIGH
**Status:** ACTIVE
**Type:** OPERATIONAL
**Created:** 2026-01-14
**Updated:** 2026-01-29

## Directive

UI features MUST be visually verified using Playwright MCP before marking RESOLVED. Data layer tests alone are INSUFFICIENT.

## Verification Requirements

1. **Screenshot/Snapshot** - `mcp__playwright__browser_snapshot()` or `mcp__playwright__browser_take_screenshot()` showing feature renders
2. **User Interaction** - `mcp__playwright__browser_click()` / `browser_fill_form()` testing user action
3. **State Binding** - Verify Vue/Trame state binds to UI component via DOM inspection

## MCP Tool Bindings (MANDATORY)

| Step | MCP Tool | Purpose |
|------|----------|---------|
| Navigate | `mcp__playwright__browser_navigate(url)` | Load the page containing the feature |
| Verify render | `mcp__playwright__browser_snapshot()` | Accessibility tree confirms elements exist |
| Screenshot | `mcp__playwright__browser_take_screenshot()` | Visual evidence for audit trail |
| Interact | `mcp__playwright__browser_click(element)` | Test button/link/tab behavior |
| Form test | `mcp__playwright__browser_fill_form(values)` | Test input/select/filter behavior |

**Prerequisite**: Dashboard must be running at `localhost:8081`. If not running, document as BLOCKED (not skip verification).

## API Companion Verification

When a UI feature calls REST API endpoints, ALSO verify the API:

| Step | MCP Tool | Purpose |
|------|----------|---------|
| Test endpoint | `mcp__rest-api__test_request(method, path)` | Confirm endpoint responds |
| Validate schema | Check response JSON structure | Confirm UI will receive expected data |

Per ARCH-MCP-01-v1: Both `rest-api` and `playwright` MCPs required for API+UI features.

## Origin

Per GAP-UI-048 lesson: TDD for data models passed (35 tests) but UI trace bar never rendered to screen. Feature was marked RESOLVED but invisible to users.

Per GAP-SESSION-METRICS-UI lesson (2026-01-29): 20 pytest tests passed, 7 implementation phases complete, but neither `rest-api` nor `playwright` MCP was called. Feature committed without live verification.

## Anti-Pattern

```
# WRONG: Only test data layer
def test_trace_event_creation():
    event = TraceEvent(...)
    assert event.to_dict() == {...}
# Tests pass, UI never built — INVISIBLE to users
```

## Correct Pattern

```python
# RIGHT: Test data layer + MCP visual verification
# Step 1: Unit test (pytest)
def test_trace_event_creation():
    event = TraceEvent(...)
    assert event.to_dict() == {...}

# Step 2: API verification (rest-api MCP)
# mcp__rest-api__test_request("GET", "/api/metrics/summary")
# → Confirm 200 + valid JSON

# Step 3: Visual verification (playwright MCP)
# mcp__playwright__browser_navigate("http://localhost:8081")
# mcp__playwright__browser_click("[data-testid='nav-metrics']")
# mcp__playwright__browser_snapshot()
# → Confirm metrics-dashboard element exists in accessibility tree
```

## Related Rules

- ARCH-MCP-01-v1: MCP Usage Protocol (verification gate)
- TEST-COMP-01-v1: LLM-Driven E2E Test Generation
- TEST-BDD-01-v1: BDD Testing Standard

## Evidence

- GAP-UI-048: Bottom bar feature — data layer done, UI missing
- GAP-SESSION-METRICS-UI: API+UI feature — 20 tests pass, no MCP verification
- Session 2026-01-14: Delivery audit revealed incomplete implementation
