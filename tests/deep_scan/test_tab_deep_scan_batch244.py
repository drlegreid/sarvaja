"""Batch 244 — TypeDB queries layer defense tests.

Validates fixes for:
- BUG-244-INJ-001: Backslash escape in update_rule
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-244-INJ-001: Backslash escape in update_rule ────────────────

class TestUpdateRuleBackslashEscape:
    """update_rule must escape backslash before quotes (matches create_rule)."""

    def test_esc_helper_defined(self):
        src = (SRC / "governance/typedb/queries/rules/crud.py").read_text()
        idx = src.index("def update_rule")
        block = src[idx:idx + 3000]
        assert "def _esc(" in block

    def test_esc_handles_backslash(self):
        src = (SRC / "governance/typedb/queries/rules/crud.py").read_text()
        idx = src.index("def _esc(")
        block = src[idx:idx + 200]
        assert "replace('\\\\" in block

    def test_name_uses_esc(self):
        src = (SRC / "governance/typedb/queries/rules/crud.py").read_text()
        idx = src.index("def update_rule")
        block = src[idx:idx + 3500]
        assert "_esc(name)" in block or "_esc(existing.name" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/typedb/queries/rules/crud.py").read_text()
        assert "BUG-244-INJ-001" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch244Imports:
    def test_rules_crud_importable(self):
        import governance.typedb.queries.rules.crud
        assert governance.typedb.queries.rules.crud is not None

    def test_rules_inference_importable(self):
        import governance.typedb.queries.rules.inference
        assert governance.typedb.queries.rules.inference is not None

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
