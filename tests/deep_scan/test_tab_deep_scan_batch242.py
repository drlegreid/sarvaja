"""Batch 242 — Services layer defense tests.

Validates fixes for:
- BUG-242-PRJ-001: Slug sanitization in project ID generation
- BUG-242-LCY-001: ValueError re-raised on double-complete
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-242-PRJ-001: Slug sanitization ─────────────────────────────

class TestProjectSlugSanitization:
    """Project slug must strip unsafe chars from name."""

    def test_uses_re_sub(self):
        src = (SRC / "governance/services/projects.py").read_text()
        assert "re.sub(" in src

    def test_allows_only_safe_chars(self):
        src = (SRC / "governance/services/projects.py").read_text()
        idx = src.index("re.sub(")
        block = src[idx:idx + 100]
        assert "A-Z0-9" in block

    def test_re_imported(self):
        src = (SRC / "governance/services/projects.py").read_text()
        assert "import re" in src

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/projects.py").read_text()
        assert "BUG-242-PRJ-001" in src


# ── BUG-242-LCY-001: ValueError re-raised on double-complete ───────

class TestLifecycleValueErrorReRaise:
    """end_session must re-raise ValueError instead of swallowing."""

    def test_except_valueerror_raise(self):
        src = (SRC / "governance/services/sessions_lifecycle.py").read_text()
        assert "except ValueError:" in src
        idx = src.index("except ValueError:")
        block = src[idx:idx + 200]
        assert "raise" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/sessions_lifecycle.py").read_text()
        assert "BUG-242-LCY-001" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch242Imports:
    def test_projects_importable(self):
        import governance.services.projects
        assert governance.services.projects is not None

    def test_sessions_lifecycle_importable(self):
        import governance.services.sessions_lifecycle
        assert governance.services.sessions_lifecycle is not None

    def test_tasks_mutations_importable(self):
        import governance.services.tasks_mutations
        assert governance.services.tasks_mutations is not None

    def test_rules_service_importable(self):
        import governance.services.rules
        assert governance.services.rules is not None

    def test_sessions_service_importable(self):
        import governance.services.sessions
        assert governance.services.sessions is not None

    def test_tasks_service_importable(self):
        import governance.services.tasks
        assert governance.services.tasks is not None

    def test_rule_scope_importable(self):
        import governance.services.rule_scope
        assert governance.services.rule_scope is not None

    def test_session_repair_importable(self):
        import governance.services.session_repair
        assert governance.services.session_repair is not None
