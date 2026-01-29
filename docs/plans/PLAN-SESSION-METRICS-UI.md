# Plan: Session Metrics Dashboard UI Integration

**Gap:** GAP-SESSION-METRICS-UI
**Rule:** SESSION-METRICS-01-v1
**Priority:** HIGH
**Created:** 2026-01-29
**Approach:** TDD/BDD (tests before implementation)

---

## Problem Statement

The session metrics backend is 100% complete (6/6 gaps resolved, 177 tests passing) with two MCP tools (`session_metrics`, `session_search`) but **0% dashboard UI integration**. Users cannot visualize session analytics, search session content, or view activity timelines through the governance dashboard.

## Architecture Integration Points

Following the established Sarvaja dashboard patterns:

```
Layer              │ New Files                              │ Pattern Source
───────────────────┼────────────────────────────────────────┼──────────────────
API Route          │ governance/routes/metrics.py           │ reports.py
Data Access        │ agent/governance_ui/data_access/metrics.py │ executive.py
State              │ agent/governance_ui/state/metrics.py   │ state/initial.py
Controller         │ agent/governance_ui/controllers/metrics.py │ data_loaders.py
View               │ agent/governance_ui/views/metrics_view.py  │ infra_view.py
Navigation         │ (modify) state/constants.py            │ existing nav items
Dashboard Wire     │ (modify) governance_dashboard.py       │ existing view wiring
Route Registration │ (modify) governance/api.py             │ existing router includes
```

## Implementation Steps (TDD)

### Phase 1: API Route (FastAPI)

**File:** `governance/routes/metrics.py`

Endpoints:
- `GET /api/metrics/summary` — Aggregated session metrics (calls session_metrics engine)
  - Query params: `days` (int, default 5), `idle_threshold_min` (int, default 30)
  - Response: `{ totals, days[], tool_breakdown, correlation, agents, metadata }`
- `GET /api/metrics/search` — Session content search
  - Query params: `query`, `session_id`, `git_branch`, `max_results` (default 50)
  - Response: `{ results[], total_matches, metadata }`
- `GET /api/metrics/timeline` — Per-day activity timeline
  - Query params: `days` (int, default 30)
  - Response: `{ timeline[], metadata }`

**Tests:** `tests/unit/test_metrics_routes.py` — 12 TDD tests
- TestMetricsSummary (4): returns 200, has totals, has days, has tool_breakdown
- TestMetricsSearch (4): returns 200, matches query, filters by branch, empty query
- TestMetricsTimeline (4): returns 200, sorted by date, has entry_count, JSON serializable

### Phase 2: Data Access Layer

**File:** `agent/governance_ui/data_access/metrics.py`

Functions:
- `get_session_metrics_summary(days, idle_threshold_min)` → calls REST API
- `search_session_content(query, session_id, git_branch, max_results)` → calls REST API
- `get_activity_timeline(days)` → calls REST API

**Tests:** `tests/unit/test_metrics_data_access.py` — 6 TDD tests
- Returns dict with expected keys, handles API errors gracefully, returns empty on 500

### Phase 3: State + Navigation

**Modify:** `agent/governance_ui/state/constants.py`
- Add `{'title': 'Metrics', 'icon': 'mdi-chart-line', 'value': 'metrics'}` to `NAVIGATION_ITEMS`

**File:** `agent/governance_ui/state/metrics.py`

State properties:
- `metrics_data`, `metrics_loading`, `metrics_error`
- `metrics_days_filter` (5/7/14/30)
- `metrics_search_query`, `metrics_search_results`, `metrics_search_loading`
- `metrics_timeline`, `metrics_active_tab` (summary/search/timeline)

### Phase 4: View Component

**File:** `agent/governance_ui/views/metrics_view.py`

UI sections:
1. **Header** — Title + days filter dropdown + refresh button
2. **Summary Tab** — Stat cards (active time, sessions, messages, tools, MCP calls, errors) + per-day table
3. **Search Tab** — Search input + session/branch filters + results list
4. **Timeline Tab** — Per-day activity cards with tools/branches/snippets
5. **Tool Breakdown** — Sorted tool usage table

All elements have `data-testid` attributes for POM testing.

### Phase 5: Controller

**File:** `agent/governance_ui/controllers/metrics.py`

Handlers:
- `load_metrics_data()` — Fetch summary from API
- `load_metrics_timeline()` — Fetch timeline from API
- `search_metrics()` — Execute content search
- `change_metrics_days()` — Update days filter + reload

### Phase 6: Dashboard Wiring

**Modify:** `agent/governance_dashboard.py`
- Import `build_metrics_view`
- Call `build_metrics_view()` in VMain content area
- Add `load_metrics_data` to view change handler for `active_view == 'metrics'`

**Modify:** `governance/api.py`
- Import and include `metrics_router`

**Modify:** `governance/routes/__init__.py`
- Export `metrics_router`

### Phase 7: Robot Framework Browser Tests

**File:** `tests/robot/unit/session_metrics_ui.robot` — 5 BDD tests
- Metrics navigation item exists
- Metrics view loads data
- Search returns results
- Timeline shows days
- Days filter changes data

## File Summary

| Action | File | Lines (est.) |
|--------|------|-------------|
| CREATE | `governance/routes/metrics.py` | ~120 |
| CREATE | `agent/governance_ui/data_access/metrics.py` | ~80 |
| CREATE | `agent/governance_ui/state/metrics.py` | ~50 |
| CREATE | `agent/governance_ui/views/metrics_view.py` | ~280 |
| CREATE | `agent/governance_ui/controllers/metrics.py` | ~100 |
| CREATE | `tests/unit/test_metrics_routes.py` | ~150 |
| CREATE | `tests/unit/test_metrics_data_access.py` | ~80 |
| MODIFY | `agent/governance_ui/state/constants.py` | +1 |
| MODIFY | `agent/governance_ui/state/initial.py` | +12 |
| MODIFY | `agent/governance_ui/data_access/__init__.py` | +8 |
| MODIFY | `agent/governance_ui/views/__init__.py` | +2 |
| MODIFY | `agent/governance_ui/controllers/__init__.py` | +6 |
| MODIFY | `agent/governance_dashboard.py` | +8 |
| MODIFY | `governance/routes/__init__.py` | +2 |
| MODIFY | `governance/api.py` | +2 |

**Total: 6 new files, 9 modified files, ~18 TDD tests + 5 BDD tests**

---

*Per SESSION-METRICS-01-v1 | GAP-SESSION-METRICS-UI*
