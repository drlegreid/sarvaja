# Sim.ai Platform Strategy

**Version:** 1.0 | **Updated:** 2026-01-10 | **Status:** Active

## Quick Reference

| What | Where |
|------|-------|
| Current Tasks | [TODO.md](../TODO.md) |
| Gap Tracking | [gaps/GAP-INDEX.md](gaps/GAP-INDEX.md) |
| Rules Reference | [RULES-DIRECTIVES.md](RULES-DIRECTIVES.md) |
| R&D Backlog | [backlog/R&D-BACKLOG.md](backlog/R&D-BACKLOG.md) |
| DevOps Guide | [DEVOPS.md](DEVOPS.md) |

---

## Platform Vision

**Sim.ai** is a multi-agent governance platform combining:
- **TypeDB** (1729) - Rule inference and entity relationships
- **ChromaDB** (8001) - Semantic search and embeddings
- **LiteLLM** (4000) - Multi-provider LLM gateway
- **Trame Dashboard** (8081) - Python-first UI

### Core Principles

1. **TypeDB-First** (DECISION-003): Governance rules stored in TypeDB with inference
2. **Evidence-Driven** (RULE-001): All sessions generate evidence artifacts
3. **MCP Integration** (RULE-036): 4-server split for modularity
4. **Incremental Progress** (RULE-031): Small changes, continuous testing

---

## Strategic Decisions

| ID | Decision | Impact |
|----|----------|--------|
| DECISION-003 | TypeDB for governance | 40 rules with inference |
| DECISION-005 | Memory Consolidation | claude-mem + TypeDB sync |
| DECISION-006 | Portable MCP Patterns | Cross-environment config |

> Full decisions: [evidence/DECISION-*.md](../evidence/)

---

## Current Phase: Maintenance & Gap Resolution

**Completed Phases:**
- Phase 1-9: Core Platform (TypeDB, MCP, UI, E2E)
- Phase 10: Architecture Debt
- Phase 11: Data Integrity
- Phase 12: Agent Orchestration

**Current Focus:**
- Gap resolution (41 OPEN, 143 RESOLVED)
- UI polish and testing
- MCP stability improvements

---

## Key Workflows

### Session Start Protocol
```
1. governance_health()           → Verify services
2. governance_get_backlog(10)    → Load prioritized gaps
3. Load to Claude Code todo      → Track progress
```

### Deep Sleep Protocol (DSP) - RULE-012
```
AUDIT → HYPOTHESIZE → MEASURE → OPTIMIZE → VALIDATE → DREAM → REPORT
```

Use DSP for backlog hygiene at:
- Session end (quick audit)
- Weekly milestones (full hygiene)
- Pre-release (deep review)

### Context Recovery (RULE-024)
```
1. Read CLAUDE.md               → Rules reference
2. governance_health()          → Verify services
3. governance_query_rules()     → Load critical rules
4. Read TODO.md                 → Current tasks
5. Read gaps/GAP-INDEX.md       → Open gaps
```

---

## Architecture Overview

```
Claude Code Host                    Podman Stack (5 containers)
├── governance-core (Rules)         ├── Dashboard :8081
├── governance-agents (Trust)       ├── LiteLLM :4000
├── governance-sessions (DSM)       ├── Ollama :11434
└── governance-tasks (Gaps)         ├── ChromaDB :8001
         ↓                          └── TypeDB :1729 (40 rules)
    MCP → TypeDB + ChromaDB
```

---

## Testing Strategy

| Level | What | Command |
|-------|------|---------|
| Unit | Python tests | `pytest tests/ -v` |
| E2E | Robot + Playwright | `robot tests/e2e/` |
| Exploratory | SFDIPOT+CRUCSS | [tests/heuristics/](../tests/heuristics/) |

> Per RULE-023: Tests must run on real services, not mocks

---

## R&D Items

| ID | Topic | Status |
|----|-------|--------|
| RD-INTENT | Session intent reconciliation | Phase 1-3 done |
| RD-INFRA | Infrastructure health backend | DONE |
| RD-WORKFLOW | Agentic workflow integrity | TODO |

> Full backlog: [R&D-BACKLOG.md](backlog/R&D-BACKLOG.md)

---

## Gap Priorities

| Priority | Count | Focus |
|----------|-------|-------|
| CRITICAL | 0 | All resolved |
| HIGH | 3 | Workflow improvements |
| MEDIUM | ~35 | UI polish, tooling |
| LOW | ~6 | Minor items |

> Use `governance_get_backlog()` for current list

---

## Technology Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Database | TypeDB | Inference engine |
| Search | ChromaDB | Vector embeddings |
| UI | Trame + Vuetify | Python-first |
| LLM | LiteLLM | Multi-provider |
| Agents | Agno | TypeDB integration |
| Container | Podman | Rootless containers |

---

## Related Documents

| Category | Documents |
|----------|-----------|
| Strategic Vision | [STRATEGIC-VISION-2024-12-24.md](STRATEGIC-VISION-2024-12-24.md) |
| Rules | [rules/RULES-GOVERNANCE.md](rules/RULES-GOVERNANCE.md), [rules/RULES-TECHNICAL.md](rules/RULES-TECHNICAL.md) |
| Testing | [backlog/rd/RD-TESTING-STRATEGY.md](backlog/rd/RD-TESTING-STRATEGY.md) |
| Agent Workspaces | [architecture/AGENT-WORKSPACES.md](architecture/AGENT-WORKSPACES.md) |

---

*Per RULE-001: Session Evidence Logging*
*Per GAP-015: Consolidated strategy document*
