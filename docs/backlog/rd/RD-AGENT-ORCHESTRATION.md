# R&D: Agent Orchestration (ORCH-001 to ORCH-007)

**Status:** ✅ COMPLETE (ORCH-001 ✅, ORCH-002 ✅, ORCH-003 ✅, ORCH-004 ✅, ORCH-005 ✅, ORCH-006 ✅, ORCH-007 ✅)
**Priority:** CRITICAL
**Date:** 2024-12-28

---

## Strategic Goal

Multi-agent task execution with orchestration, delegation, and governance per RULE-011 (Multi-Agent Governance) and RULE-014 (Autonomous Task Sequencing).

---

## Related Gaps

- GAP-AGENT-010 to GAP-AGENT-014
- GAP-UI-CHAT-001 (Agent Chat UI)
- GAP-UI-CHAT-002 (Task Execution Viewer)

---

## Task List

| ID | Task | Status | Priority | Notes |
|----|------|--------|----------|-------|
| ORCH-001 | Orchestration Agent design | ✅ DONE | **CRITICAL** | Researched patterns, see Spike Results below |
| ORCH-002 | Task polling/subscription for agents | ✅ DONE | **CRITICAL** | agent/orchestrator/ - 31 tests passing |
| ORCH-003 | Task claim/lock mechanism | ✅ DONE | HIGH | Included in ORCH-002 (claim_task, release_task) |
| ORCH-004 | Agent delegation protocol | ✅ DONE | HIGH | delegation.py - 35 tests passing |
| ORCH-005 | Rules Curator Agent | ✅ DONE | HIGH | curator_agent.py - 22 tests passing |
| ORCH-006 | Agent Chat UI (GAP-UI-CHAT-001) | ✅ DONE | **CRITICAL** | 33 tests passing |
| ORCH-007 | Task execution viewer (GAP-UI-CHAT-002) | ✅ DONE | HIGH | 26 tests passing |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Agent Orchestration Layer                             │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ Orchestrator│  │ Research    │  │ Coding      │  │ Rules       │   │
│  │ Agent       │  │ Agent       │  │ Agent       │  │ Curator     │   │
│  │ (dispatch)  │  │ (context)   │  │ (impl)      │  │ (governance)│   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘   │
│         │                │                │                │           │
│         └────────────────┴────────────────┴────────────────┘           │
│                                   │                                     │
│         ┌─────────────────────────┴─────────────────────────┐          │
│         │                                                    │          │
│         ▼                                                    ▼          │
│  ┌───────────────┐                              ┌───────────────────┐  │
│  │ TypeDB Task   │                              │ Agent Chat UI     │  │
│  │ Backlog       │                              │ (command/view)    │  │
│  │ (priority Q)  │                              │                   │  │
│  └───────────────┘                              └───────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Delegation Flow

```
User Command → Orchestrator Agent
                    │
                    ├── Simple Task? → Execute directly
                    │
                    ├── Needs context? → Delegate to Research Agent
                    │                         │
                    │                         └── Context gathered → Return to Orchestrator
                    │
                    ├── Code task? → Delegate to Coding Agent
                    │
                    └── Rule issue? → Rules Curator Agent → Escalate if ambiguous
```

---

## Agent Registry (Current)

| Agent ID | Name | Type | Trust Score | Responsibilities |
|----------|------|------|-------------|------------------|
| AGENT-001 | Claude Code R&D | claude-code | 0.95 | Development, code review |
| AGENT-002 | Docker Production Agent | docker-agent | 0.80 | Container management |
| AGENT-003 | Sync Protocol Agent | sync-agent | 0.75 | Data synchronization |
| TEST-AGENT-001 | Test Agent | test-agent | 0.80 | Testing, validation |

---

## Planned Agents

