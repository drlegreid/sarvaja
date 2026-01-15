# GAP-UI-EXP-012: Agents Not Loading in UI Views

**Status:** OPEN
**Priority:** HIGH
**Category:** data-loading
**Discovered:** 2026-01-14 via Playwright exploratory testing

## Problem Statement

The Agents view and Trust Dashboard show "0 agents registered" despite the REST API returning 8 agents.

## Evidence

### REST API Response
```json
GET /api/agents → 200 OK
Returns 8 agents with varied trust scores (0.75 - 0.95)
```

### UI State
- Agents view: "0 agents registered"
- Trust Dashboard: "Total Agents: 0", "Avg Trust Score: 0.0%"
- After clicking Refresh: Still shows 0 agents

## Root Cause Analysis

### Suspected Issue: Hardcoded API URLs in Handlers

Multiple handler files have hardcoded `API_BASE_URL = "http://localhost:8082"`:

| File | Line |
|------|------|
| `handlers/common_handlers.py` | Line 18 |
| `handlers/rule_handlers.py` | Line 11 |
| `handlers/session_handlers.py` | Line 11 |
| `handlers/task_handlers.py` | Line 11 |

While `GOVERNANCE_API_URL` environment variable is set in docker-compose.yml, the handlers don't use it.

### Alternative: Initialization Timing

The agents data might not be loaded during initial state setup. The `load_agents_data()` function in `data_loaders.py` may not be called at startup.

## Recommended Fix

1. **Option A**: Replace hardcoded URLs with environment variable:
```python
import os
API_BASE_URL = os.environ.get("GOVERNANCE_API_URL", "http://localhost:8082")
```

2. **Option B**: Ensure `load_agents_data()` is called at dashboard startup

3. **Option C**: Add agents loading to the `refresh_all_data()` function

## Verification Steps

1. Check browser console for API call errors
2. Verify `load_agents_data()` is being called
3. Check network tab for `/api/agents` requests

## Related

- TECH-DISC-001: Container networking discovery (similar pattern)
- GAP-UI-EXP-006: Infrastructure health (fixed with container-aware URLs)

---
*Per GAP-DOC-01-v1: Full technical details in evidence file*
