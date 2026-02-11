"""
Rule Impact Analyzer (P9.4)
Created: 2024-12-25

Analyzes rule dependencies and impacts:
- Dependency graph generation
- Change simulation
- Impact scoring
- Rule clustering

Per RULE-011: Multi-Agent Governance
Per RULE-010: Evidence-Based Wisdom
Per DOC-SIZE-01-v1: Graph in rule_impact_graph.py, scoring in rule_impact_scoring.py.

Usage:
    analyzer = RuleImpactAnalyzer()
    graph = analyzer.get_impact_graph()
    impact = analyzer.simulate_change("RULE-001", "deprecate")
"""

import re
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

from governance.compat import governance_query_rules
from .rule_impact_models import (  # noqa: F401 — re-export
    GraphEdge,
    GraphNode,
    ImpactResult,
)
from .rule_impact_graph import RuleImpactGraphMixin
from .rule_impact_scoring import RuleImpactScoringMixin

PROJECT_ROOT = Path(__file__).parent.parent


class RuleImpactAnalyzer(RuleImpactGraphMixin, RuleImpactScoringMixin):
    """
    Analyzes rule dependencies and impacts.

    Features:
    - Dependency graph generation (via RuleImpactGraphMixin)
    - Change impact simulation (via RuleImpactScoringMixin)
    - Impact scoring and ranking
    - Rule clustering
    """

    RULE_REF_PATTERN = re.compile(r'RULE-\d{3}')
    DECISION_REF_PATTERN = re.compile(r'DECISION-\d{3}')

    def __init__(self):
        self._rules_cache: Optional[List[Dict]] = None
        self._graph_cache: Optional[Dict] = None

    def _fetch_rules(self) -> List[Dict]:
        """Fetch rules from MCP tools."""
        if self._rules_cache is not None:
            return self._rules_cache
        try:
            result = json.loads(governance_query_rules())
            if isinstance(result, dict) and 'error' in result:
                return []
            self._rules_cache = result if isinstance(result, list) else []
            return self._rules_cache
        except Exception:
            return []

    def _get_rule(self, rule_id: str) -> Optional[Dict]:
        """Get a specific rule by ID."""
        rules = self._fetch_rules()
        for rule in rules:
            if rule.get('id') == rule_id or rule.get('rule_id') == rule_id:
                return rule
        return None

    def analyze_dependencies(self, rule_id: str) -> Dict[str, Any]:
        """Analyze dependencies for a rule."""
        rule = self._get_rule(rule_id)
        if not rule:
            return {
                'rule_id': rule_id,
                'error': 'Rule not found',
                'depends_on': [],
                'required_by': [],
            }

        depends_on = self.get_required_rules(rule_id)
        required_by = self.get_dependent_rules(rule_id)

        return {
            'rule_id': rule_id,
            'name': rule.get('name', ''),
            'depends_on': depends_on,
            'required_by': required_by,
            'total_dependencies': len(depends_on) + len(required_by),
        }

    def get_dependent_rules(self, rule_id: str) -> List[str]:
        """Find rules that depend on a given rule."""
        dependents = []
        rules = self._fetch_rules()

        for rule in rules:
            other_id = rule.get('id') or rule.get('rule_id', '')
            if other_id == rule_id:
                continue
            directive = rule.get('directive', '')
            name = rule.get('name', '')
            content = f"{name} {directive}"
            if rule_id in content:
                dependents.append(other_id)

        return dependents

    def get_required_rules(self, rule_id: str) -> List[str]:
        """Find rules required by a given rule."""
        rule = self._get_rule(rule_id)
        if not rule:
            return []
        directive = rule.get('directive', '')
        name = rule.get('name', '')
        content = f"{name} {directive}"
        references = self.RULE_REF_PATTERN.findall(content)
        return [ref for ref in references if ref != rule_id]


def create_impact_analyzer() -> RuleImpactAnalyzer:
    """Factory function to create Rule Impact Analyzer."""
    return RuleImpactAnalyzer()


def main():
    """CLI for rule impact analyzer."""
    import argparse

    parser = argparse.ArgumentParser(description="Rule Impact Analyzer")
    parser.add_argument("command", choices=["analyze", "graph", "simulate", "rank"])
    parser.add_argument("--rule", "-r", help="Rule ID")
    parser.add_argument("--change", "-c", choices=["modify", "deprecate", "delete"])
    parser.add_argument("--depth", "-d", type=int, default=2)
    args = parser.parse_args()

    analyzer = create_impact_analyzer()

    if args.command == "analyze" and args.rule:
        result = analyzer.analyze_dependencies(args.rule)
        print(json.dumps(result, indent=2))
    elif args.command == "graph":
        if args.rule:
            result = analyzer.get_subgraph(args.rule, depth=args.depth)
        else:
            result = analyzer.get_impact_graph()
        print(json.dumps(result, indent=2))
    elif args.command == "simulate" and args.rule:
        result = analyzer.simulate_change(
            args.rule, change_type=args.change or "modify"
        )
        print(json.dumps(result, indent=2))
    elif args.command == "rank":
        result = analyzer.rank_by_impact()
        for r in result[:10]:
            print(f"{r['rule_id']}: {r['impact_score']:.1f} - {r['name']}")


if __name__ == "__main__":
    main()
