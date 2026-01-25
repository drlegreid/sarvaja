"""
RF-004: Robot Framework Library for Task CRUD Split Tests.

Wraps tests/test_task_crud_split.py for Robot Framework tests.
Per DOC-SIZE-01-v1: Files under 300 lines.
"""

import sys
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

QUERIES_DIR = PROJECT_ROOT / "governance" / "typedb" / "queries" / "tasks"


class TaskCrudSplitLibrary:
    """Robot Framework library for Task CRUD Split tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def get_queries_dir(self) -> str:
        """Get the queries directory path."""
        return str(QUERIES_DIR)

    def crud_module_exists(self) -> bool:
        """Check if crud.py exists."""
        return (QUERIES_DIR / "crud.py").exists()

    def status_module_exists(self) -> bool:
        """Check if status.py exists."""
        return (QUERIES_DIR / "status.py").exists()

    def get_file_line_count(self, filename: str) -> int:
        """Get line count for a file in the queries directory."""
        filepath = QUERIES_DIR / filename
        if not filepath.exists():
            return -1
        with open(filepath, "r") as f:
            return len(f.readlines())

    def file_under_limit(self, filename: str, limit: int = 300) -> Dict[str, Any]:
        """Check if file is under line limit."""
        lines = self.get_file_line_count(filename)
        return {
            "filename": filename,
            "lines": lines,
            "limit": limit,
            "under_limit": lines >= 0 and lines < limit
        }

    def import_task_crud_operations(self) -> bool:
        """Try to import TaskCRUDOperations class."""
        try:
            from governance.typedb.queries.tasks.crud import TaskCRUDOperations
            return TaskCRUDOperations is not None
        except ImportError:
            return False

    def crud_has_method(self, method_name: str) -> bool:
        """Check if TaskCRUDOperations has a specific method."""
        try:
            from governance.typedb.queries.tasks.crud import TaskCRUDOperations
            return hasattr(TaskCRUDOperations, method_name)
        except ImportError:
            return False

    def import_status_update(self) -> bool:
        """Try to import update_task_status function."""
        try:
            from governance.typedb.queries.tasks.status import update_task_status
            return callable(update_task_status)
        except ImportError:
            return False

    def verify_backward_compatibility(self) -> Dict[str, bool]:
        """Verify all backward compatibility requirements."""
        return {
            "import_ok": self.import_task_crud_operations(),
            "has_insert_task": self.crud_has_method("insert_task"),
            "has_update_task_status": self.crud_has_method("update_task_status"),
            "has_delete_task": self.crud_has_method("delete_task"),
            "status_import_ok": self.import_status_update()
        }
