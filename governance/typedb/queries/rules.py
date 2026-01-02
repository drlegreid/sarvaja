"""
TypeDB Rule Queries.

Per RULE-012: DSP Semantic Code Structure.
Per GAP-FILE-003: Extracted from client.py.

Includes:
- Rule queries (get_all, get_by_id, get_by_category)
- Inference queries (dependencies, conflicts)
- Decision queries
- Rule CRUD (create, update, deprecate, delete)
- Rule archive operations

Created: 2024-12-28
"""

import os
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..entities import Rule, Decision

# Archive configuration
ARCHIVE_DIR = Path(os.getenv("RULE_ARCHIVE_DIR", Path(__file__).parent.parent.parent.parent / "evidence" / "archive" / "rules"))


class RuleQueries:
    """
    Rule query and CRUD operations for TypeDB.

    Requires a client with _execute_query, _execute_write, and _client attributes.
    Uses mixin pattern for TypeDBClient composition.
    """

    # =========================================================================
    # RULE QUERIES
    # =========================================================================

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

    # =========================================================================
    # INFERENCE QUERIES
    # =========================================================================

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

    # =========================================================================
    # DECISION QUERIES
    # =========================================================================

    def get_all_decisions(self) -> List[Decision]:
        """Get all strategic decisions."""
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
        return [
            Decision(
                id=r.get("id"),
                name=r.get("name"),
                context=r.get("ctx"),
                rationale=r.get("rat"),
                status=r.get("stat")
            )
            for r in results
        ]

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
    # RULE CRUD OPERATIONS
    # =========================================================================

    def create_rule(
        self,
        rule_id: str,
        name: str,
        category: str,
        priority: str,
        directive: str,
        status: str = "DRAFT"
    ) -> Optional[Rule]:
        """
        Create a new governance rule.

        Args:
            rule_id: Unique rule ID (e.g., "RULE-023")
            name: Human-readable rule name
            category: Rule category (governance, technical, operational)
            priority: Priority level (CRITICAL, HIGH, MEDIUM, LOW)
            directive: The rule directive text
            status: Initial status (default: DRAFT)

        Returns:
            Created Rule object or None if failed
        """
        # Validate inputs
        valid_categories = ["governance", "technical", "operational", "architecture", "testing"]
        valid_priorities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        valid_statuses = ["ACTIVE", "DRAFT", "DEPRECATED"]

        if category not in valid_categories:
            raise ValueError(f"Invalid category: {category}. Must be one of {valid_categories}")
        if priority not in valid_priorities:
            raise ValueError(f"Invalid priority: {priority}. Must be one of {valid_priorities}")
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")

        # Check if rule already exists
        existing = self.get_rule_by_id(rule_id)
        if existing:
            raise ValueError(f"Rule {rule_id} already exists")

        # Escape quotes in directive
        directive_escaped = directive.replace('"', '\\"')

        query = f'''
            insert $r isa rule-entity,
                has rule-id "{rule_id}",
                has rule-name "{name}",
                has category "{category}",
                has priority "{priority}",
                has status "{status}",
                has directive "{directive_escaped}";
        '''

        self._execute_write(query)

        # Return the created rule
        return self.get_rule_by_id(rule_id)

    def update_rule(
        self,
        rule_id: str,
        name: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        directive: Optional[str] = None,
        status: Optional[str] = None
    ) -> Optional[Rule]:
        """
        Update an existing rule's attributes.

        Only provided attributes will be updated.

        Args:
            rule_id: Rule ID to update
            name: New name (optional)
            category: New category (optional)
            priority: New priority (optional)
            directive: New directive (optional)
            status: New status (optional)

        Returns:
            Updated Rule object or None if not found
        """
        # Check if rule exists
        existing = self.get_rule_by_id(rule_id)
        if not existing:
            raise ValueError(f"Rule {rule_id} not found")

        from typedb.driver import SessionType, TransactionType

        # Build update queries for each changed attribute
        updates = []
        if name is not None and name != existing.name:
            updates.append(('rule-name', existing.name, name))
        if category is not None and category != existing.category:
            updates.append(('category', existing.category, category))
        if priority is not None and priority != existing.priority:
            updates.append(('priority', existing.priority, priority))
        if status is not None and status != existing.status:
            updates.append(('status', existing.status, status))
        if directive is not None and directive != existing.directive:
            updates.append(('directive', existing.directive.replace('"', '\\"'), directive.replace('"', '\\"')))

        if not updates:
            return existing  # Nothing to update

        # Execute updates in a single transaction
        with self._client.session(self.database, SessionType.DATA) as session:
            with session.transaction(TransactionType.WRITE) as tx:
                for attr_type, old_val, new_val in updates:
                    # Delete old attribute and insert new one
                    delete_query = f'''
                        match
                            $r isa rule-entity, has rule-id "{rule_id}";
                            $a isa {attr_type}; $a "{old_val}";
                            $r has $a;
                        delete
                            $r has $a;
                    '''
                    tx.query.delete(delete_query)

                    insert_query = f'''
                        match
                            $r isa rule-entity, has rule-id "{rule_id}";
                        insert
                            $r has {attr_type} "{new_val}";
                    '''
                    tx.query.insert(insert_query)

                tx.commit()

        return self.get_rule_by_id(rule_id)

    def deprecate_rule(self, rule_id: str, reason: Optional[str] = None) -> Optional[Rule]:
        """
        Deprecate a rule (set status to DEPRECATED).

        Args:
            rule_id: Rule ID to deprecate
            reason: Optional reason for deprecation

        Returns:
            Updated Rule object or None if not found
        """
        return self.update_rule(rule_id, status="DEPRECATED")

    def delete_rule(self, rule_id: str, archive: bool = True) -> bool:
        """
        Delete a rule from TypeDB (archives first by default).

        Args:
            rule_id: Rule ID to delete
            archive: If True, archive the rule before deletion (default: True)

        Returns:
            True if deleted, False if not found
        """
        # Check if rule exists
        existing = self.get_rule_by_id(rule_id)
        if not existing:
            return False

        # Archive before deletion (unless explicitly disabled)
        if archive:
            try:
                self.archive_rule(rule_id, reason="deleted")
            except Exception as e:
                # Log but don't fail deletion if archiving fails
                print(f"Warning: Could not archive rule {rule_id}: {e}")

        from typedb.driver import SessionType, TransactionType

        with self._client.session(self.database, SessionType.DATA) as session:
            with session.transaction(TransactionType.WRITE) as tx:
                # Delete the rule entity and all its attributes
                delete_query = f'''
                    match
                        $r isa rule-entity, has rule-id "{rule_id}";
                    delete
                        $r isa rule-entity;
                '''
                tx.query.delete(delete_query)
                tx.commit()

        return True

    # =========================================================================
    # RULE ARCHIVE OPERATIONS
    # =========================================================================

    def archive_rule(self, rule_id: str, reason: str = "archived") -> Optional[Dict[str, Any]]:
        """
        Archive a rule to JSON file for later retrieval.

        Args:
            rule_id: Rule ID to archive
            reason: Reason for archiving (deleted, deprecated, replaced, etc.)

        Returns:
            Archive record dict or None if rule not found
        """
        rule = self.get_rule_by_id(rule_id)
        if not rule:
            return None

        # Ensure archive directory exists
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

        # Create archive record
        archive_record = {
            "rule": asdict(rule),
            "archived_at": datetime.now().isoformat(),
            "reason": reason,
            "archived_from_db": self.database
        }

        # Get dependencies before archiving (for potential restore)
        try:
            deps = self.get_rule_dependencies(rule_id)
            archive_record["dependencies"] = deps
        except Exception:
            archive_record["dependencies"] = []

        try:
            dependents = self.get_rules_depending_on(rule_id)
            archive_record["dependents"] = dependents
        except Exception:
            archive_record["dependents"] = []

        # Save to archive file
        archive_file = ARCHIVE_DIR / f"{rule_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(archive_file, 'w', encoding='utf-8') as f:
            json.dump(archive_record, f, indent=2, default=str)

        return archive_record

    def get_archived_rules(self) -> List[Dict[str, Any]]:
        """
        Get all archived rules.

        Returns:
            List of archive records
        """
        archives = []

        if not ARCHIVE_DIR.exists():
            return archives

        for archive_file in sorted(ARCHIVE_DIR.glob("*.json"), reverse=True):
            try:
                with open(archive_file, 'r', encoding='utf-8') as f:
                    record = json.load(f)
                    record["archive_file"] = str(archive_file)
                    archives.append(record)
            except Exception:
                continue

        return archives

    def get_archived_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent archive of a specific rule.

        Args:
            rule_id: Rule ID to find in archive

        Returns:
            Most recent archive record or None
        """
        archives = self.get_archived_rules()

        for record in archives:
            if record.get("rule", {}).get("id") == rule_id:
                return record

        return None

    def restore_rule(self, rule_id: str) -> Optional[Rule]:
        """
        Restore a rule from archive.

        Args:
            rule_id: Rule ID to restore

        Returns:
            Restored Rule object or None if not in archive
        """
        archive = self.get_archived_rule(rule_id)
        if not archive:
            return None

        rule_data = archive.get("rule", {})

        # Check if rule already exists (don't overwrite)
        existing = self.get_rule_by_id(rule_id)
        if existing:
            raise ValueError(f"Rule {rule_id} already exists. Delete or rename before restore.")

        # Recreate the rule
        return self.create_rule(
            rule_id=rule_data.get("id"),
            name=rule_data.get("name"),
            category=rule_data.get("category"),
            priority=rule_data.get("priority"),
            directive=rule_data.get("directive"),
            status="DRAFT"  # Restored rules start as DRAFT
        )

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
        from datetime import datetime

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
