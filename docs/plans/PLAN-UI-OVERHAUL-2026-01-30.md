# Plan: UI Functional Overhaul - Operator Feedback Response

**ID:** PLAN-UI-OVERHAUL-001
**Priority:** CRITICAL
**Created:** 2026-01-30
**Approach:** TDD (tests before implementation, per-epic)
**Source:** Operator orthogonal review of all 16 dashboard tabs

---

## Executive Summary

Operator reviewed all 16 dashboard tabs and identified systemic gaps:
- Dark theme broken (white content on dark background)
- No grid/column views (lists instead of data tables)
- Missing traceability (task<>rule<>session linkage)
- Inactionable views (no drill-down, no "pass to agent" buttons)
- State sync across browser windows (Trame shared state)
- Container doesn't hot-reload on code changes

---

## EPIC 0: Infrastructure & Cross-Cutting (BLOCKER)

> These block all other work. Must be resolved first.

### 0.1 Dark Theme Fix (ALL TABS)

**Problem:** Content windows stay white in dark mode; text unreadable.
**Root cause:** Vuetify theme not applied to content areas; cards/dialogs use hardcoded light backgrounds.
**Impact:** Every single tab is affected.

**TDD:**
```
tests/unit/test_dark_theme.py
- test_vuetify_theme_toggle_exists()
- test_dark_mode_state_variable_wired()
- test_content_cards_inherit_theme()
- test_mermaid_uses_dynamic_theme()
```

**Fix:**
- Wire `dark_mode` state to Vuetify `v-app` theme prop: `theme="dark_mode ? 'dark' : 'light'"`
- Audit ALL `VCard`, `VDialog`, `VSheet`, `VAlert` for hardcoded `color=` overrides
- Update Mermaid init to use `theme: dark_mode ? 'dark' : 'default'`
- Add theme toggle to app bar

**Files:**
- `agent/governance_dashboard.py` (VApp theme binding)
- `agent/governance_ui/components/mermaid.py` (dynamic theme)
- `agent/governance_ui/state/initial.py` (dark_mode default)
- All view files (audit hardcoded colors)

**Priority:** CRITICAL | **Dependency:** None

### 0.2 Container Hot-Reload

**Problem:** Code changes require manual container restart.
**Root cause:** Volumes mounted `:ro`, no watchdog/reload mechanism.
**Impact:** Slows all development iteration.

**Fix:**
- Change volume mounts from `:ro` to `:rw` for agent/ and governance/
- Add `--reload` flag to uvicorn (API) in entrypoint
- Add watchdog-based Trame reload or use `TRAME_ARGS=--reload`
- Document restart-vs-reload in DEVOPS.md

**Files:**
- `docker-compose.yml` (volume mounts)
- `agent/Dockerfile.dashboard` (entrypoint script)
- `docs/DEVOPS.md` (document hot-reload)

**Priority:** HIGH | **Dependency:** None

### 0.3 Browser Window State Isolation

**Problem:** Two browser windows show synced navigation state.
**Root cause:** Trame server maintains single shared state object. `window_state.py` isolator exists but may not fully work for all state keys.
**Impact:** Cannot use multiple windows for different views.

**Analysis needed:** The `window_state.py` component already isolates `active_view` and selection states via sessionStorage. Need to verify if this is functioning correctly or if additional state keys need isolation.

**TDD:**
```
tests/e2e/test_window_isolation.py
- test_two_windows_independent_navigation()
- test_selection_not_shared()
```

**Priority:** MEDIUM | **Dependency:** 0.2

### 0.4 Move Plan File to docs/

**Problem:** Previous plan was stored in `.claude/plans/` which operator cannot open.
**Fix:** THIS document. Already in `docs/plans/`.

**Priority:** DONE

---

## EPIC 1: Grid Views & Full-Width Layout (HIGH)

> Multiple tabs use card lists instead of data grid tables. Operator wants columns.

### 1.1 Rules Tab - Grid with Columns

**Problem:** Rules shown as card list, not full-width grid.
**Columns needed:** Rule ID, Name, Status, Category, Priority, Tasks Count, Sessions Count, Created Date

**TDD:**
```
tests/unit/test_rules_view_grid.py
- test_rules_grid_has_columns()
- test_rules_grid_sortable()
- test_rules_grid_full_width()
- test_rules_row_click_opens_detail()
```

