# Gap Index - Sim.ai PoC

**Last Updated:** 2026-01-13
**Total Gaps:** 202 | Status: 171 RESOLVED, 31 OPEN
**Format Migration:** GAP-WORKFLOW-003 - Replaced strikethrough with Status column

> **Evidence Files:** Detailed analysis moved to [evidence/](evidence/) per GAP-META-001

---

## DSP-100 Hygiene Gaps (2026-01-03)

> **Source:** DSM cycle DSP-100-HYGIENE
> **Evidence:** [GAP-FILE-RESOLUTIONS.md](evidence/GAP-FILE-RESOLUTIONS.md)

| ID | Status | Gap | Priority | Category | Evidence |
|----|--------|-----|----------|----------|----------|
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
| GAP-FILE-021 | OPEN | embedding_pipeline.py 470 lines | LOW | architecture | DSP-100 |
| GAP-FILE-022 | OPEN | context_preloader.py 428 lines | LOW | architecture | DSP-100 |
| GAP-FILE-023 | OPEN | routes/chat.py 421 lines | LOW | architecture | DSP-100 |
| GAP-FILE-024 | OPEN | dsm/tracker.py 416 lines | LOW | architecture | DSP-100 |
| GAP-FILE-025 | OPEN | quality/analyzer.py 410 lines | LOW | architecture | DSP-100 |
| GAP-FILE-026 | OPEN | workspace_scanner.py 409 lines | LOW | architecture | DSP-100 |
| GAP-FILE-027 | OPEN | typedb/queries/tasks/crud.py 352 lines | LOW | architecture | DSP-100 |

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
| GAP-PODMAN-DESKTOP-001 | OPEN | Podman Desktop shows "CREATED" for running containers | LOW | tooling | RULE-021 | Bug in 1.24.x with healthcheck "starting" state. Workaround: `scripts/fix-podman-desktop.sh` |

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
| GAP-UI-039 | OPEN | No document format support | MEDIUM | functionality | RD-DOCVIEW |
| GAP-UI-040 | RESOLVED | Agent config/instructions display | HIGH | functionality | agents_view.py |
| GAP-UI-041 | RESOLVED | Agent-session/task relation links | HIGH | functionality | agents_view.py |
| GAP-UI-042 | RESOLVED | Trust score history | HIGH | functionality | Trust history card |
| GAP-UI-043 | RESOLVED | Agent metrics display | MEDIUM | functionality | agents_view.py |
| GAP-UI-044 | RESOLVED | Executive Reporting view | HIGH | functionality | executive_view.py |
| GAP-UI-045 | OPEN | Cross-workspace metrics aggregation | MEDIUM | functionality | RULE-029 |
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
| GAP-004 | DEFERRED | Grok/xAI API Key | Medium | configuration | RULE-002 | User action needed |
| GAP-005 | RESOLVED | Agent Task Backlog UI | Medium | functionality | RULE-002 | Auto-polling implemented 2026-01-11 |
| GAP-006 | RESOLVED | Sync Agent Implementation | Medium | functionality | RULE-003 | GovernanceSync in agent/sync_agent/ |
| GAP-007 | OPEN | ChromaDB v2 Test Update | Low | testing | RULE-009 | UUID error |
| GAP-008 | RESOLVED | Agent UI Image | Low | configuration | RULE-009 | Disabled |
| GAP-009 | RESOLVED | Pre-commit Hooks | Medium | tooling | RULE-001 | FIXED 2026-01-13: Added setup docs to DEVOPS.md. Config complete in .pre-commit-config.yaml |
| GAP-010 | OPEN | CI/CD Pipeline | Low | tooling | RULE-009 | - |
| GAP-014 | DEFERRED | IntelliJ Windsurf MCP not loading | Medium | tooling | RULE-005 | Environment-specific |
| GAP-015 | RESOLVED | Consolidated STRATEGY.md | Medium | docs | RULE-001 | docs/STRATEGY.md |
| GAP-019 | RESOLVED | MCP usage documentation | Medium | docs | RULE-007 | MCP-USAGE.md |
| GAP-020 | RESOLVED | Cross-project knowledge queries | HIGH | workflow | RULE-007 | MCP-USAGE.md |
| GAP-021 | DEFERRED | OctoCode for external research | Medium | workflow | RULE-007 | Tool integration pending |
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
| GAP-INFRA-005 | DEFERRED | Ollama container not started | LOW | infra | RULE-021 | Optional: local LLM not required |
| GAP-TRAME-001 | RESOLVED | nav-infra not rendered despite code | HIGH | framework | RULE-037 | Fixed: duplicate NAVIGATION_ITEMS in constants.py |
| GAP-INFRA-006 | DEFERRED | Ollama container high memory | LOW | infrastructure | RULE-021 | Optional: depends on GAP-INFRA-005 |
| GAP-MCP-004 | RESOLVED | Rule fallback to markdown | HIGH | architecture | RULE-021 | rule_fallback.py |
| GAP-TEST-001 | DEFERRED | E2E tests lack BDD paradigm | MEDIUM | testing | RULE-023 | R&D item: Requires test methodology refactoring. Current tests use pytest+playwright. |
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
| GAP-TDD-003 | OPEN | DSM advance missing 'required_mcps' | LOW | testing | RULE-012 | - |
| GAP-TDD-004 | OPEN | DSM checkpoint missing 'timestamp' | LOW | testing | RULE-012 | - |
| GAP-TDD-005 | OPEN | DSM finding missing 'related_rules' | LOW | testing | RULE-012 | - |
| GAP-TDD-006 | RESOLVED | Tests write TEST-* to production | MEDIUM | testing | RULE-023 | Cleanup fixtures added |
| GAP-TDD-007 | RESOLVED | DSM evidence renders paths char-by-char | LOW | mcp | RULE-012 | Fixed: wrap in list |

