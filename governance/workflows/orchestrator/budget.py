"""Dynamic cycle budget for the orchestrator.

Per WORKFLOW-ORCH-01-v1: Gate decision uses ROI-based budget that
balances impact (priority-weighted value) against cost (token usage)
with diminishing returns.

Budget factors:
  - remaining_value: sum of priority weights in backlog
  - value_delivered: cumulative value of completed cycles
  - token_ratio: tokens_used / token_budget
  - roi: value_delivered / max(tokens_used, 1)
"""

from typing import Any, Dict

PRIORITY_VALUE = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}

TOKEN_COST_PER_CYCLE = 10  # abstract units per cycle
TOKEN_EXHAUSTION_THRESHOLD = 0.8  # stop at 80% budget
LOW_VALUE_THRESHOLD = 0.5  # stop LOW-only tasks at 50% budget


def compute_budget(state: Dict[str, Any]) -> Dict[str, Any]:
    """Compute whether the orchestrator should continue.

    Returns dict with: should_continue, remaining_value, roi,
    token_ratio, reason.
    """
    backlog = state.get("backlog", [])
    cycles_done = state.get("cycles_completed", 0)
    hard_cap = state.get("max_cycles", 10)
    # BUG-281-BUDGET-001: Type-validate numeric fields to prevent float/str corruption
    try:
        token_budget = int(state.get("token_budget", 0) or 0)
    except (TypeError, ValueError):
        token_budget = 0
    try:
        tokens_used = max(int(state.get("tokens_used", 0) or 0), 0)
    except (TypeError, ValueError):
        tokens_used = 0
    value_delivered = state.get("value_delivered", 0)

    remaining_value = sum(
        PRIORITY_VALUE.get(t.get("priority", "LOW"), 1) for t in backlog
    )
    token_ratio = tokens_used / max(token_budget, 1) if token_budget else 0.0
    roi = value_delivered / max(tokens_used, 1)

    # Decision logic
    if not backlog:
        return _result(False, remaining_value, roi, token_ratio, "backlog_empty")

    if cycles_done >= hard_cap:
        return _result(False, remaining_value, roi, token_ratio, "max_cycles_reached")

    if token_budget and token_ratio >= TOKEN_EXHAUSTION_THRESHOLD:
        return _result(False, remaining_value, roi, token_ratio, "token_budget_exhausted")

    all_low = all(t.get("priority") == "LOW" for t in backlog)
    if all_low and token_budget and token_ratio > LOW_VALUE_THRESHOLD:
        return _result(False, remaining_value, roi, token_ratio, "low_value_remaining")

    return _result(True, remaining_value, roi, token_ratio, "budget_available")


def _result(
    should_continue: bool,
    remaining_value: int,
    roi: float,
    token_ratio: float,
    reason: str,
) -> Dict[str, Any]:
    return {
        "should_continue": should_continue,
        "remaining_value": remaining_value,
        "roi": roi,
        "token_ratio": token_ratio,
        "reason": reason,
    }