| Agent | Role | Priority | Status |
|-------|------|----------|--------|
| Orchestrator Agent | Task dispatch, priority sequencing | CRITICAL | TODO |
| Research Agent | Context gathering, knowledge retrieval | HIGH | TODO |
| Coding Agent | Implementation, code generation | HIGH | Exists (Claude Code) |
| Rules Curator Agent | Rule quality, conflict resolution | HIGH | TODO |

---

## Evidence

- Workflow report: [OPERATOR-AGENT-WORKFLOW-REPORT.md](../../OPERATOR-AGENT-WORKFLOW-REPORT.md)
- Trust scoring: RULE-011
- Task sequencing: RULE-014

---

## Spike Results: ORCH-001 (2024-12-27)

### Research Sources

| Repo | Stars | Focus | URL |
|------|-------|-------|-----|
| **iflytek/astron-agent** | 8.1K | Enterprise multi-agent orchestration | https://github.com/iflytek/astron-agent |
| **SmythOS/sre** | 1.2K | Cloud-native agent runtime | https://github.com/SmythOS/sre |
| **graniet/kheish** | 142 | Multi-role LLM agent with RAG | https://github.com/graniet/kheish |

### Astron-Agent Architecture Analysis

```
core/
├── agent/           # Agent core logic
│   ├── engine/      # Execution engine (task dispatch)
│   ├── domain/      # Domain models (agent, task)
│   ├── service/     # Business logic layer
│   └── repository/  # Data persistence
├── workflow/        # Workflow orchestration
│   ├── engine/      # Workflow execution
│   └── extensions/  # Custom workflow steps
├── knowledge/       # RAG integration
│   └── llm/         # LLM abstraction layer
├── memory/          # State persistence
│   └── database/    # Memory storage
├── plugin/          # Extensible tools
│   ├── aitools/     # AI-powered tools
│   └── rpa/         # Automation plugins
└── tenant/          # Multi-tenancy (Go service)
```

### Key Patterns Identified

| Pattern | Description | Sim.ai Application |
|---------|-------------|-------------------|
| **Engine Layer** | Separates execution logic from domain | `agent/engine/` → Task dispatch |
| **Domain-Driven** | Clear domain models for agents/tasks | Map to TypeDB entities |
| **Service Layer** | Business logic abstraction | MCP tool wrappers |
| **Repository Pattern** | Data access abstraction | TypeDB client |
| **Plugin Architecture** | Extensible tool system | MCP server plugins |
| **Workflow Engine** | Stateful workflow orchestration | DSP phase machine |

### Recommended Sim.ai Architecture

```
agent/
├── orchestrator/           # ORCH-001 implementation
│   ├── engine.py           # Task dispatch engine
│   ├── priority_queue.py   # Priority-based task queue
│   └── delegation.py       # Agent-to-agent handoff
├── agents/                 # Agent implementations
│   ├── base_agent.py       # Abstract agent class
│   ├── research_agent.py   # Context gathering
│   ├── coding_agent.py     # Implementation (Claude Code)
│   └── curator_agent.py    # Rules curation (ORCH-005)
├── domain/                 # Domain models
│   ├── task.py             # Task entity
│   ├── agent.py            # Agent entity
│   └── delegation.py       # Delegation context
└── repository/             # Data access
    └── typedb_repository.py # TypeDB integration
```

### Task Dispatch Protocol (ORCH-001 Design)

```python
class OrchestratorEngine:
    """
    Task dispatch engine per RULE-014 (Autonomous Task Sequencing).
    """

    def __init__(self, task_queue: PriorityQueue, agents: Dict[str, Agent]):
        self.queue = task_queue
        self.agents = agents

    async def dispatch(self, task: Task) -> TaskResult:
        """Dispatch task to appropriate agent based on type and priority."""
        # 1. Determine task type
        task_type = self.classify_task(task)

        # 2. Select agent based on type and trust (RULE-011)
        agent = self.select_agent(task_type, min_trust=0.7)

        # 3. Delegate with context
        context = await self.gather_context(task)
        result = await agent.execute(task, context)

        # 4. Handle delegation if needed
        if result.needs_delegation:
            return await self.delegate(task, result.delegate_to, result.context)

        return result
```

