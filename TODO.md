# TODO Index - Sim.ai PoC

**Status:** Active | **Updated:** 2024-12-31 (Infrastructure Gaps + Dev Workflow)

---

## Quick Links

| Document | Content | Lines |
|----------|---------|-------|
| [GAP-INDEX](docs/gaps/GAP-INDEX.md) | Gap tracking (12 open, 9 resolved) | ~60 |
| [R&D-BACKLOG](docs/backlog/R&D-BACKLOG.md) | Strategic R&D, TypeDB phases | ~900 |
| [TASKS-COMPLETED](docs/tasks/TASKS-COMPLETED.md) | Archived completed tasks | ~120 |
| [RULES-DIRECTIVES](docs/RULES-DIRECTIVES.md) | 25 rules (22 ACTIVE, 3 DRAFT) | ~150 |

---

## Current Sprint: P10 - UI-First Sprint

### High Priority (P0)

| # | Task | Status | Phase | Description |
|---|------|--------|-------|-------------|
| 1 | GitHub Actions workflow | ✅ DONE | P10 | E2E certification runs |
| 2 | Certification issue template | ✅ DONE | P10 | `.github/ISSUE_TEMPLATE/certification.md` |

### Medium Priority (P1)

| # | Task | Status | Effort | GAP |
|---|------|--------|--------|-----|
| 6 | Agent Task Backlog UI | ✅ DONE | 3h | GAP-005 |
| 7 | Sync Agent Implementation | ✅ DONE | 4h | GAP-006 |
| 8 | MCP usage documentation | ✅ DONE | 1h | GAP-019 |
| 9 | Opik Dashboard startup | ⏸️ N/A | - | DECISION-001 |

### Low Priority (P2)

| # | Task | Status | Effort | GAP |
|---|------|--------|--------|-----|
| 10 | ChromaDB v2 Test Update | ⏸️ Hold | 2h | GAP-007 |
| 11 | Agent UI Image | ✅ DONE | - | GAP-008 (disabled) |
| 12 | CI/CD Pipeline | 📋 TODO | 2h | GAP-010 |
| 13 | Grok/xAI API Key | ⏳ Pending | 15min | GAP-004 |
| 14 | Exploratory UI Testing Workflow | 📋 TODO | 2h | GAP-UI-EXP |

---

## Phase Status

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 1** | TypeDB Container | ✅ COMPLETE |
| **Phase 2** | Governance MCP | ✅ COMPLETE |
| **Phase 3** | Stabilization & v1.0 | ✅ COMPLETE |
| **Phase 4** | Cross-Workspace Integration | ✅ COMPLETE |
| **Phase 5** | External MCP Integration | ✅ COMPLETE |
| **Phase 6** | Agent UI Framework | ✅ COMPLETE |
| **Phase 7** | TypeDB-First Migration | ✅ COMPLETE |
| **Phase 8** | E2E Testing Framework | ✅ COMPLETE |
| **Phase 9** | Agentic Platform UI/MCP | ✅ COMPLETE |
| **Phase 10** | Architecture Debt Resolution | ✅ COMPLETE |
| **Phase 11** | Data Integrity Resolution | ✅ COMPLETE |
| **Phase 12** | Agent Orchestration | 🚧 IN_PROGRESS |

> Details: [R&D-BACKLOG.md](docs/backlog/R&D-BACKLOG.md)

---

## Recently Completed (This Session)

