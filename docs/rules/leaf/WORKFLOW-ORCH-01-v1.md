# WORKFLOW-ORCH-01-v1: Orchestrator Continuous Workflow

**Category:** `workflow` | **Priority:** CRITICAL | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Tags:** `orchestrator`, `continuous-loop`, `backlog`, `langgraph`, `workflow`

---

## Directive

The orchestrator MUST follow a continuous GATE -> BACKLOG -> SPEC -> IMPLEMENT -> VALIDATE loop with dynamic gap injection. Backlog tasks are processed in priority order (CRITICAL > HIGH > MEDIUM > LOW). The loop stops when the backlog is empty, `max_cycles` is reached, or the dynamic budget is exhausted.

---

## Workflow Phases

| Phase | Node | Purpose | Exit Criteria |
|-------|------|---------|---------------|
| GATE | `gate_node` | Check stop conditions | Decision: continue or stop |
| BACKLOG | `backlog_node` | Pick highest-priority task | Task selected, removed from backlog |
| SPEC | `spec_node` | Produce specification | acceptance_criteria + files_to_modify |
| IMPLEMENT | `implement_node` | Execute changes | files_changed + summary |
| VALIDATE | `validate_node` | Run tests + heuristics | validation_passed + gaps_discovered |
| INJECT | `inject_node` | Add discovered gaps to backlog | Backlog updated |
| COMPLETE_CYCLE | `complete_cycle_node` | Record cycle in history | cycles_completed++ |
| PARK_TASK | `park_task_node` | Shelve after exhausted retries | Task parked |
| COMPLETE | `complete_node` | Mark run as success | status = "success" |

---

## Conditional Routing

| Condition | Route |
|-----------|-------|
| Backlog empty | GATE -> COMPLETE |
| max_cycles reached | GATE -> COMPLETE |
| Budget exhausted (token_ratio >= 80%) | GATE -> COMPLETE |
| Only LOW tasks + budget > 50% used | GATE -> COMPLETE |
| Validation passed, no gaps | VALIDATE -> COMPLETE_CYCLE -> GATE |
| Validation passed, gaps found | VALIDATE -> INJECT -> COMPLETE_CYCLE -> GATE |
| Validation failed, retries < 3 | VALIDATE -> SPEC (retry) |
| Validation failed, retries >= 3 | VALIDATE -> PARK_TASK -> GATE |

---

## Dynamic Budget (ROI-Aware Gate)

When `token_budget` is set in state, the gate uses `compute_budget()` instead of a flat counter:

| Factor | Metric | Threshold |
|--------|--------|-----------|
| Impact | `PRIORITY_VALUE` (CRITICAL=4, HIGH=3, MEDIUM=2, LOW=1) | Remaining backlog value |
| Cost | `TOKEN_COST_PER_CYCLE` (10 units/cycle) | Token ratio = used/budget |
| Exhaustion | `token_ratio >= 0.8` | Stop at 80% budget |
| Low-value trap | All remaining tasks LOW + `token_ratio > 0.5` | Stop early |
| ROI | `value_delivered / tokens_used` | Tracked per cycle |

Without `token_budget`, the original static `max_cycles` check applies (backward compatible).

---

## Safety Constraints

| Constraint | Value | Rationale |
|------------|-------|-----------|
| `max_cycles` | 10 (default) | Hard cap prevents infinite loops |
| `token_budget` | None (opt-in) | Dynamic budget when set |
| `MAX_RETRIES` | 3 | Don't retry validation forever |
| `dry_run` | False (default) | Must opt-in for real execution |
| Duplicate rejection | By task_id | No double-processing |

---

## Implementation Reference

- **State**: `governance/workflows/orchestrator/state.py`
- **Nodes**: `governance/workflows/orchestrator/nodes.py`
- **Edges**: `governance/workflows/orchestrator/edges.py`
- **Budget**: `governance/workflows/orchestrator/budget.py`
- **Graph**: `governance/workflows/orchestrator/graph.py`
- **Unit Tests**: `tests/unit/test_orchestrator_workflow.py` (28 tests)
- **Budget Tests**: `tests/unit/test_orchestrator_budget.py` (18 tests)
- **E2E Tests**: `tests/robot/e2e/orchestrator_workflow.robot` (14 tests)
- **RF Library**: `tests/robot/e2e/libs/OrchestratorE2ELibrary.py`

---

## Related

- WORKFLOW-DSP-01-v1: DSP Workflow (same LangGraph mock pattern)
- WORKFLOW-SFDC-01-v1: SFDC Workflow (same LangGraph mock pattern)
- TEST-TDD-01-v1: TDD RED-GREEN-REFACTOR methodology
- TEST-BDD-01-v1: Robot Framework BDD pattern

---

*Per META-TAXON-01-v1: Semantic rule naming*
*Created: 2026-02-10 — TDD-first orchestrator continuous workflow*
