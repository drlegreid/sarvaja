# Gap Index - Sim.ai PoC

**Last Updated:** 2024-12-31
**Total Gaps:** 119 (67 resolved, 52 open) — +2 (GAP-INFRA-006, GAP-MCP-004)

---

## Active Gaps

### UI Gaps (P10 Sprint) - Exploratory Session EXP-P10-001 (2024-12-25)

| ID | Gap | Priority | Category | Entity | Operation | Evidence |
|----|-----|----------|----------|--------|-----------|----------|
| GAP-UI-001 | No data-testid attributes on Trame components | HIGH | testability | All | N/A | POM requirement |
| GAP-UI-002 | No CRUD forms for Rules | HIGH | functionality | Rule | CREATE/UPDATE | ENTITY-API-UI-MAP |
| GAP-UI-003 | No detail drill-down views | HIGH | functionality | All | READ | ENTITY-API-UI-MAP |
| ~~GAP-UI-004~~ | ~~No REST API endpoints~~ | ~~HIGH~~ | ~~backend~~ | ~~All~~ | ~~ALL~~ | **RESOLVED** governance/api.py |
| GAP-UI-005 | Missing loading/error states | MEDIUM | ux | All | READ | Exploratory |
| GAP-UI-006 | Rules list missing rule_id column | HIGH | data_binding | Rule | READ | EXP-P10-001 |
| GAP-UI-007 | List rows not clickable (no detail navigation) | HIGH | navigation | All | READ | EXP-P10-001 |
| ~~GAP-UI-008~~ | ~~Tasks view shows empty table (no data source)~~ | ~~HIGH~~ | ~~data_binding~~ | ~~Task~~ | ~~READ~~ | **RESOLVED** API seed data added |
| GAP-UI-009 | Search returns no results (unclear if functional) | MEDIUM | functionality | Evidence | SEARCH | EXP-P10-001 |
| GAP-UI-010 | No column sorting functionality | MEDIUM | ux | All | READ | EXP-P10-001 |
| GAP-UI-011 | No filtering/faceted search | MEDIUM | functionality | All | SEARCH | EXP-P10-001 |
| GAP-UI-028 | Tests pass but UI broken (lenient tests) | CRITICAL | testing | All | ALL | **RESOLVED** RULE-028 + 11 UI smoke tests |
| ~~GAP-UI-029~~ | ~~Executive Report shows 0 Rules/Agents in stats~~ | ~~HIGH~~ | ~~data~~ | ~~Report~~ | ~~READ~~ | **RESOLVED** 2024-12-31: Field name mismatch fixed (rules_total→total_rules) |
| ~~GAP-UI-030~~ | ~~Tasks view polluted with 150+ TEST-* tasks~~ | ~~MEDIUM~~ | ~~data~~ | ~~Task~~ | ~~READ~~ | **RESOLVED** 2024-12-31: Deleted 154 TEST-* tasks from TypeDB |
| GAP-UI-EXP | No exploratory UI testing workflow to discover UI gaps | MEDIUM | process | All | N/A | E2E-2024-12-27 |
| ~~GAP-UI-031~~ | ~~Rule Save button is mock-only~~ | ~~CRITICAL~~ | ~~functionality~~ | ~~Rule~~ | ~~CREATE/UPDATE~~ | **RESOLVED** wired to API |
| ~~GAP-UI-032~~ | ~~Rule Delete button is mock-only~~ | ~~CRITICAL~~ | ~~functionality~~ | ~~Rule~~ | ~~DELETE~~ | **RESOLVED** wired to API |
| GAP-UI-033 | No CRUD operations for Decisions | HIGH | functionality | Decision | ALL | UI-COVERAGE-2024-12-25 |
| GAP-UI-034 | No CRUD operations for Sessions | HIGH | functionality | Session | ALL | UI-COVERAGE-2024-12-25 |
| GAP-UI-035 | No datetime columns in tables | MEDIUM | ux | All | READ | USER-2024-12-27 |
| GAP-UI-036 | No scrolling/paging in tables | MEDIUM | ux | All | READ | USER-2024-12-27 |
| GAP-UI-037 | No entity content preview (unclear data) | HIGH | ux | All | READ | USER-2024-12-27 |
| GAP-UI-038 | No document reference viewer (fullscreen modal) | HIGH | functionality | Document | READ | USER-2024-12-27 |
| GAP-UI-039 | No document format support (CSV, Markdown, etc.) | MEDIUM | functionality | Document | READ | USER-2024-12-27 → RD-DOCVIEW |
| GAP-UI-040 | Agent dashboard lacks effective config display (Agno framework) | HIGH | functionality | Agent | READ | USER-2024-12-27 |
| GAP-UI-041 | No agent-to-session/task relation UI links | HIGH | functionality | Agent | READ | USER-2024-12-27 |
| GAP-UI-042 | No trust score change explanation/history | HIGH | functionality | Agent | READ | USER-2024-12-27 |
| GAP-UI-043 | Agent dashboard lacks execution metrics | MEDIUM | functionality | Agent | READ | USER-2024-12-27 |
| ~~GAP-UI-044~~ | ~~No Executive Reporting view in Session Evidence tab~~ | ~~HIGH~~ | ~~functionality~~ | ~~Session~~ | ~~READ~~ | **RESOLVED** governance_dashboard.py + api.py |
| GAP-UI-045 | No cross-workspace metrics aggregation | MEDIUM | functionality | Session | READ | RULE-029 |
| GAP-UI-046 | Executive Report should be per-session not quarterly/monthly | HIGH | functionality | Session | READ | User 2024-12-28 |

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

