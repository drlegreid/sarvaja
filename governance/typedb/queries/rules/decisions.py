"""
TypeDB Decision Queries and CRUD Operations.

Per RULE-032: File Size Limit (< 300 lines)
Extracted from: governance/typedb/queries/rules.py

Created: 2026-01-04
"""

import logging
from typing import List, Dict, Optional

from ...entities import Decision

logger = logging.getLogger(__name__)


class DecisionQueries:
    """
    Decision query and CRUD operations for TypeDB.

    Requires a client with _execute_query, _execute_write, _driver, and database attributes.
    Uses mixin pattern for TypeDBClient composition.
    """

    def _update_decision_attr(self, decision_id: str, attr_name: str, new_value: str) -> None:
        """Delete old attribute and insert new value for a decision.

        BUG-DECISION-DOUBLE-TRANSACTION: Single transaction for atomicity.
        """
        from typedb.driver import TransactionType
        # BUG-TYPEQL-ESCAPE-DECISION-001 + BUG-235-INJ-001: Escape backslash THEN quotes
        did = decision_id.replace('\\', '\\\\').replace('"', '\\"')
        # BUG-235-INJ-001: Escape new_value inside helper, not just at caller
        val_esc = new_value.replace('\\', '\\\\').replace('"', '\\"')
        with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
            try:
                tx.query(f'''
                    match $d isa decision, has decision-id "{did}", has {attr_name} $old;
                    delete has $old of $d;
                ''').resolve()
            except Exception:
                pass  # Attribute may not exist yet
            tx.query(f'''
                match $d isa decision, has decision-id "{did}";
                insert $d has {attr_name} "{val_esc}";
            ''').resolve()
            tx.commit()

    # =========================================================================
    # DECISION QUERIES
    # =========================================================================

    def get_all_decisions(self) -> List[Decision]:
        """Get all strategic decisions including dates."""
        from datetime import datetime

        # First get core attributes (required)
        query = """
            match $d isa decision,
                has decision-id $id,
                has decision-name $name,
                has context $ctx,
                has rationale $rat,
                has decision-status $stat;
        """
        results = self._execute_query(query)
        decisions = []
        for r in results:
            decision_id = r.get("id")

            # Try to get optional decision-date
            # BUG-TYPEQL-ESCAPE-DECISION-001: Escape decision_id from TypeDB result
            did_escaped = (decision_id or "").replace('"', '\\"')
            decision_date = None
            date_query = f"""
                match $d isa decision,
                    has decision-id "{did_escaped}",
                    has decision-date $date;
            """
            try:
                date_results = self._execute_query(date_query)
                if date_results:
                    date_val = date_results[0].get("date")
                    if isinstance(date_val, datetime):
                        decision_date = date_val
                    else:
                        # TypeDB Datetime or string — convert via str
                        try:
                            date_str = str(date_val)[:19]  # Trim nanoseconds
                            decision_date = datetime.fromisoformat(date_str)
                        except (ValueError, AttributeError):
                            pass
            except Exception:
                pass  # decision_date is optional

            decisions.append(Decision(
                id=decision_id,
                name=r.get("name"),
                context=r.get("ctx"),
                rationale=r.get("rat"),
                status=r.get("stat"),
                decision_date=decision_date
            ))
        return decisions

    def get_superseded_decisions(self) -> List[Dict[str, str]]:
        """Get decision supersession chain."""
        query = """
            match
                (superseding: $a, superseded: $b) isa decision-supersedes;
                $a has decision-id $aid;
                $b has decision-id $bid;
        """
        results = self._execute_query(query)
        return [{"superseding": r.get("aid"), "superseded": r.get("bid")} for r in results]

    # =========================================================================
    # DECISION CRUD OPERATIONS (GAP-UI-033)
    # =========================================================================

    def create_decision(
        self,
        decision_id: str,
        name: str,
        context: str,
        rationale: str,
        status: str = "PENDING"
    ) -> Optional[Decision]:
        """
        Create a new strategic decision.

        Args:
            decision_id: Unique decision ID (e.g., "DECISION-010")
            name: Decision name/title
            context: Context/problem statement
            rationale: Reasoning for the decision
            status: Initial status (default: PENDING)

        Returns:
            Created Decision object or None if failed
        """
        valid_statuses = ["PENDING", "APPROVED", "REJECTED", "IMPLEMENTED"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")

        # BUG-235-INJ-004: Escape backslash THEN quotes for all string fields
        name_escaped = name.replace('\\', '\\\\').replace('"', '\\"')
        context_escaped = context.replace('\\', '\\\\').replace('"', '\\"')
        rationale_escaped = rationale.replace('\\', '\\\\').replace('"', '\\"')
        # BUG-TYPEQL-ESCAPE-DECISION-001: Escape decision_id too
        decision_id_escaped = decision_id.replace('\\', '\\\\').replace('"', '\\"')

        query = f'''
            insert $d isa decision,
                has decision-id "{decision_id_escaped}",
                has decision-name "{name_escaped}",
                has context "{context_escaped}",
                has rationale "{rationale_escaped}",
                has decision-status "{status}";
        '''

        self._execute_write(query)

        # Return the created decision
        decisions = self.get_all_decisions()
        for d in decisions:
            if d.id == decision_id:
                return d
        return None

    def update_decision(
        self,
        decision_id: str,
        name: Optional[str] = None,
        context: Optional[str] = None,
        rationale: Optional[str] = None,
        status: Optional[str] = None,
        decision_date: Optional[str] = None
    ) -> Optional[Decision]:
        """
        Update an existing decision's attributes.

        Args:
            decision_id: Decision ID to update
            name: New name (optional)
            context: New context (optional)
            rationale: New rationale (optional)
            status: New status (optional)
            decision_date: ISO datetime string (optional)

        Returns:
            Updated Decision object or None if not found
        """
        # Check if decision exists
        decisions = self.get_all_decisions()
        existing = None
        for d in decisions:
            if d.id == decision_id:
                existing = d
                break

        if not existing:
            return None

        # Build update list from provided fields
        field_map = [
            ('decision-name', name), ('context', context),
            ('rationale', rationale), ('decision-status', status),
        ]
        updates = [(attr, val.replace('"', '\\"')) for attr, val in field_map if val is not None]

        if not updates and decision_date is None:
            return existing  # Nothing to update

        # Execute string attribute updates via DRY helper
        for attr_name, new_value in updates:
            self._update_decision_attr(decision_id, attr_name, new_value)

        # Handle decision_date (datetime type — no quotes in TypeQL)
        if decision_date is not None:
            from typedb.driver import TransactionType
            # BUG-TYPEQL-ESCAPE-DECISION-001: Escape decision_id
            did = decision_id.replace('"', '\\"')
            # BUG-DECISION-DATE-NONATOMIC: Single transaction for atomicity
            date_str = decision_date[:19]
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                try:
                    tx.query(f'''
                        match $d isa decision, has decision-id "{did}", has decision-date $old;
                        delete has $old of $d;
                    ''').resolve()
                except Exception:
                    pass  # May not have existing date
                tx.query(f'''
                    match $d isa decision, has decision-id "{did}";
                    insert $d has decision-date {date_str};
                ''').resolve()
                tx.commit()

        # Return updated decision
        decisions = self.get_all_decisions()
        for d in decisions:
            if d.id == decision_id:
                return d
        return None

    def delete_decision(self, decision_id: str) -> bool:
        """
        Delete a decision from TypeDB.

        Args:
            decision_id: Decision ID to delete

        Returns:
            True if deleted, False if not found
        """
        # Check if decision exists
        decisions = self.get_all_decisions()
        exists = any(d.id == decision_id for d in decisions)

        if not exists:
            return False

        # BUG-TYPEQL-ESCAPE-DECISION-001: Escape decision_id
        did = decision_id.replace('"', '\\"')
        query = f'''
            match $d isa decision, has decision-id "{did}";
            delete $d;
        '''

        self._execute_write(query)
        return True

    def link_decision_to_rule(self, decision_id: str, rule_id: str) -> bool:
        """
        Create a decision-affects relationship between a decision and a rule.

        Args:
            decision_id: Decision ID (e.g., "DECISION-003")
            rule_id: Rule ID (e.g., "GOV-RULE-01-v1")

        Returns:
            True if linked successfully, False if entities not found
        """
        from typedb.driver import TransactionType

        try:
            # BUG-TYPEQL-ESCAPE-DECISION-001: Escape IDs before TypeQL interpolation
            did = decision_id.replace('"', '\\"')
            rid = rule_id.replace('"', '\\"')

            # Verify both entities exist before linking
            with self._driver.transaction(self.database, TransactionType.READ) as tx:
                check_query = f"""
                    match
                        $d isa decision, has decision-id "{did}";
                        $r isa rule-entity, has rule-id "{rid}";
                """
                results = list(tx.query(check_query).resolve())
                if not results:
                    return False

            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                link_query = f"""
                    match
                        $d isa decision, has decision-id "{did}";
                        $r isa rule-entity, has rule-id "{rid}";
                    insert
                        (affecting-decision: $d, affected-rule: $r) isa decision-affects;
                """
                tx.query(link_query).resolve()
                tx.commit()
            return True
        except Exception as e:
            # BUG-472-RDC-001: Sanitize logger message + add exc_info for stack trace preservation
            logger.error(f"Failed to link decision {decision_id} to rule {rule_id}: {type(e).__name__}", exc_info=True)
            return False
