# Task Management Architecture Report

**Date:** 2024-12-26
**Requested By:** User (Strategic Backlog Review)
**Status:** ARCHITECTURAL GAP IDENTIFIED

---

## Executive Summary

**User Expectation:** "All entities managed via central TypeDB by means of MCP services"

**Current Reality:** Mixed architecture - some entities in TypeDB, others in-memory.

| Entity | Current Storage | Target Storage | Gap Status |
|--------|-----------------|----------------|------------|
| **Rules** | TypeDB | TypeDB | ✅ Compliant |
| **Decisions** | TypeDB | TypeDB | ✅ Compliant |
| **Tasks** | **In-Memory Dict** | TypeDB | ❌ GAP |
| **Sessions** | **In-Memory Dict** | TypeDB | ❌ GAP |
| **Agents** | **In-Memory Dict** | TypeDB | ❌ GAP |
| **Evidence** | File System | File + TypeDB Links | ⚠️ Partial |

---

## Current Implementation Analysis

### 1. TypeDB-Managed Entities (Compliant)

**Rules and Decisions** are properly stored in TypeDB via `governance/client.py`:

```python
# governance/client.py - TypeDB client methods
class TypeDBClient:
    def create_rule(self, rule_id, name, category, priority, directive, status="DRAFT") -> Rule
    def get_all_rules(self) -> List[Rule]
    def update_rule(self, rule_id, ...) -> Rule
    def delete_rule(self, rule_id, archive=True) -> bool

    def get_all_decisions(self) -> List[Decision]
```

**MCP Tools** properly wrap TypeDB operations:
- `governance_query_rules`
- `governance_get_rule`
- `governance_create_rule`
- `governance_update_rule`
- `governance_delete_rule`

### 2. In-Memory Entities (NON-COMPLIANT)

Found in `governance/api.py`:

```python
# LINE 360 - Tasks stored in memory, lost on restart
_tasks_store: Dict[str, Dict[str, Any]] = {}

# LINE 429 - Sessions stored in memory, lost on restart
_sessions_store: Dict[str, Dict[str, Any]] = {}

# LINE 517 - Agents stored in memory with hardcoded defaults
_agents_store: Dict[str, Dict[str, Any]] = {
    "task-orchestrator": {...},
    "rules-curator": {...},
    ...
}
```

**Problems:**
1. **Data Loss:** Tasks and Sessions lost on API restart
2. **No Persistence:** Agent metrics (tasks_executed, trust_score) not persisted
3. **No MCP Integration:** These entities bypass governance MCP tools
4. **No Inference:** TypeDB inference rules can't apply to in-memory data

---

## Target Architecture (Per R&D Backlog Vision)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Agentic Platform UI/MCP Layer                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   Trame UI      │  │   MCP Tools     │  │   REST API      │             │
│  │   (Dashboard)   │  │   (Claude/LLM)  │  │   (External)    │             │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘             │
│           │                    │                    │                       │
│           └────────────────────┴────────────────────┘                       │
│                                │                                             │
│                    ┌───────────┴───────────┐                                │
│                    │   Governance Layer    │                                │
│                    │   (TypeDB + Hybrid)   │                                │
│                    └───────────┬───────────┘                                │
│                                │                                             │
│  ┌──────────────┬──────────────┼──────────────┬──────────────┐             │
│  │              │              │              │              │              │
│  ▼              ▼              ▼              ▼              ▼              │
│ Rules      Decisions      Sessions      Tasks       Agents                  │
│ (TypeDB)   (TypeDB)       (TypeDB)    (TypeDB)    (TypeDB)                │
│   22         4+           Active       Backlog      5+                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## TypeDB Schema Extensions Required

### Task Entity (New)

```typeql
define
  task sub entity,
    owns task-id @key,
    owns description,
    owns phase,
    owns status,
    owns created-at,
    owns completed-at,
    plays task-assignment:task;

  task-assignment sub relation,
    relates task,
    relates agent;

  # Inference: Auto-complete tasks when all subtasks done
  rule auto-complete-parent-task:
  when {
    $parent isa task, has task-id $parent_id;
    $subtask isa task, has parent-task $parent_id, has status "DONE";
    not { $incomplete isa task, has parent-task $parent_id, has status != "DONE"; };
  } then {
    $parent has status "DONE";
  };
```