| ID | Gap | Priority | Category | Rule | Evidence |
|----|-----|----------|----------|------|----------|
| GAP-004 | Grok/xAI API Key | Medium | configuration | RULE-002 | test skip |
| GAP-005 | Agent Task Backlog UI | Medium | functionality | RULE-002 | PARTIAL: Status filtering fixed (TODO+pending), polling not impl |
| GAP-006 | Sync Agent Implementation | Medium | functionality | RULE-003 | skeleton only |
| GAP-007 | ChromaDB v2 Test Update | Low | testing | RULE-009 | UUID error |
| ~~GAP-008~~ | ~~Agent UI Image~~ | ~~Low~~ | ~~configuration~~ | ~~RULE-009~~ | **RESOLVED** Service disabled in docker-compose |
| GAP-009 | Pre-commit Hooks | Medium | tooling | RULE-001 | RULES-DIRECTIVES.md |
| GAP-010 | CI/CD Pipeline | Low | tooling | RULE-009 | DEPLOYMENT.md |
| GAP-014 | IntelliJ Windsurf MCP not loading | Medium | tooling | RULE-005 | ~/.codeium/mcp_config.json |
| GAP-015 | Consolidated STRATEGY.md | Medium | docs | RULE-001 | docs/GAP-ANALYSIS-2024-12-24.md |
| ~~GAP-019~~ | ~~MCP usage documentation~~ | ~~Medium~~ | ~~docs~~ | ~~RULE-007~~ | **RESOLVED** docs/MCP-USAGE.md |
| ~~GAP-020~~ | ~~Cross-project knowledge queries~~ | ~~HIGH~~ | ~~workflow~~ | ~~RULE-007~~ | **RESOLVED** MCP-USAGE.md Section 8 |
| GAP-021 | OctoCode for external research | Medium | workflow | RULE-007 | Use OctoCode for GitHub |
| ~~GAP-DEPLOY-001~~ | ~~deploy.ps1 missing dev profile support~~ | ~~MEDIUM~~ | ~~tooling~~ | ~~RULE-028~~ | **RESOLVED** 2024-12-31: Added 'dev' to ValidateSet, updated docs/endpoints |
| ~~GAP-MCP-002~~ | ~~MCP governance healthcheck should force Claude Code to stop and resolve dependent services~~ | ~~HIGH~~ | ~~stability~~ | ~~RULE-021~~ | **PARTIAL** 2024-12-31: Tool implemented but not auto-called (see GAP-MCP-003) |
| GAP-MCP-003 | governance_health not called automatically at session start | CRITICAL | workflow | RULE-021 | 2024-12-31: User restarted laptop, Claude Code continued without checking services |
| GAP-WORKFLOW-001 | Session context not auto-saved to claude-mem before restart | HIGH | workflow | RULE-001 | 2024-12-31: /save not called, context lost on restart |
| GAP-WORKFLOW-002 | Claude Code should prompt user to /save before major transitions | HIGH | workflow | RULE-001 | 2024-12-31: Autonomous work should include save prompts |
| GAP-INFRA-005 | Ollama container not started with dev profile | MEDIUM | infra | RULE-021 | 2024-12-31: docker compose --profile dev doesn't include ollama |
| GAP-INFRA-006 | Ollama container suboptimal for laptop dev workflow - high memory usage | MEDIUM | infrastructure | RULE-021 | 2024-12-31: May need to disable for DEV, use Claude API for strategic work |
| GAP-MCP-004 | Rule fallback to markdown files not implemented when TypeDB unavailable | HIGH | architecture | RULE-021 | 2024-12-31: CLAUDE.md documents hierarchy but code doesn't read from docs/rules/*.md |

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

