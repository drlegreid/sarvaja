"""Batch 255 — TypeQL inference escaping + None filter tests.

Validates fixes for:
- BUG-255-ESC-001: Backslash+quote escaping in rules/inference.py
- BUG-255-FILTER-001: None filter on inference query results
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-255-ESC-001: inference.py escaping ────────────────────────────

class TestInferenceEscaping:
    """All ID escapes in inference.py must include backslash step."""

    def test_get_rule_dependencies_backslash(self):
        src = (SRC / "governance/typedb/queries/rules/inference.py").read_text()
        idx = src.index("def get_rule_dependencies")
        block = src[idx:idx + 500]
        assert "replace('\\\\', '\\\\\\\\')" in block

    def test_get_rules_depending_on_backslash(self):
        src = (SRC / "governance/typedb/queries/rules/inference.py").read_text()
        idx = src.index("def get_rules_depending_on")
        block = src[idx:idx + 500]
        assert "replace('\\\\', '\\\\\\\\')" in block

    def test_create_rule_dependency_backslash(self):
        src = (SRC / "governance/typedb/queries/rules/inference.py").read_text()
        idx = src.index("def create_rule_dependency")
        block = src[idx:idx + 800]
        assert "replace('\\\\', '\\\\\\\\')" in block

    def test_get_decision_impacts_backslash(self):
        src = (SRC / "governance/typedb/queries/rules/inference.py").read_text()
        idx = src.index("def get_decision_impacts")
        block = src[idx:idx + 500]
        assert "replace('\\\\', '\\\\\\\\')" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/typedb/queries/rules/inference.py").read_text()
        assert "BUG-255-ESC-001" in src


# ── None filter on result lists ───────────────────────────────────────

class TestInferenceNoneFilter:
    """Result list comprehensions must filter None values."""

    def test_get_rule_dependencies_filters_none(self):
        src = (SRC / "governance/typedb/queries/rules/inference.py").read_text()
        idx = src.index("def get_rule_dependencies")
        block = src[idx:idx + 900]
        assert 'if r.get("dep_id")' in block

    def test_get_rules_depending_on_filters_none(self):
        src = (SRC / "governance/typedb/queries/rules/inference.py").read_text()
        idx = src.index("def get_rules_depending_on")
        block = src[idx:idx + 700]
        assert 'if r.get("id")' in block

    def test_get_decision_impacts_filters_none(self):
        src = (SRC / "governance/typedb/queries/rules/inference.py").read_text()
        idx = src.index("def get_decision_impacts")
        block = src[idx:idx + 900]
        assert 'if r.get("rid")' in block


# ── Module import defense tests ──────────────────────────────────────

class TestBatch255Imports:
    def test_inference_importable(self):
        import governance.typedb.queries.rules.inference
        assert governance.typedb.queries.rules.inference is not None

    def test_tasks_crud_importable(self):
        import governance.typedb.queries.tasks.crud
        assert governance.typedb.queries.tasks.crud is not None

    def test_tasks_status_importable(self):
        import governance.typedb.queries.tasks.status
        assert governance.typedb.queries.tasks.status is not None
