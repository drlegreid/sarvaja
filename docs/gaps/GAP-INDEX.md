# Gap Index - Sarvaja (Active Gaps)

**Last Updated:** 2026-01-19
**Active Gaps:** 23 | Status: 6 OPEN, 0 BLOCKED, 2 IN_PROGRESS, 1 PARTIAL, 14 DEFERRED
**Archived:** 221+ RESOLVED gaps → [GAP-INDEX-ARCHIVE.md](GAP-INDEX-ARCHIVE.md)

> **Evidence Files:** Detailed analysis in [evidence/](evidence/) per GAP-META-001
> **Archive Rule:** Per DOC-GAP-ARCHIVE-01-v1 - RESOLVED gaps move to archive

---

## Context Efficiency Gaps (2026-01-19) - RESOLVED

> **Source:** EPIC-STABILITY
> **Evidence:** [GAP-CONTEXT-EFFICIENCY-001.md](evidence/GAP-CONTEXT-EFFICIENCY-001.md)

| ID | Status | Gap | Priority | Category | Evidence |
|----|--------|-----|----------|----------|----------|
| GAP-CONTEXT-EFFICIENCY-001 | RESOLVED | 100% context burn on MCP troubleshooting - pre-flight validation + entropy monitoring | HIGH | stability | [evidence/GAP-CONTEXT-EFFICIENCY-001.md](evidence/GAP-CONTEXT-EFFICIENCY-001.md) |
| GAP-ENTROPY-HOOK-001 | RESOLVED | PostToolUse hook missing - entropy counter never incremented | HIGH | infrastructure | [evidence/GAP-ENTROPY-HOOK-001.md](evidence/GAP-ENTROPY-HOOK-001.md) |

**Resolution:** TACTIC-1 (pre-flight MCP validation), TACTIC-2 (pre-commit guard, unit tests), TACTIC-3 (entropy monitoring, CONTEXT-SAVE-01-v1 rule). GAP-ENTROPY-HOOK-001: Added PostToolUse hook + standalone CLI wrapper.

---

## Infrastructure Gaps (2026-01-16) - CRITICAL

> **Source:** Platform audit
> **Evidence:** [SESSION-2026-01-16-PLATFORM-AUDIT](../SESSION-2026-01-16-PLATFORM-AUDIT.md)

| ID | Status | Gap | Priority | Category | Evidence |
|----|--------|-----|----------|----------|----------|
| GAP-TYPEDB-DRIVER-001 | RESOLVED | TypeDB driver incompatibility - resolved via 3.x upgrade | ~~CRITICAL~~ | infrastructure | [evidence/GAP-TYPEDB-DRIVER-001.md](evidence/GAP-TYPEDB-DRIVER-001.md) |
| GAP-TYPEDB-UPGRADE-001 | RESOLVED | TypeDB Server 2.29.1 → 3.7.3 upgrade complete | ~~HIGH~~ | infrastructure | [evidence/GAP-TYPEDB-UPGRADE-001.md](evidence/GAP-TYPEDB-UPGRADE-001.md) |
| GAP-TYPEDB-INFERENCE-001 | RESOLVED | Inference rules migrated to 3.x functions | HIGH | infrastructure | [evidence/GAP-TYPEDB-INFERENCE-001.md](evidence/GAP-TYPEDB-INFERENCE-001.md) |

**Resolution:** TypeDB 3.x migration complete. 5 inference functions operational. Data sync complete: 60 Rules in TypeDB (API shows 50 ACTIVE).

---

## Platform Audit Gaps (2026-01-16) - CRITICAL

> **Source:** Exploratory testing with MCP REST & Playwright
> **Evidence:** [SESSION-2026-01-16-PLATFORM-AUDIT](../SESSION-2026-01-16-PLATFORM-AUDIT.md)

| ID | Status | Gap | Priority | Category | Evidence |
|----|--------|-----|----------|----------|----------|
| GAP-DATA-INTEGRITY-001 | RESOLVED | Dashboard traceability complete - agent_id 100%, evidence 100%, UI navigation | ~~CRITICAL~~ | data_integrity | [evidence/GAP-DATA-INTEGRITY-001.md](evidence/GAP-DATA-INTEGRITY-001.md) |
| GAP-BATCH-QUERY-001 | RESOLVED | Session LIST returns wrong tasks_completed count vs GET | HIGH | data_integrity | [evidence/GAP-BATCH-QUERY-001.md](evidence/GAP-BATCH-QUERY-001.md) |
| GAP-E2E-KANREN-001 | RESOLVED | E2E platform health test fails - kanren not in requirements.txt | HIGH | testing | FIXED: Added kanren>=0.2.3 to requirements.txt |
| GAP-API-PERF-001 | RESOLVED | API response times 7-9 seconds → <500ms achieved | HIGH | performance | [evidence/GAP-API-PERF-001.md](evidence/GAP-API-PERF-001.md) VALIDATED 2026-01-16 |
| GAP-UI-PAGING-001 | RESOLVED | UI pagination & loading states complete (EPIC-DR-003/005) | HIGH | ux | [evidence/GAP-UI-PAGING-001.md](evidence/GAP-UI-PAGING-001.md) |

### Rule Data Sync (Added 2026-01-17)

| ID | Status | Gap | Priority | Category | Evidence |
|----|--------|-----|----------|----------|----------|
| GAP-RULE-SYNC-001 | RESOLVED | TypeDB rule sync complete: 60 semantic ID rules, legacy RULE-XXX removed | ~~HIGH~~ | data_integrity | [evidence/GAP-RULE-SYNC-001.md](evidence/GAP-RULE-SYNC-001.md) |
| GAP-RULE-QUALITY-001 | RESOLVED | Rule quality: 0 CRITICAL, 0 HIGH issues, semantic ID format canonical | ~~HIGH~~ | data_integrity | [evidence/GAP-RULE-QUALITY-001.md](evidence/GAP-RULE-QUALITY-001.md) |

### Technical Debt EPICs (Added 2026-01-17)

| ID | Status | Gap | Priority | Category | Evidence |
|----|--------|-----|----------|----------|----------|
| EPIC-DRY-001 | RESOLVED | Shared constants module (APP_TITLE, URLs, ports, timeouts) | ~~HIGH~~ | architecture | [evidence/EPIC-DRY-001.md](evidence/EPIC-DRY-001.md) |

**Resolution:** Created `shared/constants.py` as single source of truth. Updated 7 Python files to use constants.

### Architecture Gaps (Added 2026-01-19)

| ID | Status | Gap | Priority | Category | Evidence |
|----|--------|-----|----------|----------|----------|
| GAP-GAPS-TASKS-001 | RESOLVED | Merge gaps/tasks as unified work items in TypeDB | HIGH | architecture | [evidence/GAP-GAPS-TASKS-001.md](evidence/GAP-GAPS-TASKS-001.md) |
| GAP-LOCAL-PYTHON-001 | RESOLVED | Local Python 3.13.7 - pip+venv installed, TypeDB driver working | MEDIUM | infrastructure | [evidence/GAP-LOCAL-PYTHON-001.md](evidence/GAP-LOCAL-PYTHON-001.md) |
| GAP-TECH-STACK-001 | RESOLVED | Tech stack homogenization - venv setup, rule DEV-VENV-01-v1 | HIGH | architecture | [evidence/GAP-TECH-STACK-001.md](evidence/GAP-TECH-STACK-001.md) |

**Description:** Gaps and tasks are currently separate entities (filesystem vs TypeDB). Merge them so gaps are stored as tasks with document_path links. GAP-INDEX.md becomes backup/sync target.

**GAP-GAPS-TASKS-001 Progress:** ✓ COMPLETE (2026-01-19)
- Phase 1: Schema attributes added ✓
- Phase 2: workspace_sync_gaps_to_typedb tool created ✓
- Phase 3: CRUD operations updated ✓
- Phase 4: WorkItem.from_task() updated ✓

### Data Quality Evidence (Updated 2026-01-17)

