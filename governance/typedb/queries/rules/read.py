"""
TypeDB Rule Read Queries.

Per RULE-032: File Size Limit (< 300 lines)
Extracted from: governance/typedb/queries/rules.py

Created: 2026-01-04
"""

from typing import List, Optional

from ...entities import Rule


class RuleReadQueries:
    """
    Rule read query operations for TypeDB.

    Requires a client with _execute_query and _execute_rule_query attributes.
    Uses mixin pattern for TypeDBClient composition.
    """

    def get_all_rules(self) -> List[Rule]:
        """Get all governance rules."""
        query = """
            match $r isa rule-entity,
                has rule-id $id,
                has rule-name $name,
                has category $cat,
                has priority $pri,
                has status $stat,
                has directive $dir;
            get $id, $name, $cat, $pri, $stat, $dir;
        """
        return self._execute_rule_query(query)

    def get_active_rules(self) -> List[Rule]:
        """Get only active rules."""
        query = """
            match $r isa rule-entity,
                has rule-id $id,
                has rule-name $name,
                has category $cat,
                has priority $pri,
                has status "ACTIVE",
                has directive $dir;
            get $id, $name, $cat, $pri, $dir;
        """
        results = self._execute_query(query)
        return [
            Rule(
                id=r.get("id"),
                name=r.get("name"),
                category=r.get("cat"),
                priority=r.get("pri"),
                status="ACTIVE",
                directive=r.get("dir")
            )
            for r in results
        ]

    def get_rule_by_id(self, rule_id: str) -> Optional[Rule]:
        """Get a specific rule by ID."""
        query = f"""
            match $r isa rule-entity,
                has rule-id "{rule_id}",
                has rule-name $name,
                has category $cat,
                has priority $pri,
                has status $stat,
                has directive $dir;
            get $name, $cat, $pri, $stat, $dir;
        """
        results = self._execute_query(query)
        if results:
            r = results[0]
            return Rule(
                id=rule_id,
                name=r.get("name"),
                category=r.get("cat"),
                priority=r.get("pri"),
                status=r.get("stat"),
                directive=r.get("dir")
            )
        return None

    def get_rules_by_category(self, category: str) -> List[Rule]:
        """Get rules by category."""
        query = f"""
            match $r isa rule-entity,
                has rule-id $id,
                has rule-name $name,
                has category "{category}",
                has priority $pri,
                has status $stat,
                has directive $dir;
            get $id, $name, $pri, $stat, $dir;
        """
        results = self._execute_query(query)
        return [
            Rule(
                id=r.get("id"),
                name=r.get("name"),
                category=category,
                priority=r.get("pri"),
                status=r.get("stat"),
                directive=r.get("dir")
            )
            for r in results
        ]
