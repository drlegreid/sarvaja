# TEST-COMP-02-v1: Test Before Ship

**Category:** `quality` | **Priority:** CRITICAL | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Legacy ID:** RULE-023
> **Location:** [RULES-TESTING.md](../operational/RULES-TESTING.md)
> **Tags:** `testing`, `quality`, `shipping`, `ci`

---

## Directive

All code, UIs, and components MUST be tested before claiming complete. No shipping untested code.

---

## Test Levels

| Level | What | When |
|-------|------|------|
| **L1: Import** | Module imports | After writing |
| **L2: Init** | Class instantiates | After writing |
| **L3: Smoke** | Basic happy path | Before claiming done |
| **L4: Edge** | Edge cases | Before merge/release |

---

## E2E Testing Mandate

For UI gaps, marking RESOLVED requires **both**:
1. Unit tests passing
2. **E2E browser verification** via Playwright

Unit tests alone are INSUFFICIENT for UI claims.

---

## Playwright Browser Testing

| Function | Python Method | Use Case |
|----------|---------------|----------|
| **Navigate** | `page.goto(url)` | Load dashboard at URL |
| **Screenshot** | `page.screenshot(path=...)` | Capture visual state |
| **Click** | `page.click(selector)` | Interact with elements |
| **Inspect** | `page.query_selector_all(...)` | Get DOM elements |
| **Debug** | `page.content()` | Check HTML output |

---

## Validation

- [ ] All test levels passed
- [ ] E2E verification complete for UI
- [ ] Evidence captured

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