| Entity | Field | Populated | Quality | Notes |
|--------|-------|-----------|---------|-------|
| Task | agent_id | **100%** | **FIXED** | EPIC-DR-007: Backfilled 76 tasks (2026-01-17) |
| Task | evidence | **100%** | **FIXED** | [EPIC-DR-008](evidence/GAP-EPIC-DR-008.md): Backfilled 63 DONE tasks (2026-01-17) |
| Task | linked_sessions | 86% | **GOOD** | 65/76 via completed-in relations |
| Session | evidence_files | 77% | **GOOD** | 17/22 have has-evidence relations |
| Session | tasks_completed | 18% | **IMPROVED** | 4 sessions have completed tasks |
| Session | linked_rules_applied | 23% | Fair | 5/22 sessions |

**Verdict:** Data integrity **COMPLETE**. agent_id: 100%, evidence: 100% for DONE tasks. All EPIC-DR tasks resolved.

---

## Governance Gaps (2026-01-16)

> **Source:** Platform audit - Rule compliance analysis
> **Evidence:** [SESSION-2026-01-16-PLATFORM-AUDIT](../SESSION-2026-01-16-PLATFORM-AUDIT.md)

| ID | Status | Gap | Priority | Category | Evidence |
|----|--------|-----|----------|----------|----------|
| GAP-GOVERNANCE-AUDIT-001 | RESOLVED | Full governance rule compliance audit (Option A) | HIGH | governance | [evidence/GAP-GOVERNANCE-AUDIT-001.md](evidence/GAP-GOVERNANCE-AUDIT-001.md) |

**Resolution:** 2026-01-17 - Rules synchronized. TypeDB: 60 rules. API: 50 ACTIVE. Scripts: `scripts/sync_rules.sh`. See [GAP-DATA-SYNC-001.md](evidence/GAP-DATA-SYNC-001.md)

---

## MCP Integration Gaps (2026-01-16)

> **Source:** Platform audit - MCP usage analysis
> **Evidence:** [SESSION-2026-01-16-PLATFORM-AUDIT](../SESSION-2026-01-16-PLATFORM-AUDIT.md)

| ID | Status | Gap | Priority | Category | Evidence |
|----|--------|-----|----------|----------|----------|
| GAP-MCP-001 | RESOLVED | gov-sessions MCP - print() to stderr fix | HIGH | integration | [evidence/GAP-MCP-001.md](evidence/GAP-MCP-001.md) - FIXED 2026-01-17 |
| GAP-MCP-002 | RESOLVED | gov-tasks MCP - print() to stderr fix | HIGH | integration | [evidence/GAP-MCP-002.md](evidence/GAP-MCP-002.md) - FIXED 2026-01-17 |
| GAP-MCP-003 | RESOLVED | REST API testing - 9 tests passing (health, rules, tasks, sessions) | MEDIUM | testing | [tests/integration/test_mcp_rest_sessions.py](../../tests/integration/test_mcp_rest_sessions.py) - FIXED 2026-01-18 |
| GAP-DATA-001 | OPEN | Evaluate TOON vs JSON for MCP output format | LOW | optimization | RD-TOON: 40% token reduction potential |
| GAP-API-001 | RESOLVED | POST /api/tasks returns 201 but doesn't persist to TypeDB | HIGH | data_integrity | FIXED 2026-01-16: Schema migration added task-resolution attribute. 9 tests pass. |
| GAP-VALIDATE-001 | RESOLVED | Integration validation suite (REST + Playwright + tests) | HIGH | testing | [evidence/GAP-VALIDATE-001.md](evidence/GAP-VALIDATE-001.md) - FIXED 2026-01-17 |
| GAP-MCP-PAGING-001 | OPEN | MCP tools need paging/truncation for large outputs (791K+ chars) | MEDIUM | tooling | [evidence/GAP-MCP-PAGING-001.md](evidence/GAP-MCP-PAGING-001.md) |
| GAP-MCP-NAMING-001 | RESOLVED | MCP tool naming - 84→26 tools (69% reduction), deprecated functions removed | HIGH | architecture | [evidence/GAP-MCP-NAMING-001.md](evidence/GAP-MCP-NAMING-001.md) - FIXED 2026-01-19 |
| GAP-MCP-DIRECTIVE-001 | RESOLVED | MCP operational directives - 3 rules created 2026-01-18 | MEDIUM | governance | [evidence/GAP-MCP-DIRECTIVE-001.md](evidence/GAP-MCP-DIRECTIVE-001.md) |
| GAP-TYPEDB3-DELETE-001 | RESOLVED | TypeDB 3.x delete syntax: `has $var of $entity` | HIGH | infrastructure | Fixed 2026-01-17: 6 files patched |

### Subtasks for GAP-MCP-001 (gov-sessions)

| Subtask | Status | Description | Test |
|---------|--------|-------------|------|
| MCP-001-A | TODO | Integrate session_start at Claude Code session begin | test_session_start_integration |
| MCP-001-B | TODO | Integrate session_end at /report command | test_session_end_integration |
| MCP-001-C | TODO | Use dsm_start/dsm_advance for DSM tracking | test_dsm_lifecycle |
| MCP-001-D | TODO | Use governance_evidence_search for context recovery | test_evidence_search_recovery |

### Subtasks for GAP-MCP-002 (gov-tasks)

| Subtask | Status | Description | Test |
|---------|--------|-------------|------|
| MCP-002-A | TODO | Sync TodoWrite with TypeDB task creation | test_todo_typedb_sync |
| MCP-002-B | TODO | Auto-mark tasks DONE when completed | test_task_completion_sync |
| MCP-002-C | TODO | Link tasks to git commits automatically | test_task_commit_link |
| MCP-002-D | TODO | Query backlog gaps via MCP | test_backlog_query |

### Subtasks for GAP-MCP-003 (rest-api) - RESOLVED 2026-01-18

| Subtask | Status | Description | Test |
|---------|--------|-------------|------|
| MCP-003-A | DONE | API health test with TypeDB status | test_api_health_includes_typedb |
| MCP-003-B | DONE | Rules listing and structure tests | test_list_rules, test_rules_have_structure |
| MCP-003-C | DONE | Tasks CRUD and persistence tests | test_list_tasks, test_create_task, test_task_persistence_round_trip |
| MCP-003-D | DONE | Session listing and creation tests | test_list_sessions, test_create_session |

### Subtasks for GAP-DATA-001 (TOON)

| Subtask | Status | Description | Test |
|---------|--------|-------------|------|
| DATA-001-A | TODO | Research Python TOON parser availability | N/A - research |
| DATA-001-B | TODO | Benchmark JSON vs TOON token counts | test_toon_token_comparison |
| DATA-001-C | TODO | Prototype MCP output formatter | test_toon_mcp_formatter |
| DATA-001-D | TODO | LLM readability test (can Claude parse TOON natively?) | test_toon_llm_native |

**TOON Reference:** https://github.com/toon-format/toon
- 40% token reduction vs JSON
- YAML-like indent + CSV tabular hybrid
- Designed for LLM context efficiency

---

## Exploratory Testing Gaps (2026-01-18)

> **Source:** LLM-driven exploratory testing via rest-api + Playwright MCPs
> **Evidence:** Heuristic-based testing: vertical/horizontal navigation, data integrity, UX elements

| ID | Status | Gap | Priority | Category | Evidence |
|----|--------|-----|----------|----------|----------|
| GAP-EXPLOR-API-001 | RESOLVED | API endpoint gaps: GET task/rule by ID (405/404), PUT task (500), sessions no pagination | HIGH | api | [evidence/GAP-EXPLOR-API-001.md](evidence/GAP-EXPLOR-API-001.md) |
| GAP-EXPLOR-UI-001 | RESOLVED | UI pagination/display: Backlog pagination, Sessions limit, Claim tooltips | ~~MEDIUM~~ | ux | [evidence/GAP-EXPLOR-UI-001.md](evidence/GAP-EXPLOR-UI-001.md) |

### Subtasks for GAP-EXPLOR-API-001 (ALL DONE 2026-01-18)

