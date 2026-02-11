"""
Rule Impact Scoring & Simulation (Mixin).

Per DOC-SIZE-01-v1: Extracted from rule_impact.py (549 lines).
Change simulation, impact scoring, and ranking.
"""

from dataclasses import asdict
from typing import Any, Dict, List, Set

from .rule_impact_models import ImpactResult


class RuleImpactScoringMixin:
    """Mixin providing scoring and simulation methods.

    Expects host class to provide:
        self._fetch_rules() -> List[Dict]
        self._get_rule(rule_id) -> Optional[Dict]
        self.get_dependent_rules(rule_id) -> List[str]
        self.get_required_rules(rule_id) -> List[str]
    """

    def simulate_change(
        self,
        rule_id: str,
        change_type: str = "modify",
    ) -> Dict[str, Any]:
        """Simulate the impact of changing a rule."""
        affected = self.get_affected_rules(rule_id)
        warnings: List[str] = []

        if change_type == "delete":
            warnings.append(f"Deleting {rule_id} will affect {len(affected)} rules")
            impact_score = len(affected) * 3.0
        elif change_type == "deprecate":
            warnings.append(f"Deprecating {rule_id} will impact {len(affected)} dependent rules")
            impact_score = len(affected) * 2.0
        else:
            impact_score = len(affected) * 1.0

        for aid in affected:
            rule = self._get_rule(aid)
            if rule and rule.get('priority') == 'CRITICAL':
                warnings.append(f"CRITICAL rule {aid} will be affected")
                impact_score += 5.0

        return asdict(ImpactResult(
            rule_id=rule_id,
            change_type=change_type,
            affected=affected,
            impact_score=impact_score,
            warnings=warnings,
        ))

    def get_affected_rules(self, rule_id: str) -> List[str]:
        """Get all rules affected by changing a given rule (transitive)."""
        affected: Set[str] = set()
        to_check = [rule_id]

        while to_check:
            current = to_check.pop()
            dependents = self.get_dependent_rules(current)

            for dep in dependents:
                if dep not in affected:
                    affected.add(dep)
                    to_check.append(dep)

        return list(affected)

    def calculate_impact_score(self, rule_id: str) -> float:
        """Calculate impact score for a rule."""
        rule = self._get_rule(rule_id)
        if not rule:
            return 0.0

        priority_scores = {
            'CRITICAL': 10.0,
            'HIGH': 5.0,
            'MEDIUM': 2.0,
            'LOW': 1.0,
        }
        score = priority_scores.get(rule.get('priority', 'MEDIUM'), 2.0)

        dependents = self.get_dependent_rules(rule_id)
        score += len(dependents) * 2.0

        required = self.get_required_rules(rule_id)
        score += len(required) * 0.5

        return score

    def rank_by_impact(self) -> List[Dict[str, Any]]:
        """Rank all rules by their impact scores."""
        rules = self._fetch_rules()
        ranked = []

        for rule in rules:
            rule_id = rule.get('id') or rule.get('rule_id', '')
            score = self.calculate_impact_score(rule_id)
            ranked.append({
                'rule_id': rule_id,
                'name': rule.get('name', ''),
                'priority': rule.get('priority', 'MEDIUM'),
                'impact_score': score,
            })

        ranked.sort(key=lambda x: x['impact_score'], reverse=True)
        return ranked
