# Phase 12: Agent Orchestration

**Status:** 🚧 IN PROGRESS (4/8 tasks complete)
**Priority:** CRITICAL
**Related Rules:** RULE-011 (Multi-Agent Governance), RULE-014 (Autonomous Task Sequencing)

---

## Strategic Goal

Enable agents to execute tasks autonomously per RULE-014. Agents must poll for tasks, claim/lock, execute, and report results. This is the **primary blocker** for agentic platform usability.

---

## Reference Gaps

- [GAP-UI-CHAT-001/002](../../gaps/GAP-INDEX.md): Agent command interface (CRITICAL)
- [GAP-AGENT-010-014](../../gaps/GAP-INDEX.md): Agent execution gaps (HIGH)
- [GAP-CTX-001-003](../../gaps/GAP-INDEX.md): Context awareness gaps (CRITICAL)

---

## Task List

| Task | Status | Description | Gap | Priority |
|------|--------|-------------|-----|----------|
| P12.1 | ✅ DONE | **Agent Task Polling**: TypeDBTaskPoller in agent/orchestrator/task_poller.py | GAP-AGENT-011 | **P0** |
| P12.2 | ✅ DONE | **Task Claim/Lock**: claim_task() in task_poller.py:162 | GAP-AGENT-012 | **P0** |
| P12.3 | 🚧 PARTIAL | **Agent Chat Backend**: UI/API done, needs DelegationProtocol wiring | GAP-UI-CHAT-001 | **P0** |
| P12.4 | 📋 TODO | **Execution Logging**: Real-time execution events to UI | GAP-UI-CHAT-002 | **P1** |
| P12.5 | ✅ DONE | **Delegation Protocol**: DelegationProtocol in agent/orchestrator/delegation.py | GAP-AGENT-013 | **P1** |
| P12.6 | 📋 TODO | **Context Auto-Loading**: DECISION-* preload on session start | GAP-CTX-002 | **P1** |
| P12.7 | ✅ DONE | **Rules Curator Agent**: RulesCuratorAgent in agent/orchestrator/curator_agent.py | GAP-AGENT-014 | **P2** |
| P12.8 | 📋 TODO | **Memory Consolidation**: Decide TypeDB vs claude-mem architecture | GAP-CTX-003 | **P2** |

### P12.3 Implementation Gap Analysis (2024-12-31)

**Current State:**
- Chat UI: ✅ agent/governance_ui/views/chat_view.py
- Chat Controller: ✅ agent/governance_ui/controllers/chat.py
- Chat API: ✅ governance/routes/chat.py (uses simulated `_process_chat_command`)
- DelegationProtocol: ✅ agent/orchestrator/delegation.py (not wired to chat)

**Gap:** Chat API at governance/routes/chat.py:40 uses simulated responses instead of DelegationProtocol

**Required Wiring:**
1. Import `DelegationProtocol` from `agent.orchestrator`
2. Replace `_process_chat_command()` with `delegation_protocol.dispatch()`
3. Wire `OrchestratorEngine` to coordinate agent selection and dispatch
4. Stream execution events to UI via WebSocket or polling

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Agent Orchestration Layer (P12)                       │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ Orchestrator│  │ Research    │  │ Coding      │  │ Rules       │   │
│  │ Agent       │  │ Agent       │  │ Agent       │  │ Curator     │   │
│  │ (dispatch)  │  │ (context)   │  │ (impl)      │  │ (governance)│   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘   │
│         │                │                │                │           │
│         └────────────────┴────────────────┴────────────────┘           │
│                                   │                                     │
│                    ┌──────────────▼──────────────┐                     │
│                    │   TypeDB Task Backlog       │                     │
│                    │   (priority queue)          │                     │
│                    └─────────────────────────────┘                     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Dependencies

- Phase 10 (Architecture Debt Resolution): ✅ Complete
- Phase 11 (Data Integrity Resolution): ✅ Complete
- ORCH-002 (Task Polling): ✅ agent/orchestrator/ module (31 tests)
- ORCH-003 (Task Claim/Lock): ✅ Included in orchestrator
- ORCH-004 (Delegation Protocol): ✅ agent/orchestrator/delegation.py (35 tests)
- ORCH-006 (Agent Chat UI): ✅ agent/governance_ui/views/chat_view.py (33 tests)

---

## Existing Infrastructure

| Component | Location | Status |
|-----------|----------|--------|
| Orchestrator module | agent/orchestrator/ | ✅ Ready |
| Delegation protocol | agent/orchestrator/delegation.py | ✅ Ready |
| Chat view UI | agent/governance_ui/views/chat_view.py | ✅ Ready |
| Chat controllers | agent/governance_ui/controllers/chat.py | ✅ Ready |
| Chat API endpoints | governance/routes/chat.py | ✅ Ready |
| Session memory | governance/session_memory.py | ✅ Ready |

---

## Success Criteria

- [ ] User can send commands to agents via chat UI
- [ ] Agents poll and pick up tasks from TypeDB backlog
- [ ] Tasks are claimed atomically (no duplicate execution)
- [ ] Execution events stream to UI in real-time
- [ ] Agents can delegate to Research Agent when lacking context
- [ ] DECISION-* files auto-loaded on session start

---

*Per RULE-012 DSP: Phase documentation created*