**Fix:**
- Replace `VCard` list with `VDataTable` (Vuetify 3 data table)
- Add columns: rule_id, name, status, category, priority, linked_tasks_count, linked_sessions_count, created_at
- Full width: remove `VCol(cols=8)` constraint, use `VCol(cols=12)`
- Row click opens detail panel
- Add link to rule document (markdown viewer)

**Files:**
- `agent/governance_ui/views/rules_view.py` (rewrite to VDataTable)
- `governance/routes/rules/crud.py` (add task/session counts to response)

**Priority:** HIGH | **Dependency:** 0.1

### 1.2 Sessions Tab - Grid with Columns

**Problem:** Sessions shown as timeline cards, no grid.
**Columns needed:** Session ID, Start Time, End Time, Status, Agent, Tasks Count, Category

**TDD:**
```
tests/unit/test_sessions_view_grid.py
- test_sessions_grid_has_columns()
- test_sessions_grid_links_to_tasks()
- test_sessions_detail_shows_tasks_and_evidence()
```

**Fix:**
- Add `VDataTable` with sortable columns
- Keep timeline as optional view toggle (grid/timeline)
- Link each session to its tasks and evidence documents

**Files:**
- `agent/governance_ui/views/sessions/list.py` (add data table)
- `agent/governance_ui/controllers/sessions.py` (task count enrichment)

**Priority:** HIGH | **Dependency:** 0.1

### 1.3 Tasks Tab - Grid with Columns

**Problem:** Missing columns for state, dates, session count, agents.
**Columns needed:** Task ID, Name, Status, Phase, Agent(s), Sessions Count, Created Date, Last Changed, Documents

**TDD:**
```
tests/unit/test_tasks_view_grid.py
- test_tasks_grid_has_all_columns()
- test_tasks_grid_shows_linked_sessions()
- test_tasks_grid_shows_linked_agents()
- test_tasks_grid_shows_linked_documents()
```

**Fix:**
- Enhance existing data table with missing columns
- Add linked_sessions, linked_agents, linked_documents fields
- API enrichment for cross-reference counts

**Files:**
- `agent/governance_ui/views/tasks_view.py`
- `governance/routes/tasks/crud.py` (enrich response)

**Priority:** HIGH | **Dependency:** 0.1

### 1.4 Session Evidence Tab - Grid with Columns

**Problem:** Evidence shown as flat list, no columns.
**Columns needed:** Session ID, Evidence Source, Type, Timestamp, Linked Tasks

**TDD:**
```
tests/unit/test_evidence_view_grid.py
- test_evidence_grid_has_columns()
- test_evidence_links_to_sessions()
```

**Files:**
- `agent/governance_ui/views/search_view.py`

**Priority:** HIGH | **Dependency:** 0.1

---

## EPIC 2: Traceability & Linkage (CRITICAL)

> Operator cannot see task<>rule<>session connections. Core governance gap.

### 2.1 Rule-to-Task Linkage Display

**Problem:** Most rules show no linked tasks despite tasks existing.
**Root cause:** `linked_rules` field in tasks rarely populated; no reverse lookup.

**TDD:**
```
tests/unit/test_rule_task_linkage.py
- test_rule_detail_shows_linked_tasks()
- test_task_detail_shows_linked_rules()
- test_api_returns_linked_tasks_for_rule()
```

**Fix:**
- Add `GET /api/rules/{rule_id}/tasks` endpoint (reverse lookup from TypeDB)
- Display linked tasks in rule detail panel
- Use TypeDB `completed-in` + `task-rule-link` relations

**Files:**
- `governance/routes/rules/crud.py` (new endpoint)
- `governance/typedb/queries/rules/` (new query)
- `agent/governance_ui/views/rules_view.py` (detail panel)

**Priority:** CRITICAL | **Dependency:** None

### 2.2 Session-to-Task Linkage Display

**Problem:** Sessions show no linked tasks.
**Root cause:** Data exists in TypeDB (`completed-in` relation) but not surfaced in UI.

**TDD:**
```
tests/unit/test_session_task_linkage.py
- test_session_detail_shows_tasks()
- test_task_detail_shows_sessions()
```

**Fix:**
- Session detail already has task loading (GAP-UI-SESSION-TASKS-001)
- Verify it works; if not, fix the API endpoint
- Add sessions list to task detail panel

**Files:**
- `agent/governance_ui/views/sessions/tasks.py`
- `agent/governance_ui/views/tasks_view.py`
- `governance/routes/sessions/crud.py`

**Priority:** CRITICAL | **Dependency:** None