| ID | Gap | Priority | Category | Rule | Evidence |
|----|-----|----------|----------|------|----------|
| ~~GAP-ARCH-001~~ | ~~Tasks in-memory, not TypeDB~~ | ~~CRITICAL~~ | ~~architecture~~ | ~~DECISION-003~~ | **RESOLVED** Hybrid TypeDB+fallback |
| ~~GAP-ARCH-002~~ | ~~Sessions in-memory, not TypeDB~~ | ~~CRITICAL~~ | ~~architecture~~ | ~~DECISION-003~~ | **RESOLVED** Hybrid TypeDB+fallback |
| ~~GAP-ARCH-003~~ | ~~Agents in-memory, not TypeDB~~ | ~~HIGH~~ | ~~architecture~~ | ~~DECISION-003~~ | **RESOLVED** P10.3: TypeDB-first seeding (seed_data.py 2024-12-28) |
| ~~GAP-ARCH-004~~ | ~~TypeDB missing RULE-012 to RULE-025~~ | ~~CRITICAL~~ | ~~data~~ | ~~RULE-012~~ | **RESOLVED** 25 rules loaded |
| ~~GAP-ARCH-005~~ | ~~No MCP tools for Tasks/Sessions~~ | ~~HIGH~~ | ~~functionality~~ | ~~RULE-007~~ | **RESOLVED** mcp_tools/tasks.py + agents.py |
| ~~GAP-ARCH-007~~ | ~~Entity hierarchy review: Decision as Task subtype~~ | ~~MEDIUM~~ | ~~architecture~~ | ~~DECISION-003~~ | **RESOLVED** P10.7-ENTITY-HIERARCHY-REVIEW.md: Keep separate |
| ~~GAP-ARCH-006~~ | ~~Session/Task MCP exports missing~~ | ~~HIGH~~ | ~~testing~~ | ~~RULE-023~~ | **RESOLVED** exports added |
| ~~GAP-ARCH-008~~ | ~~TypeDB-Filesystem Rule Linking~~ | ~~MEDIUM~~ | ~~architecture~~ | ~~DECISION-003~~ | **RESOLVED** P10.8: rule_linker.py + 4 MCP tools (3 docs, 36 rule refs) |
| GAP-ARCH-009 | TypeDB sessions created but not retrievable for end operation | MEDIUM | architecture | DECISION-003 | E2E test: test_end_session_via_api fails 404 |
| ~~GAP-ARCH-010~~ | ~~Workspace tasks not captured in TypeDB~~ | ~~HIGH~~ | ~~architecture~~ | ~~DECISION-003~~ | **RESOLVED** P10.10: workspace_scanner.py + 3 MCP tools (89 tasks) |

### TDD Stub Gaps (DSP-2024-12-26 Cycles 201-330)

| ID | Gap | Priority | Category | Rule | Evidence |
|----|-----|----------|----------|------|----------|
| ~~GAP-TDD-001~~ | ~~Task response missing 'phase' field~~ | ~~MEDIUM~~ | ~~testing~~ | ~~RULE-025~~ | **RESOLVED** mcp_server.py:169 |
| ~~GAP-TDD-002~~ | ~~Evidence search missing 'query'/'score'~~ | ~~MEDIUM~~ | ~~testing~~ | ~~RULE-025~~ | **RESOLVED** mcp_server.py:223 |
| GAP-TDD-003 | DSM advance missing 'required_mcps' | LOW | testing | RULE-012 | test_dsm_tracker_integration.py |
| GAP-TDD-006 | Tests write TEST-* data to production TypeDB | MEDIUM | testing | RULE-023 | Caused GAP-UI-030, need isolation |
| GAP-TDD-004 | DSM checkpoint missing 'timestamp' | LOW | testing | RULE-012 | test_dsm_tracker_integration.py |
| GAP-TDD-005 | DSM finding missing 'related_rules' | LOW | testing | RULE-012 | test_dsm_tracker_integration.py |

### DSP Gap Discovery (Cycles 331-380)

