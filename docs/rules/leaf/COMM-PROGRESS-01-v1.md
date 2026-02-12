# COMM-PROGRESS-01-v1: Progress Reporting with Impact and Next Steps

| Field | Value |
|-------|-------|
| **Rule ID** | COMM-PROGRESS-01-v1 |
| **Name** | Progress Reporting with Impact and Next Steps |
| **Category** | Workflow |
| **Priority** | HIGH |
| **Status** | ACTIVE |
| **Type** | OPERATIONAL |
| **Applicability** | MANDATORY |
| **Created** | 2026-02-12 |

## Directive

When delivering batch or milestone results to the user:

1. **Include quantitative stats** (e.g., test count, coverage delta, files modified)
2. **Explain the IMPACT** of what was delivered (what risk was reduced, what coverage was gained, what gaps were closed)
3. **State NEXT STEPS** tied to the active plan or backlog
4. **NEVER implicitly stop work** — either continue autonomously per standing instructions, or explicitly state "Stopping here because [reason]. Shall I continue?"

Do not present stats alone without context.

## Rationale

Sharing raw numbers without impact explanation or next steps creates confusion about whether work is paused, complete, or blocked. The user should always understand *why* the work matters and *what happens next* without having to ask.

## Examples

### Bad (violates rule)
> "Batch 128 complete: 43 tests added, 7482 total."

### Good (follows rule)
> "Batch 128 complete: +43 tests (7482 total), covering agent observability routes and TypeDB rule CRUD — the last two untested route modules. **Impact**: All FastAPI route modules now have unit test coverage. **Next**: Continuing to batch 129 targeting chat command routes and remaining TypeDB query modules."

## Related Rules

- WORKFLOW-AUTO-01-v1 (Autonomous operation)
- SESSION-EVID-01-v1 (Evidence capture)
