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

Usage:
    analyzer = RuleImpactAnalyzer()
    graph = analyzer.get_impact_graph()
    impact = analyzer.simulate_change("RULE-001", "deprecate")
"""

import re
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Set, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from collections import defaultdict

# Import MCP tools
from governance.compat import governance_query_rules

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent


@dataclass
class ImpactResult:
    """Result of impact analysis."""
    rule_id: str
    change_type: str
    affected: List[str]
    impact_score: float
    warnings: List[str]


@dataclass
class GraphNode:
    """Node in dependency graph."""
    rule_id: str
    name: str
    priority: str
    category: str


@dataclass
class GraphEdge:
    """Edge in dependency graph."""
    source: str
    target: str
    relationship: str  # depends_on, references, conflicts_with


class RuleImpactAnalyzer:
    """
    Analyzes rule dependencies and impacts.

    Features:
    - Dependency graph generation
    - Change impact simulation
    - Impact scoring
    - Rule clustering

    Example:
        analyzer = RuleImpactAnalyzer()
        graph = analyzer.get_impact_graph()
        impact = analyzer.simulate_change("RULE-001", "deprecate")
    """

    # Patterns for detecting references
    RULE_REF_PATTERN = re.compile(r'RULE-\d{3}')
    DECISION_REF_PATTERN = re.compile(r'DECISION-\d{3}')

    def __init__(self):
        """Initialize Rule Impact Analyzer."""
        self._rules_cache: Optional[List[Dict]] = None
        self._graph_cache: Optional[Dict] = None

    # =========================================================================
    # DATA FETCHING
    # =========================================================================

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

    # =========================================================================
    # DEPENDENCY ANALYSIS
    # =========================================================================

    def analyze_dependencies(self, rule_id: str) -> Dict[str, Any]:
        """
        Analyze dependencies for a rule.

        Args:
            rule_id: Rule ID to analyze

        Returns:
            Dependency analysis dict
        """
        rule = self._get_rule(rule_id)
        if not rule:
            return {
                'rule_id': rule_id,
                'error': 'Rule not found',
                'depends_on': [],
                'required_by': []
            }

        depends_on = self.get_required_rules(rule_id)
        required_by = self.get_dependent_rules(rule_id)

        return {
            'rule_id': rule_id,
            'name': rule.get('name', ''),
            'depends_on': depends_on,
            'required_by': required_by,
            'total_dependencies': len(depends_on) + len(required_by)
        }

    def get_dependent_rules(self, rule_id: str) -> List[str]:
        """
        Find rules that depend on a given rule.

        Args:
            rule_id: Rule ID to check

        Returns:
            List of dependent rule IDs
        """
        dependents = []
        rules = self._fetch_rules()

        for rule in rules:
            other_id = rule.get('id') or rule.get('rule_id', '')
            if other_id == rule_id:
                continue

            # Check if this rule references the target
            directive = rule.get('directive', '')
            name = rule.get('name', '')
            content = f"{name} {directive}"

            if rule_id in content:
                dependents.append(other_id)

        return dependents

    def get_required_rules(self, rule_id: str) -> List[str]:
        """
        Find rules required by a given rule.

        Args:
            rule_id: Rule ID to check

        Returns:
            List of required rule IDs
        """
        rule = self._get_rule(rule_id)
        if not rule:
            return []

        directive = rule.get('directive', '')
        name = rule.get('name', '')
        content = f"{name} {directive}"

        # Find all RULE-xxx references
        references = self.RULE_REF_PATTERN.findall(content)
        return [ref for ref in references if ref != rule_id]

    # =========================================================================
    # IMPACT GRAPH
    # =========================================================================

    def get_impact_graph(self) -> Dict[str, Any]:
        """
        Generate full impact graph for all rules.

        Returns:
            Graph dict with nodes and edges
        """
        if self._graph_cache is not None:
            return self._graph_cache

        rules = self._fetch_rules()
        nodes = []
        edges = []

        for rule in rules:
            rule_id = rule.get('id') or rule.get('rule_id', '')

            nodes.append({
                'id': rule_id,
                'name': rule.get('name', ''),
                'priority': rule.get('priority', 'MEDIUM'),
                'category': rule.get('category', 'governance')
            })

            # Add edges for dependencies
            required = self.get_required_rules(rule_id)
            for req in required:
                edges.append({
                    'source': rule_id,
                    'target': req,
                    'relationship': 'depends_on'
                })

        self._graph_cache = {
            'nodes': nodes,
            'edges': edges,
            'node_count': len(nodes),
            'edge_count': len(edges)
        }

        return self._graph_cache

    def get_subgraph(self, rule_id: str, depth: int = 2) -> Dict[str, Any]:
        """
        Get subgraph centered on a specific rule.

        Args:
            rule_id: Center rule
            depth: How many levels to include

        Returns:
            Subgraph dict
        """
        visited: Set[str] = set()
        nodes = []
        edges = []

        def traverse(rid: str, current_depth: int):
            if rid in visited or current_depth > depth:
                return
            visited.add(rid)

            rule = self._get_rule(rid)
            if rule:
                nodes.append({
                    'id': rid,
                    'name': rule.get('name', ''),
                    'depth': current_depth
                })

            # Get connected rules
            required = self.get_required_rules(rid)
            dependents = self.get_dependent_rules(rid)

            for req in required:
                edges.append({
                    'source': rid,
                    'target': req,
                    'relationship': 'depends_on'
                })
                traverse(req, current_depth + 1)

            for dep in dependents:
                edges.append({
                    'source': dep,
                    'target': rid,
                    'relationship': 'depends_on'
                })
                traverse(dep, current_depth + 1)

        traverse(rule_id, 0)

        return {
            'center': rule_id,
            'depth': depth,
            'nodes': nodes,
            'edges': edges
        }

    # =========================================================================
    # CHANGE SIMULATION
    # =========================================================================

    def simulate_change(
        self,
        rule_id: str,
        change_type: str = "modify"
    ) -> Dict[str, Any]:
        """
        Simulate the impact of changing a rule.

        Args:
            rule_id: Rule to change
            change_type: Type of change (modify, deprecate, delete)

        Returns:
            Impact simulation result
        """
        affected = self.get_affected_rules(rule_id)
        warnings = []

        # Calculate impact based on change type
        if change_type == "delete":
            warnings.append(f"Deleting {rule_id} will affect {len(affected)} rules")
            impact_score = len(affected) * 3.0
        elif change_type == "deprecate":
            warnings.append(f"Deprecating {rule_id} will impact {len(affected)} dependent rules")
            impact_score = len(affected) * 2.0
        else:  # modify
            impact_score = len(affected) * 1.0

        # Check for CRITICAL priority rules affected
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
            warnings=warnings
        ))

    def get_affected_rules(self, rule_id: str) -> List[str]:
        """
        Get all rules affected by changing a given rule.

        Includes direct dependents and transitive dependents.

        Args:
            rule_id: Rule to check

        Returns:
            List of affected rule IDs
        """
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

    # =========================================================================
    # IMPACT SCORING
    # =========================================================================

    def calculate_impact_score(self, rule_id: str) -> float:
        """
        Calculate impact score for a rule.

        Higher scores mean the rule has more impact on the system.

        Args:
            rule_id: Rule to score

        Returns:
            Impact score
        """
        rule = self._get_rule(rule_id)
        if not rule:
            return 0.0

        score = 0.0

        # Base score from priority
        priority_scores = {
            'CRITICAL': 10.0,
            'HIGH': 5.0,
            'MEDIUM': 2.0,
            'LOW': 1.0
        }
        score += priority_scores.get(rule.get('priority', 'MEDIUM'), 2.0)

        # Add score for each dependent
        dependents = self.get_dependent_rules(rule_id)
        score += len(dependents) * 2.0

        # Add score for references to other rules
        required = self.get_required_rules(rule_id)
        score += len(required) * 0.5

        return score

    def rank_by_impact(self) -> List[Dict[str, Any]]:
        """
        Rank all rules by their impact scores.

        Returns:
            List of rules sorted by impact score
        """
        rules = self._fetch_rules()
        ranked = []

        for rule in rules:
            rule_id = rule.get('id') or rule.get('rule_id', '')
            score = self.calculate_impact_score(rule_id)
            ranked.append({
                'rule_id': rule_id,
                'name': rule.get('name', ''),
                'priority': rule.get('priority', 'MEDIUM'),
                'impact_score': score
            })

        ranked.sort(key=lambda x: x['impact_score'], reverse=True)
        return ranked

    # =========================================================================
    # CLUSTERING
    # =========================================================================

    def identify_clusters(self) -> List[List[str]]:
        """
        Identify clusters of related rules.

        Returns:
            List of clusters (each cluster is a list of rule IDs)
        """
        rules = self._fetch_rules()
        visited: Set[str] = set()
        clusters = []

        def dfs(rule_id: str, cluster: List[str]):
            if rule_id in visited:
                return
            visited.add(rule_id)
            cluster.append(rule_id)

            # Get connected rules
            required = self.get_required_rules(rule_id)
            dependents = self.get_dependent_rules(rule_id)

            for connected in required + dependents:
                dfs(connected, cluster)

        for rule in rules:
            rule_id = rule.get('id') or rule.get('rule_id', '')
            if rule_id not in visited:
                cluster: List[str] = []
                dfs(rule_id, cluster)
                if cluster:
                    clusters.append(cluster)

        return clusters

    def get_rule_cluster(self, rule_id: str) -> Optional[List[str]]:
        """
        Get the cluster containing a specific rule.

        Args:
            rule_id: Rule to find cluster for

        Returns:
            List of rule IDs in the same cluster, or None
        """
        clusters = self.identify_clusters()
        for cluster in clusters:
            if rule_id in cluster:
                return cluster
        return None


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_impact_analyzer() -> RuleImpactAnalyzer:
    """
    Factory function to create Rule Impact Analyzer.

    Returns:
        RuleImpactAnalyzer instance
    """
    return RuleImpactAnalyzer()


# =============================================================================
# CLI
# =============================================================================

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
            args.rule,
            change_type=args.change or "modify"
        )
        print(json.dumps(result, indent=2))

    elif args.command == "rank":
        result = analyzer.rank_by_impact()
        for r in result[:10]:
            print(f"{r['rule_id']}: {r['impact_score']:.1f} - {r['name']}")


if __name__ == "__main__":
    main()