| Subtask | Status | Description | Test |
|---------|--------|-------------|------|
| EXPLOR-API-001-A | DONE | Implement GET /api/tasks/{id} route | test_get_task_by_id |
| EXPLOR-API-001-B | DONE | Fix GET /api/rules/{id} routing | test_get_rule_by_id |
| EXPLOR-API-001-C | DONE | Debug PUT /api/tasks/{id} 500 error | test_update_task |
| EXPLOR-API-001-D | DONE | Add pagination to sessions endpoint | test_sessions_pagination |

### Subtasks for GAP-EXPLOR-UI-001

| Subtask | Status | Description | Test |
|---------|--------|-------------|------|
| EXPLOR-UI-001-A | DONE | Add pagination controls to Backlog | test_backlog_pagination_ui |
| EXPLOR-UI-001-B | DONE | Fix Sessions view data limit (10→100) | test_sessions_all_visible |
| EXPLOR-UI-001-C | DONE | Add tooltip to disabled Claim buttons | test_claim_button_feedback |

---

## Dashboard UX & Data Integrity Audit (2026-01-18) - CRITICAL

> **Source:** User feedback - comprehensive UI review
> **Evidence:** [GAP-UI-AUDIT-2026-01-18.md](evidence/GAP-UI-AUDIT-2026-01-18.md)

| ID | Status | Gap | Priority | Category | Evidence |
|----|--------|-----|----------|----------|----------|
| GAP-UI-AUDIT-001 | PARTIAL | Dashboard traceability: task→session 86%, rules→tasks 0%, commit linkage 0% | HIGH | data_integrity | [evidence/GAP-UI-AUDIT-2026-01-18.md](evidence/GAP-UI-AUDIT-2026-01-18.md) |
| GAP-UI-AUDIT-002 | DEFERRED | UI State Singleton - Trame default behavior, needs architectural decision | HIGH | architecture | [evidence/GAP-UI-AUDIT-002-TRAME-STATE.md](evidence/GAP-UI-AUDIT-002-TRAME-STATE.md) |
| GAP-UI-AUDIT-003 | RESOLVED | Trace console missing request/response payloads | ~~HIGH~~ | ux | FIXED 2026-01-18: Accordion panels with req/res payloads |
| GAP-UI-AUDIT-004 | IN_PROGRESS | Tab redundancy/purpose unclear (2 task tabs, Decisions, Impact) | HIGH | ux | Needs user clarification |
| GAP-UI-SESSION-TASKS-001 | RESOLVED | Session detail not loading tasks (showed 0, API returned 7) | HIGH | ui | [evidence/GAP-UI-SESSION-TASKS-001.md](evidence/GAP-UI-SESSION-TASKS-001.md) |
| GAP-UI-TASK-SESSION-001 | RESOLVED | Task detail not showing linked_sessions | HIGH | ui | [evidence/GAP-UI-TASK-SESSION-001.md](evidence/GAP-UI-TASK-SESSION-001.md) |
| GAP-UI-ORPHAN-HANDLERS-001 | RESOLVED | Orphaned handler files not registered (systemic dead code) | HIGH | architecture | [evidence/GAP-UI-ORPHAN-HANDLERS-001.md](evidence/GAP-UI-ORPHAN-HANDLERS-001.md) |

**Fixes Applied (2026-01-18):**
1. Session tasks loading: Added `load_session_tasks()` to `controllers/sessions.py`
2. Task navigation from session: Added `navigate_to_task()` to `controllers/tasks.py`
3. Removed orphaned handlers: Deleted `handlers/{rule,task,session}_handlers.py`

**Data Integrity Metrics (Updated 2026-01-18):**
- Task→Session: **86%** (65/76 tasks linked) - IMPROVED via UI fix
- Task→Evidence: 100% (FIXED EPIC-DR-008)
- Task→Commit: **0.0%** (needs work)
- Session→Evidence: 77% (17/22 sessions)

---

## UI Exploratory Testing Gaps (2026-01-14)

> **Source:** LLM-driven exploratory testing via Playwright MCP
> **Evidence:** Session exploratory testing with real UI interaction

| ID | Status | Gap | Priority | Category | Evidence |
|----|--------|-----|----------|----------|----------|
| GAP-UI-EXP-001 | RESOLVED | Decisions view shows "No date" for all decisions | MEDIUM | data_integrity | FIXED: TypeDB query + compat layer now return decision_date |
| GAP-UI-EXP-002 | DEFERRED | Sessions lack descriptions | LOW | data_integrity | Requires markdown parsing to extract description from evidence files |
| GAP-UI-EXP-003 | DEFERRED | Task list shows only DONE tasks at top | LOW | ux | UX enhancement - add filtering/sorting controls |
| GAP-UI-EXP-004 | RESOLVED | Tasks view missing search/filter/pagination | HIGH | ux | FIXED: Added search textbox + Status/Phase dropdowns with v_show filtering |
| GAP-UI-EXP-005 | RESOLVED | Sessions view shows "No date" - UI bug | HIGH | data_integrity | FIXED: UI now checks both start_time (REST API) and date (MCP) fields |
| GAP-UI-EXP-006 | RESOLVED | Infrastructure health check shows incorrect status | CRITICAL | observability | [GAP-UI-EXP-006-INFRA-HEALTH.md](evidence/GAP-UI-EXP-006-INFRA-HEALTH.md) |
| GAP-UI-EXP-007 | RESOLVED | Chat send button throws JS error, messages don't send | CRITICAL | functionality | FIXED: Changed $trigger() to trigger() in chat/input.py and execution.py |
| GAP-UI-EXP-008 | RESOLVED | Agents trust scores - architecture clarified | MEDIUM | data_integrity | [GAP-UI-EXP-008-AGENTS-TRUST-MISMATCH.md](evidence/GAP-UI-EXP-008-AGENTS-TRUST-MISMATCH.md) |
| GAP-UI-EXP-009 | RESOLVED | TypeDB schema mismatch - graceful handling | HIGH | data_integrity | [GAP-UI-EXP-009-TYPEDB-TASK-RESOLUTION.md](evidence/GAP-UI-EXP-009-TYPEDB-TASK-RESOLUTION.md) |
| GAP-UI-EXP-010 | RESOLVED | Decisions count mismatch - UI shows 4, API returns 7 | MEDIUM | data_integrity | FIXED: API and UI now both return 4 decisions - data synchronized |
| GAP-UI-EXP-011 | RESOLVED | Workflow checker file missing - ERROR state | HIGH | functionality | [GAP-UI-EXP-011-WORKFLOW-CHECKER-MISSING.md](evidence/GAP-UI-EXP-011-WORKFLOW-CHECKER-MISSING.md) |
| GAP-UI-EXP-012 | RESOLVED | Agents not loading in UI views (0 agents shown) | HIGH | data_loading | FIXED: Handlers updated to use GOVERNANCE_API_URL env var |

---

## Architecture & UX Gaps (2026-01-14)

> **Source:** Entropy alerts, user feedback, Agile best practices
> **Status:** ALL RESOLVED (2026-01-14)