### Integration with TypeDB

```typeql
# Task claim mechanism (ORCH-003)
match
  $t isa task,
    has task-id $tid,
    has task-status "pending",
    has task-priority "CRITICAL";
  not { $t has claimed-by $a; };  # Not claimed
get $t, $tid;
limit 1;

# Claim task
insert
  $t has claimed-by "AGENT-001",
     has claimed-at 2024-12-27T10:00:00;
```

### Next Steps

1. **ORCH-002:** Implement task polling from TypeDB
2. **ORCH-003:** Add task claim/lock in TypeDB schema
3. **ORCH-004:** Design delegation context handoff
4. **ORCH-005:** Rules Curator agent skeleton

---

## Implementation Results: ORCH-002/ORCH-003 (2024-12-27)

### Files Created

**`agent/orchestrator/`** - Full orchestration module:
- `__init__.py` - Module exports
- `task_poller.py` - TypeDB task polling with async support
- `priority_queue.py` - Priority-based task queue
- `engine.py` - Central orchestrator engine

### Components Implemented

| Component | Purpose | Key Features |
|-----------|---------|--------------|
| `TypeDBTaskPoller` | Poll TypeDB for tasks | Async polling, callbacks, claim/release |
| `TaskPriorityQueue` | Priority dispatch queue | CRITICAL→LOW ordering, dedup, max size |
| `OrchestratorEngine` | Central orchestrator | Agent registry, Kanren validation, dispatch |

### Test Coverage

```
tests/test_orchestrator.py: 31 tests, 100% pass
- TestPollableTask: 4 tests
- TestTaskPriorityQueue: 8 tests
- TestTypeDBTaskPoller: 4 tests
- TestAgentInfo: 4 tests
- TestOrchestratorEngine: 11 tests
```

### Usage Example

```python
from agent.orchestrator import OrchestratorEngine, AgentInfo, AgentRole

# Create engine
engine = OrchestratorEngine(typedb_client)

# Register agents
engine.register_agent(AgentInfo(
    agent_id="AGENT-001",
    name="Claude Code R&D",
    role=AgentRole.CODING,
    trust_score=0.95
))

# Poll and dispatch
await engine.poll_and_queue()
result = await engine.dispatch_next()

# Complete with evidence
await engine.complete_task(
    task_id="TASK-001",
    agent_id="AGENT-001",
    evidence="Implementation complete with tests"
)
```

### Integration with Kanren

Engine uses `governance.kanren_constraints` for trust validation:
- `validate_agent_for_task()` checks RULE-011 trust requirements
- Falls back to simple validation if Kanren not available
- Reports constraints checked in dispatch result

### Next Steps

1. **ORCH-005:** Rules Curator Agent implementation
2. **ORCH-006:** Agent Chat UI integration
3. **ORCH-007:** Task execution viewer

---

## Implementation Results: ORCH-004 (2024-12-28)

### Files Created

**`agent/orchestrator/delegation.py`** - Agent Delegation Protocol:
- `DelegationType` - Enum: RESEARCH, IMPLEMENTATION, REVIEW, ESCALATION, VALIDATION, SYNC
- `DelegationPriority` - Enum: CRITICAL(1), HIGH(2), MEDIUM(3), LOW(4)
- `DelegationContext` - Context passed during handoff
- `DelegationRequest` - Delegation request with targeting
- `DelegationResult` - Result with followup support
- `DelegationProtocol` - Protocol orchestrator

### Delegation Flow

```
Source Agent → DelegationRequest
                     │
                     ├── Validate target agent
                     │   └── Check trust score (RULE-011)
                     │
                     ├── Execute handler if registered
                     │   └── Or return pending_manual
                     │
                     └── Return DelegationResult
                         └── Optional: needs_followup + followup_type
```

### Key Components

