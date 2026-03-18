# TEST-E2E-FRAMEWORK-01-v1: E2E Test Framework Quality Standard

| Field | Value |
|-------|-------|
| **Rule ID** | TEST-E2E-FRAMEWORK-01-v1 |
| **Category** | testing |
| **Priority** | MANDATORY |
| **Status** | ACTIVE |
| **Created** | 2026-02-20 |

## Directive

The E2E test framework MUST follow SRP, DRY, and OOP principles with Robot Framework as the execution engine. All reusable actions (clicking, scrolling, text input, waiting) MUST be centralized in Python keyword libraries. No test file may exceed 300 lines. Problematic platform behaviors (e.g., Vuetify overlay interception, Trame WebSocket degradation) MUST be addressed via centralized library methods, not duplicated per test.

## Requirements

### Architecture
- **Robot Framework** with Browser Library (Playwright backend) for all browser E2E tests
- **Python keyword libraries** for reusable actions, split by domain/action/concern
- **Resource files** (.resource) for shared variables, selectors, and keyword imports
- **Test suites** (.robot) organized by UI domain (dashboard, sessions, tasks, rules, etc.)

### File Size & Organization (DOC-SIZE-01-v1)
- Maximum **300 lines** per file (library, resource, or suite)
- Split by **concern**: actions (generic), navigation, overlay management, domain-specific
- One Python library class per file following **SRP**

### Centralized Actions (DRY)
All low-level browser interactions MUST be defined once in keyword libraries:

| Action | Library | Description |
|--------|---------|-------------|
| Click Element Safely | actions.py | Click with overlay pre-check |
| Wait For Element With Backoff | actions.py | Fibonacci backoff retry (1,1,2,3,5,8,13,21s) |
| Fill Input Field | actions.py | Clear + type with validation |
| Scroll To Element | actions.py | Scroll into viewport before interaction |
| Navigate To Tab | navigation.py | Click nav item + verify page loaded |
| Dismiss Overlays | overlay.py | CSS injection for Vuetify overlay scrim |

### Fibonacci Backoff Wait
The `Wait For Element With Backoff` keyword MUST use Fibonacci sequence intervals:
```
Attempt 1: wait 1s → check
Attempt 2: wait 1s → check
Attempt 3: wait 2s → check
Attempt 4: wait 3s → check
Attempt 5: wait 5s → check
Attempt 6: wait 8s → check (total: 20s)
Max attempts configurable (default: 6)
```

### Platform Workarounds
Known platform issues MUST be handled centrally:
- **Vuetify overlay scrim** → CSS injection in `overlay.py`, applied via Suite Setup
- **Trame WS degradation** → Fibonacci backoff in `actions.py`
- **Async state changes** → `Wait For Element With Backoff` after all click-triggers

### OOP Structure
```python
class ActionsLibrary:
    """Generic browser actions — SRP: only element interactions."""
    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def click_element_safely(self, selector, timeout=10):
        ...

    def wait_for_element_with_backoff(self, selector, max_attempts=6):
        ...
```

## Verification
- `robot --outputdir results/ tests/e2e/robot/suites/` runs all E2E tests
- No file in `tests/e2e/robot/` exceeds 300 lines
- All actions used in .robot files trace back to keyword libraries (no inline Playwright calls)
- Fibonacci backoff is used for all entity-load waits

## Dependencies
- TEST-E2E-01-v1 (3-tier validation)
- TEST-BDD-01-v1 (BDD paradigm)
- DOC-SIZE-01-v1 (file size limit)
