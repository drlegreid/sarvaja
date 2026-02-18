"""Batch 235 — TypeDB queries layer defense tests.

Validates fixes for:
- BUG-235-INJ-001: Unescaped new_value in _update_decision_attr
- BUG-235-INJ-004: Backslash not escaped in create_rule/create_decision
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-235-INJ-001: Escape new_value inside _update_decision_attr ───

class TestDecisionAttrEscaping:
    """_update_decision_attr must escape new_value locally."""

    def test_escapes_new_value_in_helper(self):
        src = (SRC / "governance/typedb/queries/rules/decisions.py").read_text()
        idx = src.index("def _update_decision_attr")
        next_def = src.index("\n    def ", idx + 1)
        block = src[idx:next_def]
        assert "val_esc" in block
        assert "BUG-235-INJ-001" in block

    def test_uses_val_esc_not_new_value(self):
        """Query should use val_esc, not raw new_value."""
        src = (SRC / "governance/typedb/queries/rules/decisions.py").read_text()
        idx = src.index("def _update_decision_attr")
        next_def = src.index("\n    def ", idx + 1)
        block = src[idx:next_def]
        # The insert query should reference val_esc
        assert '"{val_esc}"' in block


# ── BUG-235-INJ-004: Backslash escaping in create_rule ──────────────

class TestRuleBackslashEscaping:
    """create_rule must escape backslash before quotes."""

    def test_backslash_escape_in_create_rule(self):
        src = (SRC / "governance/typedb/queries/rules/crud.py").read_text()
        idx = src.index("def create_rule")
        next_def = src.index("\n    def ", idx + 1)
        block = src[idx:next_def]
        assert "BUG-235-INJ-004" in block
        # Must escape \\ before \"
        assert "replace('\\\\', '\\\\\\\\\\\\\\\\')" in block or "replace('\\\\'," in block

    def test_create_decision_backslash_escape(self):
        src = (SRC / "governance/typedb/queries/rules/decisions.py").read_text()
        idx = src.index("def create_decision")
        next_def = src.index("\n    def ", idx + 1)
        block = src[idx:next_def]
        assert "BUG-235-INJ-004" in block


# ── TypeDB queries module import defense tests ───────────────────────

class TestTypeDBQueriesImports:
    def test_rules_crud_importable(self):
        import governance.typedb.queries.rules.crud
        assert governance.typedb.queries.rules.crud is not None

    def test_rules_inference_importable(self):
        import governance.typedb.queries.rules.inference
        assert governance.typedb.queries.rules.inference is not None

    def test_rules_decisions_importable(self):
        import governance.typedb.queries.rules.decisions
        assert governance.typedb.queries.rules.decisions is not None

    def test_tasks_crud_importable(self):
        import governance.typedb.queries.tasks.crud
        assert governance.typedb.queries.tasks.crud is not None

    def test_tasks_linking_importable(self):
        import governance.typedb.queries.tasks.linking
        assert governance.typedb.queries.tasks.linking is not None

    def test_tasks_relationships_importable(self):
        import governance.typedb.queries.tasks.relationships
        assert governance.typedb.queries.tasks.relationships is not None

    def test_tasks_status_importable(self):
        import governance.typedb.queries.tasks.status
        assert governance.typedb.queries.tasks.status is not None