| ID | Status | Gap | Priority | Category | Evidence |
|----|--------|-----|----------|----------|----------|
| GAP-FILE-028 | RESOLVED | routes/agents.py 537→230 lines (package) | MEDIUM | architecture | FIXED 2026-01-14: Split to package with crud.py (230), observability.py (130), visibility.py (129), helpers.py (72). |
| GAP-UI-046 | RESOLVED | Task status/resolution per Agile DoR/DoD | MEDIUM | ux | FIXED 2026-01-14: Schema+entities+lifecycle module+TDD tests. Rule TASK-LIFE-01-v1 created. 24 unit tests pass. |
| GAP-UI-047 | RESOLVED | Reactive loaders with trace status | MEDIUM | ux | FIXED 2026-01-14: LoaderState + APITrace dataclasses, transforms module, initial state integration. 33 TDD tests pass. Rule UI-LOADER-01-v1 created. |
| GAP-UI-048 | RESOLVED | Bottom bar with technical traces | LOW | ux | FIXED 2026-01-14: VFooter trace bar UI component created. Visual verification per TEST-UI-VERIFY-01-v1. Screenshot: .playwright-mcp/GAP-UI-048-trace-bar.png |
| GAP-RULE-001 | RESOLVED | Task rule covering tech solutions | MEDIUM | governance | FIXED 2026-01-14: Created TASK-TECH-01-v1.md - Technology Solution Documentation rule. |
| GAP-TASK-LINK-001 | RESOLVED | Tasks linked to session documents | MEDIUM | data_integrity | FIXED 2026-01-14: link_task_to_session, governance_task_link_session MCP tool, 14 TDD tests pass. |
| GAP-TASK-LINK-002 | RESOLVED | Tasks linked to github commits | MEDIUM | data_integrity | FIXED 2026-01-14: Schema (git-commit entity, task-commit relation), linking methods, MCP tools, 14 TDD tests pass. |
| GAP-TASK-LINK-003 | RESOLVED | Tasks with related tasks (dependencies) | HIGH | data_integrity | FIXED 2026-01-14: Schema + entities + queries for task-hierarchy, task-blocks-task, task-related relations. |
| GAP-TASK-LINK-004 | RESOLVED | Task details: business, design, arch, test | MEDIUM | data_integrity | FIXED 2026-01-14: Schema + entity fields + details.py operations + MCP tools + read.py queries. 16 TDD tests pass. Per TASK-TECH-01-v1. |

---

## DSP-100 Hygiene Gaps (2026-01-03)

> **Source:** DSM cycle DSP-100-HYGIENE
> **Evidence:** [GAP-FILE-RESOLUTIONS.md](evidence/GAP-FILE-RESOLUTIONS.md)

| ID | Status | Gap | Priority | Category | Evidence |
|----|--------|-----|----------|----------|----------|
| GAP-FILE-029 | RESOLVED | governance/routes/tasks/workflow.py 414→296 lines | MEDIUM | architecture | FIXED 2026-01-17: Extracted helpers.py. Per DOC-SIZE-01-v1. |
| GAP-FILE-002 | RESOLVED | RULES-OPERATIONAL.md 1900→74 lines | CRITICAL | architecture | Split to 4 files |
| GAP-FILE-003 | RESOLVED | RULES-GOVERNANCE.md 633→53 lines | HIGH | architecture | Split to 2 files |
| GAP-FILE-004 | RESOLVED | RULES-TECHNICAL.md 457→59 lines | HIGH | architecture | Split to 3 files |
| GAP-DSM-001 | RESOLVED | dsm_checkpoint expects JSON string | MEDIUM | mcp | Fixed: accepts str or dict |
| GAP-DSM-002 | RESOLVED | dsm_checkpoint API should accept dict | HIGH | mcp | Union[str, Dict] type |
| GAP-MCP-005 | RESOLVED | Monolith governance MCP deprecated | HIGH | architecture | 4-server split validated |
| GAP-FILE-013 | RESOLVED | typedb/queries/rules.py 699→42 lines | MEDIUM | architecture | Modularized to 5 modules |
| GAP-FILE-014 | RESOLVED | sync_agent.py 687→77 lines | MEDIUM | architecture | Modularized to 6 modules |
| GAP-FILE-015 | RESOLVED | typedb/queries/tasks.py 652→35 lines | MEDIUM | architecture | Modularized to 3 modules |
| GAP-FILE-016 | RESOLVED | typedb/queries/sessions.py 606→35 lines | MEDIUM | architecture | Modularized to 3 modules |
| GAP-FILE-017 | RESOLVED | session_collector.py 591→49 lines | MEDIUM | architecture | Modularized to 7 modules |
| GAP-FILE-018 | RESOLVED | stores.py 503→99 lines | MEDIUM | architecture | Modularized to 6 modules |
| GAP-FILE-019 | RESOLVED | vector_store.py 531→106 lines | MEDIUM | architecture | Modularized to 5 modules |
| GAP-FILE-020 | RESOLVED | routes/tasks.py 475→27 lines | LOW | architecture | Modularized to 3 modules |
| GAP-FILE-021 | RESOLVED | embedding_pipeline.py 476→323 lines | LOW | architecture | FIXED 2026-01-14: Split to package with chunking.py (78 lines), pipeline.py (323 lines). 59 tests pass. |
| GAP-FILE-022 | RESOLVED | context_preloader.py 428→328 lines | LOW | architecture | FIXED 2026-01-14: Split to package with models.py (110 lines), preloader.py (328 lines). 19 tests pass. |
| GAP-FILE-023 | RESOLVED | routes/chat.py 421→262 lines | LOW | architecture | FIXED 2026-01-14: Split to package with commands.py (165 lines), endpoints.py (262 lines). 12 tests pass. |
| GAP-FILE-024 | RESOLVED | dsm/tracker.py 416→387 lines | LOW | architecture | FIXED 2026-01-14: Extracted memory.py (64 lines). 12 tests pass. |
| GAP-FILE-025 | RESOLVED | quality/analyzer.py 410→365 lines | LOW | architecture | Extracted impact.py. Per DOC-SIZE-01-v1. |
| GAP-FILE-026 | RESOLVED | workspace_scanner.py 409→320 lines | LOW | architecture | FIXED 2026-01-14: Extracted task_parsers.py (108 lines). 15 tests pass. |
| GAP-FILE-027 | RESOLVED | typedb/queries/tasks/crud.py 368→267 lines | LOW | architecture | FIXED 2026-01-14: Extracted status.py (142 lines). Imports verified. |

---

## CRITICAL User Feedback Gaps (2026-01-02)

| ID | Status | Gap | Priority | Category | Rule | Evidence |
|----|--------|-----|----------|----------|------|----------|
| GAP-WORKFLOW-004 | RESOLVED | Claimed UI fixes without E2E browser testing | CRITICAL | workflow | RULE-020, 023 | [test_dashboard_e2e.py](../../tests/e2e/test_dashboard_e2e.py) |
| GAP-HEALTH-003 | RESOLVED | Healthcheck hash is stale/cached | CRITICAL | observability | RULE-021 | [GAP-HEALTH-REQUIREMENTS.md](evidence/GAP-HEALTH-REQUIREMENTS.md) |
| GAP-HEALTH-004 | RESOLVED | Healthcheck lacks audit trail | CRITICAL | observability | RULE-021 | [GAP-HEALTH-REQUIREMENTS.md](evidence/GAP-HEALTH-REQUIREMENTS.md) |
| GAP-DOC-005 | RESOLVED | Document references not using relative links | CRITICAL | documentation | RULE-034 | RULE-034 created |
| GAP-RULE-003 | RESOLVED | Missing RULE-034 for document linking | HIGH | governance | RULE-013 | RULE-034 added |
| GAP-RULE-004 | RESOLVED | RULE-023 needs E2E testing mandate | CRITICAL | governance | RULE-023 | RULE-023 updated |

---

## CRITICAL Safety Gaps (2026-01-12)

> **Source:** Root Cause Analysis from AMNESIA incidents (2026-01-11)
> **Evidence:** [SESSION-2026-01-11-AMNESIA-ROOT-CAUSE.md](../../evidence/SESSION-2026-01-11-AMNESIA-ROOT-CAUSE.md)

