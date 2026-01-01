# R&D Backlog - Sim.ai PoC

**Last Updated:** 2024-12-31
**Status:** Active Development
**Pattern:** Table-of-Contents → Individual Documents

---

## Document Structure

This is the **root document** for R&D backlog. Each section links to detailed individual files for lazy content loading and TypeDB tracking.

### Document Index

| Category | Document | Status | Priority |
|----------|----------|--------|----------|
| **Platform Roadmap** | [../../ROADMAP.md](../../ROADMAP.md) | ACTIVE | **CRITICAL** |
| **Phase 10** | [phases/PHASE-10.md](phases/PHASE-10.md) | ✅ COMPLETE | HIGH |
| **Phase 11** | [phases/PHASE-11.md](phases/PHASE-11.md) | ✅ COMPLETE | CRITICAL |
| **Phase 12** | [phases/PHASE-12.md](phases/PHASE-12.md) | IN_PROGRESS | **CRITICAL** |
| **Agent Orchestration** | [rd/RD-AGENT-ORCHESTRATION.md](rd/RD-AGENT-ORCHESTRATION.md) | IN_PROGRESS | CRITICAL |
| **Kanren Context Engineering** | [rd/RD-KANREN-CONTEXT.md](rd/RD-KANREN-CONTEXT.md) | IN_PROGRESS | HIGH |
| **Haskell MCP** | [rd/RD-HASKELL-MCP.md](rd/RD-HASKELL-MCP.md) | ON HOLD | FUTURE |
| **Frankel Hash** | [rd/RD-FRANKEL-HASH.md](rd/RD-FRANKEL-HASH.md) | PARTIAL | HIGH |
| **Testing Strategy** | [rd/RD-TESTING-STRATEGY.md](rd/RD-TESTING-STRATEGY.md) | IN_PROGRESS | CRITICAL |
| **Document Viewer** | [rd/RD-DOCUMENT-VIEWER.md](rd/RD-DOCUMENT-VIEWER.md) | TODO | HIGH |

---

## Strategic Vision: Private Cluster AI Platform

**Goal:** Self-hosted platform with MCPs & UIs on private cluster

### Platform Pillars

| Pillar | Current | Target |
|--------|---------|--------|
| **Agents** | ✅ Agno/LiteLLM | TypeDB-enhanced |
| **Tasks/Projects** | ✅ Split docs | TypeDB graph |
| **Evidence/Sessions** | ✅ Markdown/scripts | Structured DB |
| **Rules** | ✅ TypeDB + Markdown | TypeDB inference |

### Architecture Target

