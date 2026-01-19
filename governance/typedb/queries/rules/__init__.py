"""
TypeDB Rule Queries Module.

Per RULE-032: File Size Limit (< 300 lines)
Modularized from: governance/typedb/queries/rules.py (699 lines)

Created: 2026-01-04

This module combines all rule-related query mixins:
- RuleReadQueries: Rule read operations
- RuleInferenceQueries: Dependency/conflict inference
- RuleCRUDOperations: Create/update/delete rules
- RuleArchiveOperations: Archive/restore rules
- DecisionQueries: Decision queries and CRUD
"""

from .read import RuleReadQueries
from .inference import RuleInferenceQueries
from .crud import RuleCRUDOperations
from .archive import RuleArchiveOperations, ARCHIVE_DIR
from .decisions import DecisionQueries


class RuleQueries(
    RuleReadQueries,
    RuleInferenceQueries,
    RuleCRUDOperations,
    RuleArchiveOperations,
    DecisionQueries
):
    """
    Combined rule query and CRUD operations for TypeDB.

    Combines all rule-related mixins:
    - RuleReadQueries: get_all_rules, get_active_rules, get_rule_by_id, get_rules_by_category
    - RuleInferenceQueries: get_rule_dependencies, get_rules_depending_on, find_conflicts, get_decision_impacts
    - RuleCRUDOperations: create_rule, update_rule, deprecate_rule, delete_rule
    - RuleArchiveOperations: archive_rule, get_archived_rules, get_archived_rule, restore_rule
    - DecisionQueries: get_all_decisions, get_superseded_decisions, create_decision, update_decision, delete_decision

    Requires a client with:
    - _execute_query(query, infer=False)
    - _execute_rule_query(query)
    - _execute_write(query)
    - _driver (TypeDB driver)
    - database (database name)

    Uses mixin pattern for TypeDBClient composition.
    """
    pass


__all__ = [
    'RuleQueries',
    'RuleReadQueries',
    'RuleInferenceQueries',
    'RuleCRUDOperations',
    'RuleArchiveOperations',
    'DecisionQueries',
    'ARCHIVE_DIR',
]