| Component | Purpose |
|-----------|---------|
| `DelegationContext` | Context handoff with constraints, evidence, trust requirements |
| `DelegationRequest` | Request targeting by role or specific agent |
| `DelegationResult` | Result with followup chain support |
| `DelegationProtocol` | Central delegator with handler registry |

### Convenience Methods

```python
# Research delegation
result = await protocol.delegate_research(
    task_id="TASK-001",
    source_agent_id="ORCH-001",
    query="Find authentication patterns"
)

# Implementation delegation
result = await protocol.delegate_implementation(
    task_id="TASK-002",
    source_agent_id="ORCH-001",
    spec="Implement JWT auth",
    constraints=["No external deps"]
)

# Validation delegation
result = await protocol.delegate_validation(
    task_id="TASK-003",
    source_agent_id="CODE-001",
    item_to_validate={"code": "..."},
    rules=["RULE-023"]
)

# Escalation
result = await protocol.escalate(
    task_id="TASK-004",
    source_agent_id="RES-001",
    reason="Cannot determine task type"
)
```

### Test Coverage

```
tests/test_delegation.py: 35 tests, 100% pass
- TestDelegationType: 4 tests
- TestDelegationPriority: 2 tests
- TestDelegationContext: 6 tests
- TestDelegationRequest: 3 tests
- TestDelegationResult: 3 tests
- TestDelegationProtocol: 10 tests
- TestConvenienceMethods: 4 tests
- TestConvenienceFunctions: 3 tests
```

### Integration with Orchestrator

```python
from agent.orchestrator import (
    OrchestratorEngine,
    DelegationProtocol,
    DelegationType,
    AgentRole,
)

# Create delegation protocol with engine
engine = OrchestratorEngine(typedb_client)
protocol = DelegationProtocol(engine)

# Register handlers
async def research_handler(ctx):
    # Gather context using MCP tools
    return {"findings": [...]}

protocol.register_handler(DelegationType.RESEARCH, research_handler)

# Delegate from orchestrator
result = await protocol.delegate_research(
    task_id="TASK-001",
    source_agent_id="ORCH-001",
    query="Research API patterns"
)

if result.needs_followup:
    # Chain to next delegation
    await protocol.delegate_implementation(...)
```

---

## Implementation Results: ORCH-006 (2024-12-28)

### Files Modified/Created

**State Management (`agent/governance_ui/state.py`):**
- Added `Chat` navigation item
- Chat state variables: `chat_messages`, `chat_input`, `chat_loading`, `chat_selected_agent`, `chat_session_id`, `chat_task_id`
- Pure state transforms: `with_chat_messages`, `with_chat_message`, `with_chat_loading`, `with_chat_input`, `with_chat_agent`, `with_chat_session`, `with_chat_task`
- UI helpers: `get_chat_role_color`, `get_chat_status_icon`, `format_chat_message`
- Message creators: `create_user_message`, `create_agent_message`, `create_system_message`

**API Endpoints (`governance/api.py`):**
- `POST /api/chat/send` - Send message and receive agent response
- `GET /api/chat/sessions` - List chat sessions
- `GET /api/chat/sessions/{session_id}` - Get session by ID
- `DELETE /api/chat/sessions/{session_id}` - Delete session
- Command processing: `/help`, `/status`, `/tasks`, `/rules`, `/agents`, `/search`, `/delegate`

**Dashboard UI (`agent/governance_dashboard.py`):**
- Chat view with message display, input field, agent selector
- Quick command chips for common operations
- Real-time message updates
- Trigger handlers: `send_chat_message`, `clear_chat`

### Chat Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/status` | Show system status (rules, tasks, agents, sessions) |
| `/tasks` | List pending tasks |
| `/rules` | List active rules |
| `/agents` | List registered agents |
| `/search <query>` | Search rules and tasks |
| `/delegate <task>` | Create delegated task |

### Test Coverage