| ID | Status | Gap | Priority | Category | Rule | Evidence |
|----|--------|-----|----------|----------|------|----------|
| GAP-DESTRUCT-001 | RESOLVED | No enforcement for destructive commands (rm -rf, reset --force, wipe) | CRITICAL | safety | RULE-042 | FIXED 2026-01-13: PreToolUse hook `.claude/hooks/pre_bash_check.py` + checker module `.claude/hooks/checkers/destructive.py`. Blocks catastrophic commands, warns on risky. |
| GAP-VERIFY-001 | RESOLVED | No verification protocol when marking fixes DONE | CRITICAL | workflow | RULE-037 | FIXED 2026-01-13: `governance_verify_completion()` MCP tool enforces evidence before marking complete. Per TEST-FIX-01-v1. |
| GAP-PERSIST-001 | RESOLVED | Containers lost on reboot - restart policy not sufficient | CRITICAL | infra | RULE-021 | FIXED 2026-01-12: Healthcheck hook auto-recovers via `ContainerRecovery.start_containers()`. Audit: `~/.claude/recovery_logs/`. E2E tested post-reboot. |
| GAP-PERSIST-002 | RESOLVED | ChromaDB data lost on reboot (0 documents) | CRITICAL | data | RULE-021 | FIXED: Mount was /chroma/chroma but persist_path=/data. Changed to /data |
| GAP-CODE-001 | RESOLVED | healthcheck.py has duplicate recovery logic (line 509) | HIGH | architecture | RULE-032 | FIXED: Uses ContainerRecovery class (runtime-agnostic, 2026-01-12) |
| GAP-REFACTOR-001 | RESOLVED | healthcheck.py exceeds 300 line limit (now 522 lines, was 1002) | HIGH | architecture | RULE-032 | FIXED 2026-01-13: 50% reduction achieved. Modular architecture: 8 checker modules in hooks/checkers/, ContainerRecovery class. Further reduction → RD-REFACTOR-001. |
| GAP-PYTHON-001 | RESOLVED | Agent uses `python` instead of `python3` | MEDIUM | devops | RULE-035 | FIXED 2026-01-13: Updated recover.py, SHELL-GUIDE.md. Added python3 pitfall warning. |
| GAP-PODMAN-DESKTOP-001 | DEFERRED | Podman Desktop shows "CREATED" for running containers | LOW | tooling | RULE-021 | Bug in 1.24.x. Needs desktop automation MCP (playwright/xdotool) for validation. Workaround: `scripts/fix-podman-desktop.sh` |
| GAP-AMNESIA-OUTPUT-001 | RESOLVED | AMNESIA detection output suppressed in summary mode | HIGH | observability | RECOVER-AMNES-01-v1 | FIXED 2026-01-15: Added amnesia param to format_summary(), now shows AMNESIA RISK in summary output. [GAP-AMNESIA-OUTPUT-001.md](evidence/GAP-AMNESIA-OUTPUT-001.md) |
| GAP-HEALTH-AGGRESSIVE-001 | RESOLVED | AMNESIA detection too quiet - needs ENV-based aggressive mode | HIGH | observability | RECOVER-AMNES-01-v1 | FIXED 2026-01-15: Added SARVAJA_HEALTH_MODE ENV (quiet/normal/aggressive), configurable thresholds. [GAP-HEALTH-AGGRESSIVE-001.md](evidence/GAP-HEALTH-AGGRESSIVE-001.md) |

---

## UI Gaps (P10 Sprint)

> **Source:** EXP-P10-001 Exploratory Session (2024-12-25)

| ID | Status | Gap | Priority | Category | Evidence |
|----|--------|-----|----------|----------|----------|
| GAP-UI-001 | RESOLVED | No data-testid attributes | HIGH | testability | 304 attrs added |
| GAP-UI-002 | RESOLVED | No CRUD forms for Rules | HIGH | functionality | build_rule_form_view |
| GAP-UI-003 | RESOLVED | No detail drill-down views | HIGH | functionality | Detail views added |
| GAP-UI-004 | RESOLVED | No REST API endpoints | HIGH | backend | governance/api.py |
| GAP-UI-005 | RESOLVED | Missing loading/error states | MEDIUM | ux | Error dialog + loading overlay added |
| GAP-UI-006 | RESOLVED | Rules list missing rule_id column | HIGH | data_binding | Fixed |
| GAP-UI-007 | RESOLVED | List rows not clickable | HIGH | navigation | Click handler added |
| GAP-UI-008 | RESOLVED | Tasks view shows empty table | HIGH | data_binding | Seed data added |
| GAP-UI-009 | RESOLVED | Search returns no results | MEDIUM | functionality | Button fix + source_type added |
| GAP-UI-010 | RESOLVED | No column sorting | MEDIUM | ux | API sort_by/order params added |
| GAP-UI-011 | RESOLVED | No filtering/faceted search | MEDIUM | functionality | API filter params: status, category, priority, agent_id, phase |
| GAP-UI-028 | RESOLVED | Tests pass but UI broken | CRITICAL | testing | RULE-028 + smoke tests |
| GAP-UI-029 | RESOLVED | Executive Report shows 0 Rules/Agents | HIGH | data | Field name fixed |
| GAP-UI-030 | RESOLVED | Tasks polluted with TEST-* tasks | MEDIUM | data | Deleted 154 tasks |
| GAP-UI-EXP | RESOLVED | No exploratory UI testing workflow | MEDIUM | process | FIXED: SFDIPOT+CRUCSS framework in tests/heuristics/ (sfdipot.py, crucss.py, coverage_report.py) |
| GAP-UI-031 | RESOLVED | Rule Save button mock-only | CRITICAL | functionality | Wired to API |
| GAP-UI-032 | RESOLVED | Rule Delete button mock-only | CRITICAL | functionality | Wired to API |
| GAP-UI-033 | RESOLVED | Decision CRUD | HIGH | functionality | Full implementation |
| GAP-UI-034 | RESOLVED | Session CRUD | HIGH | functionality | Full implementation |
| GAP-UI-035 | RESOLVED | No datetime columns | MEDIUM | ux | TypeDB schema + UI code updated |
| GAP-UI-036 | RESOLVED | No scrolling/paging | MEDIUM | ux | API pagination: sessions/tasks/rules/agents |
| GAP-UI-037 | RESOLVED | Entity content previews | HIGH | ux | Styled cards added |
| GAP-UI-038 | RESOLVED | Fullscreen document viewer | HIGH | functionality | views/dialogs.py |
| GAP-UI-039 | DEFERRED | No document format support | LOW | functionality | SCOPE: MD, logs, XML, JSON, YAML, code (py, hs, js, java, ps1, sh). Large files use lazy loading. → RD-DOCVIEW |
| GAP-UI-040 | RESOLVED | Agent config/instructions display | HIGH | functionality | agents_view.py |
| GAP-UI-041 | RESOLVED | Agent-session/task relation links | HIGH | functionality | agents_view.py |
| GAP-UI-042 | RESOLVED | Trust score history | HIGH | functionality | Trust history card |
| GAP-UI-043 | RESOLVED | Agent metrics display | MEDIUM | functionality | agents_view.py |
| GAP-UI-044 | RESOLVED | Executive Reporting view | HIGH | functionality | executive_view.py |
| GAP-UI-045 | DEFERRED | Cross-workspace metrics aggregation | MEDIUM | functionality | Blocked by RD-WORKSPACE Phase 5 (Optimization Loop). Requires agent runtime metrics. |
| GAP-UI-046 | RESOLVED | Executive Report per-session | HIGH | functionality | Session selector |
| GAP-UI-047 | RESOLVED | Rules tab: No directive shown | HIGH | ui | Directive excerpt added |
| GAP-UI-048 | RESOLVED | No entity relationships in UI | HIGH | ui | Backend populates |
| GAP-UI-049 | RESOLVED | Tasks: No description/linkage | HIGH | ui | Enhanced list view |
| GAP-UI-050 | RESOLVED | Session evidence tab empty | HIGH | functionality | Evidence files added |
| GAP-UI-051 | RESOLVED | Rule monitoring tab not functional | HIGH | functionality | Demo events seeded |
| GAP-UI-CHAT-001 | RESOLVED | No prompt/chat for agents | CRITICAL | functionality | [GAP-UI-CHAT.md](evidence/GAP-UI-CHAT.md) |
| GAP-UI-CHAT-002 | RESOLVED | Task execution viewer | CRITICAL | functionality | [GAP-UI-CHAT.md](evidence/GAP-UI-CHAT.md) |

---

## General Gaps

