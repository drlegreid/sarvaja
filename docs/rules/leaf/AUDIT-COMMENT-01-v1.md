# AUDIT-COMMENT-01-v1: Comment Trail Integrity

| Field | Value |
|-------|-------|
| **Rule ID** | AUDIT-COMMENT-01-v1 |
| **Category** | quality |
| **Priority** | HIGH |
| **Status** | ACTIVE |
| **Applicability** | MANDATORY |
| **Created** | 2026-03-25 |

## Directive

Every task MUST maintain a structured comment trail from triage through resolution. No task is closed without evidence of deliberation.

## Comment Types (Required)

### 1. Triage Comment (on pickup)
Added when a task transitions from OPEN to IN_PROGRESS:
- **Impact assessment**: What breaks if we don't fix this?
- **Scope**: Which files/modules/layers are affected?
- **Effort estimate**: S/M/L/XL
- **Priority justification**: Why this priority ranking?

### 2. Solution Comment (during implementation)
Added during active work:
- **Approach chosen**: What design/fix path was selected?
- **Alternatives considered**: What was rejected and why?
- **References**: Links to files changed, tests added, related tasks/rules
- **Architecture notes**: OOP/SRP/DRY considerations if structural change

### 3. Resolution Comment (on close)
Added when task transitions to DONE/CLOSED:
- **What was done**: Concise summary of changes
- **Evidence**: Test results (T1/T2/T3), commit refs, screenshots
- **Regressions checked**: What existing tests were re-run?
- **Follow-up tasks**: Any new gaps or tasks spawned?

## Format

```
### [TRIAGE|SOLUTION|RESOLUTION] — {date}
**Author**: {agent_id}
**Session**: {session_id}

{structured content per type above}
```

## Enforcement

- `task_update()` to IN_PROGRESS without triage comment = WARNING
- `task_update()` to DONE without resolution comment = BLOCK
- Heuristic H-AUDIT-COMMENT-001: scan DONE tasks for missing comment trail
- Comment trail stored in task `resolution_notes` field (TypeDB persisted)

## Anti-Patterns

| Shortcut | Reality |
|----------|---------|
| "Fixed it" | What did you fix? Where? How do we verify? |
| No triage, straight to code | You skipped impact analysis — regressions incoming |
| Resolution without test refs | Unverified claims are not evidence |
| Copy-paste comments | Each task has unique context; generic comments hide risk |
