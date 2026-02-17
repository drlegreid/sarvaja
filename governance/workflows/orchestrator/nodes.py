"""Orchestrator phase nodes.

Per WORKFLOW-ORCH-01-v1: Each node transforms state for one phase
of the continuous Spec -> Impl -> Validate loop.
"""

import re
from typing import Any, Dict

from governance.workflows.orchestrator.state import add_to_backlog


def gate_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Check whether to continue or stop the orchestrator loop.

    Uses dynamic budget when token_budget is set in state,
    otherwise falls back to static max_cycles check.
    """
    # BUG-220-GATE-001: Use .get() to prevent KeyError on partial state
    if not state.get("backlog"):
        return {
            "current_phase": "backlog_empty",
            "gate_decision": "stop",
        }
    if state.get("cycles_completed", 0) >= state.get("max_cycles", 10):
        return {
            "current_phase": "max_cycles_reached",
            "gate_decision": "stop",
        }
    # Dynamic budget: ROI-based decision when token_budget is configured
    if "token_budget" in state:
        from governance.workflows.orchestrator.budget import compute_budget
        budget = compute_budget(state)
        if not budget["should_continue"]:
            return {
                "current_phase": f"budget_{budget['reason']}",
                "gate_decision": "stop",
                "budget": budget,
            }
    return {"gate_decision": "continue"}


def backlog_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Pick the highest-priority task from the backlog."""
    # BUG-266-NODE-001: Use .get() to prevent KeyError on partial state
    backlog = list(state.get("backlog", []))
    # BUG-ORCH-001: Guard against empty backlog
    if not backlog:
        return {"current_phase": "backlog_empty", "gate_decision": "stop"}
    task = backlog.pop(0)
    return {
        "current_task": task,
        "current_phase": "task_selected",
        "backlog": backlog,
        "retry_count": 0,
    }


def spec_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Produce a specification for the current task."""
    # BUG-ORCH-NULL-TASK-001: Guard against None current_task
    task = state.get("current_task")
    if not task:
        return {"current_phase": "spec_error", "error_message": "No current task to specify"}
    # BUG-246-NOD-001: Sanitize task_id to prevent path traversal in file paths
    # BUG-337-NODE-001: Use .get() to prevent KeyError on malformed task dict
    raw_id = task.get('task_id', 'unknown')
    safe_id = re.sub(r'[^a-z0-9_\-]', '_', raw_id.lower())
    return {
        "current_phase": "specified",
        "specification": {
            "task_id": raw_id,
            "description": task.get("description", ""),
            "acceptance_criteria": [
                f"Resolve {raw_id} per its description",
                "All existing tests continue to pass",
                "New tests cover the change",
            ],
            "files_to_modify": [
                f"governance/workflows/orchestrator/{safe_id}.py",
            ],
        },
    }


def implement_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Record implementation changes (dry_run=True produces stubs)."""
    # BUG-ORCH-NULL-TASK-001: Guard against None current_task
    task = state.get("current_task")
    if not task:
        return {"current_phase": "impl_error", "error_message": "No current task to implement"}
    # BUG-200-IMPL-001: Guard against None specification (spec_node may have failed)
    spec = state.get("specification") or {}
    if not spec:
        return {"current_phase": "impl_error", "error_message": "No specification available"}
    return {
        "current_phase": "implemented",
        "implementation": {
            "task_id": task["task_id"],
            "files_changed": spec.get("files_to_modify", []),
            "summary": f"Implemented {task['task_id']}: {task['description']}",
            "dry_run": state.get("dry_run", False),
        },
    }


def validate_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Run validation checks on the implementation."""
    # BUG-ORCH-NULL-TASK-001: Guard against None current_task
    task = state.get("current_task")
    if not task:
        return {"current_phase": "validate_error", "error_message": "No current task to validate"}
    gaps = []
    if state.get("_simulate_gap_discovery"):
        gaps = [
            {
                "gap_id": f"GAP-DISC-{task['task_id']}",
                "priority": "MEDIUM",
                "description": f"Gap discovered while validating {task['task_id']}",
            },
        ]

    passed = True
    if state.get("_simulate_validation_failure"):
        passed = False

    # Generate 3-tier validation specs (TEST-SPEC-01-v1)
    from governance.workflows.orchestrator.spec_tiers import (
        generate_specs_from_validation,
    )
    validation_results = {
        "tests_passed": passed,
        "heuristics_passed": passed,
        "task_id": task["task_id"],
    }
    specs = generate_specs_from_validation(validation_results, task)

    return {
        "current_phase": "validated",
        "validation_results": validation_results,
        "validation_passed": passed,
        "gaps_discovered": gaps,
        "validation_specs": specs,
    }


def inject_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Inject discovered gaps back into the backlog."""
    gaps = state.get("gaps_discovered", [])
    if not gaps:
        return {"current_phase": "no_gaps_to_inject"}

    # BUG-266-NODE-001: Use .get() to prevent KeyError on partial state
    backlog = list(state.get("backlog", []))
    existing_ids = {t["task_id"] for t in backlog}
    for gap in gaps:
        gid = gap.get("gap_id", gap.get("task_id"))
        # BUG-ORCH-002: Skip gaps without valid ID
        if not gid:
            continue
        if gid not in existing_ids:
            backlog.append({
                "task_id": gid,
                "priority": gap.get("priority", "MEDIUM"),
                "description": gap.get("description", f"Gap {gid}"),
            })
            existing_ids.add(gid)

    from governance.workflows.orchestrator.state import PRIORITY_ORDER
    backlog.sort(key=lambda t: PRIORITY_ORDER.get(t["priority"], 99))
    return {
        "current_phase": "gaps_injected",
        "backlog": backlog,
    }


