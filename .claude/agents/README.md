# Sim.ai Subagent Definitions

Multi-agent orchestration for Claude Code per MULTI-001-007 R&D.

## Agent Catalog

| Agent | Role | Primary Tools | MCP Access |
|-------|------|---------------|------------|
| [coding-agent](coding-agent.md) | Implementation | Read, Write, Edit, Bash | core, tasks |
| [testing-agent](testing-agent.md) | Quality Assurance | Read, Bash (pytest) | sessions, tasks |
| [governance-agent](governance-agent.md) | Audit & Compliance | Read, Write, Glob | ALL governance |
| [research-agent](research-agent.md) | Information Gathering | WebSearch, WebFetch | core, sessions |

## Orchestration Patterns

### Sequential Pipeline

```
research-agent → coding-agent → testing-agent → governance-agent
```

Best for: New features, refactoring, complex changes

### Parallel Execution

```
┌─ coding-agent (module A) ─┐
│                           │
├─ coding-agent (module B) ─┼→ testing-agent → governance-agent
│                           │
└─ coding-agent (module C) ─┘
```

Best for: Independent changes, parallel development

### Iterative Loop

```
coding-agent ⟷ testing-agent (repeat until tests pass)
                    ↓
            governance-agent
```

Best for: Bug fixes, test-driven development

## Coordination Protocol

Agents communicate via shared state file:

```json
// .claude/agent-state.json
{
  "current_task": "TASK-123",
  "pipeline": ["research", "coding", "testing", "governance"],
  "current_agent": "coding-agent",
  "status": "IN_PROGRESS",
  "handoffs": [
    {
      "from": "research-agent",
      "to": "coding-agent",
      "timestamp": "2026-01-09T23:00:00Z",
      "notes": "Research complete, 3 options identified"
    }
  ]
}
```

## Design Principles

| Principle | Implementation |
|-----------|----------------|
| **SRP** | Each agent has single responsibility |
| **Context Isolation** | Agents don't see each other's full context |
| **Governance First** | All work tracked via MCP tools |
| **Audit Trail** | Every handoff logged |

## Quick Start

1. Define task in TODO.md or via governance_create_task
2. Assign to appropriate agent
3. Agent executes within its scope
4. Handoff to next agent in pipeline
5. Governance-agent approves final result

## Related

- [MULTI-001-007](../../docs/backlog/R&D-BACKLOG.md#local-multi-agent-setup-for-claude-code-rd-2026-01-09)
- [RULE-036](../../docs/rules/technical/RULES-ARCHITECTURE.md) - MCP Server Separation
- [DECISION-006](../../evidence/DECISION-006-PORTABLE-MCP-PATTERNS.md) - Portable Patterns
