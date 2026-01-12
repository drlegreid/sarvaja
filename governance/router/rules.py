"""
Rule Routing Mixin
Created: 2024-12-25 (P7.3)
Modularized: 2026-01-02 (RULE-032)

Handles routing rules to TypeDB.
"""
from typing import Dict, Any
from datetime import datetime
from dataclasses import asdict

from governance.router.models import RouteResult


class RuleRoutingMixin:
    """Mixin for rule routing operations."""

    def route_rule(
        self,
        rule_id: str,
        name: str,
        directive: str = "",
        category: str = "governance",
        priority: str = "MEDIUM",
        status: str = "ACTIVE"
    ) -> Dict[str, Any]:
        """
        Route a new rule to TypeDB.

        Args:
            rule_id: Rule ID (e.g., "RULE-023")
            name: Rule name/title
            directive: Rule directive (the actual rule text)
            category: Rule category
            priority: Rule priority (CRITICAL, HIGH, MEDIUM, LOW)
            status: Rule status (ACTIVE, DRAFT, DEPRECATED)

        Returns:
            RouteResult as dict
        """
        # Validate
        if not rule_id:
            return asdict(RouteResult(
                success=False,
                destination='none',
                item_type='rule',
                item_id=rule_id,
                error='rule_id is required'
            ))

        # Pre-hook
        data = {
            'rule_id': rule_id,
            'name': name,
            'directive': directive,
            'category': category,
            'priority': priority,
            'status': status
        }
        if self.pre_route_hook:
            data = self.pre_route_hook('rule', data)

        # Generate TypeQL
        typeql = self._generate_rule_typeql(**data)

        # Execute (or dry run)
        embedded = False
        if not self.dry_run:
            success = self._execute_typeql(typeql)
            if success and self.embed and self.embedding_pipeline:
                self.embedding_pipeline.embed_and_store_rule(
                    rule_id,
                    f"{name}: {directive}"
                )
                embedded = True
        else:
            success = True
            embedded = self.embed

        result = asdict(RouteResult(
            success=success,
            destination='typedb',
            item_type='rule',
            item_id=rule_id,
            embedded=embedded
        ))

        # Post-hook
        if self.post_route_hook:
            self.post_route_hook('rule', result)

        return result

    def _generate_rule_typeql(
        self,
        rule_id: str,
        name: str,
        directive: str = "",
        category: str = "governance",
        priority: str = "MEDIUM",
        status: str = "ACTIVE"
    ) -> str:
        """Generate TypeQL insert for rule."""
        return f'''
            insert $r isa rule-entity,
                has id "{self._escape(rule_id)}",
                has name "{self._escape(name)}",
                has directive "{self._escape(directive)}",
                has category "{self._escape(category)}",
                has priority "{self._escape(priority)}",
                has status "{self._escape(status)}",
                has created-date {datetime.now().isoformat()};
        '''