| ID | Gap | Priority | Category | Rule | Evidence |
|----|-----|----------|----------|------|----------|
| ~~GAP-DSP-001~~ | ~~MCP tools not registered~~ | ~~CRITICAL~~ | ~~functionality~~ | ~~RULE-007~~ | **FALSE POSITIVE** 40 tools registered |
| GAP-DSP-002 | 9 schema entities without data | HIGH | data | DECISION-003 | schema.tql vs data.tql |
| GAP-DSP-003 | API documentation at 25% | MEDIUM | docs | RULE-001 | api.py 5/20 docstrings |
| ~~GAP-SEC-001~~ | ~~No API authentication middleware~~ | ~~HIGH~~ | ~~security~~ | ~~RULE-011~~ | **RESOLVED** AuthMiddleware + X-API-Key header |
| GAP-PERF-001 | Sync I/O in async code | LOW | performance | RULE-009 | api.py:469,494 |

### Data Integrity Gaps (2024-12-26 Data Audit)

| ID | Gap | Priority | Category | Rule | Evidence |
|----|-----|----------|----------|------|----------|
| GAP-DATA-001 | Tasks have no descriptions/content/linkage | CRITICAL | data | DECISION-003 | P11.2: Structure added, P11.2b: Content recovery pending |
| ~~GAP-DATA-002~~ | ~~No entity relationships (Task→Rule, Session→Evidence)~~ | ~~CRITICAL~~ | ~~architecture~~ | ~~DECISION-003~~ | **RESOLVED** P11.3: TypeDB schema + 5 sessions + 5 evidence + relationships |
| ~~GAP-DATA-003~~ | ~~Session evidence attachments not loadable~~ | ~~HIGH~~ | ~~functionality~~ | ~~RULE-001~~ | **RESOLVED** P11.5: API + UI + TypeDB linkage |
| ~~GAP-ARCH-011~~ | ~~TypeDB migration incomplete (claude-mem disconnected)~~ | ~~CRITICAL~~ | ~~architecture~~ | ~~DECISION-003~~ | **RESOLVED** P11.4: session_memory.py + DSM integration |
| ~~GAP-PROC-001~~ | ~~Memory/context loss - no wisdom accumulation~~ | ~~CRITICAL~~ | ~~process~~ | ~~RULE-012~~ | **RESOLVED** P11.4: SessionContext + AMNESIA recovery |
| ~~GAP-ORG-001~~ | ~~Files misplaced (png/xml/html in wrong directories)~~ | ~~MEDIUM~~ | ~~organization~~ | ~~RULE-001~~ | **RESOLVED** P11.6: 24 files reorganized |
| ~~GAP-UI-035~~ | ~~UI views don't auto-load data on open~~ | ~~HIGH~~ | ~~ux~~ | ~~RULE-019~~ | **RESOLVED** Added state change handler |

### P11.8 Entity Audit Gaps (2024-12-26)

> **Source:** [DATA-AUDIT-REPORT-2024-12-26.md](DATA-AUDIT-REPORT-2024-12-26.md)

| ID | Gap | Priority | Category | Entity | Field | Evidence |
|----|-----|----------|----------|--------|-------|----------|
| GAP-TASK-001 | Tasks linked_sessions only 10% coverage | MEDIUM | data | Task | linked_sessions | P11.8 Audit |
| GAP-TASK-002 | Tasks agent_id always null | LOW | data | Task | agent_id | P11.8 Audit |
| GAP-TASK-003 | Tasks completed_at not populated | LOW | data | Task | completed_at | P11.8 Audit |
| ~~GAP-AGENT-001~~ | ~~Agent trust_score hardcoded, not calculated~~ | ~~HIGH~~ | ~~data~~ | ~~Agent~~ | ~~trust_score~~ | **RESOLVED** P11.9: Dynamic calculation |
| ~~GAP-AGENT-002~~ | ~~Agent tasks_executed always 0, resets on restart~~ | ~~HIGH~~ | ~~data~~ | ~~Agent~~ | ~~tasks_executed~~ | **RESOLVED** P11.9: Persistent metrics |
| ~~GAP-AGENT-003~~ | ~~Agent last_active never populated~~ | ~~MEDIUM~~ | ~~data~~ | ~~Agent~~ | ~~last_active~~ | **RESOLVED** P11.9: Updated on task |
| GAP-AGENT-004 | Agent capabilities field missing | MEDIUM | schema | Agent | capabilities | P11.8 Audit |
| ~~GAP-EVIDENCE-001~~ | ~~Evidence session_id never populated (no linkage)~~ | ~~HIGH~~ | ~~data~~ | ~~Evidence~~ | ~~session_id~~ | **RESOLVED** P11.10: 8/9 linked |
| GAP-EVIDENCE-002 | Evidence only reads .md files | LOW | functionality | Evidence | file_types | P11.8 Audit |
| GAP-DECISION-001 | Decision linked_rules not exposed in API | MEDIUM | api | Decision | linked_rules | P11.8 Audit |

