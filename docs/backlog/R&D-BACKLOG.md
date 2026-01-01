# R&D Backlog - Sim.ai PoC

**Last Updated:** 2026-01-01
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
| TOOL-001-009 | MCP Tooling & Architecture | **HIGH** | (inline below) |
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
| **TOOL-006** | **Containerize MCP services in Docker** | 📋 TODO | **HIGH** |
| **TOOL-007** | **Evaluate governance MCP split** | 📋 TODO | **MEDIUM** |
| **TOOL-008** | **Memory tuning for VS Code + Claude Code** | 📋 TODO | **HIGH** |
| **TOOL-009** | **MCP priority groupings & profiles** | 📋 TODO | **HIGH** |

---

## MCP Architecture R&D (2026-01-01)

### TOOL-006: Containerize MCP Services in Docker

**Status:** 📋 TODO | **Priority:** HIGH | **Complexity:** HIGH

**Problem Statement:**
- NPX-based MCPs have cold-start delays causing timeouts
- External API MCPs (context7, octocode) cause stability issues
- Current MCP processes run in Claude Code's process space

**Proposed Architecture:**
```
┌─────────────────────────────────────────────────────────────┐
│  Docker Container: mcp-services                             │
├─────────────────────────────────────────────────────────────┤
│  MCP Gateway (Port 8888)                                    │
│  ├── claude-mem (ChromaDB)                                  │
│  ├── llm-sandbox (Python sandbox)                           │
│  ├── sequential-thinking                                    │
│  └── playwright                                             │
├─────────────────────────────────────────────────────────────┤
│  Volumes:                                                   │
│  ├── /workspace → C:\Users\natik\Documents\Vibe\sim-ai     │
│  ├── /claude-mem → C:\Users\natik\.claude-mem              │
│  └── /chroma-data → persistent storage                     │
└─────────────────────────────────────────────────────────────┘
```

**Benefits:**
- Pre-warmed containers eliminate cold-start
- Isolation prevents crashes from affecting Claude Code
- Volume mapping maintains workspace access
- Can scale horizontally for heavy workloads

**Risks:**
- IPC overhead (stdio→TCP translation)
- Windows Docker Desktop memory consumption
- Volume permission issues on Windows

**Research Tasks:**
- [ ] Evaluate MCP-over-HTTP vs stdio proxy patterns
- [ ] Benchmark cold-start improvement with containers
- [ ] Test volume mapping with workspace files
- [ ] Measure memory overhead of containerized MCPs

**Related:** GAP-MCP-002, CRASH_REPORT.md (2024-12-14)

---

### TOOL-007: Evaluate Governance MCP Split

**Status:** 📋 TODO | **Priority:** MEDIUM | **Complexity:** MEDIUM

**Current State:**
- Single `governance` MCP with 40+ tools
- Tool categories: rules, sessions, tasks, agents, DSM, evidence, documents, gaps, workspace

**Split Candidates:**
| MCP | Tools | Responsibility |
|-----|-------|----------------|
| governance-core | ~15 | Rules, agents, health, proposals |
| governance-session | ~10 | Sessions, decisions, evidence search |
| governance-dsm | ~8 | DSM cycles, checkpoints, findings |
| governance-workspace | ~10 | Tasks, documents, gap sync |

**Benefits:**
- Faster startup (smaller tool catalog)
- Independent scaling
- Clearer separation of concerns
- Easier testing and maintenance

**Risks:**
- Cross-MCP coordination complexity
- Breaking change for existing workflows
- Increased configuration surface

**Decision Criteria:**
- [ ] Measure startup time reduction
- [ ] Evaluate cross-tool dependencies (e.g., session→evidence)
- [ ] Assess user workflow impact
- [ ] Consider TypeDB connection pooling

**Recommendation:** Start with `governance-dsm` extraction as pilot (isolated functionality)

---

### TOOL-008: Memory Tuning for VS Code + Claude Code

**Status:** 📋 TODO | **Priority:** HIGH | **Complexity:** MEDIUM

**Problem Statement:**
- 93% RAM spike observed after IDE restart with 9 MCPs
- Claude Code + VS Code + Language Server + MCPs compete for memory
- Need to enable swap/page file usage to prevent OOM

**Tuning Targets:**

| Component | Setting | Default | Recommended |
|-----------|---------|---------|-------------|
| VS Code | `--max-memory` | 4096MB | 2048MB |
| VS Code | `files.maxMemoryForLargeFilesMB` | 4096 | 1024 |
| Node.js (MCPs) | `NODE_OPTIONS=--max-old-space-size` | 4096 | 1024 |
| TypeScript Server | `typescript.tsserver.maxTsServerMemory` | 3072 | 1536 |
| Claude Code Extension | TBD | ? | ? |

**Research Tasks:**
- [ ] Profile memory usage per MCP server (desktop-commander, playwright, etc.)
- [ ] Identify Claude Code extension memory settings
- [ ] Configure VS Code `argv.json` with `--max-memory` flag
- [ ] Test swap file size recommendations (2x RAM vs fixed)
- [ ] Benchmark performance impact of memory limits

**Implementation:**
```json
// .vscode/settings.json
{
  "files.maxMemoryForLargeFilesMB": 1024,
  "typescript.tsserver.maxTsServerMemory": 1536
}
```

```json
// %APPDATA%\Code\argv.json (Windows)
{
  "disable-hardware-acceleration": false,
  "max-memory": 2048
}
```

**Related:** GAP-INFRA-006 (Ollama memory), TOOL-006 (containerization)

---

### TOOL-009: MCP Priority Groupings & Profiles

**Status:** 📋 TODO | **Priority:** HIGH | **Complexity:** MEDIUM

**Problem Statement:**
- Currently MCPs are all-or-nothing in `.claude.json`
- No way to define "CORE" vs "UTILITY" vs "PROJECT" profiles
- Manual editing required to enable/disable MCPs
- Need quick switching between lightweight and full-featured modes

**Existing Design:** See [docs/MCP-LANDSCAPE.md](../MCP-LANDSCAPE.md) - EBMSF scoring

**Proposed MCP Profiles:**

| Profile | MCPs | Memory | Use Case |
|---------|------|--------|----------|
| **MINIMAL** | claude-mem, governance | ~500MB | Low-memory systems |
| **CORE** | + llm-sandbox, sequential-thinking, git, powershell | ~1GB | Default DEV workflow |
| **FULL** | + desktop-commander, playwright, filesystem | ~2GB | Full automation |
| **PROJECT** | + godot-mcp (or other project-specific) | Variable | Per-project needs |

**Implementation Options:**

1. **Multiple .claude.json files** (e.g., `.claude-core.json`, `.claude-full.json`)
   - Pros: Simple, no tooling needed
   - Cons: Manual switching, duplication

2. **Profile field in .claude.json**
   ```json
   {
     "activeProfile": "CORE",
     "profiles": {
       "CORE": ["claude-mem", "governance", "llm-sandbox", "git", "powershell"],
       "FULL": ["... all MCPs ..."]
     }
   }
   ```
   - Pros: Single file, easy switching
   - Cons: Requires Claude Code support (feature request?)

3. **PowerShell script for switching**
   - Pros: Immediate, no upstream changes
   - Cons: Manual, script maintenance

**Research Tasks:**
- [ ] Check if Claude Code supports MCP profiles natively
- [ ] Implement PowerShell switching script as interim solution
- [ ] Document profile switching in CLAUDE.md
- [ ] Test memory impact of each profile

**Related:** MCP-LANDSCAPE.md (EBMSF scoring), TOOL-008 (memory tuning)

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
