"""
TypeDB Rule Inference Queries.

Per RULE-032: File Size Limit (< 300 lines)
Extracted from: governance/typedb/queries/rules.py

Created: 2026-01-04
"""

from typing import List, Dict


class RuleInferenceQueries:
    """
    Rule inference query operations for TypeDB.

    Requires a client with _execute_query attribute.
    Uses mixin pattern for TypeDBClient composition.
    """

    def get_rule_dependencies(self, rule_id: str) -> List[str]:
        """
        Get all rules that a given rule depends on (including transitive).
        Uses TypeDB inference to find transitive dependencies.
        """
        query = f"""
            match
                $r1 isa rule-entity, has rule-id "{rule_id}";
                (dependent: $r1, dependency: $r2) isa rule-dependency;
                $r2 has rule-id $dep_id;
            get $dep_id;
        """
        results = self._execute_query(query, infer=True)
        return [r.get("dep_id") for r in results]

    def get_rules_depending_on(self, rule_id: str) -> List[str]:
        """Get all rules that depend on a given rule."""
        query = f"""
            match
                $r1 isa rule-entity, has rule-id $id;
                $r2 isa rule-entity, has rule-id "{rule_id}";
                (dependent: $r1, dependency: $r2) isa rule-dependency;
            get $id;
        """
        results = self._execute_query(query, infer=True)
        return [r.get("id") for r in results]

    def find_conflicts(self) -> List[Dict[str, str]]:
        """
        Find conflicting rules using inference.
        Returns pairs of rules that have conflicts.
        """
        query = """
            match
                (conflicting-rule: $r1, conflicting-rule: $r2) isa rule-conflict;
                $r1 has rule-id $id1;
                $r2 has rule-id $id2;
            get $id1, $id2;
        """
        results = self._execute_query(query, infer=True)
        return [{"rule1": r.get("id1"), "rule2": r.get("id2")} for r in results]

    def get_decision_impacts(self, decision_id: str) -> List[str]:
        """
        Get all rules affected by a decision (including cascaded supersedes).
        Uses inference to follow supersede chains.
        """
        query = f"""
            match
                $d isa decision, has decision-id "{decision_id}";
                (affecting-decision: $d, affected-rule: $r) isa decision-affects;
                $r has rule-id $rid;
            get $rid;
        """
        results = self._execute_query(query, infer=True)
        return [r.get("rid") for r in results]
