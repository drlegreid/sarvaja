# Strategic Plan Q1 2026 - Sarvaja Platform

**Created:** 2026-01-26 | **Status:** ACTIVE | **Owner:** Claude Code Partner

---

## Executive Summary

This document preserves strategic context across session compactions per RECOVER-AMNES-01-v1.

**Current Focus:** Tier 1 - Complete Robot Framework Migration (RF-007)

---

## Tier Structure

| Tier | Focus | Status | Risk |
|------|-------|--------|------|
| **1** | RF-007: Test Migration | **ACTIVE** (86%) | LOW |
| **2** | EPIC-EA: Enterprise Architecture | PLANNED | MEDIUM |
| **3** | Deferred Items | STABLE | LOW |
| **4** | Future R&D | ON HOLD | N/A |

---

## Tier 1: RF-007 Robot Framework Migration

**Goal:** 100% test migration to Robot Framework BDD
**Progress:** 86% (1911/2217 tests)
**Remaining:** 39 Playwright browser tests (need robotframework-browser)

### Completed Files (Phase 1)

| # | File | Lines | Tests | Status |
|---|------|-------|-------|--------|
| 1 | test_dsm_tracker_integration.py | 564 | 30 | ✅ DONE |
| 2 | test_external_mcp_tools.py | 736 | 62 | ✅ DONE |
| 3 | test_task_ui.py | 542 | 29 | ✅ DONE |
| 4 | test_embedding_pipeline.py | 297 | 19 | ✅ DONE |
| 5 | test_chat.py | 414 | 33 | ✅ DONE (RF-005) |
| 6 | test_langgraph_workflow.py | 629 | 43 | ✅ DONE |

### Remaining Files (Phase 2 - Gap Analysis 2026-01-26)

**Total Remaining:** 6 files, 131 tests

| # | File | Lines | Tests | Category | Status |
|---|------|-------|-------|----------|--------|
| 7 | test_validation.py | 140 | 8 | rules | ✅ DONE |
| 8 | test_integration.py | 107 | 6 | rules | ✅ DONE |
| 9 | test_typedb3_connection.py | 165 | 10 | component | ✅ DONE |
| 10 | test_typedb3_value_extraction.py | 153 | 6 | integration | ✅ DONE |
| 11 | test_heuristics_example.py | 182 | 16 | heuristics | ✅ DONE |
| 12 | test_platform_performance.py | 248 | 12 | heuristics | ✅ DONE |
| 13 | test_typedb_functions.py | 265 | 6 | integration | ✅ DONE |
| 14 | test_mcp_rest_sessions.py | 276 | 13 | integration | ✅ DONE |
| 15 | test_archive.py | 301 | 13 | rules | ✅ DONE |
| 16 | test_lacmus.py | 455 | 20 | benchmarks | ✅ DONE |
| 17 | test_dashboard_e2e.py | 269 | 29 | browser-e2e | ⏸ PLAYWRIGHT |
| 18 | test_session_task_navigation_e2e.py | 305 | 10 | browser-e2e | ⏸ PLAYWRIGHT |
| 19 | test_data_integrity_e2e.py | 385 | 9 | api-e2e | ✅ DONE (data_integrity.robot) |
| 20 | test_platform_health_e2e.py | 387 | 7 | api-e2e | ✅ DONE (platform_health.robot) |
| 21 | test_governance_crud_e2e.py | 1123 | 54 | api-e2e | ✅ DONE (governance_crud.robot) |

**Note:** Browser E2E tests (Playwright) require robotframework-browser for migration. API E2E tests completed.

### Migration Pattern (Per DOC-SIZE-01-v1)

```
1. Read pytest file
2. If >400 lines: Split into focused libraries (facade pattern)
3. Create tests/libs/<Name>Library.py with @keyword decorators
4. Create tests/robot/unit/<name>.robot
5. Dry-run validation: .venv/bin/robot --dryrun <file>
6. Update RD-ROBOT-FRAMEWORK.md progress
```

### Quality Gates

- [ ] All tests pass dry-run
- [ ] Skip If pattern for import failures
- [ ] Libraries <400 lines per DOC-SIZE-01-v1
- [ ] Tags follow TEST-TAXON-01-v1 taxonomy

---

## Tier 2: EPIC-EA Enterprise Architecture (NEXT)

**Trigger:** After RF-007 reaches 100%

### Components

1. **Session Init Script** (RD-RESEARCH-003)
   - `scripts/session_init.sh`
   - Baseline test gate
   - Environment resurrection

2. **Context Engineering** (RD-RESEARCH-001/002)
   - Compiled view transform
   - Active compaction triggers
   - Token budget tracking

3. **Feature Tracking** (RD-RESEARCH-003)
   - JSON format for TODO items
   - Machine-readable progress

---

## Tier 3: Deferred Items (STABLE)

| Item | Trigger for Activation |
|------|------------------------|
| GAP-LANGGRAPH-QUALITY-001 | Multi-agent execution active |
| RD-DOCUMENT-MCP-SERVICE | gov-sessions >30 tools |
| GAP-MCP-PAGING-001 | External dependency fix |

---

## Tier 4: Future R&D (ON HOLD)

| Item | Trigger |
|------|---------|
| RD-HASKELL-MCP | Strategic platform complete |
| RD-002/003 | Haskell benchmark results |
| RD-004 | Robotics deployment need |
| RD-005 | TypeDB 3.x stable |

---

## Context Recovery Checklist

On session start or compaction:

```
1. Read this document first
2. Check RD-ROBOT-FRAMEWORK.md for RF-007 status
3. health_check() to verify services
4. Continue from next TODO file in Tier 1
```

---

## Session Log

| Date | Session | Accomplishment |
|------|---------|----------------|
| 2026-01-26 AM | RF-007 | +10 files migrated (64%→71%) |
| 2026-01-26 PM | RF-007 | +4 files: context_preloader, agent_platform, rules_governance, mcp_tools |
| 2026-01-26 | PLAN | Created STRATEGIC-PLAN-2026-Q1.md |
| 2026-01-26 | RF-007 | +3 files: dsm_tracker_integration (30), external_mcp_tools (62), task_ui (29) = 121 tests (71%→77%) |
| 2026-01-26 | RF-007 | +1 file: embedding_pipeline (19) = 19 tests (77%→78%) |
| 2026-01-26 | RF-007 | +2 files: chat (33), langgraph_workflow (43) = 76 tests (78%→81%) |
| 2026-01-26 | RF-007 | Gap analysis: 15 files, 221 tests remaining |
| 2026-01-26 | RF-007 | +4 files: validation (8), integration (6), typedb3_connection (10), typedb3_value_extraction (6) = 30 tests (81%→83%) |
| 2026-01-26 | RF-007 | +5 files: heuristics_example (16), platform_performance (12), typedb_functions (6), mcp_rest_sessions (13), archive (13) = 60 tests (83%→85%) |
| 2026-01-26 | RF-007 | +1 file: lacmus (20) = 20 tests; E2E analysis: 3 files already done (data_integrity, platform_health, governance_crud) (85%→86%) |

---

*Per RECOVER-AMNES-01-v1: Context preservation document*
*Per WORKFLOW-RD-01-v1: Strategic planning with human approval*
