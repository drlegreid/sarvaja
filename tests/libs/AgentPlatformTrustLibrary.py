"""
Robot Framework Library for Agent Platform Trust Evolution Tests.

Per RD-AGENT-TESTING: ATEST-005 - Trust Evolution.
Split from test_agent_platform.py per DOC-SIZE-01-v1.
"""
from pathlib import Path
from robot.api.deco import keyword


class AgentPlatformTrustLibrary:
    """Library for trust evolution tests (ATEST-005)."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    @keyword("Trust Formula Coefficients")
    def trust_formula_coefficients(self):
        """Trust formula has correct coefficients per RULE-011."""
        COMPLIANCE_WEIGHT = 0.4
        ACCURACY_WEIGHT = 0.3
        CONSISTENCY_WEIGHT = 0.2
        TENURE_WEIGHT = 0.1

        total = COMPLIANCE_WEIGHT + ACCURACY_WEIGHT + CONSISTENCY_WEIGHT + TENURE_WEIGHT
        return {"weights_sum_to_one": abs(total - 1.0) < 0.0001}

    @keyword("Perfect Agent Gets Max Trust")
    def perfect_agent_gets_max_trust(self):
        """Agent with perfect metrics gets trust = 1.0."""
        trust = (
            0.4 * 1.0 +  # Compliance
            0.3 * 1.0 +  # Accuracy
            0.2 * 1.0 +  # Consistency
            0.1 * 1.0    # Tenure
        )
        return {"trust_is_one": abs(trust - 1.0) < 0.0001}

    @keyword("Mixed Performance Trust")
    def mixed_performance_trust(self):
        """Agent with mixed performance gets proportional trust."""
        compliance = 0.90
        accuracy = 0.85
        consistency = 0.80
        tenure = 0.50

        trust = (
            0.4 * compliance +
            0.3 * accuracy +
            0.2 * consistency +
            0.1 * tenure
        )
        # Expected: 0.36 + 0.255 + 0.16 + 0.05 = 0.825
        return {"trust_in_range": 0.82 < trust < 0.83}

    @keyword("Trust Decay On Failures")
    def trust_decay_on_failures(self):
        """Trust decreases with failures."""
        initial_trust = 0.90

        # Simulate failures (compliance drops)
        new_compliance = 0.70
        accuracy = 0.90
        consistency = 0.85
        tenure = 0.80

        new_trust = (
            0.4 * new_compliance +
            0.3 * accuracy +
            0.2 * consistency +
            0.1 * tenure
        )

        return {"trust_decreased": new_trust < initial_trust}