### 2.3 Rule-to-Document Linkage

**Problem:** Rules don't link to their governance document (markdown file).
**Root cause:** Document path exists in TypeDB (`document-path` attribute) but not displayed.

**TDD:**
```
tests/unit/test_rule_document_link.py
- test_rule_detail_shows_document_link()
- test_document_viewer_renders_markdown()
```

**Fix:**
- Add document link/viewer to rule detail panel
- Use `document-path` attribute from TypeDB to resolve file
- Render markdown content inline or in modal

**Files:**
- `agent/governance_ui/views/rules_view.py` (document viewer)
- `governance/routes/rules/crud.py` (include document_path in response)

**Priority:** HIGH | **Dependency:** 2.1

### 2.4 Task-to-Document Linkage

**Problem:** Tasks have no linked documents visible.
**Fix:** Display `document_path` and related evidence files in task detail.

**Files:**
- `agent/governance_ui/views/tasks_view.py`

**Priority:** HIGH | **Dependency:** 2.2

### 2.5 Backfill Traceability Data

**Problem:** Historical data has gaps in task<>rule<>session mappings.
**Approach:** Use MCP session commands (delivered yesterday) to backfill:
- `session_link_rule()` - Link rules to sessions
- `session_link_evidence()` - Link evidence files
- `session_task()` - Link tasks to sessions

**TDD:**
```
tests/unit/test_backfill_traceability.py
- test_backfill_links_sessions_to_tasks()
- test_backfill_links_rules_to_sessions()
```

**Script:** `scripts/backfill_traceability.py`

**Priority:** HIGH | **Dependency:** 2.1, 2.2

---

## EPIC 3: Agent Management & Orchestration (HIGH)

> Operator needs agents to be actionable, configurable, with live metrics.

### 3.1 Agent Tab - Linked Sessions & Tasks

**Problem:** No linked sessions or tasks visible for agents.
**Root cause:** Agent task counter was fixed (Task 1.2 from prior plan) but existing data has null agent_id.

**TDD:**
```
tests/unit/test_agent_relations.py
- test_agent_detail_shows_sessions()
- test_agent_detail_shows_tasks()
- test_agent_detail_shows_metrics()
```

**Fix:**
- Display sessions where agent_id matches
- Display tasks where agent_id matches
- Show execution metrics (success rate, avg duration)

**Files:**
- `agent/governance_ui/views/agents/relations.py`
- `governance/routes/agents/crud.py`

**Priority:** HIGH | **Dependency:** None

### 3.2 Agent Stop/Control Actions

**Problem:** Cannot stop agent tasks/sessions from UI.
**Fix:**
- Add "Stop Task" button in agent detail -> calls `PUT /api/tasks/{id}/complete` with CANCELLED
- Add "End Session" button -> calls `POST /api/sessions/{id}/end`
- Add "Pause Agent" toggle

**Files:**
- `agent/governance_ui/views/agents/detail.py`
- `agent/governance_ui/controllers/agents.py` (new)

**Priority:** MEDIUM | **Dependency:** 3.1

### 3.3 Agent Configuration & New Agent Types

**Problem:** Cannot add new agent types (SMM, marketing, accountant, etc.) from UI.
**Fix:**
- Add "Register Agent" form with: name, type, skills/rules bundle, LangGraph workflow config
- Support agent type templates (pre-configured rule bundles)
- Store agent config in TypeDB

**TDD:**
```
tests/unit/test_agent_registration.py
- test_register_new_agent_type()
- test_agent_has_rule_bundle()
- test_agent_config_persisted()
```

**Files:**
- `agent/governance_ui/views/agents/config.py` (already exists, extend)
- `governance/routes/agents/crud.py` (POST with config)
- `governance/typedb/queries/agents.py` (store config)

**Priority:** MEDIUM | **Dependency:** 3.1
**Note:** n8n integration is NOT needed - LangGraph handles workflow orchestration.

### 3.5 Agent Chat - Wire LLM Integration

**Problem:** Chat returns canned "I'm here to help..." for ALL natural language input. `process_chat_command()` in `commands.py` admits "This is a simplified implementation." No LLM calls, no real agent processing. Only slash commands (`/status`, `/tasks`, `/delegate`) work.
**Root cause:** No LiteLLM/LLM integration in chat pipeline. DelegationProtocol exists but no handlers registered.

