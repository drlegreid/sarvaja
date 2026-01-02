# Gap Index - Sim.ai PoC

**Last Updated:** 2026-01-02
**Total Gaps:** 194 | Status: 77 RESOLVED, 8 PARTIAL, 109 OPEN
**Format Migration:** GAP-WORKFLOW-003 - Replaced strikethrough with Status column

---

## Active Gaps

### UI Gaps (P10 Sprint) - Exploratory Session EXP-P10-001 (2024-12-25)

| ID | Status | Gap | Priority | Category | Entity | Operation | Evidence |
|----|--------|-----|----------|----------|--------|-----------|----------|
| GAP-UI-001 | RESOLVED | No data-testid attributes on Trame components | HIGH | testability | All | N/A | 2026-01-02: 304 data-testid attrs across 13 files |
| GAP-UI-002 | RESOLVED | No CRUD forms for Rules | HIGH | functionality | Rule | CREATE/UPDATE | 2026-01-02: build_rule_form_view exists (rules_view.py:181) |
| GAP-UI-003 | RESOLVED | No detail drill-down views | HIGH | functionality | All | READ | 2026-01-02: detail views for rules/tasks/sessions/decisions/agents |
| GAP-UI-004 | RESOLVED | No REST API endpoints | HIGH | backend | All | ALL | governance/api.py |
| GAP-UI-005 | OPEN | Missing loading/error states | MEDIUM | ux | All | READ | Exploratory |
| GAP-UI-006 | RESOLVED | Rules list missing rule_id column | HIGH | data_binding | Rule | READ | 2026-01-02: rule.id in list title (rules_view.py:105) |
| GAP-UI-007 | RESOLVED | List rows not clickable (no detail navigation) | HIGH | navigation | All | READ | 2026-01-02: click handler navigates to detail (rules_view.py:97) |
| GAP-UI-008 | RESOLVED | Tasks view shows empty table (no data source) | HIGH | data_binding | Task | READ | API seed data added |
| GAP-UI-009 | OPEN | Search returns no results (unclear if functional) | MEDIUM | functionality | Evidence | SEARCH | EXP-P10-001 |
| GAP-UI-010 | OPEN | No column sorting functionality | MEDIUM | ux | All | READ | EXP-P10-001 |
| GAP-UI-011 | PARTIAL | No filtering/faceted search | MEDIUM | functionality | All | SEARCH | 2026-01-02: Rules + Monitor have filters, tasks/sessions pending |
| GAP-UI-028 | RESOLVED | Tests pass but UI broken (lenient tests) | CRITICAL | testing | All | ALL | RULE-028 + 11 UI smoke tests |
| GAP-UI-029 | RESOLVED | Executive Report shows 0 Rules/Agents in stats | HIGH | data | Report | READ | 2024-12-31: Field name mismatch fixed |
| GAP-UI-030 | RESOLVED | Tasks view polluted with 150+ TEST-* tasks | MEDIUM | data | Task | READ | 2024-12-31: Deleted 154 TEST-* tasks |
| GAP-UI-EXP | OPEN | No exploratory UI testing workflow to discover UI gaps | MEDIUM | process | All | N/A | E2E-2024-12-27 |
| GAP-UI-031 | RESOLVED | Rule Save button is mock-only | CRITICAL | functionality | Rule | CREATE/UPDATE | wired to API |
| GAP-UI-032 | RESOLVED | Rule Delete button is mock-only | CRITICAL | functionality | Rule | DELETE | wired to API |
| GAP-UI-033 | RESOLVED | Decision CRUD: API + UI implemented | HIGH | functionality | Decision | ALL | 2026-01-02: models, routes, typedb, view, controller |
| GAP-UI-034 | RESOLVED | Session CRUD: API + UI implemented | HIGH | functionality | Session | ALL | 2026-01-02: models, routes, typedb, view, controller |
| GAP-UI-035 | OPEN | No datetime columns in tables | MEDIUM | ux | All | READ | USER-2024-12-27 |
| GAP-UI-036 | OPEN | No scrolling/paging in tables | MEDIUM | ux | All | READ | USER-2024-12-27 |
| GAP-UI-037 | RESOLVED | Entity content previews added | HIGH | ux | All | READ | 2026-01-02: tasks/rules/decisions views have styled content cards |
| GAP-UI-038 | RESOLVED | Fullscreen document viewer added | HIGH | functionality | Document | READ | 2026-01-02: views/dialogs.py with build_file_viewer_dialog |
| GAP-UI-039 | OPEN | No document format support (CSV, Markdown, etc.) | MEDIUM | functionality | Document | READ | USER-2024-12-27 → RD-DOCVIEW |
| GAP-UI-040 | RESOLVED | Agent config/instructions/tools display | HIGH | functionality | Agent | READ | 2026-01-02: agents_view.py with config/metrics/relations cards |
| GAP-UI-041 | RESOLVED | Agent-session/task relation links | HIGH | functionality | Agent | READ | 2026-01-02: build_agent_relations_card in agents_view.py |
| GAP-UI-042 | RESOLVED | Trust score history/explanation added | HIGH | functionality | Agent | READ | 2026-01-02: build_trust_history_card with RULE-011 formula, components, timeline |
| GAP-UI-043 | RESOLVED | Agent metrics display added | MEDIUM | functionality | Agent | READ | 2026-01-02: build_agent_metrics_card in agents_view.py |
| GAP-UI-044 | RESOLVED | No Executive Reporting view in Session Evidence tab | HIGH | functionality | Session | READ | governance_dashboard.py + api.py |
| GAP-UI-045 | OPEN | No cross-workspace metrics aggregation | MEDIUM | functionality | Session | READ | RULE-029 |
| GAP-UI-046 | OPEN | Executive Report should be per-session not quarterly/monthly | HIGH | functionality | Session | READ | User 2024-12-28 |

**GAP-UI-046 Requirements:**
- Replace Sessions view with Executive Reports per session
- Each prompt = separate session with its own report
- Report should show date/time, not period selection (week/month/quarter)
- Session evidence + executive summary combined view

#### Insights Captured (EXP-P10-001)

```
Session: EXP-P10-001 | Date: 2024-12-25 | Target: Governance Dashboard

[DISCOVERY] Dashboard header shows "11 Rules | 5 Decisions" - data is loading
[DISCOVERY] Navigation works: Rules, Decisions, Sessions, Tasks, Search tabs functional
[DISCOVERY] Rules view: Shows 11 rules with title + status badge, but NO rule_id column
[DISCOVERY] Decisions view: Shows 5 decisions WITH decision_id visible (inconsistent with Rules)
[DISCOVERY] Sessions view: Shows 6 sessions with dates
[DISCOVERY] Tasks view: Empty table with "No data available" - possible missing data source
[DISCOVERY] Search view: Has search box but no results returned for "RULE-001"

[GAP] GAP-UI-006: Rules list inconsistent with Decisions (no ID column)
[GAP] GAP-UI-007: Cannot click rows to see detail - fundamental navigation broken
[GAP] GAP-UI-008: Tasks view has no data - check if API or MCP tool connected
[GAP] GAP-UI-009: Search function unclear - no results or feedback

[DECISION] Use Spec-First TDD for P10 implementation - we have full control
[DECISION] Start with Rules entity (P0) - most complete data already loaded
```

### General Gaps

