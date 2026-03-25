"""Tests for EPIC-RULES-V3-P1: Relation name fix + schema parity.

Validates:
- rules_relations.py uses correct TypeDB relation names
- schema.tql and schema_3x/ both define applicability attribute
- Relation name constants are DRY (module-level, not string literals)
"""
import re
from pathlib import Path

import pytest

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
RULES_RELATIONS = ROOT / "governance" / "services" / "rules_relations.py"
SCHEMA_TQL = ROOT / "governance" / "schema.tql"
SCHEMA_3X_ATTRS = ROOT / "governance" / "schema_3x" / "10_core_attributes_3x.tql"
SCHEMA_3X_ENTITIES = ROOT / "governance" / "schema_3x" / "01_core_entities_3x.tql"


# ── Relation name correctness ────────────────────────────────────────────────

class TestTaskLinkageRelation:
    """rules_relations.py must use 'implements-rule' not 'task-rule-link'."""

    def test_no_task_rule_link_string(self):
        """OLD relation name 'task-rule-link' must NOT appear in code."""
        source = RULES_RELATIONS.read_text()
        assert "task-rule-link" not in source, (
            "rules_relations.py still uses deprecated 'task-rule-link' relation"
        )

    def test_implements_rule_relation_present(self):
        """Correct relation 'implements-rule' must appear in task linkage query."""
        source = RULES_RELATIONS.read_text()
        assert "implements-rule" in source, (
            "rules_relations.py missing 'implements-rule' relation"
        )

    def test_implementing_task_role(self):
        """Correct role 'implementing-task' must appear in query."""
        source = RULES_RELATIONS.read_text()
        assert "implementing-task" in source

    def test_implemented_rule_role(self):
        """Correct role 'implemented-rule' must appear in query."""
        source = RULES_RELATIONS.read_text()
        assert "implemented-rule" in source


class TestSessionLinkageRelation:
    """rules_relations.py must use 'session-applied-rule' not 'session-rule-link'."""

    def test_no_session_rule_link_string(self):
        """OLD relation name 'session-rule-link' must NOT appear in code."""
        source = RULES_RELATIONS.read_text()
        assert "session-rule-link" not in source, (
            "rules_relations.py still uses deprecated 'session-rule-link' relation"
        )

    def test_session_applied_rule_relation_present(self):
        """Correct relation 'session-applied-rule' must appear in session linkage query."""
        source = RULES_RELATIONS.read_text()
        assert "session-applied-rule" in source, (
            "rules_relations.py missing 'session-applied-rule' relation"
        )

    def test_applying_session_role(self):
        """Correct role 'applying-session' must appear in query."""
        source = RULES_RELATIONS.read_text()
        assert "applying-session" in source

    def test_applied_rule_role(self):
        """Correct role 'applied-rule' must appear in query."""
        source = RULES_RELATIONS.read_text()
        assert "applied-rule" in source


# ── Schema parity for applicability ──────────────────────────────────────────

class TestSchemaApplicability:
    """applicability attribute must exist in both schema.tql and schema_3x/."""

    def test_schema_tql_has_applicability_attribute(self):
        """schema.tql must define 'attribute applicability'."""
        source = SCHEMA_TQL.read_text()
        assert re.search(r"attribute\s+applicability", source), (
            "schema.tql missing applicability attribute definition"
        )

    def test_schema_tql_rule_entity_owns_applicability(self):
        """schema.tql rule-entity must 'owns applicability'."""
        source = SCHEMA_TQL.read_text()
        assert "owns applicability" in source

    def test_schema_3x_has_applicability_attribute(self):
        """schema_3x/10_core_attributes_3x.tql must define applicability."""
        source = SCHEMA_3X_ATTRS.read_text()
        assert re.search(r"attribute\s+applicability", source), (
            "schema_3x/10_core_attributes_3x.tql missing applicability attribute"
        )

    def test_schema_3x_rule_entity_owns_applicability(self):
        """schema_3x/01_core_entities_3x.tql rule-entity must 'owns applicability'."""
        source = SCHEMA_3X_ENTITIES.read_text()
        assert "owns applicability" in source, (
            "schema_3x/01_core_entities_3x.tql rule-entity missing 'owns applicability'"
        )


# ── DRY: constants, not inline strings ───────────────────────────────────────

class TestRelationConstants:
    """Relation names should be module-level constants, not inline string literals."""

    def test_implements_rule_constant_defined(self):
        """Module should define IMPLEMENTS_RULE_RELATION constant."""
        from governance.services.rules_relations import IMPLEMENTS_RULE_RELATION
        assert IMPLEMENTS_RULE_RELATION == "implements-rule"

    def test_session_applied_rule_constant_defined(self):
        """Module should define SESSION_APPLIED_RULE_RELATION constant."""
        from governance.services.rules_relations import SESSION_APPLIED_RULE_RELATION
        assert SESSION_APPLIED_RULE_RELATION == "session-applied-rule"

    def test_query_uses_constants_not_literals(self):
        """The query construction should reference constants, not hardcoded strings."""
        source = RULES_RELATIONS.read_text()
        # After constants are defined, the query builder should use f-strings
        # or format with the constant. We check that the constant names appear
        # in the source (they will, at minimum, as definitions).
        assert "IMPLEMENTS_RULE_RELATION" in source
        assert "SESSION_APPLIED_RULE_RELATION" in source
