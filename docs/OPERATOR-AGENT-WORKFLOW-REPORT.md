# Operator & Agent Workflow Report

**Date:** 2024-12-27
**Session:** Backlog Processing Sprint
**Status:** COMPLETE

---

## Executive Summary

This report documents the operator journey, agent work pickup mechanisms, responsibilities, dependencies, and use cases for the Sim.ai governance platform.

---

## 1. Operator Journey Workflow

### 1.1 Session Start Protocol

```
┌─────────────────────────────────────────────────────────────────────┐
│                     OPERATOR SESSION WORKFLOW                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. START SESSION                                                    │
│     └─→ Claude Code connects to workspace                           │
│     └─→ Read CLAUDE.md for project context                          │
│     └─→ Read TODO.md for current tasks                              │
│     └─→ Check GAP-INDEX.md for open issues                          │
│                                                                      │
│  2. CONTEXT RECOVERY (Per RULE-024 AMNESIA Protocol)                │
│     └─→ Query claude-mem for project memories                       │
│     └─→ Load last session evidence                                  │
│     └─→ Review recent decisions                                     │
│                                                                      │
│  3. TASK EXECUTION                                                   │
│     └─→ Select task from TODO.md/TypeDB backlog                     │
│     └─→ Create TodoWrite tracking                                   │
│     └─→ Implement with TDD pattern                                  │
│     └─→ Update gaps discovered                                      │
│                                                                      │
│  4. SESSION END (Per RULE-012 DSP)                                  │
│     └─→ Document decisions made                                     │
│     └─→ Update task status in TypeDB                                │
│     └─→ Save session evidence                                       │
│     └─→ Sync to claude-mem for persistence                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Governance MCP Integration

| Tool Category | MCP Tools | Purpose |
|--------------|-----------|---------|
| **Rules** | governance_query_rules, governance_get_rule, governance_create_rule | Rule management |
| **Tasks** | governance_list_all_tasks, governance_create_task, governance_get_task | Task lifecycle |
| **Agents** | governance_list_agents, governance_create_agent, governance_get_trust_score | Agent registry |
| **Sessions** | session_start, session_decision, session_task, session_end | Session tracking |
| **Evidence** | governance_evidence_search, governance_list_sessions | Knowledge retrieval |
| **Documents** | governance_get_document, governance_get_rule_document | File content access |

---

## 2. Agent Work Pickup Mechanism

### 2.1 Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AGENT TASK PICKUP ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────┐     ┌──────────────────┐     ┌─────────────┐  │
│  │   Governance     │     │   REST API       │     │  TypeDB     │  │
│  │   Dashboard UI   │────▶│   (port 8082)    │────▶│  (port 1729)│  │
│  │   (port 8081)    │     │                  │     │             │  │
│  └────────┬─────────┘     └────────┬─────────┘     └─────────────┘  │
│           │                        │                                 │
│           │  Views tasks           │  Queries                        │
│           │                        │                                 │
│           ▼                        ▼                                 │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Task Backlog Queue                         │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐             │   │
│  │  │ TODO    │ │ pending │ │ TODO    │ │ pending │             │   │
│  │  │ P10.7   │ │ TEST-01 │ │ P10.9   │ │ TEST-02 │             │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘             │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│                              │  GET /api/tasks/available             │
│                              ▼                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    TaskBacklogAgent                           │   │
│  │  (agent/sync_agent.py:375)                                    │   │
│  │                                                                │   │
│  │  Methods:                                                      │   │
│  │  - get_available_tasks() → GET /api/tasks/available           │   │
│  │  - claim_task(id)        → PUT /api/tasks/{id}/claim          │   │
│  │  - complete_task(exec)   → PUT /api/tasks/{id}/complete       │   │
│  │  - run_loop()            → Continuous polling (30s interval)  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Task Lifecycle

| Stage | API Endpoint | Status Change | Evidence |
|-------|--------------|---------------|----------|
| **Available** | `GET /api/tasks/available` | status in (TODO, pending) | - |
| **Claimed** | `PUT /api/tasks/{id}/claim?agent_id=X` | TODO → IN_PROGRESS | agent_id set |
| **Executing** | (internal agent processing) | IN_PROGRESS | - |
| **Completed** | `PUT /api/tasks/{id}/complete?evidence=Y` | IN_PROGRESS → DONE | evidence recorded |
| **Failed** | (error handling) | IN_PROGRESS → BLOCKED | error in evidence |

### 2.3 Status Filtering (Fixed 2024-12-27)

```python
# governance/api.py - Accept both conventions
AVAILABLE_STATUSES = {"TODO", "pending", "todo", "PENDING"}
CLAIMABLE_STATUSES = {"TODO", "pending", "todo", "PENDING"}
```

---

## 3. Agent Responsibilities

### 3.1 Agent Registry (TypeDB)

| Agent ID | Name | Type | Trust Score | Responsibilities |
|----------|------|------|-------------|------------------|
| AGENT-001 | Claude Code R&D | claude-code | 0.95 | Development, code review, task execution |
| AGENT-002 | Docker Production Agent | docker-agent | 0.80 | Container management, deployment |
| AGENT-003 | Sync Protocol Agent | sync-agent | 0.75 | Data synchronization, backlog polling |
| TEST-AGENT-001 | Test Agent | test-agent | 0.80 | Testing, validation |

### 3.2 Trust Scoring (RULE-011)

```
Trust Formula:
  (Compliance × 0.4) + (Accuracy × 0.3) + (Consistency × 0.2) + (Tenure × 0.1)

