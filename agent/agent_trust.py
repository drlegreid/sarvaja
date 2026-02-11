"""
Agent Trust Dashboard (P9.5)
Created: 2024-12-25

RULE-011 compliance metrics and agent trust tracking:
- Trust score calculation
- Compliance monitoring
- Action recording
- Trust history

Per RULE-011: Multi-Agent Governance
Per RULE-013: Agent Permission Control
Per DOC-SIZE-01-v1: Models in agent_trust_models.py, compliance in agent_trust_compliance.py.

Usage:
    dashboard = AgentTrustDashboard()
    score = dashboard.get_trust_score("agent-001")
    dashboard.record_action("agent-001", "query_rules", compliant=True)
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import asdict
from collections import defaultdict

from .agent_trust_models import ActionRecord, ComplianceStatus  # noqa: F401
from .agent_trust_compliance import AgentTrustComplianceMixin  # noqa: F401 — re-export

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent


class AgentTrustDashboard(AgentTrustComplianceMixin):
    """
    Agent Trust Dashboard.

    Tracks agent trust scores based on RULE-011 compliance:
    - Trust scores from 0-100
    - Compliance monitoring
    - Action recording with trust adjustments
    - Historical tracking

    Trust Levels:
    - HIGH (80-100): Full access
    - MEDIUM (50-79): Standard access
    - LOW (25-49): Restricted access
    - UNTRUSTED (0-24): No access
    """

    # Trust score constants
    DEFAULT_TRUST_SCORE = 75.0
    MIN_TRUST_SCORE = 0.0
    MAX_TRUST_SCORE = 100.0

    # Trust adjustments
    COMPLIANT_BONUS = 0.5
    NON_COMPLIANT_PENALTY = 5.0

    # Trust thresholds
    HIGH_THRESHOLD = 80.0
    MEDIUM_THRESHOLD = 50.0
    LOW_THRESHOLD = 25.0
    TRUSTED_THRESHOLD = 50.0

    # Governance rules tracked
    GOVERNANCE_RULES = [
        'RULE-011',
        'RULE-013',
        'RULE-001',
        'RULE-007',
    ]

    def __init__(self):
        """Initialize Agent Trust Dashboard."""
        self._trust_scores: Dict[str, float] = {}
        self._action_history: Dict[str, List[ActionRecord]] = defaultdict(list)
        self._compliance_cache: Dict[str, ComplianceStatus] = {}
        self.default_trust_score = self.DEFAULT_TRUST_SCORE

    # =========================================================================
    # TRUST SCORING
    # =========================================================================

    def get_trust_score(self, agent_id: str) -> float:
        """Get trust score for an agent (0-100)."""
        if agent_id not in self._trust_scores:
            self._trust_scores[agent_id] = self.DEFAULT_TRUST_SCORE
        return self._trust_scores[agent_id]

    def set_trust_score(self, agent_id: str, score: float) -> float:
        """Set trust score for an agent (clamped to 0-100)."""
        clamped = max(self.MIN_TRUST_SCORE, min(self.MAX_TRUST_SCORE, score))
        self._trust_scores[agent_id] = clamped
        return clamped

    def get_all_trust_scores(self) -> Dict[str, float]:
        """Get trust scores for all known agents."""
        return dict(self._trust_scores)

    def get_trust_level(self, agent_id: str) -> str:
        """Get trust level category: HIGH, MEDIUM, LOW, or UNTRUSTED."""
        score = self.get_trust_score(agent_id)

        if score >= self.HIGH_THRESHOLD:
            return 'HIGH'
        elif score >= self.MEDIUM_THRESHOLD:
            return 'MEDIUM'
        elif score >= self.LOW_THRESHOLD:
            return 'LOW'
        else:
            return 'UNTRUSTED'

    def is_trusted(self, agent_id: str) -> bool:
        """Check if agent meets trust threshold."""
        return self.get_trust_score(agent_id) >= self.TRUSTED_THRESHOLD

    # =========================================================================
    # ACTION RECORDING
    # =========================================================================

    def record_action(
        self,
        agent_id: str,
        action: str,
        compliant: bool,
        metadata: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Record an agent action and adjust trust score."""
        current_score = self.get_trust_score(agent_id)

        if compliant:
            trust_delta = self.COMPLIANT_BONUS
        else:
            trust_delta = -self.NON_COMPLIANT_PENALTY

        new_score = self.set_trust_score(agent_id, current_score + trust_delta)

        record = ActionRecord(
            agent_id=agent_id,
            action=action,
            compliant=compliant,
            timestamp=datetime.now().isoformat(),
            trust_delta=trust_delta,
        )

        self._action_history[agent_id].append(record)

        # Invalidate compliance cache
        if agent_id in self._compliance_cache:
            del self._compliance_cache[agent_id]

        return {
            'success': True,
            'agent_id': agent_id,
            'action': action,
            'compliant': compliant,
            'trust_delta': trust_delta,
            'new_trust_score': new_score,
        }

    # =========================================================================
    # TRUST HISTORY
    # =========================================================================

    def get_trust_history(
        self,
        agent_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get trust history for an agent."""
        history = self._action_history.get(agent_id, [])
        recent = history[-limit:]
        return [asdict(record) for record in recent]


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_trust_dashboard() -> AgentTrustDashboard:
    """Factory function to create Agent Trust Dashboard."""
    return AgentTrustDashboard()


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI for agent trust dashboard."""
    import argparse

    parser = argparse.ArgumentParser(description="Agent Trust Dashboard")
    parser.add_argument("command", choices=["score", "compliance", "record", "metrics"])
    parser.add_argument("--agent", "-a", help="Agent ID")
    parser.add_argument("--action", help="Action to record")
    parser.add_argument("--compliant", action="store_true")
    args = parser.parse_args()

    dashboard = create_trust_dashboard()

    if args.command == "score" and args.agent:
        score = dashboard.get_trust_score(args.agent)
        level = dashboard.get_trust_level(args.agent)
        print(f"Agent: {args.agent}")
        print(f"Trust Score: {score:.1f}")
        print(f"Trust Level: {level}")

    elif args.command == "compliance":
        if args.agent:
            status = dashboard.get_compliance_status(args.agent)
        else:
            status = dashboard.get_compliance_summary()
        print(json.dumps(status, indent=2))

    elif args.command == "record" and args.agent and args.action:
        result = dashboard.record_action(
            args.agent,
            args.action,
            args.compliant,
        )
        print(json.dumps(result, indent=2))

    elif args.command == "metrics":
        if args.agent:
            metrics = dashboard.get_agent_metrics(args.agent)
        else:
            metrics = dashboard.get_system_metrics()
        print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