| ID | Status | Gap | Priority | Category | Rule | Evidence |
|----|--------|-----|----------|----------|------|----------|
| GAP-004 | OPEN | Grok/xAI API Key | Medium | configuration | RULE-002 | test skip |
| GAP-005 | OPEN | Agent Task Backlog UI | Medium | functionality | RULE-002 | Status filtering fixed, polling not impl |
| GAP-006 | OPEN | Sync Agent Implementation | Medium | functionality | RULE-003 | skeleton only |
| GAP-007 | OPEN | ChromaDB v2 Test Update | Low | testing | RULE-009 | UUID error |
| GAP-008 | RESOLVED | Agent UI Image | Low | configuration | RULE-009 | Service disabled in docker-compose |
| GAP-009 | OPEN | Pre-commit Hooks | Medium | tooling | RULE-001 | RULES-DIRECTIVES.md |
| GAP-010 | OPEN | CI/CD Pipeline | Low | tooling | RULE-009 | DEPLOYMENT.md |
| GAP-014 | OPEN | IntelliJ Windsurf MCP not loading | Medium | tooling | RULE-005 | ~/.codeium/mcp_config.json |
| GAP-015 | OPEN | Consolidated STRATEGY.md | Medium | docs | RULE-001 | docs/GAP-ANALYSIS-2024-12-24.md |
| GAP-019 | RESOLVED | MCP usage documentation | Medium | docs | RULE-007 | docs/MCP-USAGE.md |
| GAP-020 | RESOLVED | Cross-project knowledge queries | HIGH | workflow | RULE-007 | MCP-USAGE.md Section 8 |
| GAP-021 | OPEN | OctoCode for external research | Medium | workflow | RULE-007 | Use OctoCode for GitHub |
| GAP-DEPLOY-001 | RESOLVED | deploy.ps1 missing dev profile support | MEDIUM | tooling | RULE-028 | 2024-12-31: Added 'dev' to ValidateSet |
| GAP-MCP-002 | PARTIAL | MCP governance healthcheck should force Claude Code to stop and resolve dependent services | HIGH | stability | RULE-021 | Tool implemented but not auto-called |
| GAP-MCP-003 | RESOLVED | governance_health not called automatically at session start | CRITICAL | workflow | RULE-021 | 2026-01-01: Non-blocking healthcheck with 30s retry |
| GAP-WORKFLOW-001 | PARTIAL | Session context not auto-saved to claude-mem before restart | HIGH | workflow | RULE-001 | 2026-01-02: Added /save guidance in CLAUDE.md Session Directives |
| GAP-WORKFLOW-002 | OPEN | Claude Code should prompt user to /save before major transitions | HIGH | workflow | RULE-001 | Autonomous work should include save prompts |
| GAP-WORKFLOW-003 | RESOLVED | GAP-INDEX uses strikethrough instead of Status column | HIGH | data | RULE-012 | 2026-01-02: This migration |
| GAP-INFRA-005 | OPEN | Ollama container not started with dev profile | MEDIUM | infra | RULE-021 | docker compose --profile dev issue |
| GAP-INFRA-006 | OPEN | Ollama container suboptimal for laptop dev workflow | MEDIUM | infrastructure | RULE-021 | May need to disable for DEV |
| GAP-MCP-004 | RESOLVED | Rule fallback to markdown files now implemented | HIGH | architecture | RULE-021 | 2026-01-02: governance/mcp_tools/rule_fallback.py, 14 tests |
| GAP-TEST-001 | OPEN | E2E tests lack Given/When/Then BDD paradigm and OOP reusability | MEDIUM | testing | RULE-023 | No pytest fixtures, BDD patterns |
| GAP-HEALTH-001 | OPEN | Healthcheck state file lacks retry history and rotation | MEDIUM | observability | RULE-021 | Should track all retry attempts |
| GAP-HEALTH-002 | RESOLVED | Healthcheck now detects document entropy (RULE-012 DSP trigger) | HIGH | workflow | RULE-012 | 2026-01-02: _detect_document_entropy() checks gaps, files, DSM, evidence |
| GAP-TEST-002 | PARTIAL | Test output blows context window - need reporting modes | HIGH | testing | RULE-023 | Implemented --report-minimal, --report-cert |
| GAP-TEST-003 | PARTIAL | E2E tests require port 8082 API server (not Docker 8080) | HIGH | testing | RULE-023 | 2026-01-02: API containerized (TOOL-006), runs on 8082 in Docker |
| GAP-HEUR-001 | PARTIAL | Exploratory tests lack SFDIPOT/CRUCSS heuristics framework | HIGH | testing | RULE-023 | 2026-01-02: Framework created (tests/heuristics/), 16 example tests |
| GAP-META-001 | OPEN | GAPs lack evidence file references - context bloat risk | HIGH | architecture | RULE-012 | 2026-01-02: Index→Evidence split needed |
| GAP-META-002 | OPEN | No standardized CATEGORY taxonomy for gaps/rules | HIGH | governance | RULE-013 | 2026-01-02: Need GOVERNANCE/TESTING/UI/etc |
| GAP-RULE-001 | OPEN | Rules lack applicability TYPE (FORBIDDEN/CONDITIONAL/RECOMMENDED) | HIGH | governance | RULE-013 | 2026-01-02: Schema needs TYPE column |
| GAP-RULE-002 | OPEN | Rules don't include good/bad practices with rationale | HIGH | governance | RULE-013 | 2026-01-02: Need examples + anti-patterns |

**GAP-META-001 Evidence Architecture:** Index→Evidence Split
- **Problem:** GAP-INDEX.md has 1000+ lines, bloating LLM context when reading gaps
- **Current:** Evidence is inline with gaps, mixing index with content
- **Solution:**
  1. GAP-INDEX.md stays lean: ID, Status, Gap, Priority, Category, Rule, Evidence (file reference only)
  2. Evidence files in `docs/gaps/evidence/GAP-XXX.md` contain full details
  3. MCP tool `governance_get_gap_evidence(gap_id)` to fetch on demand
- **Benefits:** LLM reads index first, fetches evidence only when needed

**GAP-META-002 Category Taxonomy:**
| Category | Purpose | Examples |
|----------|---------|----------|
| GOVERNANCE | Rule/decision management | RULE-001, RULE-011 |
| ARCHITECTURE | System design | TypeDB, MCP, hybrid routing |
| TESTING | Test infrastructure | pytest, E2E, TDD |
| UI | Dashboard, views | Trame, Vuetify |
| WORKFLOW | Process automation | DSP, session, evidence |
| INFRASTRUCTURE | Docker, deployment | containers, health |
| SECURITY | Auth, validation | API keys, middleware |
| DATA | Entities, integrity | TypeDB entities, sync |
| DOCUMENTATION | Docs, comments | API docs, CLAUDE.md |
| META | Self-referential | Gap tracking itself |

**GAP-RULE-001 Applicability Types:**
| TYPE | Description | Example |
|------|-------------|---------|
| FORBIDDEN | Must never do | Commit secrets, skip tests |
| REQUIRED | Must always do | Session logging, health checks |
| CONDITIONAL | Context-dependent | Use TypeDB when available |
| RECOMMENDED | Best practice | Modularize >300 line files |
| DEPRECATED | Phase out | Strikethrough in gaps |

**GAP-RULE-002 Rule Structure Template:**
```markdown
## RULE-XXX: [Name]

**Type:** REQUIRED | FORBIDDEN | CONDITIONAL | RECOMMENDED
**Category:** GOVERNANCE | TESTING | etc.
**Priority:** CRITICAL | HIGH | MEDIUM | LOW

### Directive
[What to do/not do]

### Rationale
[Why this rule exists]

### Good Practices ✓
- [Example of correct behavior]
- [Another good pattern]

### Bad Practices ✗
- [Anti-pattern to avoid]
- [What goes wrong]

### Evidence
- [Link to evidence file]
```

**GAP-HEUR-001 Exploratory Testing Heuristics Framework:**
- **Problem:** Exploratory tests don't enforce established heuristics for systematic gap discovery
- **Required Heuristics:**

| Heuristic | Description | Test Level |
|-----------|-------------|------------|
| **SFDIPOT** | Structure, Function, Data, Interfaces, Platform, Operations, Time | API + UI |
| **CRUCSS** | Capability, Reliability, Usability, Charisma, Security, Scalability | Integration + E2E |
| **HICCUPPS** | History, Image, Claims, Competitors, Procedures, Products, Standards | Acceptance |

- **Implementation Requirements:**
  1. Create `tests/heuristics/` directory with heuristic test templates
  2. Add `@pytest.mark.heuristic(name="SFDIPOT.Data")` markers to tests
  3. Create heuristic coverage report showing which heuristics are tested
  4. Integrate with Playwright MCP for UI-level heuristic testing
  5. Add data integrity checks (lower layers) and coverage checks (upper layers)

- **SFDIPOT Test Matrix:**
  | Aspect | API Tests | UI Tests | Evidence |
  |--------|-----------|----------|----------|
  | Structure | Schema validation | Component hierarchy | TypeQL schema |
  | Function | Endpoint behavior | User workflows | test_*.py |
  | Data | Field validation | Form inputs | data.tql |
  | Interfaces | API contracts | Navigation flows | OpenAPI spec |
  | Platform | Container health | Browser compat | E2E results |
  | Operations | Error handling | User experience | Error logs |
  | Time | Response latency | Render performance | metrics.json |

- **Files to Create:**
  - `tests/heuristics/__init__.py`
  - `tests/heuristics/sfdipot.py` - SFDIPOT test decorators + fixtures
  - `tests/heuristics/crucss.py` - CRUCSS test decorators + fixtures
  - `tests/heuristics/coverage_report.py` - Heuristic coverage analyzer

**GAP-TEST-002 Test Reporting Modes:** ✅ IMPLEMENTED
- **Usage:**
  - `pytest tests/ --report-minimal` - Dots only (`. F S`)
  - `pytest tests/ --report-trace` - Full verbose output (-vv)
  - `pytest tests/ --report-cert` - JSON evidence to `/results/YYYY-MM-DD/`
  - `pytest tests/ --report-cert --results-dir=custom` - Custom output dir
- **Files:** `tests/conftest.py` (MinimalReporter, CertificationReporter classes)
- **Remaining:** Coverage HTML report generation (--report-cert + coverage)