**TDD:**
```
tests/unit/test_chat_llm_integration.py
- test_natural_language_routed_to_llm()
- test_llm_response_returned_to_user()
- test_delegation_handler_registered()
- test_chat_context_includes_rules_and_tasks()
```

**Fix:**
- Wire LiteLLM (already on port 4000) into `process_chat_command()` fallback
- Register DelegationProtocol handlers for RESEARCH, CODING, CURATOR roles
- Pass governance context (rules, tasks, sessions) as system prompt to LLM
- Return actual LLM response instead of canned template

**Files:**
- `governance/routes/chat/commands.py` (LLM fallback)
- `governance/routes/chat/endpoints.py` (handler registration)
- `governance/routes/chat/llm_bridge.py` (new - LiteLLM integration)

**Priority:** HIGH | **Dependency:** 3.1

### 3.4 Multi-Agent Task Mapping

**Problem:** Tasks don't show multiple agents (R&D, spec, security, etc.) mapped to them.
**Fix:**
- Display all agents involved in task execution via execution events
- Show agent pipeline visualization (which agents touched this task)

**Files:**
- `agent/governance_ui/views/tasks_view.py`
- `governance/routes/tasks/crud.py`

**Priority:** MEDIUM | **Dependency:** 2.2, 3.1

---

## EPIC 4: Actionable Views (HIGH)

> Multiple views show data but offer no way to act on it.

### 4.1 Executive Report Redesign

**Problem:** "Looks like total shit" - no clear UX purpose.
**Action:** Search Claude Code sessions for original intent, redesign from UX perspective.

**Redesign proposal:**
- Show aggregated weekly/monthly KPIs: rules coverage, task completion rate, session productivity
- Drill-down to daily breakdown
- Exportable PDF/markdown report
- Use all available data: rules, tasks, sessions, agents, audit trail

**TDD:**
```
tests/unit/test_executive_report.py
- test_executive_shows_kpis()
- test_executive_data_aggregation()
- test_executive_export()
```

**Files:**
- `agent/governance_ui/views/executive/` (redesign)
- `governance/routes/reports.py` (aggregation endpoint)

**Priority:** HIGH | **Dependency:** 2.1, 2.2

### 4.2 Decision Log - Operator Steering

**Problem:** Should capture operator decisions at ambiguity points with pros/cons.
**Fix:**
- Each decision has: options considered, pros/cons per option, chosen option, rationale
- Backfill from Claude Code session MCP commands
- Link decisions to rules affected and tasks spawned
- "Wisdom extraction" - derive patterns from past decisions

**TDD:**
```
tests/unit/test_decision_log.py
- test_decision_has_options_and_pros_cons()
- test_decision_links_to_rules()
- test_decision_wisdom_extraction()
```

**Files:**
- `agent/governance_ui/views/decisions/` (extend schema)
- `governance/routes/decisions.py` (extend model)
- `governance/models.py` (Decision model with options)

**Priority:** HIGH | **Dependency:** None

### 4.3 Rule Impact Analyzer - Full Graph

**Problem:** "No dependency graph data... wtf" + missing cycle/orphan detection + no action buttons.

**Fix:**
- **Before rule selection:** Show global overview - rule cycles, orphaned rules, cluster map
- **Integrate R&D visualization** (interactive graph, not just Mermaid)
- **Add "Create Task" button** on recommendations -> creates backlog task from recommendation
- **Add "Delegate to Agent" button** -> passes recommendation as prompt to agent

**TDD:**
```
tests/unit/test_impact_analyzer.py
- test_global_overview_shows_cycles()
- test_global_overview_shows_orphans()
- test_create_task_from_recommendation()
- test_delegate_recommendation_to_agent()
```

**Files:**
- `agent/governance_ui/views/impact/views.py` (global overview)
- `agent/governance_ui/views/impact/analysis.py` (action buttons)
- `agent/governance_ui/controllers/impact.py`
- `governance/typedb/queries/rules/inference.py` (cycle detection query)

**Priority:** HIGH | **Dependency:** 0.1

### 4.4 Workflow Compliance - Actionable

**Problem:** Shows checks but nothing actionable; no real workflows running.
**Fix:**
- Link violations to task creation ("Fix This" button -> creates task)
- Show LangGraph workflow execution status
- Add "Run Compliance Check" button

**Files:**
- `agent/governance_ui/views/workflow_view.py`
- `agent/governance_ui/controllers/workflow.py` (new)

**Priority:** MEDIUM | **Dependency:** 3.3

### 4.5 Test Runner - Restore Intent