| Task | Completed | Description |
|------|-----------|-------------|
| GAP-MCP-002 | 2024-12-31 | PARTIAL: MCP healthcheck implemented but not auto-called (see GAP-MCP-003) |
| GAP-MCP-003 | 2024-12-31 | IDENTIFIED: governance_health not called at session start - services down undetected |
| GAP-WORKFLOW-001 | 2024-12-31 | IDENTIFIED: Session not auto-saved to claude-mem before restart |
| GAP-WORKFLOW-002 | 2024-12-31 | IDENTIFIED: Claude Code should prompt /save before major transitions |
| GAP-INFRA-005 | 2024-12-31 | IDENTIFIED: Ollama not started with dev profile |
| GAP-INFRA-006 | 2024-12-31 | IDENTIFIED: Ollama high memory usage - consider disable for DEV workflow |
| RULE-021-ENH | 2024-12-31 | ENHANCED: Added governance_health mandatory call at session start (GAP-MCP-003) |
| RULE-024-ENH | 2024-12-31 | ENHANCED: Added save prompts before major transitions (GAP-WORKFLOW-002) |
| GAP-MCP-004 | 2024-12-31 | IDENTIFIED: Rule fallback to markdown files not implemented (CLAUDE.md documents hierarchy but code doesn't read from docs/rules/*.md) |
| DEV-CONTAINER-API | 2024-12-31 | Docker dev container now exposes port 8082 for API (E2E testing enabled) |
| E2E-FIX | 2024-12-31 | Fixed 3 E2E tests: JSON body vs query params (34/40 tests pass) |
| GAP-ARCH-009 | 2024-12-31 | IDENTIFIED: TypeDB session retrieval issue (create works, end returns 404) |
| ROADMAP-UPDATE | 2024-12-31 | Updated ROADMAP.md: Phase 4 at 90%, success metrics, quick reference |
| GAP-INFRA-001 | 2024-12-31 | RESOLVED: Docker health checks fixed (ChromaDB v2, LiteLLM liveliness) |
| GAP-INFRA-002 | 2024-12-31 | RESOLVED: Dev vs Prod workflow documented in DEPLOYMENT.md |
| GAP-INFRA-003 | 2024-12-31 | RESOLVED: Added dev profile to deploy.ps1 (ValidateSet + docs) |
| GAP-UI-029 | 2024-12-31 | RESOLVED: Executive Report field name mismatch (rules_total→total_rules) fixed |
| GAP-UI-030 | 2024-12-31 | RESOLVED: Deleted 154 TEST-* tasks from TypeDB (14 real tasks remain) |
| AGENT-FW-001 | 2024-12-31 | Added agentic AI frameworks research to R&D-BACKLOG.md |
| GAP-INFRA-003-004 | 2024-12-31 | Added 2 remaining infrastructure gaps (deploy.ps1 dev, health dashboard) |
| BUG-003 | 2024-12-31 | Fixed playground.py import scoping (shadowed global os import) |
| DEV-WORKFLOW | 2024-12-31 | Started governance-dashboard-dev container for live code editing |
| UI-SMOKE | 2024-12-28 | 11 UI smoke tests (TestUISmokeTests + TestDataIntegrity) for all navigation views |
| GAP-UI-028 | 2024-12-28 | RESOLVED: Tests pass but UI broken - fixed via RULE-028 Validation Hierarchy |
| GAP-UI-029 | 2024-12-28 | IDENTIFIED: Executive Report shows 0 Rules/Agents in stats (data discrepancy) |
| GAP-UI-030 | 2024-12-28 | IDENTIFIED: Tasks view polluted with 150+ TEST-* tasks (cleanup needed) |
| FEATURE-001 | 2024-12-28 | Session evidence file viewing: API restart + E2E validation (RULE-028 Level 3) |
| RULE-028-ENH | 2024-12-28 | Added Validation Hierarchy (Level 1-3): Bug fix ≠ Feature fix |
| E2E-FILES | 2024-12-28 | TestFilesAPI: 4 E2E tests for /api/files/content endpoint |
| BUG-002 | 2024-12-28 | Fixed async handler + rules_view.py signature (Trame UI fix) |
| RULE-030 | 2024-12-28 | Docker Dev Container Workflow rule (autonomous validation) |
| GAP-DEPLOY-001 | 2024-12-28 | Documented: deploy.ps1 missing dev profile support |
| P11.5 | 2024-12-28 | Session Evidence Attachments: API + UI + TypeDB linkage (GAP-DATA-003) |
| P11.6 | 2024-12-28 | File Reorganization: 24 files moved to proper directories (GAP-ORG-001) |
| BUG-001 | 2024-12-28 | Fixed async handler issue in controllers/chat.py (document loading) |
| GAP-FILE-001 | 2024-12-28 | governance_dashboard.py modularized: 3404→1305 lines (62% reduction), 12 view modules |
| ORCH-006 | 2024-12-28 | Agent Chat UI: chat state + API + dashboard view (33 tests) |
| ORCH-004 | 2024-12-28 | Agent delegation protocol: delegation.py (35 tests) |
| GAP-UI-044 | 2024-12-28 | Executive Reporting UI: state.py + governance_dashboard.py + api.py endpoints |
| KAN-002 | 2024-12-27 | Kanren constraints DSL: governance/kanren_constraints.py (39 tests) |
| ORCH-002 | 2024-12-27 | Task polling: agent/orchestrator/ module (31 tests) |
| ORCH-003 | 2024-12-27 | Task claim/lock: included in orchestrator |
| RULE-028 | 2024-12-27 | Change Validation Protocol (exploratory heuristics) |
| RULE-029 | 2024-12-27 | Executive Reporting Pattern (enterprise sessions) |
| KAN-001 | 2024-12-27 | Kanren spike: context engineering validated |
| ORCH-001 | 2024-12-27 | Agent orchestration design: patterns researched |
| TDD-FIX | 2024-12-27 | Fixed 7 TDD stubs (DSM, GitHub sync, governance) |
| GAP-UI-035-045 | 2024-12-27 | Added 11 new UI gaps (executive reporting, agent dashboard) |
| P10.11 | 2024-12-26 | REST API: governance/api.py (23 endpoints) |
| P10.12 | 2024-12-26 | UI: Wired Save/Delete buttons to API (GAP-UI-031/032) |
| P10.13 | 2024-12-26 | UI: Added Agents view with task execution metrics |
| P10.14 | 2024-12-26 | UI: Enhanced Tasks view with agent attribution |
| P10.15 | 2024-12-26 | E2E Tests: 15 passing CRUD workflow tests |
| P10.16 | 2024-12-26 | Fix: FastAPI 0.127.0 for Starlette 0.50 compatibility |
| P10.4 | 2024-12-25 | Governance Dashboard Docker container (dev profile) |
| P10.5 | 2024-12-25 | UI Fix: VDataTable → VList migration (GAP-UI-023) |

---

## Gap Summary

| Priority | Count | Top Items |
|----------|-------|-----------|
| HIGH | 16 | GAP-INFRA-001-004, GAP-UI-037-042 (infrastructure, agent dashboard) |
| MEDIUM | 11 | GAP-RD-001 (Kanren), GAP-UI-035-036, GAP-UI-043, GAP-UI-045 (UX, metrics) |
| Low | 2 | GAP-007, GAP-010 |

> **Total Gaps:** 119 (67 resolved, 52 open) - +2 (GAP-INFRA-006, GAP-MCP-004) 2024-12-31
> Details: [GAP-INDEX.md](docs/gaps/GAP-INDEX.md)

---

## Test Summary

| Suite | Tests | Status |
|-------|-------|--------|
| **Full Suite** | 1,106 passed | ✅ |
| **E2E CRUD** | 20 passed | ✅ |
| **E2E Files API** | 4 passed | ✅ New |
| **Kanren Constraints** | 39 passed | ✅ |
| **Orchestrator** | 31 passed | ✅ |
| **Delegation (ORCH-004)** | 35 passed | ✅ |
| **Chat (ORCH-006)** | 33 passed | ✅ |
| **Skipped** | 46 | ⏸️ |
| **Total** | **1,156** | 100% pass |

> E2E tests: tests/e2e/test_governance_crud_e2e.py (Tasks, Agents, Sessions, Evidence, Files)
> TDD stubs: Fixed 2024-12-27 (DSM, GitHub sync, governance)

---

## Task Status Legend

| Symbol | Status |
|--------|--------|
| ✅ | Completed |
| 🚧 | In Progress |
| ⏳ | Pending |
| 📋 | Not Started |
| ⏸️ | On Hold |

---

## Maintenance

- Update this index when adding new tasks
- Archive completed tasks to [TASKS-COMPLETED.md](docs/tasks/TASKS-COMPLETED.md)
- Track gaps in [GAP-INDEX.md](docs/gaps/GAP-INDEX.md)
- R&D items go to [R&D-BACKLOG.md](docs/backlog/R&D-BACKLOG.md)

---

*Per RULE-012: Deep Sleep Protocol - document hygiene*
*Per RULE-024: AMNESIA Protocol - recovery-friendly documents*