### Mock/Stub Technical Debt (P10.1-P10.3) - TO BE REMOVED

> **Per User Directive:** All mocked/stubbed data MUST be replaced with realtime TypeDB + Document MCP queries

| ID | Stub Location | Task | Priority | Target Data Source |
|----|---------------|------|----------|-------------------|
| GAP-STUB-001 | `governance/api.py:401` `_tasks_store: Dict` | P10.1 | CRITICAL | TypeDB `task` entity |
| GAP-STUB-002 | `governance/api.py:151-293` `seed_tasks` | P10.1 | CRITICAL | TypeDB + workspace TODO.md |
| GAP-STUB-003 | `governance/api.py:470` `_sessions_store: Dict` | P10.2 | CRITICAL | TypeDB `session` entity |
| GAP-STUB-004 | `governance/api.py:302-375` `seed_sessions` | P10.2 | CRITICAL | TypeDB + session evidence files |
| GAP-STUB-005 | `governance/api.py:558-604` `_agents_store: Dict` | P10.3 | HIGH | TypeDB `agent` entity |
| GAP-STUB-006 | `agent/governance_ui/data_access.py:42` `get_proposals()` | P10.7 | MEDIUM | TypeDB `proposal` entity |
| GAP-STUB-007 | `agent/governance_ui/data_access.py:48` `get_escalated_proposals()` | P10.7 | MEDIUM | TypeDB `proposal` with escalation |

### User Feedback Gaps (2024-12-26 Session)

> **Source:** User feedback during TODO-6 development

| ID | Gap | Priority | Category | Entity | Evidence |
|----|-----|----------|----------|--------|----------|
| GAP-UI-040 | Rules tab: No directive/description shown | HIGH | ui | Rule | User feedback |
| GAP-UI-041 | No entity relationships displayed in UI | HIGH | ui | All | User feedback |
| GAP-UI-042 | Tasks: No description, no linkage to sessions/evidence/rules | HIGH | ui | Task | User feedback |
| GAP-UI-043 | Session evidence tab has no data | HIGH | functionality | Session | User feedback |
| GAP-UI-044 | Real-time rule monitoring tab not functional | HIGH | functionality | Monitor | User feedback |

### Document MCP Gaps (2024-12-27 Assessment)

> **Source:** Platform usability assessment - user cannot view documents in evidence/task/rule links

| ID | Gap | Priority | Category | Entity | Evidence |
|----|-----|----------|----------|--------|----------|
| ~~GAP-DOC-001~~ | ~~No Document viewing MCP for rule markdown files~~ | ~~CRITICAL~~ | ~~functionality~~ | ~~Rule~~ | **RESOLVED** governance_get_rule_document, governance_get_document |
| ~~GAP-DOC-002~~ | ~~No Document viewing MCP for evidence files~~ | ~~CRITICAL~~ | ~~functionality~~ | ~~Evidence~~ | **RESOLVED** governance_get_document, governance_list_documents |
| GAP-DOC-003 | No TypeDB→Document sync architecture | HIGH | architecture | All | R&D-BACKLOG DOC-001 |
| GAP-DOC-004 | No Document version tracking in TypeDB | MEDIUM | architecture | All | R&D-BACKLOG DOC-004 |

### Platform UI Gaps (2024-12-27 Assessment)

> **Source:** Platform usability assessment - agent platform not ready for production use
> **Related:** RULE-011 (Multi-Agent Governance), RULE-014 (Autonomous Task Sequencing)
> **Design Doc:** [DESIGN-Governance-MCP.md](../DESIGN-Governance-MCP.md)

| ID | Gap | Priority | Category | Entity | Evidence |
|----|-----|----------|----------|--------|----------|
| GAP-UI-CHAT-001 | Platform UI has no prompt/chat functionality for commanding agents | **CRITICAL** | functionality | Agent | User feedback 2024-12-27 |
| GAP-UI-CHAT-002 | No agent interaction UI (send tasks, receive responses, view execution) | **CRITICAL** | functionality | Agent | Platform requirement |

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

| ID | Gap | Priority | Category | Evidence |
|----|-----|----------|----------|----------|
| GAP-RD-001 | Kanren integration benefit assessment: Has KAN-001/KAN-002 improved workflow stability? | MEDIUM | assessment | RD-KANREN-CONTEXT.md: 39 tests pass, but real-world usage not measured |

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