**GAP-HEALTH-001 Requirements:**
- **Current State:** `.claude/hooks/.healthcheck_state.json` stores single point-in-time status
- **Issue:** No historical retry tracking; state persists indefinitely across sessions
- **Required Changes:**
  1. Add `retry_history[]` array to track all retry attempts with timestamps
  2. Add `session_id` field to link state to Claude Code session
  3. Implement rotation: Archive old state files on session end (keep last 5)
  4. Add `total_retries_this_session` counter for debugging
- **Implementation Path:** Modify `.claude/hooks/healthcheck.py` to:
  - Append to retry_history on each check
  - Detect session change (new Claude Code instance) via env or timestamp gap
  - Archive previous session state to `.healthcheck_state.{timestamp}.json`
  - Cap retry_history to last 100 entries to prevent unbounded growth

**GAP-HEALTH-002 Entropy Detection (RULE-012 DSP Trigger):**
- **Problem:** Healthcheck doesn't detect document entropy that should trigger DEEP SLEEP mode
- **Per RULE-012:** Files >300 lines, document bloat, excessive gaps should trigger DSP
- **Required Checks in healthcheck.py:**
  1. `check_file_entropy()` - Scan for files >300 lines in governance/, agent/, docs/
  2. `check_gap_entropy()` - Count OPEN gaps, ALERT if >100 open HIGH/CRITICAL
  3. `check_test_debt()` - Detect skipped tests, failing tests ratio
  4. `check_rule_staleness()` - Rules without recent updates or evidence
- **ALERT Thresholds:**
  | Metric | Warning | Alert (DSP Trigger) |
  |--------|---------|---------------------|
  | Files >300 lines | 3+ | 5+ |
  | OPEN HIGH/CRITICAL gaps | 20+ | 40+ |
  | Test failure rate | 5% | 10% |
  | Rules without evidence | 5+ | 10+ |
- **Output:** Add `entropy_status` to healthcheck JSON with `needs_dsp: true/false`
- **Integration:** When `needs_dsp: true`, output message suggesting DEEP SLEEP mode

**GAP-MCP-004 Analysis:**
- **Issue:** When TypeDB is unavailable, agents cannot access rule content
- **Current:** hybrid_router.py has TypeDB→ChromaDB fallback for *queries*, not rule content
- **Current:** rule_linker.py has static mapping fallback for scanning, not reading
- **Needed:** Implement `get_rule_from_markdown(rule_id)` function that reads from:
  - `docs/rules/RULES-GOVERNANCE.md` (RULE-001,003,006,011,013)
  - `docs/rules/RULES-TECHNICAL.md` (RULE-002,007,008,009,010)
  - `docs/rules/RULES-OPERATIONAL.md` (RULE-004,005,012,014+)
- **Implementation:** governance/mcp_tools/rules.py should check TypeDB first, fallback to markdown
- **Evidence:** rule_linker.py:32-36 has RULE_DOCUMENT_MAP that can be leveraged

### Architecture Gaps (DSP-2024-12-26)

| ID | Status | Gap | Priority | Category | Rule | Evidence |
|----|--------|-----|----------|----------|------|----------|
| GAP-ARCH-001 | RESOLVED | Tasks in-memory, not TypeDB | CRITICAL | architecture | DECISION-003 | Hybrid TypeDB+fallback |
| GAP-ARCH-002 | RESOLVED | Sessions in-memory, not TypeDB | CRITICAL | architecture | DECISION-003 | Hybrid TypeDB+fallback |
| GAP-ARCH-003 | RESOLVED | Agents in-memory, not TypeDB | HIGH | architecture | DECISION-003 | P10.3: TypeDB-first seeding |
| GAP-ARCH-004 | RESOLVED | TypeDB missing RULE-012 to RULE-025 | CRITICAL | data | RULE-012 | 25 rules loaded |
| GAP-ARCH-005 | RESOLVED | No MCP tools for Tasks/Sessions | HIGH | functionality | RULE-007 | mcp_tools/tasks.py + agents.py |
| GAP-ARCH-007 | RESOLVED | Entity hierarchy review: Decision as Task subtype | MEDIUM | architecture | DECISION-003 | Keep separate |
| GAP-ARCH-006 | RESOLVED | Session/Task MCP exports missing | HIGH | testing | RULE-023 | exports added |
| GAP-ARCH-008 | RESOLVED | TypeDB-Filesystem Rule Linking | MEDIUM | architecture | DECISION-003 | P10.8: rule_linker.py + 4 MCP tools |
| GAP-ARCH-009 | OPEN | TypeDB sessions created but not retrievable for end operation | MEDIUM | architecture | DECISION-003 | E2E test: test_end_session_via_api fails 404 |
| GAP-ARCH-010 | RESOLVED | Workspace tasks not captured in TypeDB | HIGH | architecture | DECISION-003 | P10.10: workspace_scanner.py + 3 MCP tools |
| GAP-ARCH-012 | RESOLVED | agents-1 container fails to start | HIGH | docker | RULE-030 | 2026-01-02: Fixed OrchestratorEngine type hint |

### Sync & Integration Gaps (2026-01-02)

> **Source:** Risk of divergence between TypeDB governance data and workspace files
> **Related:** TOOL-006-009 (MCP Architecture R&D), GAP-DOC-003, GAP-CTX-003

| ID | Status | Gap | Priority | Category | Rule | Evidence |
|----|--------|-----|----------|----------|------|----------|
| GAP-SYNC-001 | OPEN | TypeDB rules/tasks may diverge from workspace files | HIGH | architecture | DECISION-003 | 2026-01-02: Bidirectional sync needed |
| GAP-SYNC-002 | OPEN | No validation workflow to detect divergence | HIGH | testing | RULE-023 | Need comparison report tool |
| GAP-SYNC-003 | OPEN | MCP services need refactoring before sync implementation | MEDIUM | architecture | RULE-012 | See TOOL-006-009 in R&D-BACKLOG |

