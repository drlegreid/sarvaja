"""Deep scan batch 182: TypeDB queries layer.

Batch 182 findings: 20 total, 2 confirmed fixes, 18 rejected/deferred.
- BUG-182-003: _set_lifecycle_timestamps missing backslash escape.
- BUG-182-005: status.py escape inconsistency (all 8 calls fixed).
"""
import pytest
from pathlib import Path


# ── TypeQL escape consistency across all task query files ──────────────


class TestTypeQLEscapeConsistencyAllFiles:
    """Verify TypeQL escaping is consistent across crud.py AND status.py."""

    def test_set_lifecycle_timestamps_escapes_backslash(self):
        """_set_lifecycle_timestamps escapes backslash before quotes."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/typedb/queries/tasks/crud.py").read_text()
        start = src.index("def _set_lifecycle_timestamps")
        end = src.index("\ndef ", start + 1) if "\ndef " in src[start + 1:] else len(src)
        func = src[start:end]
        # Should have backslash escape in task_id handling
        assert "replace('\\\\', '\\\\\\\\')" in func

    def test_status_py_all_escapes_have_backslash(self):
        """status.py: every quote escape is preceded by backslash escape."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/typedb/queries/tasks/status.py").read_text()
        # Count pattern: .replace('\\', '\\\\').replace('"', '\\"')
        full_pattern = r".replace('\\', '\\\\').replace('\"', '\\\"')"
        # Both patterns should appear the same number of times
        backslash_count = src.count(".replace('\\\\', '\\\\\\\\')")
        quote_count = src.count('.replace(\'"\', \'\\\\"\')')
        # Every quote escape should have a matching backslash escape
        assert backslash_count >= quote_count, (
            f"Found {quote_count} quote escapes but only {backslash_count} backslash escapes"
        )

    def test_status_py_escapes_task_id(self):
        """update_task_status escapes task_id with backslash pattern."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/typedb/queries/tasks/status.py").read_text()
        start = src.index("def update_task_status")
        end = src.index("\ndef ", start + 1) if "\ndef " in src[start + 1:] else len(src)
        func = src[start:end]
        # tid should use double-escape pattern
        assert "task_id.replace('\\\\', '\\\\\\\\').replace('\"', '\\\\\"')" in func

    def test_update_attribute_escapes_match_insert(self):
        """_update_attribute in crud.py escapes both old and new values."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/typedb/queries/tasks/crud.py").read_text()
        start = src.index("def _update_attribute")
        end = src.index("\ndef ", start + 1)
        func = src[start:end]
        # All three: tid, new_escaped, old_escaped should have backslash pattern
        assert func.count("replace('\\\\', '\\\\\\\\')") >= 3


# ── TypeDB queries structure defense ──────────────


class TestTypeDBQueriesStructureDefense:
    """Verify TypeDB query module structure."""

    def test_task_crud_operations_class_exists(self):
        """TaskCRUDOperations class exists in tasks/crud.py."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/typedb/queries/tasks/crud.py").read_text()
        assert "class TaskCRUDOperations" in src

    def test_task_read_has_get_task(self):
        """tasks/read.py has get_task method."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/typedb/queries/tasks/read.py").read_text()
        assert "def get_task" in src

    def test_rules_read_has_get_rule_by_id(self):
        """rules/read.py has get_rule_by_id method."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/typedb/queries/rules/read.py").read_text()
        assert "def get_rule_by_id" in src

    def test_sessions_crud_has_insert_session(self):
        """sessions/crud.py has insert_session method."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/typedb/queries/sessions/crud.py").read_text()
        assert "def insert_session" in src

    def test_decisions_has_create_decision(self):
        """decisions.py has create_decision method."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/typedb/queries/rules/decisions.py").read_text()
        assert "def create_decision" in src