| ID | Gap | Priority | Category | Evidence |
|----|-----|----------|----------|----------|
| ~~GAP-INFRA-001~~ | ~~Docker health checks misconfigured~~ | ~~HIGH~~ | ~~infrastructure~~ | **RESOLVED** 2024-12-31: ChromaDB v1→v2, LiteLLM /health→/health/liveliness |
| ~~GAP-INFRA-002~~ | ~~Dev vs Prod dashboard workflow undocumented~~ | ~~HIGH~~ | ~~documentation~~ | **RESOLVED** 2024-12-31: DEPLOYMENT.md "Development vs Production Mode" section |
| ~~GAP-INFRA-003~~ | ~~deploy.ps1 missing dev profile support~~ | ~~MEDIUM~~ | ~~tooling~~ | **RESOLVED** 2024-12-31: Added 'dev' to ValidateSet, updated docs/endpoints |
| GAP-INFRA-004 | No Docker infrastructure health dashboard or startup validation | HIGH | observability | User 2024-12-31: "rules system damaged, blocks cognition of infrastructure" |
| GAP-INFRA-006 | Ollama container suboptimal for laptop dev workflow - high memory usage | MEDIUM | infrastructure | User 2024-12-31: May need to disable for DEV, use Claude API for strategic work |

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

| ID | Gap | Priority | Category | Evidence |
|----|-----|----------|----------|----------|
| GAP-LOG-001 | Unclear Trame dashboard UI logs - tokenization messages not documented | LOW | observability | User 2024-12-31 |

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

| ID | Gap | Priority | Category | Evidence |
|----|-----|----------|----------|----------|
| GAP-CTX-001 | Agent unaware of technology decisions (Trame/Vuetify) during refactoring | **CRITICAL** | memory | User 2024-12-28 |
| GAP-CTX-002 | AMNESIA protocol not auto-loading DECISION-* context | HIGH | process | RULE-024 violation |
| GAP-CTX-003 | Duplicate memory systems (claude-mem vs TypeDB) need consolidation | HIGH | architecture | User 2024-12-28 |

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

| ID | Gap | Priority | Category | File | Lines | Evidence |
|----|-----|----------|----------|------|-------|----------|
| ~~GAP-FILE-001~~ | ~~governance_dashboard.py exceeds 300 line limit~~ | ~~CRITICAL~~ | ~~architecture~~ | ~~agent/governance_dashboard.py~~ | ~~3404→1305~~ | **RESOLVED** 2024-12-28 |
| ~~GAP-FILE-002~~ | ~~governance/api.py exceeds 300 line limit~~ | ~~CRITICAL~~ | ~~architecture~~ | ~~governance/api.py~~ | ~~2357→198~~ | **RESOLVED** 2024-12-28 |
| ~~GAP-FILE-003~~ | ~~governance/client.py exceeds 300 line limit~~ | ~~CRITICAL~~ | ~~architecture~~ | ~~governance/client.py~~ | ~~1389→135~~ | **RESOLVED** 2024-12-28 |
| ~~GAP-FILE-004~~ | ~~agent/governance_ui/state.py exceeds 300 line limit~~ | ~~CRITICAL~~ | ~~architecture~~ | ~~agent/governance_ui/state.py~~ | ~~1547→34~~ | **RESOLVED** 2024-12-28 |
| ~~GAP-FILE-005~~ | ~~agent/governance_dashboard.py controllers exceed inline limit~~ | ~~HIGH~~ | ~~architecture~~ | ~~agent/governance_dashboard.py~~ | ~~1159→592~~ | **RESOLVED** 2024-12-28 |
| ~~GAP-FILE-006~~ | ~~agent/governance_ui/data_access.py exceeds 300 line limit~~ | ~~CRITICAL~~ | ~~architecture~~ | ~~agent/governance_ui/data_access.py~~ | ~~1170→85~~ | **RESOLVED** 2024-12-28 |
| ~~GAP-FILE-007~~ | ~~governance/mcp_server.py exceeds 300 line limit~~ | ~~CRITICAL~~ | ~~architecture~~ | ~~governance/mcp_server.py~~ | ~~897→120~~ | **RESOLVED** 2024-12-28 |
| ~~GAP-FILE-008~~ | ~~governance/mcp_tools/evidence.py exceeds 300 line limit~~ | ~~HIGH~~ | ~~architecture~~ | ~~governance/mcp_tools/evidence.py~~ | ~~870→42~~ | **RESOLVED** 2024-12-28 |
| ~~GAP-FILE-009~~ | ~~governance/langgraph_workflow.py exceeds 300 line limit~~ | ~~MEDIUM~~ | ~~architecture~~ | ~~governance/langgraph_workflow.py~~ | ~~851→136~~ | **RESOLVED** 2024-12-28 |
| ~~GAP-FILE-010~~ | ~~governance/pydantic_tools.py exceeds 300 line limit~~ | ~~MEDIUM~~ | ~~architecture~~ | ~~governance/pydantic_tools.py~~ | ~~807→175~~ | **RESOLVED** 2024-12-28 |
| ~~GAP-FILE-011~~ | ~~agent/external_mcp_tools.py exceeds 300 line limit~~ | ~~MEDIUM~~ | ~~architecture~~ | ~~agent/external_mcp_tools.py~~ | ~~791→115~~ | **RESOLVED** 2024-12-28 |
| ~~GAP-FILE-012~~ | ~~governance/hybrid_router.py exceeds 300 line limit~~ | ~~MEDIUM~~ | ~~architecture~~ | ~~governance/hybrid_router.py~~ | ~~742→99~~ | **RESOLVED** 2024-12-28 |

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

