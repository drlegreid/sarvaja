"""Batch 196 — TypeDB access layer defense tests.

Validates fixes for:
- BUG-196-003: update_rule / delete_rule now wrapped in try/except
- BUG-196-006: delete_task backslash escape consistency
- BUG-196-009: Relationship read methods escape task_id
- BUG-196-021: RuntimeError included in TRANSIENT_EXCEPTIONS
"""
import ast
from pathlib import Path


SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-196-003: update_rule / delete_rule try/except ───────────────

class TestRuleCrudExceptionSafety:
    """Rules CRUD operations must be wrapped in try/except."""

    def test_update_rule_has_try_except(self):
        """Verify update_rule transaction is inside try/except."""
        src = (SRC / "governance/typedb/queries/rules/crud.py").read_text()
        # Find the update_rule method and verify try/except exists
        in_method = False
        has_try = False
        has_except = False
        for line in src.splitlines():
            if "def update_rule" in line:
                in_method = True
            elif in_method and line.strip().startswith("def "):
                break
            elif in_method:
                if "try:" in line:
                    has_try = True
                if "except Exception" in line:
                    has_except = True
        assert has_try and has_except, "update_rule must have try/except"

    def test_delete_rule_has_try_except(self):
        """Verify delete_rule transaction is inside try/except."""
        src = (SRC / "governance/typedb/queries/rules/crud.py").read_text()
        in_method = False
        has_try = False
        has_except = False
        for line in src.splitlines():
            if "def delete_rule" in line:
                in_method = True
            elif in_method and line.strip().startswith("def ") and "delete_rule" not in line:
                break
            elif in_method:
                if "try:" in line:
                    has_try = True
                if "except Exception" in line:
                    has_except = True
        assert has_try and has_except, "delete_rule must have try/except"


# ── BUG-196-006: delete_task escape consistency ─────────────────────

class TestDeleteTaskEscape:
    """delete_task must escape both backslash and quotes."""

    def test_delete_task_escapes_backslash(self):
        """Verify delete_task escapes backslash before quotes."""
        src = (SRC / "governance/typedb/queries/tasks/crud.py").read_text()
        in_method = False
        for line in src.splitlines():
            if "def delete_task" in line:
                in_method = True
            elif in_method and line.strip().startswith("def "):
                break
            elif in_method and "replace" in line and "'\\\\'" in line:
                return  # Found backslash escape
        assert False, "delete_task must escape backslash in task_id"


# ── BUG-196-009: Relationship methods escape task_id ────────────────

class TestRelationshipEscaping:
    """All relationship read methods must escape task_id."""

    def _check_method_escapes(self, method_name: str):
        src = (SRC / "governance/typedb/queries/tasks/relationships.py").read_text()
        in_method = False
        has_escape = False
        for line in src.splitlines():
            if f"def {method_name}" in line:
                in_method = True
            elif in_method and line.strip().startswith("def "):
                break
            elif in_method and "replace" in line and "'\\\\'" in line:
                has_escape = True
        return has_escape

    def test_get_task_children_escapes(self):
        assert self._check_method_escapes("get_task_children"), \
            "get_task_children must escape task_id"

    def test_get_task_parent_escapes(self):
        assert self._check_method_escapes("get_task_parent"), \
            "get_task_parent must escape task_id"

    def test_get_tasks_blocking_escapes(self):
        assert self._check_method_escapes("get_tasks_blocking"), \
            "get_tasks_blocking must escape task_id"

    def test_get_tasks_blocked_by_escapes(self):
        assert self._check_method_escapes("get_tasks_blocked_by"), \
            "get_tasks_blocked_by must escape task_id"

    def test_get_related_tasks_escapes(self):
        assert self._check_method_escapes("get_related_tasks"), \
            "get_related_tasks must escape task_id"


# ── BUG-196-021: RuntimeError in TRANSIENT_EXCEPTIONS ──────────────

class TestRetryTransientExceptions:
    """retry_on_transient must catch RuntimeError from _execute_query."""

    def test_runtime_error_in_transient_exceptions(self):
        from governance.stores.retry import TRANSIENT_EXCEPTIONS
        assert RuntimeError in TRANSIENT_EXCEPTIONS, \
            "TRANSIENT_EXCEPTIONS must include RuntimeError"

    def test_transient_exceptions_still_has_originals(self):
        from governance.stores.retry import TRANSIENT_EXCEPTIONS
        assert ConnectionError in TRANSIENT_EXCEPTIONS
        assert TimeoutError in TRANSIENT_EXCEPTIONS
        assert OSError in TRANSIENT_EXCEPTIONS
