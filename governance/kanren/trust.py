"""
Trust Level Constraints (RULE-011).

Per RULE-011: Multi-Agent Governance - trust-weighted constraints.
"""

from typing import Tuple
from kanren import run, var, eq, conde


def trust_level(score: float) -> str:
    """Determine trust level from score per RULE-011."""
    if score >= 0.9:
        return "expert"
    elif score >= 0.7:
        return "trusted"
    elif score >= 0.5:
        return "supervised"
    else:
        return "restricted"


def requires_supervisor(trust: str) -> Tuple:
    """
    Determine if agent trust level requires supervisor context.

    Per RULE-011: Trust < 0.7 requires supervisor approval for critical tasks.
    """
    x = var()
    return run(1, x, conde(
        [eq(trust, 'restricted'), eq(x, True)],
        [eq(trust, 'supervised'), eq(x, True)],
        [eq(trust, 'trusted'), eq(x, False)],
        [eq(trust, 'expert'), eq(x, False)]
    ))


def can_execute_priority(trust: str, priority: str) -> Tuple:
    """
    Check if agent can execute task of given priority.

    Per RULE-011:
    - CRITICAL: expert or trusted only
    - HIGH: trusted and above
    - MEDIUM/LOW: all levels
    """
    from kanren import membero
    x = var()
    return run(1, x, conde(
        # CRITICAL tasks
        [eq(priority, 'CRITICAL'), eq(trust, 'expert'), eq(x, True)],
        [eq(priority, 'CRITICAL'), eq(trust, 'trusted'), eq(x, True)],
        [eq(priority, 'CRITICAL'), eq(trust, 'supervised'), eq(x, False)],
        [eq(priority, 'CRITICAL'), eq(trust, 'restricted'), eq(x, False)],
        # HIGH tasks
        [eq(priority, 'HIGH'), membero(trust, ['expert', 'trusted', 'supervised']), eq(x, True)],
        [eq(priority, 'HIGH'), eq(trust, 'restricted'), eq(x, False)],
        # MEDIUM/LOW tasks - all can execute
        [eq(priority, 'MEDIUM'), eq(x, True)],
        [eq(priority, 'LOW'), eq(x, True)]
    ))
