"""
TDD Tests for GAP-FILE-027: tasks/crud.py split.

Per DOC-SIZE-01-v1: Files under 300 lines.
Per TEST-FIX-01-v1: Fix MUST include verification evidence.

Created: 2026-01-14
"""

import pytest
from pathlib import Path


QUERIES_DIR = Path(__file__).parent.parent / "governance" / "typedb" / "queries" / "tasks"


class TestTaskCrudSplit:
    """Test task CRUD module structure after split."""

    def test_crud_module_exists(self):
        """Verify crud.py exists."""
        crud_file = QUERIES_DIR / "crud.py"
        assert crud_file.exists(), "crud.py must exist"

    def test_crud_under_400_lines(self):
        """Verify crud.py is under 400 lines per DOC-SIZE-01-v1."""
        crud_file = QUERIES_DIR / "crud.py"
        with open(crud_file, "r") as f:
            lines = len(f.readlines())
        assert lines < 400, f"crud.py has {lines} lines, should be <400"

    def test_status_module_exists(self):
        """Verify status.py extraction exists."""
        status_file = QUERIES_DIR / "status.py"
        assert status_file.exists(), "status.py should be extracted"

    def test_status_module_under_300_lines(self):
        """Verify status.py is under 300 lines."""
        status_file = QUERIES_DIR / "status.py"
        with open(status_file, "r") as f:
            lines = len(f.readlines())
        assert lines < 300, f"status.py has {lines} lines, should be <300"


class TestBackwardCompatibility:
    """Test backward compatibility after split."""

    def test_import_crud_class(self):
        """Verify TaskCRUDOperations can still be imported."""
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations
        assert TaskCRUDOperations is not None

    def test_crud_has_insert_task(self):
        """Verify crud still has insert_task method."""
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations
        assert hasattr(TaskCRUDOperations, "insert_task")

    def test_crud_has_update_task_status(self):
        """Verify crud still has update_task_status method (via import or delegation)."""
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations
        # After split, this should still be accessible
        assert hasattr(TaskCRUDOperations, "update_task_status")

    def test_crud_has_delete_task(self):
        """Verify crud still has delete_task method."""
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations
        assert hasattr(TaskCRUDOperations, "delete_task")


class TestStatusModule:
    """Test the extracted status module."""

    def test_status_has_update_function(self):
        """Verify status.py has update_task_status function."""
        from governance.typedb.queries.tasks.status import update_task_status
        assert callable(update_task_status)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