| ID | Gap | Priority | Category | Entity | Evidence |
|----|-----|----------|----------|--------|----------|
| GAP-AGENT-010 | Agent Task Backlog tab shows tasks but agents don't execute | HIGH | functionality | Agent | PARTIAL: Status filtering fixed, polling impl needed |
| GAP-AGENT-011 | No agent polling/subscription for new tasks | HIGH | architecture | Agent | Missing implementation |
| GAP-AGENT-012 | No task claim/lock mechanism for multi-agent coordination | HIGH | architecture | Task | Concurrent access |
| GAP-AGENT-013 | No delegation protocol when agent needs more context | HIGH | architecture | Agent | Workflow gap |
| GAP-AGENT-014 | Rules Curator agent not implemented | MEDIUM | functionality | Agent | RULE-011 requirement |

**Stub Migration Strategy:**
1. **TypeDB Schema Update** (`governance/schema.tql`): Add `task`, `session`, `proposal` entities
2. **Data Loading** (`governance/data.tql`): Populate from workspace files via Document MCP
3. **API Refactor**: Replace in-memory dicts with TypeDB client queries
4. **Document MCP Integration**: Real-time file content for evidence attachments

---

## Resolved Gaps

| ID | Gap | Resolution | Date |
|----|-----|------------|------|
| GAP-ARCH-001 | Tasks in-memory, not TypeDB | Hybrid: TypeDB client CRUD + in-memory fallback in api.py | 2024-12-27 |
| GAP-ARCH-002 | Sessions in-memory, not TypeDB | Hybrid: TypeDB client CRUD + in-memory fallback in api.py | 2024-12-27 |
| GAP-ARCH-003 | Agents in-memory, not TypeDB | Hybrid: TypeDB registry + local persistent metrics | 2024-12-27 |
| GAP-020 | Cross-project knowledge queries | MCP-USAGE.md Section 8 + claude-mem patterns | 2024-12-27 |
| GAP-SEC-001 | No API authentication middleware | AuthMiddleware + X-API-Key header + GOVERNANCE_API_KEY env | 2024-12-27 |
| GAP-ARCH-011 | TypeDB migration incomplete (claude-mem disconnected) | P11.4: session_memory.py + DSM tracker integration | 2024-12-26 |
| GAP-PROC-001 | Memory/context loss - no wisdom accumulation | P11.4: SessionContext, SessionMemoryManager, AMNESIA recovery | 2024-12-26 |
| GAP-DATA-002 | No entity relationships (Task→Rule, Session→Evidence) | P11.3: TypeDB schema + 5 sessions + 5 evidence + linkages | 2024-12-26 |
| GAP-TDD-001 | Task response missing 'phase' field | Fixed governance_list_tasks in mcp_server.py | 2024-12-26 |
| GAP-TDD-002 | Evidence search missing 'query'/'score' | Fixed governance_evidence_search in mcp_server.py | 2024-12-26 |
| GAP-MCP-001 | Governance MCP not visible in Claude Code | Created .mcp.json at project root | 2024-12-26 |
| GAP-DSP-001 | MCP tools not registered | FALSE POSITIVE - 40 tools registered via mcp_tools pkg | 2024-12-26 |
| GAP-ARCH-004 | TypeDB missing RULE-012 to RULE-025 | Reloaded data.tql with 25 rules | 2024-12-26 |
| GAP-ARCH-005 | No MCP tools for Tasks/Sessions | Created mcp_tools/tasks.py (5 tools) + agents.py (4 tools) | 2024-12-26 |
| GAP-ARCH-006 | Session/Task MCP exports missing | Added 15 backward compat exports | 2024-12-26 |
| GAP-UI-004 | No REST API endpoints | Created governance/api.py (23 endpoints) | 2024-12-26 |
| GAP-UI-031 | Rule Save mock-only | Wired to REST API via httpx | 2024-12-26 |
| GAP-UI-032 | Rule Delete mock-only | Wired to REST API via httpx | 2024-12-26 |
| GAP-035 | FastAPI/Starlette version mismatch | Updated FastAPI to 0.127.0 | 2024-12-26 |
| GAP-UI-035 | UI views don't auto-load data on open | P11.1: Added @state.change handler | 2024-12-26 |
| GAP-FILE-001 | governance_dashboard.py exceeds 300 line limit | Modularized 3404→1305 lines (62% reduction), 12 view modules | 2024-12-28 |
| GAP-FILE-002 | governance/api.py exceeds 300 line limit | Modularized 2357→198 lines (92% reduction), 8 route modules | 2024-12-28 |
| GAP-FILE-003 | governance/client.py exceeds 300 line limit | Modularized 1389→135 lines (90% reduction), 6 typedb modules | 2024-12-28 |
| GAP-FILE-004 | agent/governance_ui/state.py exceeds 300 line limit | Modularized 1547→34 lines (98% reduction), 11 state modules | 2024-12-28 |
| GAP-FILE-005 | governance_dashboard.py controllers exceed inline limit | Modularized 1159→592 lines (49% reduction), 10 controller modules | 2024-12-28 |
| GAP-FILE-006 | agent/governance_ui/data_access.py exceeds 300 line limit | Modularized 1170→85 lines (93% reduction), 8 data access modules | 2024-12-28 |
| GAP-FILE-007 | governance/mcp_server.py exceeds 300 line limit | Modularized 897→120 lines (87% reduction), 7 compat modules | 2024-12-28 |
| GAP-FILE-008 | governance/mcp_tools/evidence.py exceeds 300 line limit | Modularized 870→42 lines (95% reduction), 6 evidence modules | 2024-12-28 |
| GAP-FILE-009 | governance/langgraph_workflow.py exceeds 300 line limit | Modularized 851→136 lines (84% reduction), 5 langgraph modules | 2024-12-28 |
| GAP-FILE-010 | governance/pydantic_tools.py exceeds 300 line limit | Modularized 807→175 lines (78% reduction), 8 pydantic modules | 2024-12-28 |
| GAP-FILE-011 | agent/external_mcp_tools.py exceeds 300 line limit | Modularized 791→115 lines (85% reduction), 6 external MCP modules | 2024-12-28 |
| GAP-FILE-012 | governance/hybrid_router.py exceeds 300 line limit | Modularized 742→99 lines (87% reduction), 3 hybrid modules | 2024-12-28 |
| GAP-UI-023 | VDataTable binding fails in Trame | Replaced with VList | 2024-12-25 |
| GAP-UI-024 | Add Rule button crashes (TypeError) | Direct state assignment | 2024-12-25 |
| GAP-UI-025 | Rule items not clickable | Added click handler | 2024-12-25 |
| GAP-UI-026 | Search does not filter results | Added v-show filter | 2024-12-25 |
| GAP-UI-027 | Status filter shows corrupted options | State-bound items | 2024-12-25 |
| GAP-029 | TypeDB driver 3.x incompatibility in Docker | Pin to <3.0.0 | 2024-12-25 |
| GAP-030 | Trame server exits on idle (no connections) | timeout=0 in server.start() | 2024-12-25 |
| GAP-001 | ChromaDB Knowledge Integration | HttpClient injection | 2024-12-24 |
| GAP-002 | Opik Tracing Integration | OPIK_URL_OVERRIDE | 2024-12-24 |
| GAP-003 | Ollama Model Pull | gemma3:4b | 2024-12-24 |
| GAP-011 | OctoCode MCP not in use | GITHUB_PAT configured | 2024-12-24 |
| GAP-012 | TypeDB R&D | Phase 1+2 complete | 2024-12-24 |
| GAP-013 | MCPs tested but not invoked | DECISION-001 | 2024-12-24 |
| GAP-016 | ChromaDB sync TDD stubs | test_chromadb_sync.py | 2024-12-24 |
| GAP-017 | Pre-commit hooks | Duplicate of GAP-009 | 2024-12-24 |
| GAP-018 | Session documentation workflow | SESSION-TEMPLATE.md | 2024-12-24 |

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
