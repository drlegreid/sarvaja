# Agent Platform Roadmap Session
**Date:** 2026-01-11
**Topic:** Functional Agent Platform with Data Linking
**Status:** RESOLVED - claude-mem implemented

---

## 1. Claude-mem MCP Failure - Root Cause

### Problem
The `.mcp.json` references `claude_mem.mcp_server` but this module doesn't exist:
- Not in sim-ai project
- Not in localgai project
- Not installed as pip package

### Impact
- **GAP-MEM-001** (CRITICAL): AMNESIA recovery fallback unavailable
- **GAP-MEM-002** (HIGH): Per RULE-024, claude-mem is required for context recovery

### Resolution (2026-01-11)

**RESOLVED**: Created `claude_mem/mcp_server.py` with full MCP implementation:
- `chroma_query_documents` - Semantic search for memories
- `chroma_get_documents` - Get specific documents by ID
- `chroma_add_documents` - Add new memories with project isolation
- `chroma_delete_documents` - Remove memories
- `chroma_health` - Check ChromaDB connection
- `chroma_save_session_context` - Save session context for AMNESIA recovery
- `chroma_recover_context` - Recover recent session contexts

ChromaDB telemetry disabled. Collection: `claude_memories`.

---

## 2. Agent Platform - Current State

### What Works (Data Linking: 100%)

| Entity | Linking Status | Evidence |
|--------|---------------|----------|
| Task→Agent | 74/74 (100%) | GAP-LINK-001 RESOLVED |
| Task→Session | 74/74 (100%) | GAP-LINK-002 RESOLVED |
| Rule→Document | Connected | workspace_link_rules_to_documents() |
| Session→Evidence | Connected | session_link_evidence() |
| Decision→Rules | Connected | get_decision_impacts() |

### MCP Infrastructure (Functional)

| Server | Tools | Status |
|--------|-------|--------|
| governance-core | 15 | Working |
| governance-agents | 9 | Working |
| governance-sessions | 25 | Working |
| governance-tasks | 15 | Working |
| **claude-mem** | 7 | **Working** |

### Workspace Structure (Created, Not Activated)

```
workspaces/
├── research/    # RESEARCH agent
├── coding/      # CODING agent
├── curator/     # CURATOR agent
├── sync/        # SYNC agent (skeleton only)
└── qa/          # QA agent
```

---

## 3. Blocking Gaps for Functional Agent Platform

### CRITICAL

| Gap | Issue | Resolution |
|-----|-------|------------|
| ~~GAP-MEM-001~~ | ~~claude-mem MCP not implemented~~ | **RESOLVED** - claude_mem/mcp_server.py |
| GAP-006 | Sync Agent skeleton only | Implement workspace_capture_tasks, git sync |

### HIGH

| Gap | Issue | Resolution |
|-----|-------|------------|
| ~~GAP-MEM-002~~ | ~~AMNESIA fallback unavailable~~ | **RESOLVED** - chroma_save/recover_context |
| MULTI-007 | No observability & conflict mgmt | Implement agent status dashboard |
| TOOL-010 | MCP via SSE (consolidation) | Research Claude Code SSE transport |

### MEDIUM (Non-Blocking)

| Gap | Issue | Status |
|-----|-------|--------|
| GAP-UI-039 | No document format support | Can use markdown viewer |
| GAP-UI-045 | Cross-workspace metrics | Post-MVP |
| GAP-INFRA-005 | Ollama not started | Optional for local LLM |

---

## 4. Minimum Viable Agent Platform (MVP)

