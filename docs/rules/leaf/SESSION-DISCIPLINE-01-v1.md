# SESSION-DISCIPLINE-01-v1: Session Duration and Autonomy Limits

| Field | Value |
|-------|-------|
| **Rule ID** | SESSION-DISCIPLINE-01-v1 |
| **Category** | workflow |
| **Priority** | CRITICAL |
| **Applicability** | MANDATORY |
| **Status** | ACTIVE |
| **Created** | 2026-03-20 |

## Directive

Sessions MUST follow strict discipline to prevent mega-session rot:

1. **Max 4 hours per session** — if more work is needed, end session and start fresh
2. **Max 10 autonomous cycles per run** — then stop and report to user
3. **Checkpoint after each completed task** — brief status update, no silent 100-cycle runs
4. **New session per topic** — never mix unrelated work in one session
5. **Session start**: `health_check()` → load backlog → pick 1-2 items max
6. **Session end**: save context to ChromaDB, push commits, update plan

## Rationale

A 505MB, 33-day mega-session with 200+ compactions proved that unbounded sessions destroy code quality, cause context rot, and create false confidence. The "Fresh Start Plan" (2026-03-18) established these limits after analyzing recurring anti-patterns:

| Anti-Pattern | Consequence |
|---|---|
| Mega-sessions (33 days) | Context rot, 200+ compactions, 505MB bloat |
| Autonomous marathons ("run 500 cycles") | Unchecked work, quality degradation |
| No checkpoints | User discovers problems too late |
| Mixed topics | Impossible to resume or recover context |

## Related Rules

- WORKFLOW-AUTO-01-v1: Autonomous Task Sequencing (HALT commands)
- WORKFLOW-AUTO-02-v1: Autonomous Task Sequencing (priority-based)
- RECOVER-AMNES-01-v1: Context Recovery Protocol
- RECOVER-CRASH-01-v1: Crash Prevention (file size limits)
- COMM-PROGRESS-01-v1: Progress Reporting with Impact
