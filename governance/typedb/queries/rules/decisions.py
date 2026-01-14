"""
TypeDB Decision Queries and CRUD Operations.

Per RULE-032: File Size Limit (< 300 lines)
Extracted from: governance/typedb/queries/rules.py

Created: 2026-01-04
"""

from typing import List, Dict, Optional

from ...entities import Decision


class DecisionQueries:
    """
    Decision query and CRUD operations for TypeDB.

    Requires a client with _execute_query, _execute_write, _driver, and _database attributes.
    Uses mixin pattern for TypeDBClient composition.
    """

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
            get $id, $name, $ctx, $rat, $stat;
        """
        results = self._execute_query(query)
        decisions = []
        for r in results:
            decision_id = r.get("id")

            # Try to get optional decision-date
            decision_date = None
            date_query = f"""
                match $d isa decision,
                    has decision-id "{decision_id}",
                    has decision-date $date;
                get $date;
            """
            try:
                date_results = self._execute_query(date_query)
                if date_results:
                    date_val = date_results[0].get("date")
                    if isinstance(date_val, datetime):
                        decision_date = date_val
                    elif isinstance(date_val, str):
                        try:
                            decision_date = datetime.fromisoformat(
                                date_val.replace("Z", "+00:00"))
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
            get $aid, $bid;
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

        # Escape quotes
        name_escaped = name.replace('"', '\\"')
        context_escaped = context.replace('"', '\\"')
        rationale_escaped = rationale.replace('"', '\\"')

        query = f'''
            insert $d isa decision,
                has decision-id "{decision_id}",
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
        status: Optional[str] = None
    ) -> Optional[Decision]:
        """
        Update an existing decision's attributes.

        Args:
            decision_id: Decision ID to update
            name: New name (optional)
            context: New context (optional)
            rationale: New rationale (optional)
            status: New status (optional)

        Returns:
            Updated Decision object or None if not found
        """
        from typedb.driver import SessionType, TransactionType

        # Check if decision exists
        decisions = self.get_all_decisions()
        existing = None
        for d in decisions:
            if d.id == decision_id:
                existing = d
                break

        if not existing:
            return None

        # Build update queries for each attribute
        updates = []
        if name is not None:
            name_escaped = name.replace('"', '\\"')
            updates.append(('decision-name', name_escaped))
        if context is not None:
            context_escaped = context.replace('"', '\\"')
            updates.append(('context', context_escaped))
        if rationale is not None:
            rationale_escaped = rationale.replace('"', '\\"')
            updates.append(('rationale', rationale_escaped))
        if status is not None:
            updates.append(('decision-status', status))

        if not updates:
            return existing  # Nothing to update

        # Execute updates
        with self._driver.session(self._database, SessionType.DATA) as session:
            for attr_name, new_value in updates:
                with session.transaction(TransactionType.WRITE) as tx:
                    # Delete old attribute
                    delete_query = f'''
                        match $d isa decision, has decision-id "{decision_id}", has {attr_name} $old;
                        delete $d has $old;
                    '''
                    tx.query.delete(delete_query)
                    tx.commit()

                with session.transaction(TransactionType.WRITE) as tx:
                    # Insert new attribute
                    insert_query = f'''
                        match $d isa decision, has decision-id "{decision_id}";
                        insert $d has {attr_name} "{new_value}";
                    '''
                    tx.query.insert(insert_query)
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

        query = f'''
            match $d isa decision, has decision-id "{decision_id}";
            delete $d isa decision;
        '''

        self._execute_write(query)
        return True