```
┌─────────────────────────────────────────────────────────────────┐
│                    sim-ai v1.0 Target Architecture              │
├─────────────────────────────────────────────────────────────────┤
│  Agents (7777) ─────────────────────────────────────────────    │
│       │                                                         │
│       ├── LiteLLM (4000) ── Ollama (11434)                     │
│       │                                                         │
│       ├── ChromaDB (8001)     │  TypeDB (1729)                 │
│       │   └── Semantic search │  └── Inference + Types         │
│       │   └── Documents (53)  │  └── Rules (24) + Decisions    │
│       │                       │                                 │
│       └── HYBRID QUERY LAYER ─┴─────────────────────────────   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase Summary

### Completed Phases (1-9) ✅

| Phase | Name | Status | Tests |
|-------|------|--------|-------|
| Phase 1 | TypeDB Container | ✅ COMPLETE | 68 |
| Phase 2 | Governance MCP | ✅ COMPLETE | 11 tools |
| Phase 3 | Stabilization | ✅ COMPLETE | 472 |
| Phase 4 | Cross-Workspace Integration | ✅ COMPLETE | P4.1-P4.5 |
| Phase 5 | External MCP Integration | ✅ COMPLETE | 64 |
| Phase 6 | Agent UI Framework | ✅ COMPLETE | 41 |
| Phase 7 | TypeDB-First Migration | ✅ COMPLETE | 609 |
| Phase 8 | E2E Testing Framework | ✅ COMPLETE | Robot + Playwright |
| Phase 9 | Agentic Platform UI/MCP | ✅ COMPLETE | 40+ MCP tools |

### Active Phases (10-12)

| Phase | Name | Status | Link |
|-------|------|--------|------|
| Phase 10 | Architecture Debt Resolution | ✅ COMPLETE | [PHASE-10.md](phases/PHASE-10.md) |
| Phase 11 | Data Integrity Resolution | ✅ COMPLETE | [PHASE-11.md](phases/PHASE-11.md) |
| Phase 12 | Agent Orchestration | 🚧 IN_PROGRESS | [PHASE-12.md](phases/PHASE-12.md) |

---

## R&D Task Summary

### Active R&D

| ID Range | Topic | Priority | Link |
|----------|-------|----------|------|
| ORCH-001-007 | Agent Orchestration | **CRITICAL** | [RD-AGENT-ORCHESTRATION.md](rd/RD-AGENT-ORCHESTRATION.md) |
| KAN-001-005 | Kanren Context Engineering | **HIGH** | [RD-KANREN-CONTEXT.md](rd/RD-KANREN-CONTEXT.md) |
| FH-001-008 | Frankel Hash | HIGH | [RD-FRANKEL-HASH.md](rd/RD-FRANKEL-HASH.md) |
| TEST-001-006 | Testing Strategy | **CRITICAL** | [RD-TESTING-STRATEGY.md](rd/RD-TESTING-STRATEGY.md) |
| TOOL-001-005 | MCP Tooling Efficiency | MEDIUM | (inline below) |
| DOC-001-005 | Document Management MCP | HIGH | (inline below) |

### Deferred R&D

| ID Range | Topic | Priority | Link |
|----------|-------|----------|------|
| RD-001-005 | Haskell Inference MCP | FUTURE | [RD-HASKELL-MCP.md](rd/RD-HASKELL-MCP.md) |

---

## Agent Framework Research (2024-12-31)

| ID | Task | Status | Priority | Reference |
|----|------|--------|----------|-----------|
| AGENT-FW-001 | Review open-source agentic AI frameworks comparison | 📋 TODO | HIGH | [Medium Article](https://medium.com/data-science-collective/agentic-ai-comparing-new-open-source-frameworks-21ec676732df) |
| AGENT-FW-002 | Evaluate alternatives to Agno (CrewAI, AutoGen, LangGraph) | 📋 TODO | MEDIUM | AGENT-FW-001 |
| AGENT-FW-003 | Document framework selection criteria for sim-ai | 📋 TODO | MEDIUM | DECISION-003 |

### Research Context
- **Source:** User-provided Medium article comparing open-source agentic frameworks
- **Relevance:** Evaluate if current Agno framework is optimal or if migration warranted
- **Related Gaps:** GAP-AGENT-010 through GAP-AGENT-014 (agent orchestration)
- **Strategic Vision:** [ROADMAP.md](../../ROADMAP.md) - 5-phase platform evolution (Foundation → Knowledge → Simplify → Differentiate → Scale)

---

## Workflow & Memory R&D (2024-12-31)

| ID | Task | Status | Priority | GAP Reference |
|----|------|--------|----------|---------------|
| WF-001 | Implement governance_health auto-call at session start | ✅ DONE | CRITICAL | GAP-MCP-003 |
| WF-002 | Add save prompts before major transitions | ✅ DONE | HIGH | GAP-WORKFLOW-002 |
| WF-003 | Implement context limit detection for proactive saves | 📋 TODO | HIGH | GAP-WORKFLOW-002 |
| WF-004 | Auto-save session context to claude-mem before restart | 📋 TODO | HIGH | GAP-WORKFLOW-001 |
| WF-005 | Ollama memory optimization for laptop DEV workflow | ⏳ ANALYSIS | MEDIUM | GAP-INFRA-006 |

### Completed 2024-12-31

**WF-001 (GAP-MCP-003):** Updated RULE-021 Level 2 with mandatory `governance_health` call
- Added enforcement language to RULE-021 directive
- Level 2 now explicitly requires: `CALL governance_health tool` before task execution
- If unhealthy: NOTIFY user, PROVIDE recovery command, WAIT for acknowledgment

**WF-002 (GAP-WORKFLOW-002):** Updated RULE-024 with save prompt triggers
- Added "Save Prompts Before Transitions" table to RULE-024
- Triggers: restart request, context limit, long pause, milestone completion
- Integration with `/save` and `/remember` skills

### Pending Implementation

**WF-003:** Context limit detection requires monitoring conversation token count
**WF-004:** Requires hook into Claude Code session lifecycle
**WF-005:** Options documented in GAP-INFRA-006 - recommend disabling Ollama in DEV profile

### Related Rules
- RULE-021: MCP Healthcheck Protocol (Level 2 enforcement)
- RULE-024: AMNESIA Protocol (save prompts, recovery)
- RULE-001: Session Evidence Logging

---

## MCP Tooling Efficiency R&D

| ID | Task | Status | Priority |
|----|------|--------|----------|
| TOOL-001 | llm-sandbox usage audit | 📋 TODO | HIGH |
| TOOL-002 | MCP call frequency analysis | 📋 TODO | MEDIUM |
| TOOL-003 | Playwright MCP heuristic catalog | 📋 TODO | HIGH |
| TOOL-004 | PowerShell MCP use cases | 📋 TODO | LOW |
| TOOL-005 | Desktop-Commander vs filesystem MCP | 📋 TODO | LOW |

---

## Document Management MCP R&D

| ID | Task | Status | Priority |
|----|------|--------|----------|
| DOC-001 | TypeDB→Document sync architecture | ⏳ PARTIAL | HIGH |
| DOC-002 | Document Management MCP design | ✅ DONE | HIGH |
| DOC-003 | Cross-system agent integration | 📋 TODO | HIGH |
| DOC-004 | Document version tracking in TypeDB | 📋 TODO | MEDIUM |
| DOC-005 | Evidence folder structure protocol | 📋 TODO | HIGH |

---

## Deferred Items

| Item | Status | Notes |
|------|--------|-------|
| Mem0 / OpenMemory MCP | ⏸️ DEFERRED | Superseded by TypeDB |
| Replace Agno with Memory MCP | ⏸️ DEFERRED | Pending TypeDB outcome |
| Custom Session/Memory UI | ⏸️ DEFERRED | After TypeDB validation |
| MCP-Monitor | LOW | Nice-to-have |
| AnythingLLM | LOW | Evaluate later |

---

## TypeDB Document Tracking (P10.7)

Documents in this backlog are tracked in TypeDB using the `document` entity:

```typeql
match
  $d isa document,
    has document-path "docs/backlog/R&D-BACKLOG.md",
    has document-type "markdown";