**GAP-SYNC-001 Analysis:**
- **Problem:** Rules in TypeDB (25) vs rules in docs/rules/*.md may diverge
- **Problem:** Tasks in TypeDB vs workspace TODO.md may diverge
- **Problem:** Sessions in TypeDB vs evidence/*.md files may diverge
- **Current State:**
  - workspace_capture_tasks() syncs TODO.md → TypeDB (one-way)
  - workspace_link_rules_to_documents() links rules → markdown (references only)
  - No bidirectional sync or divergence detection
- **Required:**
  1. `governance_sync_status()` - Report divergence between TypeDB and files
  2. `governance_sync_rules()` - Bidirectional rule sync with conflict detection
  3. `governance_sync_tasks()` - Bidirectional task sync with status tracking

**Safe/Quality-Driven Approach for MCP Refactoring:**
```
┌─────────────────────────────────────────────────────────────────────────┐
│               MCP REFACTORING PRIORITY ORDER (SAFE PATH)                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  STEP 1: STABILIZE (Before any refactoring)                             │
│  ─────────────────────────────────────────────                          │
│  □ Run full test suite: pytest tests/ -v                                │
│  □ Document baseline: 1160 tests passing                                │
│  □ Commit current state as checkpoint                                   │
│                                                                          │
│  STEP 2: SYNC VALIDATION (GAP-SYNC-002)                                 │
│  ─────────────────────────────────────────                              │
│  □ Add governance_sync_status() MCP tool                                │
│  □ Compare TypeDB rules vs docs/rules/*.md                              │
│  □ Compare TypeDB tasks vs TODO.md                                      │
│  □ Generate divergence report                                           │
│                                                                          │
│  STEP 3: MCP CONSOLIDATION (TOOL-007)                                   │
│  ────────────────────────────────────                                   │
│  □ Evaluate: Should governance MCP be split into smaller MCPs?          │
│  □ Current: 40+ tools in single governance MCP                          │
│  □ Consider: rules-mcp, tasks-mcp, sessions-mcp, evidence-mcp           │
│                                                                          │
│  STEP 4: BIDIRECTIONAL SYNC (GAP-SYNC-001)                              │
│  ─────────────────────────────────────────                              │
│  □ Implement with conflict detection                                    │
│  □ Last-write-wins vs merge strategy                                    │
│  □ Audit trail for sync operations                                      │
│                                                                          │
│  STEP 5: CONTAINERIZATION (TOOL-006)                                    │
│  ───────────────────────────────────                                    │
│  □ Only after sync is stable                                            │
│  □ Docker container for MCP services                                    │
│  □ Eliminates NPX cold-start issues                                     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### TDD Stub Gaps (DSP-2024-12-26 Cycles 201-330)

| ID | Status | Gap | Priority | Category | Rule | Evidence |
|----|--------|-----|----------|----------|------|----------|
| GAP-TDD-001 | RESOLVED | Task response missing 'phase' field | MEDIUM | testing | RULE-025 | mcp_server.py:169 |
| GAP-TDD-002 | RESOLVED | Evidence search missing 'query'/'score' | MEDIUM | testing | RULE-025 | mcp_server.py:223 |
| GAP-TDD-003 | OPEN | DSM advance missing 'required_mcps' | LOW | testing | RULE-012 | test_dsm_tracker_integration.py |
| GAP-TDD-006 | OPEN | Tests write TEST-* data to production TypeDB | MEDIUM | testing | RULE-023 | Caused GAP-UI-030, need isolation |
| GAP-TDD-004 | OPEN | DSM checkpoint missing 'timestamp' | LOW | testing | RULE-012 | test_dsm_tracker_integration.py |
| GAP-TDD-005 | OPEN | DSM finding missing 'related_rules' | LOW | testing | RULE-012 | test_dsm_tracker_integration.py |

### DSP Gap Discovery (Cycles 331-380)

| ID | Status | Gap | Priority | Category | Rule | Evidence |
|----|--------|-----|----------|----------|------|----------|
| GAP-DSP-001 | RESOLVED | MCP tools not registered | CRITICAL | functionality | RULE-007 | FALSE POSITIVE: 40 tools registered |
| GAP-DSP-002 | OPEN | 9 schema entities without data | HIGH | data | DECISION-003 | schema.tql vs data.tql |
| GAP-DSP-003 | OPEN | API documentation at 25% | MEDIUM | docs | RULE-001 | api.py 5/20 docstrings |
| GAP-SEC-001 | RESOLVED | No API authentication middleware | HIGH | security | RULE-011 | AuthMiddleware + X-API-Key header |
| GAP-PERF-001 | OPEN | Sync I/O in async code | LOW | performance | RULE-009 | api.py:469,494 |

### Data Integrity Gaps (2024-12-26 Data Audit)

| ID | Status | Gap | Priority | Category | Rule | Evidence |
|----|--------|-----|----------|----------|------|----------|
| GAP-DATA-001 | RESOLVED | Tasks have no descriptions/content/linkage | CRITICAL | data | DECISION-003 | 2026-01-02: _task_to_dict uses body>description>name fallback + linked_rules/sessions |
| GAP-DATA-002 | RESOLVED | No entity relationships (Task→Rule, Session→Evidence) | CRITICAL | architecture | DECISION-003 | P11.3: TypeDB schema + relationships |
| GAP-DATA-003 | RESOLVED | Session evidence attachments not loadable | HIGH | functionality | RULE-001 | P11.5: API + UI + TypeDB linkage |
| GAP-ARCH-011 | RESOLVED | TypeDB migration incomplete (claude-mem disconnected) | CRITICAL | architecture | DECISION-003 | P11.4: session_memory.py + DSM |
| GAP-PROC-001 | RESOLVED | Memory/context loss - no wisdom accumulation | CRITICAL | process | RULE-012 | P11.4: SessionContext + AMNESIA recovery |
| GAP-ORG-001 | RESOLVED | Files misplaced (png/xml/html in wrong directories) | MEDIUM | organization | RULE-001 | P11.6: 24 files reorganized |
| GAP-UI-035-DUP | RESOLVED | UI views don't auto-load data on open | HIGH | ux | RULE-019 | Added state change handler |

### P11.8 Entity Audit Gaps (2024-12-26)

> **Source:** [DATA-AUDIT-REPORT-2024-12-26.md](DATA-AUDIT-REPORT-2024-12-26.md)

| ID | Status | Gap | Priority | Category | Entity | Field | Evidence |
|----|--------|-----|----------|----------|--------|-------|----------|
| GAP-TASK-001 | OPEN | Tasks linked_sessions only 10% coverage | MEDIUM | data | Task | linked_sessions | P11.8 Audit |
| GAP-TASK-002 | OPEN | Tasks agent_id always null | LOW | data | Task | agent_id | P11.8 Audit |
| GAP-TASK-003 | OPEN | Tasks completed_at not populated | LOW | data | Task | completed_at | P11.8 Audit |
| GAP-AGENT-001 | RESOLVED | Agent trust_score hardcoded, not calculated | HIGH | data | Agent | trust_score | P11.9: Dynamic calculation |
| GAP-AGENT-002 | RESOLVED | Agent tasks_executed always 0, resets on restart | HIGH | data | Agent | tasks_executed | P11.9: Persistent metrics |
| GAP-AGENT-003 | RESOLVED | Agent last_active never populated | MEDIUM | data | Agent | last_active | P11.9: Updated on task |
| GAP-AGENT-004 | OPEN | Agent capabilities field missing | MEDIUM | schema | Agent | capabilities | P11.8 Audit |
| GAP-EVIDENCE-001 | RESOLVED | Evidence session_id never populated (no linkage) | HIGH | data | Evidence | session_id | P11.10: 8/9 linked |
| GAP-EVIDENCE-002 | OPEN | Evidence only reads .md files | LOW | functionality | Evidence | file_types | P11.8 Audit |
| GAP-DECISION-001 | OPEN | Decision linked_rules not exposed in API | MEDIUM | api | Decision | linked_rules | P11.8 Audit |

### Mock/Stub Technical Debt (P10.1-P10.3) - HYBRID ARCHITECTURE

> **Resolution:** TypeDB-first with in-memory fallback per RULE-021 (graceful degradation)
> Implemented: `governance/stores.py` wrappers + `routes/tasks.py`, `routes/sessions.py` usage

| ID | Status | Stub Location | Task | Priority | Target Data Source |
|----|--------|---------------|------|----------|-------------------|
| GAP-STUB-001 | RESOLVED | `governance/stores.py:48` `_tasks_store: Dict` | P10.1 | CRITICAL | TypeDB via `get_all_tasks_from_typedb()` |
| GAP-STUB-002 | RESOLVED | `governance/stores.py:71-118` TypeDB wrapper | P10.1 | CRITICAL | TypeDB + fallback to in-memory |
| GAP-STUB-003 | RESOLVED | `governance/stores.py:56` `_sessions_store: Dict` | P10.2 | CRITICAL | TypeDB via `get_all_sessions_from_typedb()` |
| GAP-STUB-004 | RESOLVED | `governance/stores.py:147+` TypeDB wrapper | P10.2 | CRITICAL | TypeDB + fallback to in-memory |
| GAP-STUB-005 | OPEN | `governance/api.py:558-604` `_agents_store: Dict` | P10.3 | HIGH | TypeDB `agent` entity |
| GAP-STUB-006 | OPEN | `agent/governance_ui/data_access.py:42` `get_proposals()` | P10.7 | MEDIUM | TypeDB `proposal` entity |
| GAP-STUB-007 | OPEN | `agent/governance_ui/data_access.py:48` `get_escalated_proposals()` | P10.7 | MEDIUM | TypeDB `proposal` with escalation |

### User Feedback Gaps (2024-12-26 Session)

> **Source:** User feedback during TODO-6 development
> **Note:** IDs corrected 2026-01-01 (previously duplicated GAP-UI-040-044)

| ID | Status | Gap | Priority | Category | Entity | Evidence |
|----|--------|-----|----------|----------|--------|----------|
| GAP-UI-047 | OPEN | Rules tab: No directive/description shown | HIGH | ui | Rule | User feedback |
| GAP-UI-048 | OPEN | No entity relationships displayed in UI | HIGH | ui | All | User feedback |
| GAP-UI-049 | OPEN | Tasks: No description, no linkage to sessions/evidence/rules | HIGH | ui | Task | User feedback |
| GAP-UI-050 | OPEN | Session evidence tab has no data | HIGH | functionality | Session | User feedback |
| GAP-UI-051 | OPEN | Real-time rule monitoring tab not functional | HIGH | functionality | Monitor | User feedback |

### Document MCP Gaps (2024-12-27 Assessment)

> **Source:** Platform usability assessment - user cannot view documents in evidence/task/rule links

| ID | Status | Gap | Priority | Category | Entity | Evidence |
|----|--------|-----|----------|----------|--------|----------|
| GAP-DOC-001 | RESOLVED | No Document viewing MCP for rule markdown files | CRITICAL | functionality | Rule | governance_get_rule_document |
| GAP-DOC-002 | RESOLVED | No Document viewing MCP for evidence files | CRITICAL | functionality | Evidence | governance_get_document |
| GAP-DOC-003 | OPEN | No TypeDB→Document sync architecture | HIGH | architecture | All | R&D-BACKLOG DOC-001 |
| GAP-DOC-004 | OPEN | No Document version tracking in TypeDB | MEDIUM | architecture | All | R&D-BACKLOG DOC-004 |

### Platform UI Gaps (2024-12-27 Assessment)

> **Source:** Platform usability assessment - agent platform not ready for production use
> **Related:** RULE-011 (Multi-Agent Governance), RULE-014 (Autonomous Task Sequencing)
> **Design Doc:** [DESIGN-Governance-MCP.md](../DESIGN-Governance-MCP.md)

| ID | Status | Gap | Priority | Category | Entity | Evidence |
|----|--------|-----|----------|----------|--------|----------|
| GAP-UI-CHAT-001 | RESOLVED | Platform UI has no prompt/chat functionality for commanding agents | CRITICAL | functionality | Agent | 2026-01-02: Chat view + API exists (governance_ui/views/chat_view.py) |
| GAP-UI-CHAT-002 | RESOLVED | Task execution viewer added to chat | CRITICAL | functionality | Agent | 2026-01-02: build_task_execution_viewer() in chat_view.py |

#### GAP-UI-CHAT-001/002 Requirements Specification

**Problem:** User cannot command agents from the platform UI. Agents are not picking up tasks from the backlog.

**Required Capabilities:**

1. **Agent Command Interface**
   - Prompt/chat UI for sending commands to agents
   - Task assignment to specific agents
   - View agent execution status and responses

2. **Task Orchestration (per RULE-014)**
   - Orchestration Agent coordinates task execution
   - Tasks picked up from TypeDB backlog automatically
   - Priority-based task sequencing

3. **Agent Delegation Chain**
   - If agent lacks context → delegate to Research Agent
   - Research Agent gathers context → returns to original agent
   - Delegation tracked in session evidence

4. **Rules Curator Agent**
   - Monitors rule quality and conflicts
   - Clarifies ambiguous rules
   - Escalates to human when resolution unclear
   - Per RULE-011 trust-weighted voting

**Related Tasks:**
- P9.5: Agent Trust Dashboard ✅ (trust scores visible)
- P10.7: Entity Hierarchy (Decision as Task subtype)
- GAP-AGENT-010: Agent Task Backlog not functional

**Architecture:**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Agent Orchestration Layer                             │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ Orchestrator│  │ Research    │  │ Coding      │  │ Rules       │   │
│  │ Agent       │  │ Agent       │  │ Agent       │  │ Curator     │   │
│  │ (dispatch)  │  │ (context)   │  │ (impl)      │  │ (governance)│   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘   │
│         │                │                │                │           │
│         └────────────────┴────────────────┴────────────────┘           │
│                                   │                                     │
│                    ┌──────────────▼──────────────┐                     │
│                    │   TypeDB Task Backlog       │                     │
│                    │   (priority queue)          │                     │
│                    └─────────────────────────────┘                     │
└─────────────────────────────────────────────────────────────────────────┘
```

### R&D Assessment Gaps (2024-12-31)

| ID | Status | Gap | Priority | Category | Evidence |
|----|--------|-----|----------|----------|----------|
| GAP-RD-001 | OPEN | Kanren integration benefit assessment: Has KAN-001/KAN-002 improved workflow stability? | MEDIUM | assessment | RD-KANREN-CONTEXT.md: 39 tests pass, but real-world usage not measured |

**GAP-RD-001 Assessment Criteria:**
- **KAN-001/KAN-002 Status:** ✅ DONE (governance/kanren_constraints.py, 39 tests)
- **Constraints Implemented:** trust_level, requires_supervisor, can_execute_priority, valid_task_assignment, valid_rag_chunk
- **Expected Benefits:**
  1. Formal constraint validation before task execution
  2. Trust-based supervisor requirements per RULE-011
  3. RAG chunk filtering per RULE-007
  4. Reversible context queries ("what caused this?")
- **Measurement Needed:**
  - [ ] Count: How many times Kanren constraints prevented invalid states?
  - [ ] Coverage: Which workflows actually use Kanren validation?
  - [ ] Performance: Latency impact of constraint checking?
  - [ ] Stability: Reduction in runtime errors post-integration?
- **Related:** KAN-003 (RAG filter), KAN-004 (TypeDB→Kanren sync), KAN-005 (benchmarks)

### Infrastructure Gaps (2024-12-31)

| ID | Status | Gap | Priority | Category | Evidence |
|----|--------|-----|----------|----------|----------|
| GAP-INFRA-001 | RESOLVED | Docker health checks misconfigured | HIGH | infrastructure | 2024-12-31: ChromaDB v1→v2, LiteLLM /health→/health/liveliness |
| GAP-INFRA-002 | RESOLVED | Dev vs Prod dashboard workflow undocumented | HIGH | documentation | DEPLOYMENT.md "Development vs Production Mode" section |
| GAP-INFRA-003 | RESOLVED | deploy.ps1 missing dev profile support | MEDIUM | tooling | Added 'dev' to ValidateSet, updated docs/endpoints |
| GAP-INFRA-004 | OPEN | No Docker infrastructure health dashboard or startup validation | HIGH | observability | User 2024-12-31: "rules system damaged, blocks cognition" |
| GAP-INFRA-006-DUP | OPEN | Ollama container suboptimal for laptop dev workflow - high memory usage | MEDIUM | infrastructure | May need to disable for DEV, use Claude API |

**GAP-INFRA-006 Analysis:**
- **Issue:** Ollama-1 container consumes significant laptop memory (models loaded)
- **Risk:** Memory pressure may cause Claude Code crashes (exit code 3221226505)
- **Current State:** Ollama started with dev profile but may not be needed for strategic/gaps/R&D tasks
- **Options:**
  1. **Disable Ollama in DEV profile** - Remove from docker-compose dev profile, use Claude API
  2. **Migrate to server** - Move Ollama to dedicated server, connect via network
  3. **Load on demand** - Only start Ollama when local LLM inference needed
- **Recommendation:** For Claude Code strategic work (gaps, R&D, governance), disable Ollama in DEV profile

**GAP-INFRA-001 Analysis:**
- ChromaDB: heartbeat responds `{"nanosecond heartbeat": ...}` ✅
- TypeDB: gRPC port (not HTTP), curl returns empty but service running ✅
- Ollama: `/api/tags` returns models ✅
- LiteLLM: `/health` returns 401 (needs API key) ✅
- **Root cause:** docker-compose.yml health checks use wrong commands/endpoints

**GAP-MCP-002 Requirements Specification:**

**Problem:** MCP governance service should check if dependencies (TypeDB, ChromaDB) are healthy before operations. If dependencies fail, Claude Code should be notified to stop and attempt to resolve the issue automatically.

**Related:**
- RULE-021: MCP Healthcheck Protocol (Level 3: Recovery Protocol)
- R&D-BACKLOG: "Docker Wrapper" pattern for MCP dependency auto-start
- GAP-INFRA-004: Infrastructure health dashboard

**Required Capabilities:**

1. **Pre-Operation Health Check (RULE-021 Level 1)**
   - Before MCP tool calls, verify TypeDB (port 1729) and ChromaDB (port 8001) are responding
   - If unhealthy, return structured error with dependency status

2. **Session Start Health Check (RULE-021 Level 2)**
   - At MCP server initialization, run full dependency audit
   - Log health status to session evidence

3. **Recovery Protocol (RULE-021 Level 3)**
   - On dependency failure:
     - Attempt 1: Wait 5s, retry connection
     - Attempt 2: Restart dependent service via Docker CLI
     - Attempt 3: Return actionable error to Claude Code
   - Claude Code should interpret error and:
     - Run `docker compose up -d <service>` for failed dependencies
     - Wait for health check to pass
     - Retry original operation

4. **Implementation Path:**
   ```python
   # governance/mcp_tools/healthcheck.py
   @tool
   def governance_health_check() -> dict:
       """Check all governance dependencies."""
       status = {
           "typedb": check_typedb_health(),
           "chromadb": check_chromadb_health(),
           "overall": "healthy" | "degraded" | "unhealthy"
       }
       if status["overall"] == "unhealthy":
           return {
               "error": "DEPENDENCY_FAILURE",
               "action_required": "START_SERVICES",
               "services": [s for s, v in status.items() if v == "unhealthy"]
           }
       return status
   ```

5. **Claude Code Integration (via CLAUDE.md or MCP response):**
   - When MCP returns `action_required: START_SERVICES`, Claude Code should:
     - Stop current operation
     - Run `docker compose up -d <services>`
     - Re-run health check
     - Resume original operation

**Related Tasks:**
- RD-MCP-WRAPPER: Docker Wrapper pattern (R&D-BACKLOG)
- GAP-INFRA-004: Infrastructure health dashboard

**GAP-INFRA-002 Clarification:**
| Mode | Container | Port | Volumes | Use Case |
|------|-----------|------|---------|----------|
| **dev** | governance-dashboard-dev | 8081 | Mapped to local `agent/` | Live code editing |
| **prod** | governance-dashboard | 8081 | Baked into image | Production/CI |
| **Conflict:** Both use port 8081 - mutually exclusive

### Dashboard Logging Gaps (2024-12-31)

| ID | Status | Gap | Priority | Category | Evidence |
|----|--------|-----|----------|----------|----------|
| GAP-LOG-001 | OPEN | Unclear Trame dashboard UI logs - tokenization messages not documented | LOW | observability | User 2024-12-31 |

**GAP-LOG-001 Evidence:**
```
INFO (prefix=None) token length         namespace.py:130
INFO has(length => length) = False      state.py:188
INFO (prefix=None) token ===            namespace.py:130
INFO => backlog_agent_id && claimed_tasks.length === 0  namespace.py:138
INFO after: v-if = backlog_agent_id && claimed_tasks.length === 0  core.py:614
```
- These are **Trame internal DEBUG logs** from the Vue.js variable binding system
- `namespace.py` - Variable name resolution and tokenization
- `state.py` - State variable lookup (`has()` checks if var is in Python state)
- `core.py` - Final Vue.js binding generation
- **Resolution path:** Set logging level to WARNING for `trame.internal` or document in DEPLOYMENT.md

### Context Awareness Gaps (2024-12-28)

> **Source:** User observation - agent forgetting technology decisions (Trame/Vuetify)

| ID | Status | Gap | Priority | Category | Evidence |
|----|--------|-----|----------|----------|----------|
| GAP-CTX-001 | RESOLVED | Agent unaware of technology decisions (Trame/Vuetify) during refactoring | CRITICAL | memory | 2026-01-02: CLAUDE.md "Technology Decisions" section |
| GAP-CTX-002 | OPEN | AMNESIA protocol not auto-loading DECISION-* context | HIGH | process | RULE-024 violation |
| GAP-CTX-003 | OPEN | Duplicate memory systems (claude-mem vs TypeDB) need consolidation | HIGH | architecture | User 2024-12-28 |

**GAP-CTX-003: claude-mem vs TypeDB Memory Decision Needed**
| Aspect | claude-mem (ChromaDB) | TypeDB Governance |
|--------|----------------------|-------------------|
| Purpose | Semantic search, conversation context | Structured governance entities |
| Data | Unstructured memories, embeddings | Rules, decisions, sessions, tasks |
| Search | Vector similarity | TypeQL inference |
| Scope | Cross-project knowledge | This workspace only |

**Options:**
1. **Keep both** - TypeDB for governance, claude-mem for cross-project semantic search
2. **TypeDB only** - Migrate memories to TypeDB `memory` entity, remove claude-mem
3. **Consolidate** - TypeDB stores metadata, ChromaDB stores embeddings (hybrid)

### File Modularization Gaps (2024-12-28)

> **Source:** DSP Audit - RULE-012 Semantic Code Structure violation
> **Rule:** Files >300 lines MUST be restructured during DSP night cycles

| ID | Status | Gap | Priority | Category | File | Lines | Evidence |
|----|--------|-----|----------|----------|------|-------|----------|
| GAP-FILE-001 | RESOLVED | governance_dashboard.py exceeds 300 line limit | CRITICAL | architecture | agent/governance_dashboard.py | 3404→1305 | 2024-12-28 |
| GAP-FILE-002 | RESOLVED | governance/api.py exceeds 300 line limit | CRITICAL | architecture | governance/api.py | 2357→198 | 2024-12-28 |
| GAP-FILE-003 | RESOLVED | governance/client.py exceeds 300 line limit | CRITICAL | architecture | governance/client.py | 1389→135 | 2024-12-28 |
| GAP-FILE-004 | RESOLVED | agent/governance_ui/state.py exceeds 300 line limit | CRITICAL | architecture | agent/governance_ui/state.py | 1547→34 | 2024-12-28 |
| GAP-FILE-005 | RESOLVED | agent/governance_dashboard.py controllers exceed inline limit | HIGH | architecture | agent/governance_dashboard.py | 1159→592 | 2024-12-28 |
| GAP-FILE-006 | RESOLVED | agent/governance_ui/data_access.py exceeds 300 line limit | CRITICAL | architecture | agent/governance_ui/data_access.py | 1170→85 | 2024-12-28 |
| GAP-FILE-007 | RESOLVED | governance/mcp_server.py exceeds 300 line limit | CRITICAL | architecture | governance/mcp_server.py | 897→120 | 2024-12-28 |
| GAP-FILE-008 | RESOLVED | governance/mcp_tools/evidence.py exceeds 300 line limit | HIGH | architecture | governance/mcp_tools/evidence.py | 870→42 | 2024-12-28 |
| GAP-FILE-009 | RESOLVED | governance/langgraph_workflow.py exceeds 300 line limit | MEDIUM | architecture | governance/langgraph_workflow.py | 851→136 | 2024-12-28 |
| GAP-FILE-010 | RESOLVED | governance/pydantic_tools.py exceeds 300 line limit | MEDIUM | architecture | governance/pydantic_tools.py | 807→175 | 2024-12-28 |
| GAP-FILE-011 | RESOLVED | agent/external_mcp_tools.py exceeds 300 line limit | MEDIUM | architecture | agent/external_mcp_tools.py | 791→115 | 2024-12-28 |
| GAP-FILE-012 | RESOLVED | governance/hybrid_router.py exceeds 300 line limit | MEDIUM | architecture | governance/hybrid_router.py | 742→99 | 2024-12-28 |

**Resolution GAP-FILE-002 (2024-12-28):**
- ✅ 8 route modules extracted to `governance/routes/`
- ✅ Pydantic models extracted to `governance/models.py`
- ✅ Shared state/helpers extracted to `governance/stores.py`
- ✅ Seed data extracted to `governance/seed_data.py`
- ✅ api.py refactored to use route modules (2357→198 lines, 92% reduction)
- ✅ All 35 API endpoints verified working

**Extracted Route Modules:**
| Module | Lines | Responsibility |
|--------|-------|----------------|
| routes/rules.py | ~200 | Rules + Decisions CRUD |
| routes/tasks.py | ~370 | Tasks CRUD + workflow (claim/complete) |
| routes/sessions.py | ~110 | Sessions CRUD |
| routes/agents.py | ~120 | Agents CRUD |
| routes/evidence.py | ~80 | Evidence endpoints |
| routes/files.py | ~70 | File content with security |
| routes/reports.py | ~220 | Executive reports (RULE-029) |
| routes/chat.py | ~230 | Agent chat (ORCH-006) |
| models.py | ~260 | 18 Pydantic models |
| stores.py | ~250 | Shared state + helpers |

**Final Structure:**
```
governance/
├── api.py (198 lines - COMPLIANT ✅)
├── models.py (Pydantic models)
├── stores.py (shared state)
├── seed_data.py (startup data)
├── routes/
│   ├── __init__.py
│   ├── rules.py
│   ├── tasks.py
│   ├── sessions.py
│   ├── agents.py
│   ├── evidence.py
│   ├── files.py
│   ├── reports.py
│   └── chat.py
```

**Resolution GAP-FILE-003 (2024-12-28):**
- ✅ Entity dataclasses extracted to `governance/typedb/entities.py`
- ✅ Base client (connection + query execution) extracted to `governance/typedb/base.py`
- ✅ 4 query modules extracted to `governance/typedb/queries/`
- ✅ client.py refactored using mixin pattern composition (1389→135 lines, 90% reduction)
- ✅ All 78 tests pass after refactoring

**Extracted TypeDB Modules:**
| Module | Lines | Responsibility |
|--------|-------|----------------|
| typedb/entities.py | ~90 | Rule, Task, Session, Agent, Decision, InferenceResult dataclasses |
| typedb/base.py | ~150 | Connection, health_check, query execution |
| typedb/queries/tasks.py | ~480 | Task CRUD operations |
| typedb/queries/sessions.py | ~200 | Session CRUD operations |
| typedb/queries/rules.py | ~540 | Rule queries, CRUD, inference, archive |
| typedb/queries/agents.py | ~100 | Agent CRUD operations |

**Final Structure:**
```
governance/
├── client.py (135 lines - COMPLIANT ✅)
├── typedb/
│   ├── __init__.py (package exports)
│   ├── entities.py (6 dataclasses)
│   ├── base.py (TypeDBBaseClient)
│   └── queries/
│       ├── __init__.py
│       ├── tasks.py (TaskQueries mixin)
│       ├── sessions.py (SessionQueries mixin)
│       ├── rules.py (RuleQueries mixin)
│       └── agents.py (AgentQueries mixin)
```

**Resolution GAP-FILE-001 (2024-12-28):**
- ✅ All 12 view modules extracted to `agent/governance_ui/views/`
- ✅ Monolith refactored to use extracted modules (3404→1305 lines, 62% reduction)
- ✅ 36/36 tests pass after refactoring
- ✅ Each view module follows Page Object Model with data-testid attributes

**Extracted View Modules (Total: ~2,800 lines):**
| Module | Lines | Responsibility |
|--------|-------|----------------|
| rules_view.py | 267 | Rule list + detail + CRUD |
| tasks_view.py | 433 | Task list + detail + CRUD |
| sessions_view.py | 190 | Session timeline + evidence |
| decisions_view.py | 190 | Strategic decisions |
| executive_view.py | 214 | Executive reports (RULE-029) |
| agents_view.py | 77 | Agent registry |
| backlog_view.py | 171 | Agent task backlog (TODO-6) |
| search_view.py | 42 | Evidence semantic search |
| chat_view.py | 227 | Agent chat (ORCH-006) |
| trust_view.py | 370 | Trust dashboard (RULE-011) |
| monitor_view.py | 277 | Real-time monitoring (P9.6) |
| impact_view.py | 332 | Rule impact analyzer (P9.4) |

**Final Structure:**
```
agent/
├── governance_dashboard.py (1305 lines - COMPLIANT ✅)
├── governance_ui/
│   ├── __init__.py
│   ├── views/              # 12 modules, ~2800 lines
│   │   ├── __init__.py (40 lines)
│   │   └── *_view.py (12 files)
│   ├── components/
│   │   └── navigation.py
│   ├── data_access.py
│   ├── state.py (34 lines - COMPLIANT ✅)
│   └── state/              # 11 modules, ~1500 lines
│       ├── __init__.py
│       └── *.py (11 files)
```

**Resolution GAP-FILE-004 (2024-12-28):**
- ✅ Constants extracted to `agent/governance_ui/state/constants.py`
- ✅ Initial state factory extracted to `agent/governance_ui/state/initial.py`
- ✅ Core transforms extracted to `agent/governance_ui/state/core.py`
- ✅ Feature-specific state modules extracted (trust, monitor, journey, backlog, executive, chat, file_viewer, execution)
- ✅ state.py refactored to re-export package (1547→34 lines, 98% reduction)
- ✅ All 36 governance UI tests pass after refactoring

**Extracted State Modules (Total: ~1,500 lines):**
| Module | Lines | Responsibility |
|--------|-------|----------------|
| constants.py | ~180 | Color mappings, icons, navigation items |
| initial.py | ~130 | get_initial_state() factory |
| core.py | ~165 | Core transforms (with_loading, with_error, etc.) |
| trust.py | ~115 | Trust dashboard state (P9.5) |
| monitor.py | ~115 | Real-time monitoring state (P9.6) |
| journey.py | ~155 | Journey pattern analyzer state (P9.7) |
| backlog.py | ~115 | Agent task backlog state (TODO-6) |
| executive.py | ~145 | Executive reports state (GAP-UI-044) |
| chat.py | ~215 | Agent chat state (ORCH-006) |
| file_viewer.py | ~75 | File viewer state (GAP-DATA-003) |
| execution.py | ~80 | Task execution state (ORCH-007) |

**Final Structure:**
```
agent/governance_ui/
├── state.py (34 lines - COMPLIANT ✅)
├── state/
│   ├── __init__.py (re-exports all)
│   ├── constants.py
│   ├── initial.py
│   ├── core.py
│   ├── trust.py
│   ├── monitor.py
│   ├── journey.py
│   ├── backlog.py
│   ├── executive.py
│   ├── chat.py
│   ├── file_viewer.py
│   └── execution.py
```

**Resolution GAP-FILE-005 (2024-12-28):**
- ✅ Created `agent/governance_ui/controllers/` package
- ✅ 10 controller modules extracted from inline build_ui() function
- ✅ `register_all_controllers()` provides single entry point
- ✅ governance_dashboard.py reduced from 1159→592 lines (49% reduction)
- ✅ All 36 governance UI tests pass after refactoring

**Extracted Controller Modules (Total: ~700 lines):**
| Module | Lines | Responsibility |
|--------|-------|----------------|
| rules.py | ~150 | Rule CRUD + filter/sort controllers |
| tasks.py | ~150 | Task CRUD + create_task controllers |
| sessions.py | ~40 | Session detail controllers |
| decisions.py | ~40 | Decision detail controllers |
| data_loaders.py | ~200 | Data loading/refresh (returns loaders dict) |
| impact.py | ~35 | Impact analysis controllers |
| trust.py | ~40 | Trust dashboard controllers (P9.5) |
| monitor.py | ~50 | Monitoring controllers (P9.6) |
| backlog.py | ~80 | Agent task backlog controllers (TODO-6) |
| chat.py | ~150 | Agent chat controllers (ORCH-006) |

**Final Structure:**
```
agent/governance_ui/
├── controllers/
│   ├── __init__.py (register_all_controllers)
│   ├── rules.py
│   ├── tasks.py
│   ├── sessions.py
│   ├── decisions.py
│   ├── data_loaders.py
│   ├── impact.py
│   ├── trust.py
│   ├── monitor.py
│   ├── backlog.py
│   └── chat.py
├── views/         # 12 modules (GAP-FILE-001)
├── state/         # 11 modules (GAP-FILE-004)
└── state.py (34 lines - COMPLIANT ✅)
```

**Resolution GAP-FILE-006 (2024-12-28):**
- ✅ Created `agent/governance_ui/data_access/` package
- ✅ 8 modules extracted by functional domain
- ✅ data_access.py refactored to re-export package (1170→85 lines, 93% reduction)
- ✅ All 68 governance UI tests pass after refactoring

**Extracted Data Access Modules (Total: ~1,100 lines):**
| Module | Lines | Responsibility |
|--------|-------|----------------|
| core.py | ~160 | MCP registry, core data access (rules, decisions, sessions, tasks) |
| backlog.py | ~110 | Agent task backlog (TODO-6) |
| filters.py | ~50 | Filter & transform pure functions |
| impact.py | ~260 | Rule impact analysis (P9.4) |
| trust.py | ~300 | Agent trust dashboard (P9.5, RULE-011) |
| monitoring.py | ~120 | Real-time monitoring (P9.6) |
| journey.py | ~110 | Journey pattern analyzer (P9.7) |
| executive.py | ~60 | Executive reports (GAP-UI-044) |

**Final Structure:**
```
agent/governance_ui/
├── data_access.py (85 lines - COMPLIANT ✅)
├── data_access/
│   ├── __init__.py (re-exports all)
│   ├── core.py
│   ├── backlog.py
│   ├── filters.py
│   ├── impact.py
│   ├── trust.py
│   ├── monitoring.py
│   ├── journey.py
│   └── executive.py
├── controllers/      # 10 modules (GAP-FILE-005)
├── views/            # 12 modules (GAP-FILE-001)
└── state/            # 11 modules (GAP-FILE-004)
```

**Resolution GAP-FILE-007 (2024-12-28):**
- ✅ Created `governance/compat/` package for backward compatibility exports
- ✅ 7 modules extracted by functional domain
- ✅ mcp_server.py refactored to import from compat package (897→120 lines, 87% reduction)
- ✅ All 50 MCP tests pass after refactoring

**Extracted Compat Modules (Total: ~1,000 lines):**
| Module | Lines | Responsibility |
|--------|-------|----------------|
| core.py | ~225 | Core query functions (rules, sessions, decisions, tasks, evidence) |
| dsm.py | ~135 | DSM tracker exports (RULE-012) |
| sessions.py | ~115 | Session collector exports |
| quality.py | ~50 | Rule quality analyzer exports |
| tasks.py | ~90 | Task CRUD exports (P10.4) |
| agents.py | ~85 | Agent CRUD exports (P10.4) |
| documents.py | ~130 | Document viewing exports (P10.8) |

**Final Structure:**
```
governance/
├── mcp_server.py (120 lines - COMPLIANT ✅)
├── compat/
│   ├── __init__.py (re-exports all)
│   ├── core.py
│   ├── dsm.py
│   ├── sessions.py
│   ├── quality.py
│   ├── tasks.py
│   ├── agents.py
│   └── documents.py
├── mcp_tools/         # MCP tool implementations
├── typedb/            # TypeDB modules (GAP-FILE-003)
└── routes/            # API routes (GAP-FILE-002)
```

**Resolution GAP-FILE-008 (2024-12-28):**
- ✅ Created `governance/mcp_tools/evidence/` package for modular MCP tools
- ✅ 6 domain modules extracted from monolithic evidence.py
- ✅ evidence.py refactored to import from package (870→42 lines, 95% reduction)
- ✅ All 84 MCP tests pass after refactoring

**Extracted Evidence Modules (Total: ~700 lines):**
| Module | Lines | Responsibility |
|--------|-------|----------------|
| common.py | ~25 | Shared constants (EVIDENCE_DIR, DOCS_DIR, etc.) |
| sessions.py | ~130 | governance_list_sessions, governance_get_session |
| decisions.py | ~130 | governance_list_decisions, governance_get_decision |
| tasks.py | ~175 | governance_list_tasks, governance_get_task_deps |
| search.py | ~100 | governance_evidence_search |
| quality.py | ~85 | governance_analyze_rules, governance_rule_impact, governance_find_issues |
| documents.py | ~275 | governance_get_document, governance_list_documents, governance_get_rule_document, governance_get_task_document |

**Final Structure:**
```
governance/mcp_tools/
├── evidence.py (42 lines - COMPLIANT ✅)
├── evidence/
│   ├── __init__.py (re-exports all + register_evidence_tools)
│   ├── common.py
│   ├── sessions.py
│   ├── decisions.py
│   ├── tasks.py
│   ├── search.py
│   ├── quality.py
│   └── documents.py
├── agents.py          # Agent MCP tools (P10.4)
├── tasks.py           # Task MCP tools (P10.4)
└── common.py          # Shared utilities
```

**Resolution GAP-FILE-009 (2024-12-28):**
- ✅ Created `governance/langgraph/` package for LangGraph workflow
- ✅ 5 modules extracted by functional domain
- ✅ langgraph_workflow.py refactored to re-export package (851→136 lines, 84% reduction)
- ✅ All 43 langgraph tests pass after refactoring

**Extracted LangGraph Modules (Total: ~700 lines):**
| Module | Lines | Responsibility |
|--------|-------|----------------|
| state.py | ~95 | Vote, ProposalState TypedDicts, voting constants |
| nodes.py | ~330 | 8 workflow node functions |
| edges.py | ~35 | 3 router functions |
| graph.py | ~260 | Graph construction + execution |
| mcp_wrapper.py | ~60 | proposal_submit_mcp MCP tool |

**Final Structure:**
```
governance/
├── langgraph_workflow.py (136 lines - COMPLIANT ✅)
├── langgraph/
│   ├── __init__.py (re-exports all)
│   ├── state.py
│   ├── nodes.py
│   ├── edges.py
│   ├── graph.py
│   └── mcp_wrapper.py
```

**Resolution GAP-FILE-010 (2024-12-28):**
- ✅ Created `governance/pydantic/` package for type-safe tools
- ✅ 8 modules extracted by functional domain
- ✅ pydantic_tools.py refactored to re-export package (807→175 lines, 78% reduction)
- ✅ All 130 pydantic/MCP tests pass after refactoring

**Extracted Pydantic Modules (Total: ~550 lines):**
| Module | Lines | Responsibility |
|--------|-------|----------------|
| models/inputs.py | ~140 | 6 input configuration models |
| models/outputs.py | ~120 | 7 output result models |
| tools/rules.py | ~100 | query_rules_typed, analyze_dependencies_typed |
| tools/agents.py | ~90 | calculate_trust_score_typed |
| tools/proposals.py | ~40 | create_proposal_typed |
| tools/analysis.py | ~100 | analyze_impact_typed, health_check_typed |
| mcp.py | ~70 | MCP tool wrappers with JSON serialization |

**Final Structure:**
```
governance/
├── pydantic_tools.py (175 lines - COMPLIANT ✅)
├── pydantic/
│   ├── __init__.py (re-exports all)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── inputs.py
│   │   └── outputs.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── rules.py
│   │   ├── agents.py
│   │   ├── proposals.py
│   │   └── analysis.py
│   └── mcp.py
```

**Resolution GAP-FILE-011 (2024-12-28):**
- ✅ Created `agent/external_mcp/` package for external MCP tool wrappers
- ✅ 6 modules extracted by tool category (per RULE-007 MCP Tool Matrix)
- ✅ external_mcp_tools.py refactored to re-export package (791→115 lines, 85% reduction)
- ✅ All 21 tools across 4 toolkits verified working

**Extracted External MCP Modules (Total: ~600 lines):**
| Module | Lines | Responsibility |
|--------|-------|----------------|
| common.py | ~35 | Agno stubs, tool decorator, Toolkit class |
| playwright.py | ~190 | PlaywrightConfig + PlaywrightTools (7 tools) |
| powershell.py | ~75 | PowerShellConfig + PowerShellTools (2 tools) |
| desktop_commander.py | ~190 | DesktopCommanderConfig + DesktopCommanderTools (7 tools) |
| octocode.py | ~200 | OctoCodeConfig + OctoCodeTools (5 tools) |
| combined.py | ~90 | ExternalMCPTools + factory functions |

**Final Structure:**
```
agent/
├── external_mcp_tools.py (115 lines - COMPLIANT ✅)
├── external_mcp/
│   ├── __init__.py (re-exports all)
│   ├── common.py
│   ├── playwright.py
│   ├── powershell.py
│   ├── desktop_commander.py
│   ├── octocode.py
│   └── combined.py
```

**Resolution GAP-FILE-012 (2024-12-28):**
- ✅ Created `governance/hybrid/` package for hybrid query routing
- ✅ 3 modules extracted by functional domain
- ✅ hybrid_router.py refactored to re-export package (742→99 lines, 87% reduction)
- ✅ All backward compatibility validated

**Extracted Hybrid Modules (Total: ~560 lines):**
| Module | Lines | Responsibility |
|--------|-------|----------------|
| models.py | ~55 | QueryType enum, QueryResult, SyncStatus dataclasses |
| router.py | ~370 | HybridQueryRouter with TypeDB/ChromaDB routing |
| sync.py | ~240 | MemorySyncBridge for TypeDB→ChromaDB sync |

**Final Structure:**
```
governance/
├── hybrid_router.py (99 lines - COMPLIANT ✅)
├── hybrid/
│   ├── __init__.py (re-exports all)
│   ├── models.py
│   ├── router.py
│   └── sync.py
```

### Agent Execution Gaps (2024-12-27)

> **Source:** Agent Task Backlog tab not functional - agents not picking up tasks

| ID | Status | Gap | Priority | Category | Entity | Evidence |
|----|--------|-----|----------|----------|--------|----------|
| GAP-AGENT-010 | RESOLVED | Agent Task Backlog tab shows tasks but agents don't execute | HIGH | functionality | Agent | OrchestratorEngine integrated into playground.py (2026-01-01) |
| GAP-AGENT-011 | RESOLVED | No agent polling/subscription for new tasks | HIGH | architecture | Agent | TypeDBTaskPoller + OrchestratorEngine polling loop (2026-01-01) |
| GAP-AGENT-012 | PARTIAL | No task claim/lock mechanism for multi-agent coordination | HIGH | architecture | Task | claim_task() implemented, atomic locking TBD |
| GAP-AGENT-013 | RESOLVED | No delegation protocol when agent needs more context | HIGH | architecture | Agent | DelegationProtocol in delegation.py (ORCH-004) |
| GAP-AGENT-014 | RESOLVED | Rules Curator agent not implemented | MEDIUM | functionality | Agent | RulesCuratorAgent in curator_agent.py (ORCH-005) |

**Stub Migration Strategy:**
1. **TypeDB Schema Update** (`governance/schema.tql`): Add `task`, `session`, `proposal` entities
2. **Data Loading** (`governance/data.tql`): Populate from workspace files via Document MCP
3. **API Refactor**: Replace in-memory dicts with TypeDB client queries
4. **Document MCP Integration**: Real-time file content for evidence attachments

---

## Resolved Gaps (Summary)

> **Note:** All gaps now use Status column in main tables above. This summary lists resolved gaps with dates.

| ID | Gap | Resolution | Date |
|----|-----|------------|------|
| GAP-WORKFLOW-003 | GAP-INDEX strikethrough → Status column | 2026-01-02: This migration | 2026-01-02 |
| GAP-MCP-003 | governance_health not called at session start | Non-blocking healthcheck with retry | 2026-01-01 |
| GAP-ARCH-001 | Tasks in-memory, not TypeDB | Hybrid: TypeDB + fallback | 2024-12-27 |
| GAP-ARCH-002 | Sessions in-memory, not TypeDB | Hybrid: TypeDB + fallback | 2024-12-27 |
| GAP-ARCH-003 | Agents in-memory, not TypeDB | Hybrid: TypeDB + fallback | 2024-12-27 |
| GAP-FILE-001-012 | 12 files exceeding 300 line limit | Modularized all (avg 85% reduction) | 2024-12-28 |
| GAP-UI-004 | No REST API endpoints | governance/api.py (23 endpoints) | 2024-12-26 |
| GAP-SEC-001 | No API authentication | AuthMiddleware + X-API-Key | 2024-12-27 |
| GAP-DOC-001-002 | No document viewing MCP | governance_get_document tools | 2024-12-27 |
| GAP-AGENT-010-014 | Agent orchestration gaps | OrchestratorEngine + delegation | 2026-01-01 |

---

## Gap Categories

| Category | Count | Priority |
|----------|-------|----------|
| **data/integrity** | 2 | CRITICAL |
| **architecture** | 5 | CRITICAL |
| **process** | 1 | CRITICAL |
| **UI (P10)** | 12 | HIGH |
| functionality | 4 | CRITICAL/HIGH |
| security | 1 | HIGH |
| workflow | 2 | HIGH |
| testing | 6 | MEDIUM/LOW |
| docs | 3 | Medium |
| organization | 1 | Medium |
| configuration | 2 | Medium |
| tooling | 4 | Medium/Low |
| performance | 1 | Low |

### UI Gap Breakdown by Type

| Type | Count | Examples |
|------|-------|----------|
| **testability** | 1 | GAP-UI-001 (data-testid) |
| **functionality** | 4 | GAP-UI-002, 009, 011 (CRUD, search) |
| **navigation** | 1 | GAP-UI-007 (clickable rows) |
| **data_binding** | 2 | GAP-UI-006, 008 (missing columns, empty data) |
| **backend** | 1 | GAP-UI-004 (REST API) |
| **ux** | 2 | GAP-UI-005, 010 (loading states, sorting) |

---

*Gap tracking per RULE-013: Rules Applicability Convention*
