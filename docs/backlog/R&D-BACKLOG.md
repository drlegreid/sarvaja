# R&D Backlog - Sarvaja

**Last Updated:** 2026-02-11 | **Source of Truth:** TypeDB via MCP tools

---

## Quick Commands

```bash
# Get R&D tasks from TypeDB
mcp__gov-sessions__governance_list_tasks(phase="RD")

# Get task details
mcp__gov-tasks__task_get(task_id="RD-001")

# Get backlog
mcp__gov-tasks__backlog_get(limit=20)
```

---

## Document Index

| Category | Document | Status |
|----------|----------|--------|
| **Roadmap** | [ROADMAP.md](../../ROADMAP.md) | ACTIVE |
| **Phase 10** | [PHASE-10.md](phases/PHASE-10.md) | ✅ COMPLETE |
| **Phase 11** | [PHASE-11.md](phases/PHASE-11.md) | ✅ COMPLETE |
| **Phase 12** | [PHASE-12.md](phases/PHASE-12.md) | ✅ COMPLETE |
| **Agent Orchestration** | [RD-AGENT-ORCHESTRATION.md](rd/RD-AGENT-ORCHESTRATION.md) | ✅ COMPLETE |
| **Kanren Context** | [RD-KANREN-CONTEXT.md](rd/RD-KANREN-CONTEXT.md) | ✅ COMPLETE |
| **Haskell MCP** | [RD-HASKELL-MCP.md](rd/RD-HASKELL-MCP.md) | ON HOLD |
| **Frankel Hash** | [RD-FRANKEL-HASH.md](rd/RD-FRANKEL-HASH.md) | ✅ CORE COMPLETE |
| **Testing Strategy** | [RD-TESTING-STRATEGY.md](rd/RD-TESTING-STRATEGY.md) | ✅ COMPLETE |
| **Robot Framework BDD** | [RD-ROBOT-FRAMEWORK.md](rd/RD-ROBOT-FRAMEWORK.md) | PARTIAL |
| **Agent Testing** | [RD-AGENT-TESTING.md](rd/RD-AGENT-TESTING.md) | ✅ COMPLETE |
| **Document Viewer** | [RD-DOCUMENT-VIEWER.md](rd/RD-DOCUMENT-VIEWER.md) | ✅ COMPLETE |
| **Document MCP Service** | [RD-DOCUMENT-MCP-SERVICE.md](rd/RD-DOCUMENT-MCP-SERVICE.md) | TRIGGER MET |
| **Rule Applicability** | [RD-RULE-APPLICABILITY.md](rd/RD-RULE-APPLICABILITY.md) | ✅ COMPLETE |
| **Memory Gaps** | [RD-RESEARCH-001](rd/RD-RESEARCH-001-MEMORY-GAPS.md) | ✅ COMPLETE |
| **Context Engineering** | [RD-RESEARCH-002](rd/RD-RESEARCH-002-CONTEXT-ENGINEERING.md) | ✅ COMPLETE |
| **Long-Running Harnesses** | [RD-RESEARCH-003](rd/RD-RESEARCH-003-LONG-RUNNING-HARNESSES.md) | ✅ COMPLETE |
| **Lacmus Benchmark** | [RD-LACMUS.md](rd/RD-LACMUS.md) | PARTIAL (Phase 4 blocked) |

---

## Active EPICs

| EPIC | Document | Status |
|------|----------|--------|
| **EPIC-CLEANUP-001** | [PLAN-REMAINING-WORK-2026-01-20.md](rd/PLAN-REMAINING-WORK-2026-01-20.md) | ✅ COMPLETE |
| Dashboard Production Readiness | [EPIC-DR.md](rd/EPIC-DR.md) | ✅ COMPLETE |
| Enterprise Architecture | [EPIC-EA.md](rd/EPIC-EA.md) | TODO |
| Gov-Sessions Audit + Rich UI | [generic-soaring-flute.md](../../.claude/plans/generic-soaring-flute.md) | ✅ COMPLETE (18/18) |

---

## Data Architecture

```
TypeDB (Source of Truth)
    └── task entities (phase="RD")
         └── linked to sessions, evidence

R&D-BACKLOG.md (View)
    └── Document Index (links to details)
    └── Human-readable quick reference

rd/*.md (Detail Documents)
    └── Full specifications per R&D item
    └── Write-once, archive on completion
```

---

*Per DATA-ARCH-CLEANUP DSM: TypeDB = source of truth.*
*Per DOC-SIZE-01-v1: Keep files <300 lines.*
