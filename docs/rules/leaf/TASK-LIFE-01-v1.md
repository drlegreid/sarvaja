# TASK-LIFE-01-v1: Task Lifecycle Management

**Category:** `workflow` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **GAP:** GAP-UI-046
> **Location:** [RULES-OPERATIONAL.md](../operational/RULES-OPERATIONAL.md)
> **Tags:** `tasks`, `workflow`, `agile`, `lifecycle`

---

## Directive

Task lifecycle follows Agile Definition of Ready/Done patterns. Tasks have separate **Status** (lifecycle) and **Resolution** (outcome) fields.

---

## Status (Lifecycle)

| Status | Description | Entry Criteria |
|--------|-------------|----------------|
| `OPEN` | Ready to be worked on | Task created/reopened |
| `IN_PROGRESS` | Being worked on | Agent claims task |
| `CLOSED` | Work complete | Task finished |

### Valid Transitions

```
OPEN → IN_PROGRESS    (Task started)
OPEN → CLOSED         (Quick close, trivial tasks)
IN_PROGRESS → CLOSED  (Work completed)
IN_PROGRESS → OPEN    (Work paused, unclaim)
CLOSED → OPEN         (Reopen for issues)
CLOSED → IN_PROGRESS  (Reopen and resume)
```

---

## Resolution (Outcome - Definition of Done)

| Resolution | Description | Requirements |
|------------|-------------|--------------|
| `NONE` | No resolution yet | Active tasks (OPEN/IN_PROGRESS) |
| `DEFERRED` | Postponed for later | Task closed without implementation |
| `IMPLEMENTED` | Solution delivered | Code/fix committed |
| `VALIDATED` | Tests pass | Verification evidence |
| `CERTIFIED` | User accepted | User feedback enrolled |

### Resolution Progression

```
NONE → IMPLEMENTED    (Solution delivered)
NONE → DEFERRED       (Postpone task)
IMPLEMENTED → VALIDATED    (Tests pass)
VALIDATED → CERTIFIED      (User accepts)
DEFERRED → IMPLEMENTED     (Resume and complete)
```

---

## Combination Rules

| Rule | Description |
|------|-------------|
| Active = NONE | OPEN/IN_PROGRESS tasks MUST have resolution NONE |
| CLOSED requires resolution | CLOSED tasks MUST have resolution (not NONE) |
| Reopen clears resolution | When reopening, resolution resets to NONE |

---

## Backward Compatibility

| Old Status | New Status | Resolution |
|------------|------------|------------|
| `TODO` | `OPEN` | `NONE` |
| `IN_PROGRESS` | `IN_PROGRESS` | `NONE` |
| `DONE` | `CLOSED` | `IMPLEMENTED` |
| `BLOCKED` | `IN_PROGRESS` | `NONE` |

---

## Implementation

**TypeDB Schema:**
```tql
task-status sub attribute, value string;     # OPEN, IN_PROGRESS, CLOSED
task-resolution sub attribute, value string; # NONE, DEFERRED, IMPLEMENTED, VALIDATED, CERTIFIED
```

**Python Module:** `governance/task_lifecycle.py`

**MCP Tools:**
- `governance_update_task(task_id, status, resolution)`
- `governance_verify_completion(task_id, verification_method, evidence)`

---

## Evidence Requirements

Per TEST-FIX-01-v1:

| Resolution | Evidence Required |
|------------|-------------------|
| IMPLEMENTED | Commit SHA, file changes |
| VALIDATED | Test output, verification method |
| CERTIFIED | User feedback reference |

---

*Per SESSION-EVID-01-v1: Evidence-Based Sessions*
