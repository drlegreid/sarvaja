# WORKFLOW-PLAN-01-v1: EPIC Plan-File-First Delivery

| Field | Value |
|-------|-------|
| **Category** | Operational |
| **Priority** | HIGH |
| **Status** | ACTIVE |
| **Applicability** | MANDATORY |
| **Created** | 2026-03-20 |

## Directive

Multi-phase EPIC work MUST use a plan file as the single source of truth. Session prompts reference the plan file path — they do NOT duplicate its content. Each phase is independently deliverable in one session, tracked with status, and gated by an explicit dependency graph.

## Requirements

### 1. Plan File Structure (MANDATORY)

Every EPIC plan file MUST contain:

```
Context              — why this change exists
Common Rules         — shared constraints stated ONCE (DRY)
Phase N (per phase)  — goal, files, BDD acceptance, deps, verify command, status
Dependency Graph     — explicit phase ordering
Summary Table        — phase / deliverable / tests / deps / status
```

### 2. DRY Session Prompts (MANDATORY)

Session prompts MUST be minimal — reference the plan, don't repeat it:

**WRONG:**
> Paste full context, file lists, BDD specs, rules into the prompt

**CORRECT:**
> `EPIC-NAME, Phase N of M: Phase Title.`
> `PLAN: Read ~/.claude/plans/{plan-file}.md`
> `Update Phase N status to DONE when complete.`

### 3. Phase-Per-Session (MANDATORY)

Each phase MUST be:
- Independently deliverable in one Claude Code session
- Self-contained with its own BDD acceptance criteria
- Verifiable via a single test command

### 4. Status Tracking (MANDATORY)

Each phase has a status in the plan file header:

| Status | Meaning |
|--------|---------|
| `TODO` | Not started |
| `IN_PROGRESS` | Currently being worked |
| `DONE` | Completed and verified |

The executing agent updates status in the plan file upon completion.

### 5. Dependency Graph (MANDATORY)

Phases declare explicit dependencies. No phase may start before its dependencies are DONE. The plan file includes a visual dependency graph.

### 6. BDD Acceptance (MANDATORY)

Every phase includes Gherkin scenario titles as acceptance criteria. These drive TDD — tests are written FIRST from these scenarios.

### 7. Common Rules Section (MANDATORY)

Constraints shared across all phases (TDD, file size limits, verify commands, tool preferences) are stated ONCE in a "Common Rules" section — not repeated per phase.

### 8. Dispatch Mode (MANDATORY)

A **dispatch session** reviews EPIC progress and outputs the next phase prompt — it does NOT execute work. This prevents accidental phase execution in the wrong session.

**Dispatch prompt format:**
```
EPIC-NAME: Phase N is DONE.
PLAN: Read ~/.claude/plans/{plan-file}.md
DISPATCH ONLY — do not execute. Review plan, confirm ready phase, output prompt.
```

**Dispatch session output:**
1. Confirm completed phase(s) and their deliverables
2. Identify unblocked phase(s) via dependency graph
3. Recommend next phase with rationale
4. Output the exact session prompt to paste into a new session

**Boundary rule:** If a session prompt does NOT contain a phase number to execute, the agent MUST NOT write code or tests. It may only read, analyze, and output prompts.

## Anti-Patterns

| Don't | Do Instead |
|-------|-----------|
| Duplicate plan content in session prompts | Reference plan file path |
| Repeat common rules per phase | Use Common Rules section |
| Start phases out of dependency order | Check dependency graph |
| Skip BDD acceptance criteria | Write Gherkin scenarios for every phase |
| Leave phase status as TODO after completing | Update to DONE immediately |
| Execute code in a dispatch session | Output prompt only, execute in new session |

## Rationale

Duplicating plan content in session prompts violates DRY, inflates prompt tokens, and drifts from the plan as phases evolve. Plan-file-first ensures one place to read, update, and track progress across sessions. Phase-per-session prevents context exhaustion and enables clean handoffs.

---

*Per TASK-EPIC-01-v1: All work framed within EPICs.*
*Per DOC-SIZE-01-v1: Plan files follow same size constraints as code.*