| ID | Status | Gap | Priority | Category | Rule | Evidence |
|----|--------|-----|----------|----------|------|----------|
| GAP-004 | NOT_IMPLEMENTED | Grok/xAI API Key | Medium | configuration | CLOSED: Not to be implemented. Using other LLM providers. |
| GAP-005 | RESOLVED | Agent Task Backlog UI | Medium | functionality | RULE-002 | Auto-polling implemented 2026-01-11 |
| GAP-006 | RESOLVED | Sync Agent Implementation | Medium | functionality | RULE-003 | GovernanceSync in agent/sync_agent/ |
| GAP-007 | DEFERRED | ChromaDB v2 Test Update | Low | testing | Tests use raw HTTP API needing v2 UUID endpoints. App uses client lib. 8 tests skipped. Tech debt. |
| GAP-008 | RESOLVED | Agent UI Image | Low | configuration | RULE-009 | Disabled |
| GAP-009 | RESOLVED | Pre-commit Hooks | Medium | tooling | RULE-001 | FIXED 2026-01-13: Added setup docs to DEVOPS.md. Config complete in .pre-commit-config.yaml |
| GAP-010 | RESOLVED | CI/CD Pipeline | Low | tooling | FIXED: .github/workflows/ci.yml + e2e-certification.yml. Unit, integration, E2E, Phase7 jobs. |
| GAP-014 | DEFERRED | IntelliJ Windsurf MCP not loading | Medium | tooling | RULE-005 | Environment-specific |
| GAP-015 | RESOLVED | Consolidated STRATEGY.md | Medium | docs | RULE-001 | docs/STRATEGY.md |
| GAP-019 | RESOLVED | MCP usage documentation | Medium | docs | RULE-007 | MCP-USAGE.md |
| GAP-020 | RESOLVED | Cross-project knowledge queries | HIGH | workflow | RULE-007 | MCP-USAGE.md |
| GAP-021 | NOT_IMPLEMENTED | OctoCode for external research | LOW | workflow | CLOSED: Not to be implemented. Using WebSearch MCP instead. |
| GAP-MCP-006 | RESOLVED | REST MCP server integration | Medium | tooling | RULE-036 | Added to .mcp.json |
| GAP-MCP-007 | RESOLVED | Podman MCP server integration | Medium | tooling | RULE-036 | Added to .mcp.json |
| GAP-MCP-008 | RESOLVED | MCP semantic ID support for workspace_link_rules_to_documents | HIGH | mcp | META-TAXON-01-v1 | FIXED: rule_linker.py dual pattern + subdirs + normalize_rule_id() |
| GAP-DEPLOY-001 | RESOLVED | deploy.ps1 missing dev profile | MEDIUM | tooling | RULE-028 | Added 'dev' |
| GAP-MCP-002 | RESOLVED | MCP healthcheck should stop Claude Code | HIGH | stability | RULE-021 | healthcheck.py auto-recovery |
| GAP-MCP-003 | RESOLVED | governance_health not called at start | CRITICAL | workflow | RULE-021 | Non-blocking retry |
| GAP-WORKFLOW-001 | RESOLVED | Session context not auto-saved | HIGH | workflow | RULE-001 | RD-INTENT MCP tools added |
| GAP-WORKFLOW-002 | RESOLVED | Claude Code should prompt /save | HIGH | workflow | RULE-001 | External: Claude Code CLI feature |
| GAP-WORKFLOW-003 | RESOLVED | GAP-INDEX strikethrough format | HIGH | data | RULE-012 | This file |
| GAP-INFRA-001 | RESOLVED | Docker health checks misconfigured | HIGH | infrastructure | RULE-021 | Fixed |
| GAP-INFRA-002 | RESOLVED | Dev vs Prod workflow undocumented | HIGH | documentation | RULE-030 | DEPLOYMENT.md |
| GAP-INFRA-003 | RESOLVED | deploy.ps1 missing dev profile | MEDIUM | tooling | RULE-028 | Added 'dev' |
| GAP-INFRA-004 | RESOLVED | No Docker health dashboard | HIGH | observability | RULE-021 | infra_view.py + nav fixed |
| GAP-INFRA-005 | DEFERRED | Ollama container not started | LOW | infra | RULE-021 | INDEFINITE: Local LLM optional. LiteLLM routes to cloud APIs. |
| GAP-TRAME-001 | RESOLVED | nav-infra not rendered despite code | HIGH | framework | RULE-037 | Fixed: duplicate NAVIGATION_ITEMS in constants.py |
| GAP-INFRA-006 | DEFERRED | Ollama container high memory | LOW | infrastructure | RULE-021 | INDEFINITE: Depends on GAP-INFRA-005. |
| GAP-MCP-004 | RESOLVED | Rule fallback to markdown | HIGH | architecture | RULE-021 | rule_fallback.py |
| GAP-TEST-001 | RESOLVED | E2E tests lack BDD paradigm | MEDIUM | testing | RULE-023 | FIXED 2026-01-14: pytest-bdd + Gherkin features + step definitions. TEST-BDD-01-v1 rule created. 9 BDD scenarios. |
| GAP-HEALTH-001 | RESOLVED | Healthcheck file size exceeds RULE-032 | MEDIUM | architecture | RULE-032 | FIXED 2026-01-13: 522 lines (was 1002). Modular checkers integrated: services, entropy, amnesia, zombies, destructive, intent, workflow. See GAP-REFACTOR-001. |
| GAP-HEALTH-002 | RESOLVED | Entropy detection for DSP | HIGH | workflow | RULE-012 | healthcheck.py |
| GAP-TEST-002 | RESOLVED | Test output blows context | HIGH | testing | RULE-023 | --report-minimal/trace/cert modes in conftest.py |
| GAP-TEST-003 | RESOLVED | E2E tests require port 8082 | HIGH | testing | RULE-023 | Port config standardized: Dashboard=8081, API=8082 |
| GAP-HEUR-001 | RESOLVED | Exploratory tests lack heuristics | HIGH | testing | RULE-023 | SFDIPOT+CRUCSS framework + Playwright validation |
| GAP-META-001 | RESOLVED | GAPs lack evidence file references | HIGH | architecture | RULE-012 | This refactoring |
| GAP-META-002 | RESOLVED | No CATEGORY taxonomy | HIGH | governance | RULE-013 | [GAP-TAXONOMY.md](evidence/GAP-TAXONOMY.md) |
| GAP-RULE-001 | RESOLVED | Rules lack TYPE field | HIGH | governance | RULE-013 | [GAP-TAXONOMY.md](evidence/GAP-TAXONOMY.md) |
| GAP-RULE-002 | RESOLVED | Rules lack anti-patterns | HIGH | governance | RULE-013 | [GAP-TAXONOMY.md](evidence/GAP-TAXONOMY.md) |
| GAP-SYNC-001 | RESOLVED | governance_sync_status returns typedb_count=0 | MEDIUM | data | RULE-021 | Fixed: added client.connect() |
| GAP-SERIAL-001 | RESOLVED | governance_list_all_tasks datetime serialization | MEDIUM | data | RULE-023 | Fixed: added default=str to json.dumps |
| GAP-LINK-001 | RESOLVED | Task→Session linkage 99.5% (199/200) | MEDIUM | data | RULE-001 | enrich_linkage.py + link API |
| GAP-LINK-002 | RESOLVED | Task→Rule linkage 60.0% (120/200) | HIGH | data | RULE-011 | enrich_linkage.py + link API |
| GAP-LINK-003 | RESOLVED | Session→Evidence linkage 94.4% (17/18) | HIGH | data | RULE-001 | enrich_linkage.py |
| GAP-LINK-004 | RESOLVED | Task→Agent linkage 17.5% (35/200) | HIGH | data | RULE-011 | Above 10% threshold |
| GAP-LINK-005 | RESOLVED | Session→Agent linkage 66.7% (12/18) | MEDIUM | data | RULE-011 | Above 10% threshold |
| GAP-SEARCH-001 | RESOLVED | Evidence search fallback to keyword | MEDIUM | search | RULE-007 | SESSION-2026-01-10-DATA-INTEGRITY |

---

## Architecture Gaps