Where:
  - Compliance: % of rules followed
  - Accuracy: % of tasks completed correctly
  - Consistency: Variance in performance
  - Tenure: Days active (capped at 1.0)
```

### 3.3 Planned Agents (ORCH-001-007)

| Agent | Role | Priority | Status |
|-------|------|----------|--------|
| Orchestrator Agent | Task dispatch, priority sequencing | CRITICAL | TODO |
| Research Agent | Context gathering, knowledge retrieval | HIGH | TODO |
| Coding Agent | Implementation, code generation | HIGH | Exists (Claude Code) |
| Rules Curator Agent | Rule quality, conflict resolution | HIGH | TODO |

---

## 4. Dependencies

### 4.1 Infrastructure Dependencies

```
┌─────────────────────────────────────────────────────────────────────┐
│                      DEPENDENCY GRAPH                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  TypeDB (1729)                                                       │
│     │                                                                │
│     ├──▶ Governance MCP Server (stdio)                              │
│     │       └──▶ 40+ MCP tools                                      │
│     │                                                                │
│     ├──▶ REST API (8082)                                            │
│     │       └──▶ 23 endpoints                                       │
│     │       └──▶ Task lifecycle management                          │
│     │                                                                │
│     └──▶ Governance Dashboard (8081)                                │
│             └──▶ Trame UI components                                │
│             └──▶ Agent Task Backlog view                            │
│                                                                      │
│  ChromaDB (8001)                                                     │
│     └──▶ claude-mem MCP Server                                      │
│             └──▶ Session memory persistence                         │
│                                                                      │
│  LiteLLM (4000)                                                      │
│     └──▶ Model routing (Ollama, OpenAI, etc.)                       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Data Dependencies

| Entity | Depends On | Used By |
|--------|------------|---------|
| Task | Rule (implements-rule), Session (completed-in) | Agent execution, Evidence |
| Session | Evidence (has-evidence), Rule (applied-rule) | Task completion, Memory |
| Agent | Task (claims), Trust metrics | Orchestration, Voting |
| Decision | Rule (affects), Session (made-in) | Task creation, Priority |
| Evidence | Session (belongs-to), Task (supports) | Audit trail, Recovery |

---

## 5. Use Cases

### 5.1 Primary Use Cases

#### UC-1: Operator Task Execution
```
Actor: Human Operator (via Claude Code)
Precondition: Session started, context recovered
Flow:
  1. Review TODO.md for prioritized tasks
  2. Select task from backlog
  3. Implement with TDD pattern
  4. Update TypeDB task status
  5. Document session evidence
Postcondition: Task completed, evidence saved
```

