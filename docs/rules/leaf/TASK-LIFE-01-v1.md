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
| `DONE` | Work completed, pending verification | DONE gate passes (see TASK-VALID-01-v1) |
| `BLOCKED` | Cannot proceed | External dependency or blocker identified |
| `CANCELED` | Abandoned without completion | Explicit cancellation (soft delete alternative) |
| `CLOSED` | Fully verified and accepted | All evidence + verification complete |

### Valid Transitions

```
OPEN → IN_PROGRESS    (Task started)
OPEN → CANCELED       (Canceled before work begins)
OPEN → CLOSED         (Quick close, trivial tasks)
IN_PROGRESS → DONE    (Work completed, DONE gate validates)
IN_PROGRESS → BLOCKED (Blocker identified)
IN_PROGRESS → OPEN    (Work paused, unclaim)
IN_PROGRESS → CANCELED (Abandoned mid-work)
DONE → CLOSED         (Verification passed)
DONE → IN_PROGRESS    (Rework needed)
BLOCKED → IN_PROGRESS (Blocker resolved)
BLOCKED → CANCELED    (Blocker unresolvable)
CANCELED → OPEN       (Reopen canceled task)
CLOSED → OPEN         (Reopen for issues)
CLOSED → IN_PROGRESS  (Reopen and resume)
```

**Canonical source**: `governance/task_lifecycle.py:TaskStatus` enum + `VALID_STATUS_TRANSITIONS` dict.

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

## CANCELED vs DELETE

| Action | When | Reversible | Data |
|--------|------|------------|------|
| CANCELED | Task abandoned, context preserved | Yes (reopen) | Kept in TypeDB |
| DELETE | Only for CANCELED/CLOSED tasks | No | Removed from TypeDB |

**Hard delete is restricted**: Only CANCELED or CLOSED tasks may be deleted. Active tasks (OPEN, IN_PROGRESS, BLOCKED) must be canceled first.

---

## Backward Compatibility

| Old Status | New Status | Resolution |
|------------|------------|------------|
| `TODO` | `OPEN` | `NONE` |
| `IN_PROGRESS` | `IN_PROGRESS` | `NONE` |
| `DONE` | `DONE` | `NONE` (pending verification) |
| `BLOCKED` | `BLOCKED` | `NONE` |

---

## Implementation

**TypeDB Schema:**
```tql
task-status sub attribute, value string;     # OPEN, IN_PROGRESS, DONE, BLOCKED, CANCELED, CLOSED
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

## Test Coverage

**8 robot test file(s)** validate this rule:

| File | Scope |
|------|-------|
| `tests/robot/unit/kanren_task.robot` | unit |
| `tests/robot/unit/sync_status.robot` | unit |
| `tests/robot/unit/task_completion_sync.robot` | unit |
| `tests/robot/unit/task_crud_split.robot` | unit |
| `tests/robot/unit/task_execution.robot` | unit |
| `tests/robot/unit/task_lifecycle.robot` | unit |
| `tests/robot/unit/task_ui.robot` | unit |
| `tests/robot/unit/task_ui_extended.robot` | unit |

```bash
# Run all tests validating this rule
robot --include TASK-LIFE-01-v1 tests/robot/
```

---

*Per SESSION-EVID-01-v1: Evidence-Based Sessions*
