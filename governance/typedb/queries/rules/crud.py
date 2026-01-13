"""
TypeDB Rule CRUD Operations.

Per RULE-032: File Size Limit (< 300 lines)
Extracted from: governance/typedb/queries/rules.py

Created: 2026-01-04
"""

from typing import Optional

from ...entities import Rule


class RuleCRUDOperations:
    """
    Rule CRUD operations for TypeDB.

    Requires a client with _execute_query, _execute_write, _client, and database attributes.
    Uses mixin pattern for TypeDBClient composition.
    """

    def create_rule(
        self,
        rule_id: str,
        name: str,
        category: str,
        priority: str,
        directive: str,
        status: str = "DRAFT",
        rule_type: Optional[str] = None
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
            rule_type: Rule type (FOUNDATIONAL, OPERATIONAL, TECHNICAL, META, LEAF)

        Returns:
            Created Rule object or None if failed
        """
        # Validate inputs
        valid_categories = ["governance", "technical", "operational", "architecture", "testing",
                          "reporting", "autonomy", "maintenance", "traceability", "stability",
                          "strategic", "devops", "development", "workflow", "documentation", "quality", "safety"]
        valid_priorities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        valid_statuses = ["ACTIVE", "DRAFT", "DEPRECATED", "PROPOSED", "DISABLED"]
        valid_types = ["FOUNDATIONAL", "OPERATIONAL", "TECHNICAL", "META", "LEAF", None]

        if category not in valid_categories:
            raise ValueError(f"Invalid category: {category}. Must be one of {valid_categories}")
        if priority not in valid_priorities:
            raise ValueError(f"Invalid priority: {priority}. Must be one of {valid_priorities}")
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
        if rule_type not in valid_types:
            raise ValueError(f"Invalid rule_type: {rule_type}. Must be one of {valid_types}")

        # Check if rule already exists
        existing = self.get_rule_by_id(rule_id)
        if existing:
            raise ValueError(f"Rule {rule_id} already exists")

        # Escape quotes in directive
        directive_escaped = directive.replace('"', '\\"')

        # Build query with optional rule_type
        type_clause = f',\n                has rule-type "{rule_type}"' if rule_type else ''
        query = f'''
            insert $r isa rule-entity,
                has rule-id "{rule_id}",
                has rule-name "{name}",
                has category "{category}",
                has priority "{priority}",
                has status "{status}",
                has directive "{directive_escaped}"{type_clause};
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
        status: Optional[str] = None,
        rule_type: Optional[str] = None,
        semantic_id: Optional[str] = None
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
            rule_type: New rule type (optional)
            semantic_id: New semantic ID (optional) - per META-TAXON-01-v1

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
        new_attrs = []  # For attributes that don't exist yet
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
        if rule_type is not None:
            if existing.rule_type is None:
                new_attrs.append(('rule-type', rule_type))
            elif rule_type != existing.rule_type:
                updates.append(('rule-type', existing.rule_type, rule_type))
        if semantic_id is not None:
            if existing.semantic_id is None:
                new_attrs.append(('semantic-id', semantic_id))
            elif semantic_id != existing.semantic_id:
                updates.append(('semantic-id', existing.semantic_id, semantic_id))

        if not updates and not new_attrs:
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

                # Insert new attributes (that didn't exist before)
                for attr_type, new_val in new_attrs:
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
