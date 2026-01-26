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
| **1** | RF-007: Test Migration | **ACTIVE** (77%) | LOW |
| **2** | EPIC-EA: Enterprise Architecture | PLANNED | MEDIUM |
| **3** | Deferred Items | STABLE | LOW |
| **4** | Future R&D | ON HOLD | N/A |

---

## Tier 1: RF-007 Robot Framework Migration

**Goal:** 100% test migration to Robot Framework BDD
**Progress:** 77% (1706/2217 tests)
**Remaining:** ~511 tests across 3 files (+ 2 DEFERRED)

### Remaining Files (Priority Order)

| # | File | Lines | Est. Tests | Status |
|---|------|-------|------------|--------|
| 1 | test_dsm_tracker_integration.py | 564 | 30 | ✅ DONE |
| 2 | test_external_mcp_tools.py | 736 | 62 | ✅ DONE |
| 3 | test_task_ui.py | 542 | 29 | ✅ DONE |
| 4 | test_embedding_pipeline.py | ~150 | ~10 | TODO |
| 5 | test_chat.py | ~400 | ~25 | DEFERRED (RF-005) |
| 6 | test_langgraph_workflow.py | ~300 | ~20 | DEFERRED |

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

---

*Per RECOVER-AMNES-01-v1: Context preservation document*
*Per WORKFLOW-RD-01-v1: Strategic planning with human approval*
