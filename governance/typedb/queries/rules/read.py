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
        """Get all governance rules including optional attributes."""
        # First get core attributes (required)
        # TypeDB 3.x: no 'get' clause, just 'match'
        query = """
            match $r isa rule-entity,
                has rule-id $id,
                has rule-name $name,
                has category $cat,
                has priority $pri,
                has status $stat,
                has directive $dir;
        """
        results = self._execute_query(query)

        # Build rules with core attributes
        rules = []
        for r in results:
            rule_id = r.get("id")

            # Try to get optional rule_type
            rule_type = None
            type_query = f"""
                match $r isa rule-entity,
                    has rule-id "{rule_id}",
                    has rule-type $type;
                            """
            try:
                type_results = self._execute_query(type_query)
                if type_results:
                    rule_type = type_results[0].get("type")
            except Exception:
                pass  # rule_type is optional

            # Try to get optional semantic_id (META-TAXON-01-v1)
            semantic_id = None
            sid_query = f"""
                match $r isa rule-entity,
                    has rule-id "{rule_id}",
                    has semantic-id $sid;
                            """
            try:
                sid_results = self._execute_query(sid_query)
                if sid_results:
                    semantic_id = sid_results[0].get("sid")
            except Exception:
                pass  # semantic_id is optional

            # Try to get optional applicability (RD-RULE-APPLICABILITY)
            applicability = None
            app_query = f"""
                match $r isa rule-entity,
                    has rule-id "{rule_id}",
                    has applicability $app;
                            """
            try:
                app_results = self._execute_query(app_query)
                if app_results:
                    applicability = app_results[0].get("app")
            except Exception:
                pass  # applicability is optional

            rules.append(Rule(
                id=rule_id,
                name=r.get("name"),
                category=r.get("cat"),
                priority=r.get("pri"),
                status=r.get("stat"),
                directive=r.get("dir"),
                rule_type=rule_type,
                semantic_id=semantic_id,
                applicability=applicability
            ))

        return rules

    def get_active_rules(self) -> List[Rule]:
        """Get only active rules including optional attributes."""
        query = """
            match $r isa rule-entity,
                has rule-id $id,
                has rule-name $name,
                has category $cat,
                has priority $pri,
                has status "ACTIVE",
                has directive $dir;
        """
        results = self._execute_query(query)

        rules = []
        for r in results:
            rule_id = r.get("id")

            # Try to get optional rule_type
            rule_type = None
            type_query = f"""
                match $r isa rule-entity,
                    has rule-id "{rule_id}",
                    has rule-type $type;
                            """
            try:
                type_results = self._execute_query(type_query)
                if type_results:
                    rule_type = type_results[0].get("type")
            except Exception:
                pass

            # Try to get optional semantic_id
            semantic_id = None
            sid_query = f"""
                match $r isa rule-entity,
                    has rule-id "{rule_id}",
                    has semantic-id $sid;
                            """
            try:
                sid_results = self._execute_query(sid_query)
                if sid_results:
                    semantic_id = sid_results[0].get("sid")
            except Exception:
                pass

            # Try to get optional applicability (RD-RULE-APPLICABILITY)
            applicability = None
            app_query = f"""
                match $r isa rule-entity,
                    has rule-id "{rule_id}",
                    has applicability $app;
                            """
            try:
                app_results = self._execute_query(app_query)
                if app_results:
                    applicability = app_results[0].get("app")
            except Exception:
                pass

            rules.append(Rule(
                id=rule_id,
                name=r.get("name"),
                category=r.get("cat"),
                priority=r.get("pri"),
                status="ACTIVE",
                directive=r.get("dir"),
                rule_type=rule_type,
                semantic_id=semantic_id,
                applicability=applicability
            ))

        return rules

    def get_rule_by_id(self, rule_id: str) -> Optional[Rule]:
        """Get a specific rule by ID."""
        # First get core attributes
        query = f"""
            match $r isa rule-entity,
                has rule-id "{rule_id}",
                has rule-name $name,
                has category $cat,
                has priority $pri,
                has status $stat,
                has directive $dir;
        """
        results = self._execute_query(query)
        if not results:
            return None

        r = results[0]

        # Try to get optional rule_type
        rule_type = None
        type_query = f"""
            match $r isa rule-entity,
                has rule-id "{rule_id}",
                has rule-type $type;
                    """
        type_results = self._execute_query(type_query)
        if type_results:
            rule_type = type_results[0].get("type")

        # Try to get optional semantic_id (META-TAXON-01-v1)
        semantic_id = None
        sid_query = f"""
            match $r isa rule-entity,
                has rule-id "{rule_id}",
                has semantic-id $sid;
                    """
        sid_results = self._execute_query(sid_query)
        if sid_results:
            semantic_id = sid_results[0].get("sid")

        # Try to get optional applicability (RD-RULE-APPLICABILITY)
        applicability = None
        app_query = f"""
            match $r isa rule-entity,
                has rule-id "{rule_id}",
                has applicability $app;
                    """
        app_results = self._execute_query(app_query)
        if app_results:
            applicability = app_results[0].get("app")

        return Rule(
            id=rule_id,
            name=r.get("name"),
            category=r.get("cat"),
            priority=r.get("pri"),
            status=r.get("stat"),
            directive=r.get("dir"),
            rule_type=rule_type,
            semantic_id=semantic_id,
            applicability=applicability
        )

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

    def get_tasks_for_rule(self, rule_id: str) -> List[dict]:
        """
        Get tasks implementing a specific rule.

        Per UI-AUDIT-003: Rule↔task traceability for dashboard.
        Per GAP-UI-AUDIT-001: Rules view should show implementing tasks.

        Args:
            rule_id: Rule ID (e.g., "RULE-001" or "SESSION-EVID-01-v1")

        Returns:
            List of task dicts with id, name, status, priority
        """
        query = f"""
            match
                $r isa rule-entity, has rule-id "{rule_id}";
                (implementing-task: $t, implemented-rule: $r) isa implements-rule;
                $t has task-id $tid,
                   has task-name $tname,
                   has task-status $tstat;
        """
        results = self._execute_query(query)

        tasks = []
        for r in results:
            task_id = r.get("tid")
            # Get optional priority
            priority = "MEDIUM"
            try:
                pq = f'''
                    match $t isa task, has task-id "{task_id}", has priority $p;
                '''
                pr = self._execute_query(pq)
                if pr:
                    priority = pr[0].get("p", "MEDIUM")
            except Exception:
                pass

            tasks.append({
                "task_id": task_id,
                "name": r.get("tname"),
                "status": r.get("tstat"),
                "priority": priority
            })

        return tasks
