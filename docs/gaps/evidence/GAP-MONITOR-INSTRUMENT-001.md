# GAP-MONITOR-INSTRUMENT-001: Rule Monitoring Instrumentation

**Priority:** MEDIUM | **Category:** feature/observability | **Status:** BLOCKED
**Discovered:** 2026-01-20 | **Source:** UI-AUDIT-012 Investigation
**Assignee:** Claude | **Resolution:** PARTIAL (43/43 code, blocked by GAP-MONITOR-IPC-001)
**Blocked By:** GAP-MONITOR-IPC-001 (Process isolation - MCP and Dashboard are separate processes)

---

## Problem Statement

The Real-time Rule Monitoring feature (`agent/rule_monitor.py`) currently shows only static demo data because no real events are logged to it.

**Current State:**
- `RuleMonitor` class exists and works correctly
- `create_rule_monitor(seed_demo_data=True)` seeds 8 static demo events
- `log_event()` method exists but is never called in production flows
- UI works but displays stale demo data

---

## What "Instrumentation" Means

Instrumentation = Adding `log_event()` calls at key points in the codebase to capture real governance activity.

### Instrumentation Points Required

| Location | Event Type | Example |
|----------|------------|---------|
| `governance/typedb/queries/rules/read.py` | `rule_query` | Every `get_rule()`, `get_all_rules()` call |
| `governance/typedb/queries/rules/write.py` | `rule_change` | Every rule create/update/delete |
| `governance/mcp_tools/rules.py` | `rule_query` | MCP tool invocations |
| `governance/mcp_tools/trust.py` | `trust_increase`/`trust_decrease` | Trust score changes |
| `governance/workflow_compliance.py` | `compliance_check` | Compliance validation runs |
| `governance/typedb/queries/tasks/*.py` | `task_event` | Task lifecycle events |

### Implementation Pattern

```python
# In each instrumentation point:
from agent.rule_monitor import get_rule_monitor

def some_operation():
    result = do_work()

    # Instrument the operation
    monitor = get_rule_monitor()
    monitor.log_event(
        event_type="rule_query",
        source="mcp-tool-name",
        details={"rule_id": rule_id, "operation": "get"},
        severity="INFO"
    )

    return result
```

---

## Scope Estimate

| Component | Files | Estimated Points |
|-----------|-------|------------------|
| Rule queries | 2 | ~10 instrumentation points |
| Rule mutations | 1 | ~5 instrumentation points |
| MCP tools | 5 | ~15 instrumentation points |
| Task operations | 3 | ~10 instrumentation points |
| Compliance checks | 1 | ~3 instrumentation points |
| **Total** | **12** | **~43 instrumentation points** |

---

## Scope Assessment

Per GOV-NOEST-01-v1: No time estimates. Scope-based assessment:
- **Complexity**: MEDIUM - additive changes, no breaking changes
- **Files**: ~12 files to modify
- **Points**: ~43 instrumentation points
- **Risk**: LOW
- **Dependencies**: None
- **Testing**: Monitor UI should show live events after instrumentation

---

## Acceptance Criteria

1. [x] Rule queries logged with rule_id and operation type
2. [x] Rule changes logged with change type and actor
3. [x] Trust score changes logged with old/new values
4. [x] Compliance checks logged with pass/fail status
5. [x] Task events logged (create, get, update, delete, verify)
6. [x] Session events logged (start, end, decision, task, intent, outcome)
7. [x] Agent events logged (create, get, trust_update)
8. [x] Governance events logged (proposal create, vote, dispute)
9. [x] DSM events logged (start, advance, checkpoint, finding, complete)
10. [x] Session linking events logged (get_tasks, link_rule, link_decision, link_evidence)
11. [x] Task linking events logged (link_session, link_rule, link_evidence, link_commit, get_*, update_details)
12. [ ] **BLOCKED** Monitor UI shows real events - requires GAP-MONITOR-IPC-001 (audit file + document service)
13. [ ] No performance regression - blocked until #12 resolved

---

## Progress (2026-01-20)

**43/43 points instrumented (100%):**

| File | Points | Event Types |
|------|--------|-------------|
| `governance/mcp_tools/rules_query.py` | 3 | rule_query (rules_query, rule_get, wisdom_get) |
| `governance/mcp_tools/rules_crud.py` | 4 | rule_change (create, update, deprecate, delete) |
| `governance/mcp_tools/trust.py` | 1 | trust_query (governance_get_trust_score) |
| `governance/workflow_compliance.py` | 1 | compliance_check (run_compliance_checks) |
| `governance/mcp_tools/tasks_crud.py` | 5 | task_event (create, get, update, delete, verify) |
| `governance/mcp_tools/sessions_core.py` | 4 | session_event (start, decision, end, task) |
| `governance/mcp_tools/agents.py` | 3 | agent_event (create, get, trust_update) |
| `governance/mcp_tools/proposals.py` | 3 | governance_event (proposal create, vote, dispute) |
| `governance/mcp_tools/sessions_intent.py` | 2 | session_event (capture_intent, capture_outcome) |
| `governance/mcp_tools/dsm.py` | 5 | dsm_event (start, advance, checkpoint, finding, complete) |
| `governance/mcp_tools/sessions_linking.py` | 4 | link_event (get_tasks, link_rule, link_decision, link_evidence) |
| `governance/mcp_tools/tasks_linking.py` | 8 | link_event + task_event (link_session, link_rule, link_evidence, get_evidence, link_commit, get_commits, update_details, get_details) |

**Remaining: NONE** ✓

---

## Architecture Gap Discovered (2026-01-20)

**Critical Finding:** MCP tools and Dashboard run in separate processes with separate RuleMonitor singletons.

```
Claude Code Host                    Container (governance-dashboard-dev)
├── MCP Tools (Python)              ├── FastAPI Dashboard (Python)
│   └── log_monitor_event()         │   └── RuleMonitor singleton ← UI reads from here
│       └── RuleMonitor singleton   │       └── seed_demo_data=True
│           └── events go HERE      │           └── shows demo data
└── events NEVER reach container    └── never receives real events
```

**Why Container Restart Won't Work:**
- Events logged by MCP tools go to a RuleMonitor singleton in Claude Code's Python process
- Dashboard container has its own Python process with its own RuleMonitor singleton
- No IPC mechanism exists to bridge the two processes

**Solution (GAP-MONITOR-IPC-001):**
- MCP tools write audit files to filesystem
- Document service ingests, collects, and visualizes logs
- Dashboard reads from document service instead of in-process singleton

---

## Evidence

- **Discovery session**: SESSION-2026-01-20-UI-AUDIT
- **Code analysis**: `agent/rule_monitor.py` lines 352-370 show `seed_demo_data` pattern
- **Related**: UI-AUDIT-012, UI-AUDIT-D02
- **Blocking gap**: GAP-MONITOR-IPC-001

---

## User Consultation Required

Per GOV-CONSULT-01-v1: Before implementation, confirm with user:
1. Priority relative to other work
2. Whether all 43 points needed or subset
3. Performance requirements (sync vs async logging)

---

*Per GOV-TRANSP-01-v1: Task logged with full scope definition rather than dismissed*
