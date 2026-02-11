"""
Agent Trust Compliance & Metrics (Mixin).

Per DOC-SIZE-01-v1: Extracted from agent_trust.py (437 lines).
Compliance tracking, agent metrics, and system-wide metrics.
"""

from collections import defaultdict
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict

from .agent_trust_models import ComplianceStatus


class AgentTrustComplianceMixin:
    """Mixin providing compliance and metrics methods.

    Expects host class to provide:
        self._trust_scores: Dict[str, float]
        self._action_history: Dict[str, List[ActionRecord]]
        self._compliance_cache: Dict[str, ComplianceStatus]
        self.GOVERNANCE_RULES: List[str]
        self.get_trust_score(agent_id) -> float
        self.get_trust_level(agent_id) -> str
        self.is_trusted(agent_id) -> bool
    """

    def get_compliance_status(self, agent_id: str) -> Dict[str, Any]:
        """Get compliance status for an agent."""
        if agent_id in self._compliance_cache:
            cached = self._compliance_cache[agent_id]
            return asdict(cached)

        history = self._action_history.get(agent_id, [])
        violations = [a.action for a in history if not a.compliant]

        status = ComplianceStatus(
            agent_id=agent_id,
            compliant=len(violations) == 0,
            rules=self.GOVERNANCE_RULES,
            violations=violations[-5:],
            last_check=datetime.now().isoformat(),
        )

        self._compliance_cache[agent_id] = status
        return asdict(status)

    def get_compliance_summary(self) -> Dict[str, Any]:
        """Get system-wide compliance summary."""
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
            'timestamp': datetime.now().isoformat(),
        }

    def get_agent_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Get metrics for an agent."""
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
            'last_action': asdict(history[-1]) if history else None,
        }

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-wide metrics."""
        scores = list(self._trust_scores.values())
        avg_score = sum(scores) / max(len(scores), 1)

        trust_levels: Dict[str, int] = defaultdict(int)
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
            'timestamp': datetime.now().isoformat(),
        }
