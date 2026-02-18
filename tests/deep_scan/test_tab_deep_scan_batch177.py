"""Deep scan batch 177: Stores + TypeDB layer.

Batch 177 findings: 24 total, 2 confirmed fixes, 22 rejected/deferred.
- BUG-TYPEQL-ESCAPE-UPDATE-001: _update_attribute missing backslash escape.
- BUG-AUDIT-MICROSECOND-001: query_audit_trail date_to misses microseconds.
"""
import pytest
from pathlib import Path


# ── TypeQL escape consistency defense ──────────────


class TestTypeQLEscapeConsistencyDefense:
    """Verify TypeQL escaping is consistent across CRUD operations."""

    def test_update_attribute_escapes_backslash_first(self):
        """_update_attribute escapes backslash before quotes."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/typedb/queries/tasks/crud.py").read_text()
        start = src.index("def _update_attribute")
        end = src.index("\ndef ", start + 1) if "\ndef " in src[start + 1:] else len(src)
        func = src[start:end]
        # Backslash escape must appear before quote escape in the same line
        for line in func.split("\n"):
            if '.replace(' in line and '"\\\\"' in line:
                # Should have backslash escape first
                backslash_pos = line.index("'\\\\'")
                quote_pos = line.index("'\\\"'") if "'\\\"'" in line else len(line)
                assert backslash_pos < quote_pos, f"Wrong order in: {line}"

    def test_insert_task_escapes_backslash_first(self):
        """insert_task escapes backslash before quotes."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/typedb/queries/tasks/crud.py").read_text()
        start = src.index("def insert_task")
        end = src.index("\ndef ", start + 1) if "\ndef " in src[start + 1:] else len(src)
        func = src[start:end]
        assert "replace('\\\\', '\\\\\\\\')" in func  # replace('\\', '\\\\')

    def test_escape_consistency_update_vs_insert(self):
        """Both _update_attribute and insert_task use same escape pattern."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/typedb/queries/tasks/crud.py").read_text()
        # Both should have the pattern: replace('\\', '\\\\').replace('"', '\\"')
        assert src.count("replace('\\\\', '\\\\\\\\').replace('\"', '\\\\\"')") >= 2


# ── Audit query date range defense ──────────────


class TestAuditQueryDateRangeDefense:
    """Verify audit trail date_to includes full day with microseconds."""

    def test_date_to_includes_microseconds(self):
        """date_to_end includes .999999 for microsecond precision."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/stores/audit.py").read_text()
        assert "T23:59:59.999999" in src

    def test_date_to_no_truncated_seconds(self):
        """No residual T23:59:59 without microseconds."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/stores/audit.py").read_text()
        # Count instances — should only have the .999999 variant
        count_with_micro = src.count("T23:59:59.999999")
        count_without = src.count("T23:59:59") - count_with_micro
        assert count_without == 0, f"Found {count_without} instances without microseconds"


# ── Audit retention defense ──────────────


class TestAuditRetentionDefense:
    """Verify audit retention is applied correctly."""

    def test_retention_default_is_7_days(self):
        """_apply_retention default is 7 days."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/stores/audit.py").read_text()
        assert "def _apply_retention(days: int = 7)" in src

    def test_record_audit_callable(self):
        """record_audit function is importable."""
        from governance.stores.audit import record_audit
        assert callable(record_audit)


# ── TypeDB access helpers defense ──────────────


class TestTypeDBAccessHelpersDefense:
    """Verify TypeDB access helpers handle edge cases."""

    def test_get_all_sessions_has_fallback(self):
        """get_all_sessions_from_typedb has allow_fallback parameter."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/stores/typedb_access.py").read_text()
        assert "allow_fallback" in src

    def test_session_to_dict_exists(self):
        """_session_to_dict conversion function exists."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/stores/typedb_access.py").read_text()
        assert "def _session_to_dict" in src


# ── Task description field defense ──────────────


class TestTaskDescriptionFieldDefense:
    """Verify task description resolution across conversion paths."""

    def test_task_to_response_uses_name_first(self):
        """task_to_response uses task.name as first fallback."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/stores/helpers.py").read_text()
        assert "task.name or task.description" in src

    def test_task_to_dict_uses_body_first(self):
        """_task_to_dict in typedb_access uses task.body as first fallback."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/stores/typedb_access.py").read_text()
        assert "task.body or task.description" in src

    def test_task_response_model_has_description(self):
        """TaskResponse model has description field."""
        from governance.models import TaskResponse
        assert "description" in TaskResponse.model_fields