---

## DSP Gap Discovery

| ID | Status | Gap | Priority | Category | Rule | Evidence |
|----|--------|-----|----------|----------|------|----------|
| GAP-DSP-001 | RESOLVED | MCP tools not registered | CRITICAL | functionality | RULE-007 | FALSE POSITIVE |
| GAP-DSP-002 | RESOLVED | 9 schema entities without data | HIGH | data | DECISION-003 | Rules 37/37, Tasks synced (2026-01-11) |
| GAP-DSP-003 | RESOLVED | API documentation at 25% | MEDIUM | docs | RULE-001 | All 35+ endpoints have docstrings |
| GAP-SEC-001 | RESOLVED | No API authentication | HIGH | security | RULE-011 | AuthMiddleware |
| GAP-PERF-001 | OPEN | Sync I/O in async code | LOW | performance | RULE-009 | api.py:469,494 |

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
| GAP-TASK-002 | PARTIAL | agent_id always null | LOW | data | Task | Code done (set on claim), existing tasks need migration |
| GAP-TASK-003 | PARTIAL | completed_at not populated | LOW | data | Task | Code done (set on DONE), existing tasks need migration |
| GAP-AGENT-001 | RESOLVED | trust_score hardcoded | HIGH | data | Agent | Dynamic calc |
| GAP-AGENT-002 | RESOLVED | tasks_executed always 0 | HIGH | data | Agent | Persistent |
| GAP-AGENT-003 | RESOLVED | last_active not populated | MEDIUM | data | Agent | Updated on task |
| GAP-AGENT-004 | RESOLVED | capabilities field missing | MEDIUM | schema | Agent | Added to model, schema, routes, stores |
| GAP-EVIDENCE-001 | RESOLVED | session_id not populated | HIGH | data | Evidence | 8/9 linked |
| GAP-EVIDENCE-002 | OPEN | Only reads .md files | LOW | functionality | Evidence | P11.8 Audit |
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
| GAP-DOC-004 | OPEN | No Document version tracking | MEDIUM | architecture | R&D-BACKLOG |

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
| GAP-LOG-001 | OPEN | Unclear Trame dashboard logs | LOW | observability | Trame internal DEBUG |

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