**Problem:** "Totally inactionable" - search sessions for original intent.
**Fix:**
- Actually execute tests from UI (via API endpoint)
- Show real-time test output streaming
- Link test results to evidence files
- "Run All" + per-category run buttons should trigger real pytest/robot runs

**Files:**
- `agent/governance_ui/views/tests_view.py`
- `governance/routes/tests.py` (execution endpoint)

**Priority:** MEDIUM | **Dependency:** 0.2

---

## EPIC 5: View Consolidation & UX (MEDIUM)

> Some tabs are redundant or need merging.

### 5.1 Merge Session Metrics into Sessions Tab

**Problem:** Session Metrics is a separate tab but should be part of Sessions.
**Fix:**
- Add metrics summary cards at top of Sessions grid view
- Session detail shows per-session metrics drill-down
- Fix: Show hours when minutes > 60

**Files:**
- `agent/governance_ui/views/sessions/` (integrate metrics)
- `agent/governance_ui/views/metrics_view.py` (remove or redirect)

**Priority:** MEDIUM | **Dependency:** 1.2

### 5.2 Session Drill-Down with MCP Tool Call Metadata

**Problem:** Cannot drill into session to see tool calls, thinking items, input/output.
**Fix:**
- Parse Claude Code JSONL transcripts for tool call metadata
- Display expandable tree: Session -> Tool Calls -> Input/Output
- Display thinking items as collapsible blocks
- Use MCP session fetch command for data

**TDD:**
```
tests/unit/test_session_drill_down.py
- test_session_shows_tool_calls()
- test_tool_call_shows_input_output()
- test_thinking_items_displayed()
```

**Files:**
- `agent/governance_ui/views/sessions/detail.py` (tool call viewer)
- `governance/routes/sessions/` (tool call data endpoint)
- `agent/governance_ui/data_access/sessions.py` (JSONL parser)

**Priority:** HIGH | **Dependency:** 1.2

### 5.3 Merge Evidence Search into Sessions

**Problem:** Evidence Search is redundant with Sessions tab.
**Fix:**
- Add search bar to Sessions view
- Evidence results shown inline with session context
- Remove standalone Evidence Search tab or redirect

**Files:**
- `agent/governance_ui/views/sessions/` (add search)
- `agent/governance_ui/views/search_view.py` (deprecate)

**Priority:** LOW | **Dependency:** 5.1

### 5.4 Merge Agent Trust into Registered Agents

**Problem:** "Don't see real sense in it... merge with registered agents"
**Fix:**
- Move trust scores and leaderboard into Agents tab
- Trust displayed per-agent in the grid and detail views

**Files:**
- `agent/governance_ui/views/agents/` (integrate trust)
- `agent/governance_ui/views/trust_view.py` (deprecate)

**Priority:** LOW | **Dependency:** 3.1

---

## EPIC 6: Monitoring & Audit (MEDIUM)

### 6.1 Audit Trail - Restore Intent

**Problem:** "Has no info" - audit wiring was just added (Task 1.3 from prior plan).
**Fix:**
- Verify audit data is flowing after prior wiring work
- Add grid view with columns: Timestamp, Action, Entity Type, Entity ID, Actor, Details
- Add filtering and search
- Search sessions for original design intent

**Files:**
- `agent/governance_ui/views/audit_view.py`
- `governance/routes/audit.py`

**Priority:** MEDIUM | **Dependency:** None

### 6.2 Real-Time Monitor - Event Type Fix & Grid

**Problem:** Event type combobox broken; events not in grid.
**Fix:**
- Event type combobox already fixed (Task 2.3 from prior plan) - verify
- Add `VDataTable` for event feed with columns: Timestamp, Event Type, Source, Details, Actions
- Add "Act on Event" button -> creates task from event

**Files:**
- `agent/governance_ui/views/monitor_view.py`

**Priority:** MEDIUM | **Dependency:** 0.1

### 6.3 Infrastructure Health - Restore Intent

**Problem:** "Search carefully for session... where is due diligence"
**Fix:**
- Search Claude Code sessions for original infra health design
- Verify all service cards show real status
- Add MCP server health check (not just process detection)
- Add "Restart Service" buttons that actually work

**Files:**
- `agent/governance_ui/views/infra_view.py`
- `agent/governance_ui/controllers/infra.py` (new)

**Priority:** MEDIUM | **Dependency:** 0.2

---

## Execution Order (Priority + Dependencies)

