"""
TypeDB Rule CRUD Operations.

Per RULE-032: File Size Limit (< 300 lines)
Extracted from: governance/typedb/queries/rules.py

Created: 2026-01-04
"""

import logging
from typing import Optional

from ...entities import Rule

logger = logging.getLogger(__name__)


class RuleCRUDOperations:
    """
    Rule CRUD operations for TypeDB.

    Requires a client with _execute_query, _execute_write, _driver, and database attributes.
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

        # BUG-RULE-CREATE-NAME-001 + BUG-235-INJ-004: Escape backslash THEN quotes
        name_escaped = name.replace('\\', '\\\\').replace('"', '\\"')
        directive_escaped = directive.replace('\\', '\\\\').replace('"', '\\"')
        # BUG-TYPEQL-ESCAPE-RULE-001: Escape rule_id for defense-in-depth
        rule_id_escaped = rule_id.replace('\\', '\\\\').replace('"', '\\"')

        # Build query with optional rule_type
        type_clause = f',\n                has rule-type "{rule_type}"' if rule_type else ''
        query = f'''
            insert $r isa rule-entity,
                has rule-id "{rule_id_escaped}",
                has rule-name "{name_escaped}",
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
        semantic_id: Optional[str] = None,
        applicability: Optional[str] = None
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
            applicability: New applicability (optional) - per RD-RULE-APPLICABILITY

        Returns:
            Updated Rule object or None if not found
        """
        # BUG-360-RCR-001: Validate update values against allowlists (matches create_rule)
        valid_categories = ["governance", "technical", "operational", "architecture", "testing",
                          "reporting", "autonomy", "maintenance", "traceability", "stability",
                          "strategic", "devops", "development", "workflow", "documentation", "quality", "safety"]
        valid_priorities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        valid_statuses = ["ACTIVE", "DRAFT", "DEPRECATED", "PROPOSED", "DISABLED"]
        valid_types = ["FOUNDATIONAL", "OPERATIONAL", "TECHNICAL", "META", "LEAF"]
        if category is not None and category not in valid_categories:
            raise ValueError(f"Invalid category: {category}. Must be one of {valid_categories}")
        if priority is not None and priority not in valid_priorities:
            raise ValueError(f"Invalid priority: {priority}. Must be one of {valid_priorities}")
        if status is not None and status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
        if rule_type is not None and rule_type not in valid_types:
            raise ValueError(f"Invalid rule_type: {rule_type}. Must be one of {valid_types}")

        # Check if rule exists
        existing = self.get_rule_by_id(rule_id)
        if not existing:
            raise ValueError(f"Rule {rule_id} not found")

        from typedb.driver import TransactionType

        # Build update queries for each changed attribute
        updates = []
        new_attrs = []  # For attributes that don't exist yet
        # BUG-244-INJ-001: Escape backslash THEN quotes for all update values (matches create_rule)
        def _esc(v: str) -> str:
            return v.replace('\\', '\\\\').replace('"', '\\"')

        if name is not None and name != existing.name:
            # BUG-RULE-NULL-001: Guard against None from corrupted TypeDB data
            old_name = _esc(existing.name or "")
            updates.append(('rule-name', old_name, _esc(name)))
        if category is not None and category != existing.category:
            old_cat = _esc(existing.category or "")
            updates.append(('category', old_cat, _esc(category)))
        if priority is not None and priority != existing.priority:
            old_pri = _esc(existing.priority or "")
            updates.append(('priority', old_pri, _esc(priority)))
        if status is not None and status != existing.status:
            old_status = _esc(existing.status or "")
            updates.append(('status', old_status, _esc(status)))
        if directive is not None and directive != existing.directive:
            old_dir = _esc(existing.directive or "")
            updates.append(('directive', old_dir, _esc(directive)))
        if rule_type is not None:
            if existing.rule_type is None:
                new_attrs.append(('rule-type', _esc(rule_type)))
            elif rule_type != existing.rule_type:
                updates.append(('rule-type', _esc(existing.rule_type), _esc(rule_type)))
        if semantic_id is not None:
            if existing.semantic_id is None:
                new_attrs.append(('semantic-id', _esc(semantic_id)))
            elif semantic_id != existing.semantic_id:
                updates.append(('semantic-id', _esc(existing.semantic_id), _esc(semantic_id)))
        if applicability is not None:
            # Validate applicability value
            valid_applicability = ["MANDATORY", "RECOMMENDED", "FORBIDDEN", "CONDITIONAL"]
            if applicability not in valid_applicability:
                raise ValueError(f"Invalid applicability: {applicability}. Must be one of {valid_applicability}")
            if existing.applicability is None:
                new_attrs.append(('applicability', _esc(applicability)))
            elif applicability != existing.applicability:
                updates.append(('applicability', _esc(existing.applicability), _esc(applicability)))

        if not updates and not new_attrs:
            return existing  # Nothing to update

        # BUG-254-ESC-001: Use _esc() for consistent backslash+quote escaping
        rule_id_escaped = _esc(rule_id)

        # BUG-196-003: Wrap transaction in try/except to prevent unhandled propagation
        try:
            # Execute updates - TypeDB 3.x: driver.transaction() directly
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                for attr_type, old_val, new_val in updates:
                    # Delete old attribute and insert new one (TypeDB 3.x: has $var of $entity)
                    delete_query = f'''
                        match
                            $r isa rule-entity, has rule-id "{rule_id_escaped}", has {attr_type} $a;
                            $a == "{old_val}";
                        delete
                            has $a of $r;
                    '''
                    tx.query(delete_query).resolve()

                    insert_query = f'''
                        match
                            $r isa rule-entity, has rule-id "{rule_id_escaped}";
                        insert
                            $r has {attr_type} "{new_val}";
                    '''
                    tx.query(insert_query).resolve()

                # Insert new attributes (that didn't exist before)
                for attr_type, new_val in new_attrs:
                    insert_query = f'''
                        match
                            $r isa rule-entity, has rule-id "{rule_id_escaped}";
                        insert
                            $r has {attr_type} "{new_val}";
                    '''
                    tx.query(insert_query).resolve()

                tx.commit()
        except Exception as e:
            # BUG-389-RCR-001: Add exc_info for stack trace visibility in logs
            logger.error(f"Failed to update rule {rule_id}: {e}", exc_info=True)
            return None

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
                # BUG-412-RCR-001: Add exc_info for stack trace preservation
                logger.warning(f"Could not archive rule {rule_id}: {e}", exc_info=True)

        from typedb.driver import TransactionType

        # BUG-254-ESC-001: Escape backslash THEN quotes for TypeQL safety
        rule_id_escaped = rule_id.replace('\\', '\\\\').replace('"', '\\"')

        # BUG-196-003: Wrap transaction in try/except to prevent unhandled propagation
        try:
            # TypeDB 3.x: driver.transaction() directly
            with self._driver.transaction(self.database, TransactionType.WRITE) as tx:
                # Delete the rule entity and all its attributes
                # TypeDB 3.x syntax: delete $r; (not delete $r isa rule-entity;)
                delete_query = f'''
                    match
                        $r isa rule-entity, has rule-id "{rule_id_escaped}";
                    delete
                        $r;
                '''
                tx.query(delete_query).resolve()
                tx.commit()
        except Exception as e:
            # BUG-389-RCR-002: Add exc_info for stack trace visibility in logs
            logger.error(f"Failed to delete rule {rule_id}: {e}", exc_info=True)
            return False

        return True