| ID | Status | Gap | Priority | Category | Rule | Evidence |
|----|--------|-----|----------|----------|------|----------|
| GAP-ARCH-001 | RESOLVED | Tasks in-memory, not TypeDB | CRITICAL | architecture | DECISION-003 | Hybrid |
| GAP-ARCH-002 | RESOLVED | Sessions in-memory, not TypeDB | CRITICAL | architecture | DECISION-003 | Hybrid |
| GAP-ARCH-003 | RESOLVED | Agents in-memory, not TypeDB | HIGH | architecture | DECISION-003 | TypeDB-first |
| GAP-ARCH-004 | RESOLVED | TypeDB missing RULE-012 to RULE-025 | CRITICAL | data | RULE-012 | 25 rules loaded |
| GAP-ARCH-005 | RESOLVED | No MCP tools for Tasks/Sessions | HIGH | functionality | RULE-007 | mcp_tools/ |
| GAP-ARCH-006 | RESOLVED | Session/Task MCP exports missing | HIGH | testing | RULE-023 | Exports added |
| GAP-ARCH-007 | RESOLVED | Entity hierarchy review | MEDIUM | architecture | DECISION-003 | Keep separate |
| GAP-ARCH-008 | RESOLVED | TypeDB-Filesystem Rule Linking | MEDIUM | architecture | DECISION-003 | rule_linker.py |
| GAP-ARCH-009 | RESOLVED | TypeDB sessions not retrievable | MEDIUM | architecture | DECISION-003 | MCP + API now working |
| GAP-ARCH-010 | RESOLVED | Workspace tasks not in TypeDB | HIGH | architecture | DECISION-003 | workspace_scanner.py |
| GAP-ARCH-012 | RESOLVED | agents-1 container fails | HIGH | docker | RULE-030 | Type hint fixed |

---

## Sync & Integration Gaps

> **Evidence:** [GAP-SYNC-ARCHITECTURE.md](evidence/GAP-SYNC-ARCHITECTURE.md)

| ID | Status | Gap | Priority | Category | Rule | Evidence |
|----|--------|-----|----------|----------|------|----------|
| GAP-SYNC-001 | RESOLVED | TypeDB divergence detection done, sync pending | HIGH | architecture | DECISION-003 | Tasks synced, rules linked |
| GAP-SYNC-002 | RESOLVED | No validation to detect divergence | HIGH | testing | RULE-023 | governance_sync_status() |
| GAP-SYNC-003 | RESOLVED | MCP needs refactoring before sync | MEDIUM | architecture | RULE-012 | 4-server split per RULE-036 |

---

## TDD Stub Gaps

| ID | Status | Gap | Priority | Category | Rule | Evidence |
|----|--------|-----|----------|----------|------|----------|
| GAP-TDD-001 | RESOLVED | Task missing 'phase' field | MEDIUM | testing | RULE-025 | Fixed |
| GAP-TDD-002 | RESOLVED | Evidence search missing fields | MEDIUM | testing | RULE-025 | Fixed |
| GAP-TDD-003 | RESOLVED | DSM advance missing 'required_mcps' | LOW | testing | FIXED: dsm.py:76 returns new_phase.required_mcps |
| GAP-TDD-004 | RESOLVED | DSM checkpoint missing 'timestamp' | LOW | testing | FIXED: dsm.py:127 returns checkpoint.timestamp |
| GAP-TDD-005 | RESOLVED | DSM finding missing 'related_rules' | LOW | testing | FIXED: dsm.py:176 returns related_rules list |
| GAP-TDD-006 | RESOLVED | Tests write TEST-* to production | MEDIUM | testing | RULE-023 | Cleanup fixtures added |
| GAP-TDD-007 | RESOLVED | DSM evidence renders paths char-by-char | LOW | mcp | RULE-012 | Fixed: wrap in list |

---

## Mock/Stub Configuration Gaps (2026-01-14)

> **Source:** Audit of stubs/mocks in production code
> **Evidence:** Session 2026-01-14 - TDD test coverage analysis

| ID | Status | Gap | Priority | Category | Rule | Evidence |
|----|--------|-----|----------|----------|------|----------|
| GAP-EMBED-001 | RESOLVED | MockEmbeddings hardcoded as default in production code | CRITICAL | testing | RULE-004 | FIXED 2026-01-14: governance/embedding_config.py created. 24 tests in test_embedding_config.py. |
| GAP-EMBED-002 | RESOLVED | No USE_MOCK_EMBEDDINGS env var | HIGH | config | RULE-021 | FIXED 2026-01-14: Added USE_MOCK_EMBEDDINGS, EMBEDDING_PROVIDER env vars. See .env.example. |
| GAP-EMBED-003 | RESOLVED | create_embedding_pipeline use_mock=True default | HIGH | testing | RULE-004 | FIXED 2026-01-14: Default now uses env config (production = real embeddings). |
| GAP-EMBED-004 | RESOLVED | Evidence search uses hardcoded MockEmbeddings | HIGH | functionality | RULE-004 | FIXED 2026-01-14: search.py and evidence.py now use create_embedding_generator(). |

---

## DSP Gap Discovery

| ID | Status | Gap | Priority | Category | Rule | Evidence |
|----|--------|-----|----------|----------|------|----------|
| GAP-DSP-001 | RESOLVED | MCP tools not registered | CRITICAL | functionality | RULE-007 | FALSE POSITIVE |
| GAP-DSP-002 | RESOLVED | 9 schema entities without data | HIGH | data | DECISION-003 | Rules 37/37, Tasks synced (2026-01-11) |
| GAP-DSP-003 | RESOLVED | API documentation at 25% | MEDIUM | docs | RULE-001 | All 35+ endpoints have docstrings |
| GAP-SEC-001 | RESOLVED | No API authentication | HIGH | security | RULE-011 | AuthMiddleware |
| GAP-PERF-001 | RESOLVED | Sync I/O in async code | LOW | performance | FIXED: api.py refactored to 213 lines, no sync I/O patterns remaining. Original lines 469,494 no longer exist. |

---

## Data Integrity Gaps

| ID | Status | Gap | Priority | Category | Rule | Evidence |
|----|--------|-----|----------|----------|------|----------|
| GAP-DATA-001 | RESOLVED | Tasks have no content/linkage | CRITICAL | data | DECISION-003 | Fallback added |
| GAP-DATA-002 | RESOLVED | No entity relationships | CRITICAL | architecture | DECISION-003 | TypeDB schema |
| GAP-DATA-003 | RESOLVED | Session evidence not loadable | HIGH | functionality | RULE-001 | API + UI + TypeDB |
| GAP-ARCH-011 | RESOLVED | TypeDB migration incomplete | CRITICAL | architecture | DECISION-003 | session_memory.py |
| GAP-PROC-001 | RESOLVED | Memory/context loss | CRITICAL | process | RULE-012 | SessionContext |
| GAP-ORG-001 | RESOLVED | Files misplaced | MEDIUM | organization | RULE-001 | 24 files moved |

---

## Entity Audit Gaps (P11.8)

| ID | Status | Gap | Priority | Category | Entity | Evidence |
|----|--------|-----|----------|----------|--------|----------|
| GAP-TASK-001 | RESOLVED | linked_sessions 10% coverage | MEDIUM | data | Task | 74/74 tasks have linked_sessions (100%) |
| GAP-TASK-002 | DEFERRED | agent_id always null | LOW | data | Code fixed (set on claim). Existing 200 tasks need backfill migration. Non-critical. |
| GAP-TASK-003 | DEFERRED | completed_at not populated | LOW | data | Code fixed (set on DONE). Existing tasks need backfill migration. Non-critical. |
| GAP-AGENT-001 | RESOLVED | trust_score hardcoded | HIGH | data | Agent | Dynamic calc |
| GAP-AGENT-002 | RESOLVED | tasks_executed always 0 | HIGH | data | Agent | Persistent |
| GAP-AGENT-003 | RESOLVED | last_active not populated | MEDIUM | data | Agent | Updated on task |
| GAP-AGENT-004 | RESOLVED | capabilities field missing | MEDIUM | schema | Agent | Added to model, schema, routes, stores |
| GAP-EVIDENCE-001 | RESOLVED | session_id not populated | HIGH | data | Evidence | 8/9 linked |
| GAP-EVIDENCE-002 | DEFERRED | Only reads .md files | LOW | functionality | Blocked by RD-DOC-SERVICE. Needs multi-format support (JSON, YAML, logs, images). |
| GAP-DECISION-001 | RESOLVED | linked_rules not in API | MEDIUM | api | Decision | Added to model + routes via get_decision_impacts |