def complete_cycle_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Record a completed cycle and advance the counter.

    Also tracks budget: increments value_delivered and tokens_used.
    """
    # BUG-ORCH-NULL-TASK-002: Guard consistent with spec/implement/validate nodes
    task = state.get("current_task")
    if not task:
        # BUG-220-GAPS-001: Clear gaps_discovered in error path to prevent stale re-injection
        return {"current_phase": "cycle_error", "error_message": "No current task to complete", "gaps_discovered": []}
    history = list(state.get("cycle_history", []))
    history.append({
        "task_id": task["task_id"],
        "specification": state.get("specification"),
        "implementation": state.get("implementation"),
        "validation": state.get("validation_results"),
    })
    result = {
        "current_phase": "cycle_complete",
        # BUG-234-LOGIC-002: Use .get() to avoid KeyError on partial state
        "cycles_completed": state.get("cycles_completed", 0) + 1,
        "cycle_history": history,
        "current_task": None,
        "specification": None,
        "implementation": None,
        "validation_results": None,
        "validation_passed": None,
        "gaps_discovered": [],
    }
    # Budget tracking: accumulate value delivered and tokens consumed
    if "value_delivered" in state:
        from governance.workflows.orchestrator.budget import (
            PRIORITY_VALUE, TOKEN_COST_PER_CYCLE,
        )
        task_value = PRIORITY_VALUE.get(task.get("priority", "LOW"), 1)
        result["value_delivered"] = state["value_delivered"] + task_value
        result["tokens_used"] = (
            state.get("tokens_used", 0) + TOKEN_COST_PER_CYCLE
        )
    return result


def park_task_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Park a task that exhausted retries.

    BUG-ORCH-PARK-001: Also tracks tokens_used for budget consistency.
    """
    # BUG-ORCH-NULL-TASK-003: Guard consistent with spec/implement/validate nodes
    task = state.get("current_task")
    if not task:
        return {"current_phase": "park_error", "error_message": "No current task to park"}
    history = list(state.get("cycle_history", []))
    history.append({
        "task_id": task["task_id"],
        "status": "parked",
        "reason": "exhausted_retries",
    })
    result = {
        "current_phase": "task_parked",
        # BUG-234-LOGIC-002: Use .get() to avoid KeyError on partial state
        "cycles_completed": state.get("cycles_completed", 0) + 1,
        "cycle_history": history,
        "current_task": None,
    }
    # Track token cost even for parked tasks (budget consistency)
    if "tokens_used" in state:
        from governance.workflows.orchestrator.budget import TOKEN_COST_PER_CYCLE
        result["tokens_used"] = state["tokens_used"] + TOKEN_COST_PER_CYCLE
    return result


def certify_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate certification record with impact summary.

    Produces a lightweight summary of what was done, files changed,
    and tasks completed — suitable for commit messages and GitHub issues.
    """
    history = state.get("cycle_history", [])
    # BUG-246-NOD-005: Use != for clarity (not x == y is confusing precedence)
    completed = [h for h in history if h.get("task_id") and h.get("status") != "parked"]
    parked = [h for h in history if h.get("status") == "parked"]

    # Collect all files changed across cycles
    all_files = []
    for h in completed:
        impl = h.get("implementation") or {}
        all_files.extend(impl.get("files_changed", []))
    unique_files = sorted(set(all_files))

    # BUG-ORCH-003: Use .get() for null-safe task_id access
    impact_lines = []
    for h in completed:
        tid = h.get("task_id", "unknown")
        impl = h.get("implementation") or {}
        summary = impl.get("summary", f"Completed {tid}")
        impact_lines.append(f"- {tid}: {summary}")

    certification = {
        "cycles_completed": len(completed),
        "cycles_parked": len(parked),
        "tasks_completed": [h.get("task_id", "unknown") for h in completed],
        "tasks_parked": [h.get("task_id", "unknown") for h in parked],
        "files_changed": unique_files,
        "impact_summary": "\n".join(impact_lines),
        "remaining_backlog": len(state.get("backlog", [])),
    }

    # Budget metrics if available
    if "value_delivered" in state:
        certification["value_delivered"] = state["value_delivered"]
        certification["tokens_used"] = state.get("tokens_used", 0)
        budget = state.get("token_budget", 0)
        if budget:
            certification["budget_utilization"] = round(
                state.get("tokens_used", 0) / budget * 100, 1)

    return {
        "current_phase": "certified",
        "certification": certification,
    }


def complete_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Mark the orchestrator run as complete."""
    return {
        "status": "success",
        "current_phase": "complete",
    }
