"""
SFDC Fallback Workflow Runner & Diagram.

Per DOC-SIZE-01-v1: Extracted from graph.py (436 lines).
Linear fallback execution when LangGraph is not available.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state import SFDCState

from .state import MAX_DEPLOY_RETRIES

logger = logging.getLogger(__name__)


def run_fallback_workflow(graph, initial_state: "SFDCState") -> "SFDCState":
    """Run workflow in fallback mode without LangGraph.

    Executes nodes in linear sequence with basic routing.
    """
    state = initial_state.copy()

    phase_sequence = [
        "start",
        "discover",
        "develop",
        "test",
        "review",
        "deploy",
        "validate",
        "monitor",
        "report",
        "complete",
    ]

    i = 0
    while i < len(phase_sequence):
        node_name = phase_sequence[i]

        if node_name not in graph.nodes:
            i += 1
            continue

        # Check abort condition
        if state.get("status") == "failed":
            if "abort" in graph.nodes:
                state.update(graph.nodes["abort"](state))
            if "complete" in graph.nodes:
                state.update(graph.nodes["complete"](state))
            break

        # Check skip conditions
        if node_name == "monitor" and state.get("should_skip_monitor"):
            i += 1
            continue

        # Check breaking changes skip
        if node_name == "develop" and state.get("has_breaking_changes"):
            if "skip_to_report" in graph.nodes:
                state.update(graph.nodes["skip_to_report"](state))
            i = phase_sequence.index("report")
            continue

        # Execute node
        try:
            result = graph.nodes[node_name](state)
            state.update(result)
        except Exception as e:
            # BUG-473-SGF-1: Sanitize logger message + add exc_info for stack trace preservation
            logger.error(f"[SFDC] Node {node_name} failed: {type(e).__name__}", exc_info=True)
            state["status"] = "failed"
            state["error_message"] = f"Node '{node_name}' failed: {type(e).__name__}"
            break

        # Check for deployment failure -> rollback
        if node_name == "deploy" and state.get("deployment_status") == "Failed":
            if "rollback" in graph.nodes:
                state.update(graph.nodes["rollback"](state))
            i = phase_sequence.index("report")
            continue

        # Check for validation failure -> rollback
        if node_name == "validate" and not state.get("validation_passed"):
            if "rollback" in graph.nodes:
                state.update(graph.nodes["rollback"](state))
            i = phase_sequence.index("report")
            continue

        # Loop back on test failure
        if node_name == "test" and not state.get("coverage_met"):
            retry_count = state.get("retry_count", 0)
            if retry_count < MAX_DEPLOY_RETRIES:
                state["retry_count"] = retry_count + 1
                logger.info(
                    f"[SFDC] Tests failed, looping to develop "
                    f"(retry {retry_count + 1}/{MAX_DEPLOY_RETRIES})"
                )
                i = phase_sequence.index("develop")
                continue

        i += 1

    return state


def print_sfdc_workflow_diagram():
    """Print ASCII visualization of SFDC workflow."""
    print("""
SFDC LangGraph Workflow:

    START
      |
      v
    [start]--failed-->[abort]
      |                  |
      | success          |
      v                  |
    [discover]           |
      |                  |
      +--breaking-->[skip_to_report]--+
      |                               |
      | normal                        |
      v                               |
    [develop]<----------------+       |
      |                       |       |
      v                       |       |
    [test]                    |       |
      |                  loop |       |
      +--fail(retry<3)-------+       |
      |                               |
      | pass                          |
      v                               |
    [review]                          |
      |                               |
      +--security fail(retry<3)-->[develop]
      |                               |
      | pass                          |
      v                               |
    [deploy]                          |
      |                               |
      +--failed-->[rollback]----------+
      |                               |
      | success                       |
      v                               |
    [validate]                        |
      |                               |
      +--failed-->[rollback]----------+
      |                               |
      | passed                        |
      v                               |
    [monitor]                         |
      |                               |
      +---------->[report]<-----------+
                    |
                    v
               [complete]
                    |
                    v
                   END
    """)