| Phase | Epic | Task | Priority | Depends On |
|-------|------|------|----------|------------|
| **P0** | 0 | 0.1 Dark Theme Fix | CRITICAL | - |
| **P0** | 0 | 0.2 Container Hot-Reload | HIGH | - |
| **P1** | 2 | 2.1 Rule-Task Linkage | CRITICAL | - |
| **P1** | 2 | 2.2 Session-Task Linkage | CRITICAL | - |
| **P1** | 1 | 1.1 Rules Grid | HIGH | 0.1 |
| **P1** | 1 | 1.2 Sessions Grid | HIGH | 0.1 |
| **P1** | 1 | 1.3 Tasks Grid | HIGH | 0.1 |
| **P2** | 2 | 2.3 Rule-Document Link | HIGH | 2.1 |
| **P2** | 2 | 2.4 Task-Document Link | HIGH | 2.2 |
| **P2** | 2 | 2.5 Backfill Traceability | HIGH | 2.1, 2.2 |
| **P2** | 4 | 4.2 Decision Log Redesign | HIGH | - |
| **P2** | 4 | 4.3 Impact Analyzer Full | HIGH | 0.1 |
| **P2** | 5 | 5.2 Session Drill-Down | HIGH | 1.2 |
| **P3** | 3 | 3.1 Agent Sessions/Tasks | HIGH | - |
| **P3** | 3 | 3.2 Agent Stop/Control | MEDIUM | 3.1 |
| **P3** | 3 | 3.3 Agent Config/Types | MEDIUM | 3.1 |
| **P3** | 3 | 3.5 Chat LLM Integration | HIGH | 3.1 |
| **P3** | 4 | 4.1 Executive Redesign | HIGH | 2.1, 2.2 |
| **P3** | 4 | 4.4 Workflow Actionable | MEDIUM | 3.3 |
| **P3** | 4 | 4.5 Test Runner Intent | MEDIUM | 0.2 |
| **P4** | 5 | 5.1 Merge Metrics+Sessions | MEDIUM | 1.2 |
| **P4** | 5 | 5.3 Merge Evidence+Sessions | LOW | 5.1 |
| **P4** | 5 | 5.4 Merge Trust+Agents | LOW | 3.1 |
| **P4** | 6 | 6.1 Audit Trail | MEDIUM | - |
| **P4** | 6 | 6.2 Monitor Grid | MEDIUM | 0.1 |
| **P4** | 6 | 6.3 Infra Health Intent | MEDIUM | 0.2 |
| **P4** | 0 | 0.3 Window State Isolation | MEDIUM | 0.2 |
| **P4** | 3 | 3.4 Multi-Agent Tasks | MEDIUM | 2.2, 3.1 |
| **P4** | 1 | 1.4 Evidence Grid | HIGH | 0.1 |

---

## Verification Strategy

**Per-task:**
1. Write unit tests FIRST (TDD)
2. Implement minimum code to pass
3. Run full suite: `.venv/bin/python3 -m pytest tests/unit/ -v`
4. Verify via REST API: `mcp__rest-api__test_request`
5. Verify via Playwright: Navigate affected tab

**Per-epic:**
1. Run E2E tests: `.venv/bin/python3 -m pytest tests/e2e/ -v`
2. Full Robot suite: `robot tests/robot/`
3. Operator visual review of affected tabs

---

## Answers to Operator Questions

| # | Question | Answer |
|---|----------|--------|
| 0a | Plan location | NOW in `docs/plans/` (this file) |
| 0b | Dark theme | Vuetify theme not wired to content areas - EPIC 0.1 |
| 0c | Container hot-reload | NO - volumes `:ro`, no reload flag - EPIC 0.2 |
| 0d | State sync | Trame shared server state; window_state.py partially isolates - EPIC 0.3 |
| 1a | Chat sends to agents? | NO - canned responses only. DelegationProtocol exists but NO LLM integration. Only `/delegate` command triggers actual delegation. Natural language falls through to template: "I'm here to help..." - EPIC 3.5 |
| 1b | Free-type prompt? | NO - no LLM/LiteLLM wired into chat. Slash commands work (`/status`, `/tasks`, `/rules`, `/delegate`), free text returns canned response - EPIC 3.5 |
| 3a | n8n needed? | NO - LangGraph handles orchestration |
| 8 | No dependency data | 27 relations populated (prior task 3.1); need global overview - EPIC 4.3 |
| 9 | Trust dashboard | Will merge into Agents tab - EPIC 5.4 |
