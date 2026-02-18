"""
TypeDB Rule Inference Queries.

Per RULE-032: File Size Limit (< 300 lines)
Extracted from: governance/typedb/queries/rules.py

Created: 2026-01-04
Updated: 2026-01-30 - Added create_rule_dependency
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


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
        # BUG-255-ESC-001: Escape backslash THEN quotes for TypeQL safety
        # BUG-385-INF-001: Also strip control chars that can break TypeQL queries
        rid = rule_id.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '').replace('\r', '').replace('\t', '')
        query = f"""
            match
                $r1 isa rule-entity, has rule-id "{rid}";
                (dependent: $r1, dependency: $r2) isa rule-dependency;
                $r2 has rule-id $dep_id;
            select $dep_id;
        """
        # BUG-289-INF-001: Guard _execute_query against DB unavailability
        try:
            results = self._execute_query(query, infer=True)
        except Exception as e:
            # BUG-385-INF-002: Add exc_info for stack trace visibility
            logger.error(f"get_rule_dependencies query failed for {rule_id}: {e}", exc_info=True)
            return []
        return [r.get("dep_id") for r in results if r.get("dep_id")]

    def get_rules_depending_on(self, rule_id: str) -> List[str]:
        """Get all rules that depend on a given rule."""
        # BUG-255-ESC-001: Escape backslash THEN quotes for TypeQL safety
        # BUG-385-INF-001: Also strip control chars that can break TypeQL queries
        rid = rule_id.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '').replace('\r', '').replace('\t', '')
        query = f"""
            match
                $r1 isa rule-entity, has rule-id $id;
                $r2 isa rule-entity, has rule-id "{rid}";
                (dependent: $r1, dependency: $r2) isa rule-dependency;
            select $id;
        """
        # BUG-289-INF-001: Guard _execute_query against DB unavailability
        try:
            results = self._execute_query(query, infer=True)
        except Exception as e:
            # BUG-385-INF-002: Add exc_info for stack trace visibility
            logger.error(f"get_rules_depending_on query failed for {rule_id}: {e}", exc_info=True)
            return []
        return [r.get("id") for r in results if r.get("id")]

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
            select $id1, $id2;
        """
        # BUG-289-INF-001: Guard _execute_query against DB unavailability
        try:
            results = self._execute_query(query, infer=True)
        except Exception as e:
            # BUG-385-INF-002: Add exc_info for stack trace visibility
            logger.error(f"find_conflicts query failed: {e}", exc_info=True)
            return []
        return [{"rule1": r.get("id1"), "rule2": r.get("id2")} for r in results if r.get("id1") and r.get("id2")]

    def create_rule_dependency(self, dependent_id: str, dependency_id: str) -> bool:
        """
        Create a rule-dependency relation between two rules.

        Args:
            dependent_id: Rule that depends on the other
            dependency_id: Rule being depended upon

        Returns:
            True if relation was created
        """
        from typedb.driver import TransactionType

        try:
            # BUG-255-ESC-001: Escape backslash THEN quotes for TypeQL safety
            # BUG-385-INF-001: Also strip control chars that can break TypeQL queries
            dep_id_esc = dependent_id.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '').replace('\r', '').replace('\t', '')
            dep_on_esc = dependency_id.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '').replace('\r', '').replace('\t', '')
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                query = f"""
                    match
                        $r1 isa rule-entity, has rule-id "{dep_id_esc}";
                        $r2 isa rule-entity, has rule-id "{dep_on_esc}";
                    insert
                        (dependent: $r1, dependency: $r2) isa rule-dependency;
                """
                tx.query(query).resolve()
                tx.commit()
            logger.info(f"Created dependency: {dependent_id} -> {dependency_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to create dependency {dependent_id}->{dependency_id}: {e}")
            return False

    def get_decision_impacts(self, decision_id: str) -> List[str]:
        """
        Get all rules affected by a decision (including cascaded supersedes).
        Uses inference to follow supersede chains.
        """
        # BUG-255-ESC-001: Escape backslash THEN quotes for TypeQL safety
        # BUG-385-INF-001: Also strip control chars that can break TypeQL queries
        did = decision_id.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '').replace('\r', '').replace('\t', '')
        query = f"""
            match
                $d isa decision, has decision-id "{did}";
                (affecting-decision: $d, affected-rule: $r) isa decision-affects;
                $r has rule-id $rid;
            select $rid;
        """
        # BUG-289-INF-001: Guard _execute_query against DB unavailability
        try:
            results = self._execute_query(query, infer=True)
        except Exception as e:
            # BUG-385-INF-002: Add exc_info for stack trace visibility
            logger.error(f"get_decision_impacts query failed for {decision_id}: {e}", exc_info=True)
            return []
        return [r.get("rid") for r in results if r.get("rid")]