### MVP Definition
A multi-agent system where:
1. Tasks flow between workspaces via evidence handoffs
2. Agents can read/write shared state (TypeDB + ChromaDB)
3. Context recovery works after AMNESIA events
4. Basic observability exists (who's doing what)

### MVP Implementation Tasks

| Priority | Task | Effort | Blocks |
|----------|------|--------|--------|
| 1 | Fix claude-mem or remove dependency | 1-2h | All agents |
| 2 | Implement Sync Agent core logic | 2-4h | Workspace coordination |
| 3 | Add agent status tracking MCP tools | 2h | Observability |
| 4 | Test multi-workspace handoff flow | 2h | Validation |
| 5 | Update AGENT-WORKSPACES.md Phase 5 status | 30m | Documentation |

### MVP Architecture

```
                    ┌──────────────────────┐
                    │   Orchestrator/User  │
                    └──────────┬───────────┘
                               │
           ┌───────────────────┼───────────────────┐
           │                   │                   │
    ┌──────▼──────┐     ┌──────▼──────┐     ┌──────▼──────┐
    │  RESEARCH   │     │   CODING    │     │    QA       │
    │  Workspace  │────▶│  Workspace  │────▶│  Workspace  │
    └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
           │                   │                   │
           └───────────────────┼───────────────────┘
                               │
                    ┌──────────▼───────────┐
                    │   SHARED RESOURCES   │
                    ├──────────────────────┤
                    │ TypeDB :1729 (rules) │
                    │ ChromaDB :8001 (RAG) │
                    │ Evidence files       │
                    │ governance-* MCPs    │
                    └──────────────────────┘
```

---

## 5. Data Linking - Full Picture

### Entity Relationships (TypeDB Schema)

```
rule ──┬── depends-on ──► rule
       └── impacts ──► decision

task ──┬── implements-rule ──► rule
       ├── completed-in ──► session
       └── assigned-to ──► agent

session ──┬── session-applied-rule ──► rule
          ├── session-decision ──► decision
          └── has-evidence ──► evidence-file

agent ──── has-trust-score ──► trust-history
```

### MCP Tools for Data Linking

| Tool | Creates Relation |
|------|------------------|
| `governance_task_link_session` | task→session |
| `governance_task_link_rule` | task→rule |
| `governance_task_link_evidence` | task→evidence |
| `governance_create_handoff` | Creates handoff with all links |
| `session_link_rule` | session→rule |
| `session_link_decision` | session→decision |
| `session_link_evidence` | session→evidence |

### Current Data Integrity

```
TypeDB Entities:
  - Rules: 40 (100% linked to documents)
  - Tasks: 74 (100% linked to sessions, agents)
  - Sessions: 22+ DSM cycles
  - Agents: 4+ registered
  - Decisions: 6+ recorded

ChromaDB Collections:
  - Evidence embeddings: Active
  - Semantic search: Working
```

---

## 6. Roadmap Summary

### Immediate (This Session) - ALL DONE
- [x] Investigate claude-mem failure - Root cause: module doesn't exist
- [x] Document gaps - GAP-MEM-001, GAP-MEM-002 added
- [x] Analyze data linking - 100% task linking confirmed
- [x] Create roadmap - This document
- [x] **Implement claude-mem MCP server** - 7 tools, ChromaDB backend
- [x] **Test AMNESIA recovery tools** - chroma_save/recover_context working

### Short-term (Next 2-3 Sessions)
- [x] ~~Resolve GAP-MEM-001~~ - DONE
- [ ] Implement Sync Agent core
- [ ] Add agent observability MCP tools
- [ ] Test end-to-end workspace handoff

### Medium-term (1-2 Weeks)
- [ ] Evidence pattern analyzer (Phase 5)
- [ ] Trust-weighted voting
- [ ] MCP via SSE consolidation (TOOL-010)
- [ ] Multi-agent conflict management

### Long-term (Future Phases)
- [ ] Claude Agent SDK integration
- [ ] Automated rule optimization loop
- [ ] Cross-workspace metrics dashboard
- [ ] Production multi-agent deployment

---

## 7. Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| claude-mem resolution | **Implemented from scratch** | Full control, 7 tools, AMNESIA-optimized |
| Agent communication | Evidence files + MCP | Per AGENT-WORKSPACES.md design |
| Orchestration | Manual first, SDK later | Prove concept before complexity |
| Data store | TypeDB + ChromaDB hybrid | Per DECISION-003, permanent |
| Telemetry | Disabled | User request for privacy |

---

*Session per RULE-001: Session Evidence Logging*
*Per RULE-024: AMNESIA Protocol analysis*
