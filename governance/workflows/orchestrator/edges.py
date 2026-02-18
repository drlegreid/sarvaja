"""Orchestrator conditional routing edges.

Per WORKFLOW-ORCH-01-v1: Edges determine the next node
based on gate decisions and validation outcomes.
"""

from typing import Any, Dict

from governance.workflows.orchestrator.state import MAX_RETRIES


def check_gate_decision(state: Dict[str, Any]) -> str:
    """Route based on gate node's decision."""
    if state.get("gate_decision") == "continue":
        return "backlog"
    return "complete"


def check_validation_result(state: Dict[str, Any]) -> str:
    """Route based on validation outcome.

    BUG-246-EDG-001: Distinguish None (never ran / error) from False (failed).
    None → park immediately (no point retrying a broken pipeline).
    False → retry up to MAX_RETRIES, then park.
    """
    vp = state.get("validation_passed")
    if vp is True:
        if state.get("gaps_discovered"):
            return "inject"
        return "complete_cycle"

    # None means validation didn't produce a result — park, don't retry
    if vp is None:
        return "park_task"

    # Explicit False — retry if budget allows
    if state.get("retry_count", 0) < MAX_RETRIES:
        return "loop_to_spec"
    return "park_task"