```
tests/test_chat.py: 33 tests, 100% pass
- TestChatStateConstants: 2 tests
- TestChatStateTransforms: 7 tests
- TestChatHelpers: 2 tests
- TestChatMessageFormatting: 2 tests
- TestChatMessageCreation: 3 tests
- TestChatAPIModels: 3 tests
- TestChatCommandProcessing: 8 tests
- TestChatSessionManagement: 2 tests
- TestChatIntegration: 4 tests
```

### Next Steps

All orchestration tasks complete. Ready for production integration.

---

## Implementation Results: ORCH-007 (2024-12-28)

### Files Created/Modified

**API (`governance/api.py`):**
- `TaskExecutionEvent` - Pydantic model for execution events
- `TaskExecutionResponse` - Response model with event timeline
- `GET /api/tasks/{task_id}/execution` - Get execution history
- `POST /api/tasks/{task_id}/execution` - Add execution event
- `_synthesize_execution_events()` - Generate events from task timestamps

**State (`agent/governance_ui/state.py`):**
- `EXECUTION_EVENT_TYPES` - Event type styling (icons, colors)
- `with_task_execution_log()` - Set execution log
- `with_task_execution_loading()` - Set loading state
- `with_task_execution_event()` - Add event
- `clear_task_execution()` - Clear log
- `get_execution_event_style()` - Get event styling
- `format_execution_event()` - Format for display

**Dashboard (`agent/governance_dashboard.py`):**
- Execution Log section in task detail view
- Timeline display with event icons and colors
- Expand/collapse with refresh button
- `load_task_execution` trigger handler

### UI Components

| Component | Purpose |
|-----------|---------|
| Execution Log Card | Collapsible card in task detail view |
| VTimeline | Timeline display of execution events |
| VTimelineItem | Individual event with icon, time, message |
| Refresh Button | Reload execution history |
| Expand/Collapse | Toggle timeline visibility |

### Event Types

| Type | Icon | Color | Description |
|------|------|-------|-------------|
| `claimed` | hand-back-right | info | Agent claimed task |
| `started` | play | primary | Execution started |
| `progress` | progress-clock | info | Progress update |
| `delegated` | account-switch | warning | Delegated to another agent |
| `completed` | check-circle | success | Task completed |
| `failed` | alert-circle | error | Execution failed |
| `evidence` | file-document | secondary | Evidence attached |

### Test Coverage

```
tests/test_task_execution.py: 26 tests, 100% pass
- TestTaskExecutionImports: 7 tests
- TestExecutionStateTransforms: 5 tests
- TestExecutionHelpers: 5 tests
- TestExecutionAPIModels: 2 tests
- TestExecutionAPIEndpoints: 4 tests
- TestExecutionIntegration: 3 tests
```

### Usage Example

```python
# Add execution event from orchestrator
import httpx

async with httpx.AsyncClient() as client:
    # Log task claimed
    await client.post(
        "http://localhost:8082/api/tasks/TASK-001/execution",
        params={
            "event_type": "claimed",
            "message": "Claimed by Rules Curator",
            "agent_id": "rules-curator"
        }
    )

    # Log progress
    await client.post(
        "http://localhost:8082/api/tasks/TASK-001/execution",
        params={
            "event_type": "progress",
            "message": "Analyzing rule dependencies",
            "agent_id": "rules-curator"
        }
    )

    # Log completion
    await client.post(
        "http://localhost:8082/api/tasks/TASK-001/execution",
        params={
            "event_type": "completed",
            "message": "Analysis complete: 3 conflicts found",
            "agent_id": "rules-curator"
        }
    )

# Get execution history
response = await client.get(
    "http://localhost:8082/api/tasks/TASK-001/execution"
)
data = response.json()
# {
#   "task_id": "TASK-001",
#   "events": [...],
#   "current_status": "DONE",
#   "current_agent": "rules-curator",
#   "started_at": "2024-12-28T10:00:00",
#   "completed_at": "2024-12-28T10:05:00"
# }
```

---

*Per RULE-012 DSP: Agent orchestration R&D documented*