#### UC-2: Agent Automatic Task Pickup
```
Actor: TaskBacklogAgent
Precondition: API running, tasks available
Flow:
  1. Poll GET /api/tasks/available every 30s
  2. Select highest priority task
  3. Claim task via PUT /api/tasks/{id}/claim
  4. Execute task using task_handler
  5. Complete task via PUT /api/tasks/{id}/complete
Postcondition: Task marked DONE, evidence recorded
```

#### UC-3: Context Recovery (AMNESIA Protocol)
```
Actor: Claude Code (new session)
Precondition: Previous session exists
Flow:
  1. Read CLAUDE.md for project context
  2. Query claude-mem for recent memories
  3. Load last session evidence from TypeDB
  4. Review active tasks and decisions
  5. Continue work from last checkpoint
Postcondition: Context fully recovered
```

#### UC-4: Rule Conflict Resolution
```
Actor: Rules Curator Agent (future)
Precondition: Conflict detected via governance_find_conflicts
Flow:
  1. Identify conflicting rules
  2. Analyze semantic overlap
  3. Propose resolution (merge, deprecate, clarify)
  4. Submit proposal via governance_propose_rule
  5. Collect votes from trusted agents
  6. Escalate to human if threshold not met
Postcondition: Conflict resolved or escalated
```

### 5.2 Edge Cases & Error Handling

| Scenario | Handling |
|----------|----------|
| TypeDB unavailable | Fall back to in-memory store |
| Task already claimed | Return 409 Conflict |
| Agent trust < 0.5 | Reduce vote weight |
| Session evidence missing | Query claude-mem for recovery |
| Rule conflict detected | Trigger escalation workflow |

---

## 6. Session Accomplishments

### 6.1 Completed Tasks

| Task | Description | Evidence |
|------|-------------|----------|
| Document MCP (P10.8) | 4 tools: get_document, list_documents, get_rule_document, get_task_document | governance/mcp_tools/evidence.py |
| Agent Task Backlog Fix | Status filtering for TODO and pending | governance/api.py, governance/client.py |
| Test Fix | description→body parameter mapping | governance/mcp_server.py |
| P10.7 Entity Hierarchy | Decision kept separate from Task | docs/P10.7-ENTITY-HIERARCHY-REVIEW.md |
| P10.9 Task-Session Linkage | Infrastructure verified, 18% coverage | docs/P10.9-TASK-SESSION-LINKAGE.md |
| GAP Documentation | 11 new gaps added, requirements enriched | docs/gaps/GAP-INDEX.md |
| ORCH-001-007 Tasks | Agent orchestration requirements | docs/backlog/R&D-BACKLOG.md |

### 6.2 Test Results

```
tests/test_mcp_tasks.py: 14 passed
Full suite: 827 passed, 28 TDD stubs (future work)
```

### 6.3 Open Items (Deferred)

| Item | Priority | Reason |
|------|----------|--------|
| P11.5 Evidence Attachments | P2 | UI file picker - not blocking |
| P11.6 File Reorganization | P2 | Files properly placed in results/ |
| ORCH-001-007 | CRITICAL | Agent orchestration - future phase |
| Haskell tasks | On Hold | Per user directive |

---

## 7. Recommendations

### 7.1 Immediate Actions
1. **Start API server**: `python governance/api.py` on port 8082
2. **Start Dashboard**: `python agent/run_governance_server.py` on port 8081
3. **Run TaskBacklogAgent**: `python agent/sync_agent.py --run`

### 7.2 Near-term (P1)
1. Implement Orchestrator Agent (ORCH-001)
2. Add task polling/subscription (ORCH-002)
3. Build Agent Chat UI (ORCH-006)

### 7.3 Medium-term (P2)
1. Implement Research Agent for context delegation
2. Add Rules Curator Agent for governance quality
3. Complete session evidence coverage to 100%

---

## 8. Conclusion

The Sim.ai governance platform has:
- **40+ MCP tools** for full governance lifecycle
- **TypeDB-first architecture** with in-memory fallback
- **Task lifecycle management** via REST API
- **Agent trust scoring** per RULE-011
- **Session evidence tracking** with claude-mem integration

**Platform Status:** Ready for agent orchestration phase (ORCH-001-007).

---

*Per RULE-012 DSP: Session evidence documented*
*Per RULE-024 AMNESIA: Recovery-friendly format*
