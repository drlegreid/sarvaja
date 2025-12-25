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

Usage:
    dashboard = AgentTrustDashboard()
    score = dashboard.get_trust_score("agent-001")
    dashboard.record_action("agent-001", "query_rules", compliant=True)
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict
from collections import defaultdict

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent


@dataclass
class ActionRecord:
    """Record of an agent action."""
    agent_id: str
    action: str
    compliant: bool
    timestamp: str
    trust_delta: float


@dataclass
class ComplianceStatus:
    """Compliance status for an agent."""
    agent_id: str
    compliant: bool
    rules: List[str]
    violations: List[str]
    last_check: str


class AgentTrustDashboard:
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

    Example:
        dashboard = AgentTrustDashboard()
        score = dashboard.get_trust_score("agent-001")
        dashboard.record_action("agent-001", "query_rules", compliant=True)
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
        'RULE-011',  # Multi-Agent Governance
        'RULE-013',  # Agent Permission Control
        'RULE-001',  # Session Evidence Logging
        'RULE-007',  # MCP Usage Protocol
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
        """
        Get trust score for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Trust score (0-100)
        """
        if agent_id not in self._trust_scores:
            self._trust_scores[agent_id] = self.DEFAULT_TRUST_SCORE
        return self._trust_scores[agent_id]

    def set_trust_score(self, agent_id: str, score: float) -> float:
        """
        Set trust score for an agent.

        Args:
            agent_id: Agent identifier
            score: New trust score

        Returns:
            Clamped trust score
        """
        clamped = max(self.MIN_TRUST_SCORE, min(self.MAX_TRUST_SCORE, score))
        self._trust_scores[agent_id] = clamped
        return clamped

    def get_all_trust_scores(self) -> Dict[str, float]:
        """
        Get trust scores for all known agents.

        Returns:
            Dict of agent_id -> trust_score
        """
        return dict(self._trust_scores)

    def get_trust_level(self, agent_id: str) -> str:
        """
        Get trust level category for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Trust level: HIGH, MEDIUM, LOW, or UNTRUSTED
        """
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
        """
        Check if agent meets trust threshold.

        Args:
            agent_id: Agent identifier

        Returns:
            True if trusted
        """
        return self.get_trust_score(agent_id) >= self.TRUSTED_THRESHOLD

    # =========================================================================
    # COMPLIANCE TRACKING
    # =========================================================================

    def get_compliance_status(self, agent_id: str) -> Dict[str, Any]:
        """
        Get compliance status for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Compliance status dict
        """
        # Check cached status
        if agent_id in self._compliance_cache:
            cached = self._compliance_cache[agent_id]
            return asdict(cached)

        # Calculate compliance from action history
        history = self._action_history.get(agent_id, [])
        violations = [a.action for a in history if not a.compliant]

        status = ComplianceStatus(
            agent_id=agent_id,
            compliant=len(violations) == 0,
            rules=self.GOVERNANCE_RULES,
            violations=violations[-5:],  # Last 5 violations
            last_check=datetime.now().isoformat()
        )

        self._compliance_cache[agent_id] = status
        return asdict(status)

    def get_compliance_summary(self) -> Dict[str, Any]:
        """
        Get system-wide compliance summary.

        Returns:
            Compliance summary dict
        """
        total_agents = len(self._trust_scores)
        compliant_count = 0
        violation_count = 0

        for agent_id in self._trust_scores:
            status = self.get_compliance_status(agent_id)
            if status['compliant']:
                compliant_count += 1
            violation_count += len(status.get('violations', []))

        return {
            'total_agents': total_agents,
            'compliant_agents': compliant_count,
            'non_compliant_agents': total_agents - compliant_count,
            'total_violations': violation_count,
            'compliance_rate': compliant_count / max(total_agents, 1),
            'tracked_rules': self.GOVERNANCE_RULES,
            'timestamp': datetime.now().isoformat()
        }

    # =========================================================================
    # ACTION RECORDING
    # =========================================================================

    def record_action(
        self,
        agent_id: str,
        action: str,
        compliant: bool,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Record an agent action.

        Args:
            agent_id: Agent identifier
            action: Action taken
            compliant: Whether action was compliant
            metadata: Optional action metadata

        Returns:
            Recording result
        """
        # Calculate trust adjustment
        current_score = self.get_trust_score(agent_id)

        if compliant:
            trust_delta = self.COMPLIANT_BONUS
        else:
            trust_delta = -self.NON_COMPLIANT_PENALTY

        new_score = self.set_trust_score(agent_id, current_score + trust_delta)

        # Record action
        record = ActionRecord(
            agent_id=agent_id,
            action=action,
            compliant=compliant,
            timestamp=datetime.now().isoformat(),
            trust_delta=trust_delta
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
            'new_trust_score': new_score
        }

    # =========================================================================
    # TRUST HISTORY
    # =========================================================================

    def get_trust_history(
        self,
        agent_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get trust history for an agent.

        Args:
            agent_id: Agent identifier
            limit: Maximum records to return

        Returns:
            List of action records
        """
        history = self._action_history.get(agent_id, [])
        recent = history[-limit:]
        return [asdict(record) for record in recent]

    # =========================================================================
    # METRICS
    # =========================================================================

    def get_agent_metrics(self, agent_id: str) -> Dict[str, Any]:
        """
        Get metrics for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent metrics dict
        """
        history = self._action_history.get(agent_id, [])
        total_actions = len(history)
        compliant_actions = sum(1 for a in history if a.compliant)

        return {
            'agent_id': agent_id,
            'trust_score': self.get_trust_score(agent_id),
            'trust_level': self.get_trust_level(agent_id),
            'is_trusted': self.is_trusted(agent_id),
            'total_actions': total_actions,
            'compliant_actions': compliant_actions,
            'compliance_rate': compliant_actions / max(total_actions, 1),
            'last_action': asdict(history[-1]) if history else None
        }

    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get system-wide metrics.

        Returns:
            System metrics dict
        """
        scores = list(self._trust_scores.values())
        avg_score = sum(scores) / max(len(scores), 1)

        trust_levels = defaultdict(int)
        for agent_id in self._trust_scores:
            level = self.get_trust_level(agent_id)
            trust_levels[level] += 1

        total_actions = sum(len(h) for h in self._action_history.values())

        return {
            'total_agents': len(self._trust_scores),
            'average_trust_score': avg_score,
            'trust_levels': dict(trust_levels),
            'total_actions_recorded': total_actions,
            'compliance_summary': self.get_compliance_summary(),
            'timestamp': datetime.now().isoformat()
        }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_trust_dashboard() -> AgentTrustDashboard:
    """
    Factory function to create Agent Trust Dashboard.

    Returns:
        AgentTrustDashboard instance
    """
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
            args.compliant
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
