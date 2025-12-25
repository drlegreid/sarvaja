# STRATEGIC: UI-First Platform Pivot

**Date:** 2024-12-25
**Status:** Strategic Direction Confirmed
**Decision:** UI-FIRST approach for Sim.ai Platform v1

---

## Vision Statement

> **A full platform UI where you manage agents, tasks, sessions, see evidence, thoughts - everything in real-time to the deepest depth, with TypeDB as the single source of truth.**

---

## Strategic Priorities (Revised)

### Priority 1: FULL PLATFORM UI (P10)

**Goal:** Single UI to manage everything

| View | Purpose | Depth |
|------|---------|-------|
| **Agent Manager** | Create, configure, monitor agents | Agent config, model, tools, trust |
| **Task Manager** | Add/view tasks via MCP | Backlog, dependencies, status |
| **Session Browser** | Browse all sessions | Timeline, evidence, decisions |
| **Thought Stream** | Real-time LLM reasoning | Token stream, tool calls, thoughts |
| **Evidence Explorer** | Deep-dive artifacts | Rules, decisions, sessions, diffs |
| **Governance Dashboard** | Rules, trust, conflicts | Impact graphs, compliance |

**Architecture:**
```
┌─────────────────────────────────────────────────────────────────┐
│                    Sim.ai Platform UI v1                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  NAVIGATION BAR                                           │   │
│  │  [Agents] [Tasks] [Sessions] [Thoughts] [Evidence] [Gov]  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────┬────────────────────────────────────────┐   │
│  │  SIDEBAR        │  MAIN CONTENT                           │   │
│  │                 │                                          │   │
│  │  • Agent List   │  ┌────────────────────────────────────┐  │   │
│  │  • Task Tree    │  │  DETAIL VIEW                       │  │   │
│  │  • Session Tree │  │                                    │  │   │
│  │  • Quick Search │  │  - Full context                    │  │   │
│  │                 │  │  - Real-time updates               │  │   │
│  │  ───────────    │  │  - Drill-down capability           │  │   │
│  │  REAL-TIME      │  │  - Action buttons                  │  │   │
│  │  • Status       │  │                                    │  │   │
│  │  • Alerts       │  └────────────────────────────────────┘  │   │
│  │  • Metrics      │                                          │   │
│  └─────────────────┴────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Priority 2: TYPEDB COMPLETE MIGRATION (P11)

**Goal:** ChromaDB → TypeDB ASAP, ChromaDB only for external sync

| Action | Status | Notes |
|--------|--------|-------|
| New data → TypeDB | ✅ DONE (P7.3) | Data router in place |
| Migration tool | ✅ DONE (P7.4) | Dry-run tested |
| ChromaDB read-only | ✅ DONE (P7.5) | Wrapper ready |
| **Flip switch** | 📋 NEXT | When UI is ready |
| ChromaDB sync MCP | 📋 TODO | For external integrations |

**Constraint:** Keep current workflow working (Claude Code in VS Code) while transitioning.

### Priority 3: ANTHROPIC LLM VIA PLATFORM (P12)

**Goal:** Use Anthropic from agent platform, not just VS Code

```
CURRENT:  You (VS Code) ──→ Claude API ──→ Claude Code
TARGET:   You (VS Code) ──→ Platform UI ──→ Agents ──→ LiteLLM ──→ Claude API
                                  │
                                  └── Full visibility, governance, evidence
