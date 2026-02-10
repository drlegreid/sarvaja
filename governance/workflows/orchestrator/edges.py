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
    """Route based on validation outcome."""
    if state.get("validation_passed"):
        if state.get("gaps_discovered"):
            return "inject"
        return "complete_cycle"

    if state.get("retry_count", 0) < MAX_RETRIES:
        return "loop_to_spec"
    return "park_task"