---

## Mock/Stub Technical Debt

> **Resolution:** TypeDB-first with in-memory fallback per RULE-021

| ID | Status | Stub | Priority | Evidence |
|----|--------|------|----------|----------|
| GAP-STUB-001 | RESOLVED | _tasks_store Dict | CRITICAL | TypeDB wrapper |
| GAP-STUB-002 | RESOLVED | TypeDB wrapper | CRITICAL | + fallback |
| GAP-STUB-003 | RESOLVED | _sessions_store Dict | CRITICAL | TypeDB wrapper |
| GAP-STUB-004 | RESOLVED | TypeDB wrapper | CRITICAL | + fallback |
| GAP-STUB-005 | RESOLVED | _agents_store Dict | HIGH | TypeDB-first + JSON |
| GAP-STUB-006 | RESOLVED | get_proposals() | MEDIUM | TypeDB proposal: governance_get_proposals() |
| GAP-STUB-007 | RESOLVED | get_escalated_proposals() | MEDIUM | TypeDB proposal: governance_get_escalated_proposals() |

---

## Agent Execution Gaps

| ID | Status | Gap | Priority | Category | Evidence |
|----|--------|-----|----------|----------|----------|
| GAP-AGENT-010 | RESOLVED | Task Backlog not functional | HIGH | functionality | OrchestratorEngine |
| GAP-AGENT-011 | RESOLVED | No agent polling | HIGH | architecture | TypeDBTaskPoller |
| GAP-AGENT-012 | RESOLVED | No task claim/lock mechanism | HIGH | architecture | claim_task() + E2E tests |
| GAP-AGENT-013 | RESOLVED | No delegation protocol | HIGH | architecture | delegation.py |
| GAP-AGENT-014 | RESOLVED | Rules Curator not impl | MEDIUM | functionality | curator_agent.py |

---

## Document MCP Gaps

| ID | Status | Gap | Priority | Category | Evidence |
|----|--------|-----|----------|----------|----------|
| GAP-DOC-001 | RESOLVED | No Document MCP for rules | CRITICAL | functionality | governance_get_rule_document |
| GAP-DOC-002 | RESOLVED | No Document MCP for evidence | CRITICAL | functionality | governance_get_document |
| GAP-DOC-003 | RESOLVED | No TypeDB→Document sync | HIGH | architecture | workspace_link_rules_to_documents |
| GAP-DOC-004 | DEFERRED | No Document version tracking | MEDIUM | architecture | Blocked by RD-DOC-SERVICE. Requires TypeDB schema + version history logic. |

---

## Context Awareness Gaps

| ID | Status | Gap | Priority | Category | Evidence |
|----|--------|-----|----------|----------|----------|
| GAP-CTX-001 | RESOLVED | Agent unaware of tech decisions | CRITICAL | memory | CLAUDE.md section |
| GAP-CTX-002 | RESOLVED | AMNESIA not loading DECISION-* | HIGH | process | ContextPreloader |
| GAP-CTX-003 | RESOLVED | Duplicate memory systems | HIGH | architecture | DECISION-005 Hybrid |
| GAP-CTX-004 | RESOLVED | CLAUDE.md needs SRP/OCP optimization | MEDIUM | documentation | Rules count, index updated |
| GAP-CTX-005 | RESOLVED | Diagrams lack MCP integration details | MEDIUM | documentation | MCP layer added to diagram |
| GAP-CTX-006 | RESOLVED | Rules 033-036 missing from TypeDB | HIGH | sync | 4 rules synced, RULE-032 fixed |
| GAP-CTX-007 | RESOLVED | CLAUDE.md 495→93 lines SRP split | HIGH | documentation | Split to DEVOPS.md, SHELL-GUIDE.md |

---

## File Modularization Gaps

> **Evidence:** [GAP-FILE-RESOLUTIONS.md](evidence/GAP-FILE-RESOLUTIONS.md)

| ID | Status | Gap | Before | After | Reduction |
|----|--------|-----|--------|-------|-----------|
| GAP-FILE-001 | RESOLVED | governance_dashboard.py | 3404 | 1305 | 62% |
| GAP-FILE-002 | RESOLVED | governance/api.py | 2357 | 198 | 92% |
| GAP-FILE-003 | RESOLVED | governance/client.py | 1389 | 135 | 90% |
| GAP-FILE-004 | RESOLVED | state.py | 1547 | 34 | 98% |
| GAP-FILE-005 | RESOLVED | controllers | 1159 | 592 | 49% |
| GAP-FILE-006 | RESOLVED | data_access.py | 1170 | 85 | 93% |
| GAP-FILE-007 | RESOLVED | mcp_server.py | 897 | 120 | 87% |
| GAP-FILE-008 | RESOLVED | evidence.py | 870 | 42 | 95% |
| GAP-FILE-009 | RESOLVED | langgraph_workflow.py | 851 | 136 | 84% |
| GAP-FILE-010 | RESOLVED | pydantic_tools.py | 807 | 175 | 78% |
| GAP-FILE-011 | RESOLVED | external_mcp_tools.py | 791 | 115 | 85% |
| GAP-FILE-012 | RESOLVED | hybrid_router.py | 742 | 99 | 87% |

---

## R&D Assessment Gaps

| ID | Status | Gap | Priority | Category | Evidence |
|----|--------|-----|----------|----------|----------|
| GAP-RD-001 | RESOLVED | Kanren integration benefit assessment | MEDIUM | assessment | 39 tests; used in orchestrator/engine.py for trust-based validation; value confirmed 2026-01-11 |

---

## Memory/Recovery Gaps

| ID | Status | Gap | Priority | Category | Evidence |
|----|--------|-----|----------|----------|----------|
| GAP-MEM-001 | RESOLVED | claude-mem MCP module not implemented | CRITICAL | architecture | Implemented: claude_mem/mcp_server.py (2026-01-11) |
| GAP-MEM-002 | RESOLVED | AMNESIA recovery fallback unavailable | HIGH | resilience | chroma_save_session_context + chroma_recover_context tools |

---

## Infrastructure Gaps

| ID | Status | Gap | Priority | Category | Evidence |
|----|--------|-----|----------|----------|----------|
| GAP-LOG-001 | DEFERRED | Unclear Trame dashboard logs | LOW | observability | Tech debt: Configure Trame logging levels. Low priority. |

---

## Gap Categories Summary

| Category | Count | Priority |
|----------|-------|----------|
| data/integrity | 2 | CRITICAL |
| architecture | 5 | CRITICAL |
| process | 1 | CRITICAL |
| UI (P10) | 12 | HIGH |
| functionality | 4 | CRITICAL/HIGH |
| security | 1 | HIGH |
| workflow | 2 | HIGH |
| testing | 6 | MEDIUM/LOW |
| docs | 3 | Medium |
| organization | 1 | Medium |
| configuration | 2 | Medium |
| tooling | 4 | Medium/Low |
| performance | 1 | Low |

---

*Gap tracking per RULE-013: Rules Applicability Convention*
*Evidence architecture per GAP-META-001: Index→Evidence split*
| GAP-MCP-VALIDATE-001 | MITIGATED | MCP server validation gap - need pre-restart checks | HIGH | testing | [evidence/GAP-MCP-VALIDATE-001.md](evidence/GAP-MCP-VALIDATE-001.md) |
| GAP-MCP-DAEMON-001 | ON_HOLD | MCP daemon architecture - blocked by VSCode #9522 | MEDIUM | architecture | [evidence/GAP-MCP-DAEMON-001.md](evidence/GAP-MCP-DAEMON-001.md) |
