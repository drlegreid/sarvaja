# Entity-API-UI Mapping

**Per:** UI-FIRST-SPRINT-WORKFLOW.md, STRATEGIC-UI-FIRST-PIVOT.md
**Created:** 2024-12-25

---

## Purpose

Map every domain entity to its API endpoints and UI views. Ensures complete coverage and identifies implementation gaps.

---

## Entity Matrix

| Entity | TypeDB Type | API Endpoint | UI View | Status |
|--------|-------------|--------------|---------|--------|
| **Rule** | `governance-rule` | `/api/rules` | Rules Browser | P0 |
| **Decision** | `strategic-decision` | `/api/decisions` | Decisions List | P0 |
| **Session** | `session` | `/api/sessions` | Session Browser | P0 |
| **Task** | `task-item` | `/api/tasks` | Task Manager | P1 |
| **Agent** | `agent` | `/api/agents` | Agent Manager | P1 |
| **Evidence** | `evidence-artifact` | `/api/evidence` | Evidence Explorer | P1 |
| **Thought** | `thought-stream` | `/ws/thoughts` | Thought Stream | P2 |
| **Trust** | `agent-trust` | `/api/trust` | Trust Dashboard | P2 |

---

## Detailed Entity Mapping

### RULE (governance-rule)

```yaml
entity: governance-rule
priority: P0

typedb:
  schema: |
    governance-rule sub entity,
      owns rule-id,
      owns rule-title,
      owns rule-directive,
      owns rule-category,
      owns rule-priority,
      owns rule-status,
      plays rule-dependency:dependent,
      plays rule-dependency:dependency;

api:
  list:
    method: GET
    path: /api/rules
    params: [category, status, search]
    response: { rules: [], total: int }

  get:
    method: GET
    path: /api/rules/{rule_id}
    response: { rule_id, title, directive, category, priority, status, ... }

  create:
    method: POST
    path: /api/rules
    body: { rule_id, title, directive, category, priority }
    response: { success: bool, rule_id }

  update:
    method: PUT
    path: /api/rules/{rule_id}
    body: { title?, directive?, category?, priority?, status? }
    response: { success: bool }

  delete:
    method: DELETE
    path: /api/rules/{rule_id}
    response: { success: bool }

ui:
  list_view:
    location: /rules
    columns: [rule_id, title, status, category, priority]
    actions: [view, edit, deprecate]
    filters: [status, category]
    sort: [rule_id, title, updated_at]

  detail_view:
    location: /rules/{rule_id}
    sections: [header, metadata, content, relations, history]
    actions: [edit, deprecate, view_history]

  form_view:
    location: /rules/new, /rules/{rule_id}/edit
    fields: [rule_id, title, directive, category, priority]
    validation: [required, format, uniqueness]

mcp_tools:
  - governance_query_rules
  - governance_get_rule
  - governance_add_rule
  - governance_update_rule
  - governance_find_conflicts
```

### DECISION (strategic-decision)

```yaml
entity: strategic-decision
priority: P0

typedb:
  schema: |
    strategic-decision sub entity,
      owns decision-id,
      owns decision-title,
      owns decision-context,
      owns decision-rationale,
      owns decision-date,
      owns decision-status;

api:
  list:
    method: GET
    path: /api/decisions
    params: [status, date_from, date_to]
    response: { decisions: [], total: int }

  get:
    method: GET
    path: /api/decisions/{decision_id}
    response: { decision_id, title, context, rationale, impacts, ... }

ui:
  list_view:
    location: /decisions
    columns: [decision_id, title, date, status]
    actions: [view]

  detail_view:
    location: /decisions/{decision_id}
    sections: [summary, context, rationale, impacts, related_rules]

mcp_tools:
  - governance_list_decisions
  - governance_get_decision
  - governance_add_decision
```

### SESSION (session)

```yaml
entity: session
priority: P0

typedb:
  schema: |
    session sub entity,
      owns session-id,
      owns session-date,
      owns session-summary,
      owns session-outcomes;

api:
  list:
    method: GET
    path: /api/sessions
    params: [date_from, date_to, search]
    response: { sessions: [], total: int }

  get:
    method: GET
    path: /api/sessions/{session_id}
    response: { session_id, date, summary, outcomes, evidence, ... }

ui:
  list_view:
    location: /sessions
    columns: [session_id, date, summary]
    actions: [view, browse_evidence]

  detail_view:
    location: /sessions/{session_id}
    sections: [timeline, evidence, decisions, tasks_completed]

mcp_tools:
  - governance_list_sessions
  - governance_get_session
  - governance_evidence_search
```

