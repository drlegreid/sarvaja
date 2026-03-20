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

### 9. Exploratory Validation Gate (MANDATORY)

Per TEST-EXPLSPEC-01-v1, every EPIC plan MUST include an **exploratory test phase using the 3-MCP triad** (playwright + rest-api + log-analyzer) before the final phase(s). This is a quality gate — not optional.

**Plan structure requirement:**
- The plan MUST include an EDS validation phase after implementation phases and before remediation/migration phases
- This phase uses Playwright MCP to explore the delivered UI/API and produces an EDS spec file
- The EDS phase validates that all prior phases actually work end-to-end in the running system

**EDS phase template:**
```
## Phase N: Exploratory Validation (EDS) — Status: TODO

**Goal**: Validate P1-P(N-1) deliverables via Playwright MCP exploratory testing.

**Output**:
- `docs/backlog/specs/EDS-{DOMAIN}-{DATE}.eds.md` (3-layer spec)
- Screenshots in `evidence/test-results/`

**BDD**:
  Scenario: Navigate to affected UI views and verify new functionality
  Scenario: Exercise API endpoints for new/changed entities
  Scenario: Capture EDS 3-layer spec (Business → Actions → Locators)

**Deps**: All implementation phases | **Gate for**: Remaining phases
```

**Boundary rule:** No remediation or migration phase may start until the EDS gate phase is DONE with ALL scenarios PASS.

### 10. EDS Fail → Bugfix → Revalidate Loop (MANDATORY)

When the EDS gate finds bugs:

1. **Phase Nb**: Insert a bugfix phase immediately after the EDS gate. Include:
   - Bug IDs with severity (from EDS findings)
   - TDD tests for each bug fix
   - Gap items discovered during EDS (missing endpoints, UI sections)
2. **Phase Nc**: Insert a revalidation phase that re-runs ONLY the failing EDS scenarios
3. **Pass criteria**: ALL original EDS scenarios must PASS. Any remaining FAIL → loop back to Nb
4. **No skipping**: The bugfix-revalidate loop MUST complete before downstream phases proceed

This is the quality ratchet — bugs found by EDS are blockers, not backlog items.

## Anti-Patterns

| Don't | Do Instead |
|-------|-----------|
| Duplicate plan content in session prompts | Reference plan file path |
| Repeat common rules per phase | Use Common Rules section |
| Start phases out of dependency order | Check dependency graph |
| Skip BDD acceptance criteria | Write Gherkin scenarios for every phase |
| Leave phase status as TODO after completing | Update to DONE immediately |
| Execute code in a dispatch session | Output prompt only, execute in new session |
| Skip exploratory testing before final phases | Run EDS gate per TEST-EXPLSPEC-01-v1 |
| Treat screenshots alone as validation | Produce full 3-layer EDS spec |

## Rationale

Duplicating plan content in session prompts violates DRY, inflates prompt tokens, and drifts from the plan as phases evolve. Plan-file-first ensures one place to read, update, and track progress across sessions. Phase-per-session prevents context exhaustion and enables clean handoffs.

---

*Per TASK-EPIC-01-v1: All work framed within EPICs.*
*Per DOC-SIZE-01-v1: Plan files follow same size constraints as code.*