get $d;
```

### Referenced Documents (for TypeDB sync)

| Path | Type | Last Updated |
|------|------|--------------|
| ROADMAP.md | strategic-vision | 2024-12-31 |
| docs/backlog/R&D-BACKLOG.md | root-toc | 2024-12-31 |
| docs/backlog/phases/PHASE-10.md | phase | 2024-12-27 |
| docs/backlog/phases/PHASE-11.md | phase | 2024-12-27 |
| docs/backlog/phases/PHASE-12.md | phase | 2024-12-31 |
| docs/backlog/rd/RD-AGENT-ORCHESTRATION.md | rd-task | 2024-12-27 |
| docs/backlog/rd/RD-KANREN-CONTEXT.md | rd-task | 2024-12-27 |
| docs/backlog/rd/RD-HASKELL-MCP.md | rd-task | 2024-12-27 |
| docs/backlog/rd/RD-FRANKEL-HASH.md | rd-task | 2024-12-27 |
| docs/backlog/rd/RD-TESTING-STRATEGY.md | rd-task | 2024-12-27 |

---

## Cross-Workspace Tools Captured

**Source:** [CROSS-WORKSPACE-WISDOM.md](../CROSS-WORKSPACE-WISDOM.md)

### From local-gai

| Tool | Purpose |
|------|---------|
| **EBMSF** | MCP selection scoring |
| **DSM Tracker** | Cycle evidence automation |
| **Docker Wrapper** | MCP dependency auto-start |
| **Pydantic Tools** | Type-safe MCP tools |
| **LangGraph Workflow** | State machine patterns |

### From agno-agi

| Tool | Purpose |
|------|---------|
| **agents.yaml** | Agent config template |
| **playground.py** | Agno agent setup |
| **docker-compose** | Cluster template |

---

## Strategy Cycle End Directives

See: [STRATEGY-CYCLE-DIRECTIVES.md](../STRATEGY-CYCLE-DIRECTIVES.md) (to be extracted)

---

*R&D tracking per RULE-010: Evidence-Based Wisdom*
*Document pattern: Table-of-Contents per user directive (2024-12-27)*