### TASK (task-item)

```yaml
entity: task-item
priority: P1

typedb:
  schema: |
    task-item sub entity,
      owns task-id,
      owns task-title,
      owns task-status,
      owns task-priority,
      plays task-dependency:blocked,
      plays task-dependency:blocker;

api:
  list:
    method: GET
    path: /api/tasks
    params: [status, priority, phase]
    response: { tasks: [], total: int }

  get:
    method: GET
    path: /api/tasks/{task_id}
    response: { task_id, title, description, status, dependencies, ... }

  create:
    method: POST
    path: /api/tasks
    body: { title, description, priority, phase }

  update:
    method: PUT
    path: /api/tasks/{task_id}
    body: { status?, priority?, assignee? }

ui:
  list_view:
    location: /tasks
    columns: [task_id, title, status, priority, phase]
    actions: [view, complete, assign]
    grouping: [phase, status]

  board_view:
    location: /tasks/board
    columns: [TODO, IN_PROGRESS, DONE]
    drag_drop: true

mcp_tools:
  - platform_add_task
  - platform_get_tasks
  - platform_update_task
  - platform_assign_agent
  - governance_get_task_deps
```

### AGENT (agent)

```yaml
entity: agent
priority: P1

typedb:
  schema: |
    agent sub entity,
      owns agent-id,
      owns agent-name,
      owns agent-model,
      owns agent-tools,
      owns agent-trust-score;

api:
  list:
    method: GET
    path: /api/agents
    response: { agents: [], total: int }

  get:
    method: GET
    path: /api/agents/{agent_id}
    response: { agent_id, name, model, tools, trust_score, ... }

ui:
  list_view:
    location: /agents
    columns: [agent_id, name, model, trust_score, status]
    actions: [view, configure, deactivate]

  detail_view:
    location: /agents/{agent_id}
    sections: [config, tools, trust_history, activity_log]

mcp_tools:
  - governance_list_agents
  - governance_get_agent
  - governance_agent_trust
```

---

## Implementation Status

### P0 Entities (Current Sprint)

| Entity | TypeDB | API | MCP | UI List | UI Detail | UI Form |
|--------|--------|-----|-----|---------|-----------|---------|
| Rule | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ❌ |
| Decision | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | ❌ |
| Session | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | N/A |

**Legend:** ✅ Complete | ⚠️ Partial | ❌ Missing | N/A Not Applicable

### P1 Entities (Next Sprint)

| Entity | TypeDB | API | MCP | UI List | UI Detail | UI Form |
|--------|--------|-----|-----|---------|-----------|---------|
| Task | ✅ | ⚠️ | ⚠️ | ⚠️ | ❌ | ❌ |
| Agent | ✅ | ❌ | ⚠️ | ❌ | ❌ | ❌ |
| Evidence | ✅ | ⚠️ | ✅ | ❌ | ❌ | N/A |

### P2 Entities (Future)

| Entity | TypeDB | API | MCP | UI |
|--------|--------|-----|-----|-----|
| Thought | ❌ | ❌ | ❌ | ❌ |
| Trust | ✅ | ❌ | ⚠️ | ❌ |

---

## Gap Summary

Based on mapping analysis:

| Gap | Entity | Layer | Priority |
|-----|--------|-------|----------|
| No REST API endpoints | All | API | HIGH |
| No CRUD forms | Rule, Task | UI | HIGH |
| No detail drill-down | All | UI | HIGH |
| No real-time updates | Thought | API+UI | P2 |
| Trust dashboard missing | Trust | UI | P2 |

---

## Next Steps

1. **P10.1**: Implement REST API for P0 entities (Rule, Decision, Session)
2. **P10.2**: Add CRUD forms to Governance Dashboard
3. **P10.3**: Implement detail views with full data binding
4. **P10.4**: Add Task/Agent management views
5. **P10.5**: WebSocket for real-time thought streaming

---

*Per STRATEGIC-UI-FIRST-PIVOT.md*
*Per UI-FIRST-SPRINT-WORKFLOW.md*
