"""
Rule Impact Graph & Clustering (Mixin).

Per DOC-SIZE-01-v1: Extracted from rule_impact.py (549 lines).
Dependency graph generation, subgraph extraction, and rule clustering.
"""

from typing import Any, Dict, List, Optional, Set


class RuleImpactGraphMixin:
    """Mixin providing graph and clustering methods.

    Expects host class to provide:
        self._graph_cache: Optional[Dict]
        self._fetch_rules() -> List[Dict]
        self._get_rule(rule_id) -> Optional[Dict]
        self.get_required_rules(rule_id) -> List[str]
        self.get_dependent_rules(rule_id) -> List[str]
    """

    def get_impact_graph(self) -> Dict[str, Any]:
        """Generate full impact graph for all rules."""
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
                'category': rule.get('category', 'governance'),
            })

            required = self.get_required_rules(rule_id)
            for req in required:
                edges.append({
                    'source': rule_id,
                    'target': req,
                    'relationship': 'depends_on',
                })

        self._graph_cache = {
            'nodes': nodes,
            'edges': edges,
            'node_count': len(nodes),
            'edge_count': len(edges),
        }
        return self._graph_cache

    def get_subgraph(self, rule_id: str, depth: int = 2) -> Dict[str, Any]:
        """Get subgraph centered on a specific rule."""
        visited: Set[str] = set()
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, str]] = []

        def traverse(rid: str, current_depth: int):
            if rid in visited or current_depth > depth:
                return
            visited.add(rid)

            rule = self._get_rule(rid)
            if rule:
                nodes.append({
                    'id': rid,
                    'name': rule.get('name', ''),
                    'depth': current_depth,
                })

            required = self.get_required_rules(rid)
            dependents = self.get_dependent_rules(rid)

            for req in required:
                edges.append({
                    'source': rid,
                    'target': req,
                    'relationship': 'depends_on',
                })
                traverse(req, current_depth + 1)

            for dep in dependents:
                edges.append({
                    'source': dep,
                    'target': rid,
                    'relationship': 'depends_on',
                })
                traverse(dep, current_depth + 1)

        traverse(rule_id, 0)

        return {
            'center': rule_id,
            'depth': depth,
            'nodes': nodes,
            'edges': edges,
        }

    def identify_clusters(self) -> List[List[str]]:
        """Identify clusters of related rules."""
        rules = self._fetch_rules()
        visited: Set[str] = set()
        clusters: List[List[str]] = []

        def dfs(rule_id: str, cluster: List[str]):
            if rule_id in visited:
                return
            visited.add(rule_id)
            cluster.append(rule_id)

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
        """Get the cluster containing a specific rule."""
        clusters = self.identify_clusters()
        for cluster in clusters:
            if rule_id in cluster:
                return cluster
        return None
