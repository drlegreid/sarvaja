"""
TypeDB Capability Queries — agent-capability relation CRUD.

Per P2-12: Wires rule→agent capability bindings to TypeDB.
Uses mixin pattern for TypeDBClient composition.

Created: 2026-03-19
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class CapabilityQueries:
    """
    Capability query operations for TypeDB.

    Manages agent-capability relations: which rules govern which agents.
    Requires a client with _execute_query, _execute_write, and _driver attributes.
    """

    def _escape_id(self, value: str) -> str:
        """Escape a string for TypeQL safety."""
        return value.replace('\\', '\\\\').replace('"', '\\"')

    def create_capability(
        self,
        agent_id: str,
        rule_id: str,
        category: str = "general",
        status: str = "active",
    ) -> bool:
        """Create an agent-capability relation in TypeDB.

        Args:
            agent_id: Agent ID (e.g., "code-agent")
            rule_id: Rule ID (e.g., "TEST-GUARD-01")
            category: Capability category (coding, testing, governance, etc.)
            status: Initial status ("active" or "suspended")

        Returns:
            True if created successfully, False otherwise
        """
        from typedb.driver import TransactionType

        aid = self._escape_id(agent_id)
        rid = self._escape_id(rule_id)
        cat = self._escape_id(category)
        stat = self._escape_id(status)

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                query = f"""
                    match
                        $a isa agent, has agent-id "{aid}";
                        $r isa rule-entity, has rule-id "{rid}";
                    insert
                        (capable-agent: $a, governing-rule: $r) isa agent-capability,
                            has capability-category "{cat}",
                            has capability-status "{stat}";
                """
                tx.query(query).resolve()
                tx.commit()
            return True
        except Exception as e:
            logger.error(
                f"Failed to create capability {agent_id}→{rule_id}: {type(e).__name__}",
                exc_info=True,
            )
            return False

    def delete_capability(self, agent_id: str, rule_id: str) -> bool:
        """Delete an agent-capability relation from TypeDB.

        Args:
            agent_id: Agent ID
            rule_id: Rule ID

        Returns:
            True if deleted, False otherwise
        """
        from typedb.driver import TransactionType

        aid = self._escape_id(agent_id)
        rid = self._escape_id(rule_id)

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                query = f"""
                    match
                        $a isa agent, has agent-id "{aid}";
                        $r isa rule-entity, has rule-id "{rid}";
                        $c (capable-agent: $a, governing-rule: $r) isa agent-capability;
                    delete $c;
                """
                tx.query(query).resolve()
                tx.commit()
            return True
        except Exception as e:
            logger.error(
                f"Failed to delete capability {agent_id}→{rule_id}: {type(e).__name__}",
                exc_info=True,
            )
            return False

    def update_capability_status(
        self, agent_id: str, rule_id: str, new_status: str
    ) -> bool:
        """Update the status of an agent-capability relation.

        Args:
            agent_id: Agent ID
            rule_id: Rule ID
            new_status: New status ("active" or "suspended")

        Returns:
            True if updated, False otherwise
        """
        from typedb.driver import TransactionType

        aid = self._escape_id(agent_id)
        rid = self._escape_id(rule_id)
        stat = self._escape_id(new_status)

        try:
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                # Delete old status attribute
                try:
                    tx.query(f"""
                        match
                            $a isa agent, has agent-id "{aid}";
                            $r isa rule-entity, has rule-id "{rid}";
                            $c (capable-agent: $a, governing-rule: $r) isa agent-capability,
                                has capability-status $old;
                        delete has $old of $c;
                    """).resolve()
                except Exception:
                    pass  # May not have existing status
                # Insert new status
                tx.query(f"""
                    match
                        $a isa agent, has agent-id "{aid}";
                        $r isa rule-entity, has rule-id "{rid}";
                        $c (capable-agent: $a, governing-rule: $r) isa agent-capability;
                    insert $c has capability-status "{stat}";
                """).resolve()
                tx.commit()
            return True
        except Exception as e:
            logger.error(
                f"Failed to update capability status {agent_id}→{rule_id}: {type(e).__name__}",
                exc_info=True,
            )
            return False

    def get_capabilities_for_agent(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all capability bindings for an agent from TypeDB.

        Returns:
            List of dicts with agent_id, rule_id, category, status
        """
        aid = self._escape_id(agent_id)
        try:
            results = self._execute_query(f"""
                match
                    $a isa agent, has agent-id "{aid}";
                    $r isa rule-entity, has rule-id $rid;
                    $c (capable-agent: $a, governing-rule: $r) isa agent-capability,
                        has capability-category $cat,
                        has capability-status $stat;
                select $rid, $cat, $stat;
            """)
            return [
                {
                    "agent_id": agent_id,
                    "rule_id": r.get("rid", ""),
                    "category": r.get("cat", "general"),
                    "status": r.get("stat", "active"),
                }
                for r in results
            ]
        except Exception as e:
            logger.error(
                f"Failed to get capabilities for agent {agent_id}: {type(e).__name__}",
                exc_info=True,
            )
            return []

    def get_agents_for_rule(self, rule_id: str) -> List[Dict[str, Any]]:
        """Get all agents bound to a rule from TypeDB.

        Returns:
            List of dicts with agent_id, rule_id, category, status
        """
        rid = self._escape_id(rule_id)
        try:
            results = self._execute_query(f"""
                match
                    $a isa agent, has agent-id $aid;
                    $r isa rule-entity, has rule-id "{rid}";
                    $c (capable-agent: $a, governing-rule: $r) isa agent-capability,
                        has capability-category $cat,
                        has capability-status $stat;
                select $aid, $cat, $stat;
            """)
            return [
                {
                    "agent_id": r.get("aid", ""),
                    "rule_id": rule_id,
                    "category": r.get("cat", "general"),
                    "status": r.get("stat", "active"),
                }
                for r in results
            ]
        except Exception as e:
            logger.error(
                f"Failed to get agents for rule {rule_id}: {type(e).__name__}",
                exc_info=True,
            )
            return []

    def get_all_capabilities(self) -> List[Dict[str, Any]]:
        """Get all agent-capability relations from TypeDB.

        Returns:
            List of dicts with agent_id, rule_id, category, status
        """
        try:
            results = self._execute_query("""
                match
                    $a isa agent, has agent-id $aid;
                    $r isa rule-entity, has rule-id $rid;
                    $c (capable-agent: $a, governing-rule: $r) isa agent-capability,
                        has capability-category $cat,
                        has capability-status $stat;
                select $aid, $rid, $cat, $stat;
            """)
            return [
                {
                    "agent_id": r.get("aid", ""),
                    "rule_id": r.get("rid", ""),
                    "category": r.get("cat", "general"),
                    "status": r.get("stat", "active"),
                }
                for r in results
            ]
        except Exception as e:
            logger.error(
                f"Failed to get all capabilities: {type(e).__name__}",
                exc_info=True,
            )
            return []