### Session Entity (New)

```typeql
define
  session sub entity,
    owns session-id @key,
    owns start-time,
    owns end-time,
    owns status,
    owns agent-id,
    owns tasks-completed,
    plays session-evidence:session;

  session-evidence sub relation,
    relates session,
    relates evidence;
```

### Agent Entity (Extend Existing)

```typeql
define
  agent sub entity,
    owns agent-id @key,
    owns agent-name,
    owns agent-type,
    owns status,
    owns tasks-executed,
    owns trust-score,
    owns last-active,
    plays task-assignment:agent,
    plays session:executor;

  # Inference: Update trust score based on compliance
  rule update-trust-from-compliance:
  when {
    $agent isa agent, has agent-id $id;
    $compliance = count {$task isa task, has status "DONE"; (task: $task, agent: $agent) isa task-assignment;};
    $total = count {(task: $_, agent: $agent) isa task-assignment;};
    $rate = $compliance / $total;
  } then {
    $agent has compliance-rate $rate;
  };
```

---

## MCP Tools Required

| Tool | Purpose | Current | Target |
|------|---------|---------|--------|
| `governance_create_task` | Create task | REST API only | TypeDB + MCP |
| `governance_list_tasks` | List tasks | REST API only | TypeDB + MCP |
| `governance_update_task` | Update task | REST API only | TypeDB + MCP |
| `governance_delete_task` | Delete task | REST API only | TypeDB + MCP |
| `governance_create_session` | Start session | REST API only | TypeDB + MCP |
| `governance_end_session` | End session | REST API only | TypeDB + MCP |
| `governance_list_agents` | List agents | REST API only | TypeDB + MCP |
| `governance_update_agent` | Update agent metrics | REST API only | TypeDB + MCP |

---

## Migration Plan

### Phase 1: Schema Extension (P10.X)
1. Add Task, Session, Agent entities to `governance/schema.tql`
2. Add relationships and inference rules
3. Update schema version

### Phase 2: Client Extension (P10.X)
1. Add TypeDBClient methods for Task/Session/Agent CRUD
2. Add validation (same pattern as Rules)
3. Unit tests for new methods

### Phase 3: MCP Tool Registration (P10.X)
1. Create `governance/mcp_tools/tasks.py`
2. Create `governance/mcp_tools/sessions.py`
3. Create `governance/mcp_tools/agents.py`
4. Register in `governance/mcp_server.py`

### Phase 4: REST API Migration (P10.X)
1. Replace in-memory stores with TypeDB calls
2. Update Pydantic models if needed
3. Maintain backward compatibility

### Phase 5: UI Integration (P10.X)
1. Update Dashboard to use API (already done)
2. Verify data persists across restarts
3. E2E tests for persistence

---

## Gap Summary

| GAP ID | Description | Priority | Resolution |
|--------|-------------|----------|------------|
| GAP-ARCH-001 | Tasks in-memory, not TypeDB | CRITICAL | Migrate to TypeDB |
| GAP-ARCH-002 | Sessions in-memory, not TypeDB | CRITICAL | Migrate to TypeDB |
| GAP-ARCH-003 | Agents in-memory, not TypeDB | HIGH | Migrate to TypeDB |
| GAP-ARCH-004 | No MCP tools for Tasks | HIGH | Create MCP tools |
| GAP-ARCH-005 | No MCP tools for Sessions | HIGH | Create MCP tools |
| GAP-ARCH-006 | No inference for Task/Agent | MEDIUM | Add TypeQL rules |

---

## Recommendation

**Immediate Action:** Add GAP-ARCH-001 through GAP-ARCH-006 to GAP-INDEX.md and prioritize in TODO.md.

**Strategic Decision Required:** Should we migrate Tasks/Sessions/Agents to TypeDB before continuing UI work, or complete UI first then migrate?

**Arguments for Migrate First:**
- Foundation work - everything else builds on solid persistence
- MCP tools enable LLM agents to manage tasks properly
- Inference rules enable smart automation

**Arguments for UI First:**
- Users can see and use the system sooner
- Validates requirements before deep infrastructure work
- In-memory is fine for demo/prototype

---

*Report created per RULE-001 (Session Evidence Logging)*
*Architecture per DECISION-003 (TypeDB-First Strategy)*