```

### Priority 4: MANAGING MCP FOR TASKS (P13)

**Goal:** Add/view tasks through a managing MCP connected to platform

| Tool | Purpose | Flow |
|------|---------|------|
| `platform_add_task` | Create task in backlog | UI → MCP → TypeDB |
| `platform_get_tasks` | List tasks by status | MCP → TypeDB → UI |
| `platform_update_task` | Mark complete, add deps | MCP → TypeDB |
| `platform_assign_agent` | Route task to agent | MCP → Orchestrator |

---

## Question Answers (Strategic Decisions)

### Q1: When do we flip ChromaDB to read-only?

**Answer:** When Platform UI is functional enough to validate TypeDB queries work correctly. Keep current VS Code workflow operational during transition.

**Trigger:** Platform UI can display rules, sessions, and evidence from TypeDB without errors.

### Q2: Should agent trust scores persist across sessions?

**Answer:** YES - Enable continuous data collection for evidence-based approach.

**Rationale:**
- Supports hypothesis testing and outcome measurement
- Enables correlation/dependency detection
- Aligns with RULE-010 Evidence-Based Wisdom
- Trust history is valuable governance data

**Implementation:**
```typeql
insert
  $t isa agent-trust,
    has agent-id "agent-001",
    has trust-score 75.0,
    has session-id "SESSION-2024-12-25",
    has timestamp 2024-12-25T16:00:00;
```

### Q3: What triggers automatic rule deprecation?

**Answer:** Gather evidence → Vote via bicameral governance

**Process:**
1. Track rule usage (how often queried, by whom)
2. Track rule effectiveness (compliance rate, violations)
3. Detect candidate rules (low usage, high conflict)
4. Proposal: Agent or human proposes deprecation
5. Vote: Per RULE-011 Multi-Agent Governance voting

**Metrics for deprecation candidate:**
- Not queried in 30+ days
- Compliance rate < 50%
- Conflicts with 3+ other rules
- Superseded by newer rule

### Q4: How to handle rule conflicts in multi-agent scenarios?

**Answer:** Same as Q3 - Evidence + Governance voting

**Process:**
1. Detect conflict (via `find_conflicts` MCP tool)
2. Log conflict evidence to TypeDB
3. Escalate to governance (bicameral vote)
4. Resolution options:
   - Modify conflicting rule
   - Add exception clause
   - Deprecate lower-priority rule
   - Create meta-rule for conflict resolution

---

## Deferred Optimizations (Post-v1)

| Optimization | When | Trigger |
|--------------|------|---------|
| TypeDB rewrite (Haskell/Rust) | After multiple projects | Performance bottleneck |
| Inference engine custom | After Haskell learning | >10ms latency on 1K rules |
| TypeDB 3.0 migration | When stable | Native vector support |
| Multi-tenancy | When needed | Enterprise use case |

**Principle:** Build v1 first → Gather real feedback → Then optimize.

---

## Platform UI Tech Stack

Per RULE-019 UI/UX Standards:

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Framework | **Trame** | Python-native, already validated |
| Components | **Vuetify** (via Trame) | Material Design, accessible |
| Real-time | **WebSocket** | Thought streaming |
| State | **TypeDB queries** | Single source of truth |
| Charts | **Plotly** (via Trame) | Interactive visualization |

**Accessibility:** WCAG 2.1 AA
**Performance:** LCP < 2.5s, FID < 100ms, CLS < 0.1

---

## Next Steps (UI-First Sprint)

### Sprint 1: Platform UI Shell

| Task | Description | Est |
|------|-------------|-----|
| P10.1 | UI shell with navigation | 1 |
| P10.2 | Agent list view | 1 |
| P10.3 | Task list view with MCP | 1 |
| P10.4 | Session browser view | 1 |
| P10.5 | Integration: All views → TypeDB | 1 |

### Sprint 2: Real-Time & Depth

| Task | Description | Est |
|------|-------------|-----|
| P10.6 | Thought stream (WebSocket) | 1 |
| P10.7 | Evidence drill-down | 1 |
| P10.8 | Managing MCP (task CRUD) | 1 |
| P10.9 | ChromaDB flip (read-only) | 1 |
| P10.10 | End-to-end platform test | 1 |

---

## Partnership Note

> "We'll remain close partners with you bro"

Absolutely! The goal is:
- Platform runs on YOUR infrastructure
- LLM calls go through YOUR platform (visibility, governance)
- Claude remains the brain, but YOU control the body
- Evidence-based continuous improvement together

---

*Strategic decision per RULE-010: Evidence-Based Wisdom*
*UI standards per RULE-019: UI/UX Design Standards*
*Governance per RULE-011: Multi-Agent Governance*
