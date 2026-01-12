# Agent Chat UI Requirements

> **Gaps:** GAP-UI-CHAT-001, GAP-UI-CHAT-002
> **Rules:** RULE-011 (Multi-Agent Governance), RULE-014 (Autonomous Task Sequencing)
> **Status:** RESOLVED 2026-01-02

---

## Problem Statement

User cannot command agents from the platform UI. Agents are not picking up tasks from the backlog.

---

## Required Capabilities

### 1. Agent Command Interface
- Prompt/chat UI for sending commands to agents
- Task assignment to specific agents
- View agent execution status and responses

### 2. Task Orchestration (per RULE-014)
- Orchestration Agent coordinates task execution
- Tasks picked up from TypeDB backlog automatically
- Priority-based task sequencing

### 3. Agent Delegation Chain
- If agent lacks context → delegate to Research Agent
- Research Agent gathers context → returns to original agent
- Delegation tracked in session evidence

### 4. Rules Curator Agent
- Monitors rule quality and conflicts
- Clarifies ambiguous rules
- Escalates to human when resolution unclear
- Per RULE-011 trust-weighted voting

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
│                    ┌──────────────▼──────────────┐                     │
│                    │   TypeDB Task Backlog       │                     │
│                    │   (priority queue)          │                     │
│                    └─────────────────────────────┘                     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Resolution

**GAP-UI-CHAT-001:** Chat view + API exists (governance_ui/views/chat_view.py)

**GAP-UI-CHAT-002:** build_task_execution_viewer() in chat_view.py

**Related Tasks:**
- P9.5: Agent Trust Dashboard (trust scores visible)
- P10.7: Entity Hierarchy (Decision as Task subtype)
- GAP-AGENT-010: Agent Task Backlog functional

---

*Per RULE-011: Multi-Agent Governance Protocol*
