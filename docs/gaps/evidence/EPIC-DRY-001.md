# EPIC-DRY-001: Enforce DRY Principle with Shared Constants

## Status: RESOLVED
## Priority: HIGH
## Created: 2026-01-17
## Resolved: 2026-01-17

## Problem Statement

The codebase has scattered hardcoded strings that violate the DRY (Don't Repeat Yourself) principle. The recent "Sim.ai" → "Sarvaja" rename required updating 15+ files with the same string.

## Resolution

Created `shared/constants.py` as single source of truth for application constants.

### Files Created
- `shared/__init__.py` - Package exports
- `shared/constants.py` - Central constants (103 lines)

### Constants Defined
- `APP_NAME`, `APP_TITLE`, `APP_VERSION`
- `DEFAULT_PORTS` (dashboard, api, typedb, chromadb, litellm, ollama)
- `DEFAULT_HOSTS` (localhost for all services)
- `DEFAULT_TIMEOUTS` (page_load, element_wait, api_request, typedb_query, test_step)
- `API_BASE_URL`, `DASHBOARD_URL` (computed from hosts/ports)
- `TYPEDB_DATABASE`, `CHROMADB_COLLECTION`

### Files Updated (7 files)
| File | Changes |
|------|---------|
| `agent/governance_dashboard.py` | Import APP_TITLE, replaced 2 hardcoded strings |
| `tests/e2e/conftest.py` | Import APP_TITLE, DASHBOARD_URL, API_BASE_URL |
| `tests/e2e/test_dashboard_e2e.py` | Replaced 7 occurrences |
| `tests/shared/pages.py` | Import constants, use APP_TITLE |
| `tests/e2e/steps/conftest.py` | Import constants |
| `tests/e2e/steps/test_dashboard_steps.py` | Import constants, replaced DASHBOARD_URL and title |
| `tests/ui/pages/base_page.py` | Import constants, use DASHBOARD_URL and APP_TITLE |

### Remaining (Acceptable)
- `tests/e2e/features/dashboard.feature` - BDD Gherkin files use human-readable strings by design
- `tests/ui/resources/governance.resource` - Robot Framework docs/vars (could be refactored later)

## Subtasks

| ID | Task | Status |
|----|------|--------|
| DRY-001.1 | Create shared/constants.py with APP_TITLE, VERSION | ✅ DONE |
| DRY-001.2 | Create shared/locators.py with UI selectors | ⏭️ DEFERRED |
| DRY-001.3 | Create shared/urls.py with API endpoints | ✅ DONE (in constants.py) |
| DRY-001.4 | Update agent/governance_dashboard.py | ✅ DONE |
| DRY-001.5 | Update all test files to use constants | ✅ DONE |
| DRY-001.6 | Add pre-commit hook for constant enforcement | ⏭️ DEFERRED |

## Benefits

1. **Single source of truth** - Change one place, update everywhere
2. **Type safety** - IDE autocomplete for constants
3. **Documentation** - Constants module documents valid values
4. **Test reliability** - Tests always match implementation

## Related Rules

- RULE-032 (DOC-SIZE-01-v1): File size limits promote modularization
- RULE-017 (UI-TRAME-01-v1): Cross-workspace pattern reuse

## Example Implementation

```python
# shared/constants.py
APP_TITLE = "Sarvaja Governance Dashboard"
APP_VERSION = "1.3.1"
DEFAULT_PORTS = {
    "dashboard": 8081,
    "api": 8082,
    "typedb": 1729,
    "chromadb": 8001,
}
```

```python
# agent/governance_dashboard.py
from shared.constants import APP_TITLE
v3.VAppBarTitle(APP_TITLE)

# tests/e2e/conftest.py
from shared.constants import APP_TITLE
page.wait_for_selector(f"text={APP_TITLE}", timeout=10000)
```
