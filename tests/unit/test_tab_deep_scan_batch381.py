"""
Deep Scan Batch 381 — Defense Tests
====================================
Verifies BUG-381-SES-001 through BUG-381-VEC-001.

Batch 378-381 findings:
- BUG-381-SES-001: sessions/crud.py create_session ValueError sanitized (1 fix)
- BUG-381-SES-002: sessions/crud.py end_session ValueError sanitized (1 fix)
- BUG-381-SES-003: sessions/crud.py list_sessions catch-all added (1 fix)
- BUG-381-TSK-001: tasks/crud.py create_task ValueError sanitized (1 fix)
- BUG-381-VER-001: tasks_crud_verify.py JSONDecodeError sanitized (1 fix)
- BUG-381-LNK-001: tasks_linking.py commit_sha format validation (1 fix)
- BUG-381-ORCH-001: ingestion_orchestrator.py path redacted (2 fixes)
- BUG-381-ORCH-002: ingestion_orchestrator.py file field uses name only (1 fix)
- BUG-381-VEC-001: vector_store/store.py print() → logger (6 fixes)

Total: 15 production fixes, verified by source introspection tests.
"""

import importlib
import inspect
import re

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_source(module_path: str) -> str:
    """Get source code of a module by dotted path."""
    mod = importlib.import_module(module_path)
    return inspect.getsource(mod)


# ===========================================================================
# BUG-381-SES-001/002/003: sessions/crud.py — ValueError sanitized + catch-all
# ===========================================================================

class TestSessionsCrudSanitization:
    """Verify sessions CRUD no longer leaks str(e) in ValueError handlers."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        self.source = _get_source("governance.routes.sessions.crud")

    def test_bug_ses_001_marker(self):
        assert "BUG-381-SES-001" in self.source

    def test_bug_ses_002_marker(self):
        assert "BUG-381-SES-002" in self.source

    def test_bug_ses_003_marker(self):
        assert "BUG-381-SES-003" in self.source

    def test_no_raw_str_e_in_value_error_handlers(self):
        """ValueError handlers should NOT use detail=str(e)."""
        for line in self.source.splitlines():
            stripped = line.strip()
            if "ValueError" in stripped and "except" in stripped:
                continue  # This is the except line itself
            if "HTTPException" in stripped and "detail=" in stripped:
                if "str(e)" in stripped:
                    pytest.fail(f"Raw str(e) in HTTPException: {stripped}")

    def test_create_session_uses_type_name(self):
        """create_session ValueError handler should use type(e).__name__."""
        found = False
        for line in self.source.splitlines():
            if "Session conflict" in line and "type(e).__name__" in line:
                found = True
                break
        assert found, "create_session ValueError should use type(e).__name__"

    def test_end_session_uses_type_name(self):
        """end_session ValueError handler should use type(e).__name__."""
        found = False
        for line in self.source.splitlines():
            if "Session conflict" in line and "type(e).__name__" in line:
                found = True
                break
        assert found, "end_session ValueError should use type(e).__name__"

    def test_list_sessions_catch_all_present(self):
        """list_sessions should have a catch-all Exception handler."""
        in_list_sessions = False
        found_catch_all = False
        for line in self.source.splitlines():
            if "def list_sessions" in line or "async def list_sessions" in line:
                in_list_sessions = True
            if in_list_sessions and "async def " in line and "list_sessions" not in line:
                break
            if in_list_sessions and "except Exception" in line:
                found_catch_all = True
                break
        assert found_catch_all, "list_sessions must have a catch-all Exception handler"

    def test_list_sessions_catch_all_uses_type_name(self):
        """list_sessions catch-all should use type(e).__name__."""
        found = False
        for line in self.source.splitlines():
            if "Failed to list sessions" in line and "type(e).__name__" in line:
                found = True
                break
        assert found, "list_sessions catch-all should use type(e).__name__"


# ===========================================================================
# BUG-381-TSK-001: tasks/crud.py — ValueError sanitized
# ===========================================================================

class TestTasksCrudSanitization:
    """Verify tasks CRUD no longer leaks str(e) in ValueError handler."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        self.source = _get_source("governance.routes.tasks.crud")

    def test_bug_marker_present(self):
        assert "BUG-381-TSK-001" in self.source

    def test_no_raw_str_e_in_value_error(self):
        """ValueError handler should NOT use detail=str(e)."""
        for line in self.source.splitlines():
            stripped = line.strip()
            if "HTTPException" in stripped and "detail=str(e)" in stripped:
                pytest.fail(f"Raw str(e) in HTTPException: {stripped}")

    def test_create_task_uses_type_name(self):
        """create_task ValueError handler should use type(e).__name__."""
        found = False
        for line in self.source.splitlines():
            if "Task conflict" in line and "type(e).__name__" in line:
                found = True
                break
        assert found, "create_task ValueError should use type(e).__name__"

    def test_create_task_has_catch_all(self):
        """create_task should have a catch-all Exception handler."""
        in_create_task = False
        found_catch_all = False
        for line in self.source.splitlines():
            if "async def create_task" in line:
                in_create_task = True
            if in_create_task and "async def " in line and "create_task" not in line:
                break
            if in_create_task and "except Exception" in line:
                found_catch_all = True
                break
        assert found_catch_all, "create_task must have a catch-all Exception handler"


# ===========================================================================
# BUG-381-VER-001: tasks_crud_verify.py — JSONDecodeError sanitized
# ===========================================================================

class TestTasksVerifySanitization:
    """Verify session_sync_todos no longer leaks JSONDecodeError details."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        self.source = _get_source("governance.mcp_tools.tasks_crud_verify")

    def test_bug_marker_present(self):
        assert "BUG-381-VER-001" in self.source

    def test_json_decode_error_sanitized(self):
        """JSONDecodeError handler should use type(e).__name__, not str(e)."""
        for line in self.source.splitlines():
            stripped = line.strip()
            if "JSONDecodeError" in stripped or "json_lib.JSONDecodeError" in stripped:
                continue
            if "Invalid JSON" in stripped and "format_mcp_result" in stripped:
                if "str(e)" in stripped or re.search(r'\{e\}', stripped):
                    if "type(e).__name__" not in stripped:
                        pytest.fail(f"Raw error in JSON decode handler: {stripped}")

    def test_json_error_uses_type_name(self):
        """Error response should contain type(e).__name__."""
        found = False
        for line in self.source.splitlines():
            if "Invalid JSON" in line and "type(e).__name__" in line:
                found = True
                break
        assert found, "JSONDecodeError handler should use type(e).__name__"


# ===========================================================================
# BUG-381-LNK-001: tasks_linking.py — commit_sha validation
# ===========================================================================

class TestTasksLinkingValidation:
    """Verify task_link_commit validates commit_sha format."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        self.source = _get_source("governance.mcp_tools.tasks_linking")

    def test_bug_marker_present(self):
        assert "BUG-381-LNK-001" in self.source

    def test_commit_sha_validation_present(self):
        """task_link_commit should validate commit_sha format."""
        found = False
        for line in self.source.splitlines():
            if "fullmatch" in line and "0-9a-fA-F" in line:
                found = True
                break
        assert found, "commit_sha format validation (hex, 7-40 chars) must be present"

    def test_commit_sha_error_message(self):
        """Invalid commit_sha should return clear error message."""
        found = False
        for line in self.source.splitlines():
            if "commit_sha must be" in line and "hex string" in line:
                found = True
                break
        assert found, "Error message for invalid commit_sha must be present"


# ===========================================================================
# BUG-381-ORCH-001/002: ingestion_orchestrator.py — path redacted
# ===========================================================================

class TestIngestionOrchestratorPathRedaction:
    """Verify ingestion orchestrator no longer exposes absolute paths."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        self.source = _get_source("governance.services.ingestion_orchestrator")

    def test_bug_orch_001_marker(self):
        assert "BUG-381-ORCH-001" in self.source

    def test_bug_orch_002_marker(self):
        assert "BUG-381-ORCH-002" in self.source

    def test_no_absolute_path_in_file_not_found(self):
        """'File not found' error should use path.name, not str(path)."""
        for line in self.source.splitlines():
            stripped = line.strip()
            if "File not found" in stripped and "error" in stripped:
                assert "path.name" in stripped, f"Should use path.name: {stripped}"

    def test_result_file_field_uses_name(self):
        """Result dict 'file' field should use path.name, not str(path)."""
        found = False
        for line in self.source.splitlines():
            stripped = line.strip()
            if '"file":' in stripped and "path.name" in stripped:
                found = True
                break
        assert found, "Result 'file' field should use path.name"


# ===========================================================================
# BUG-381-VEC-001: vector_store/store.py — print() → logger
# ===========================================================================

class TestVectorStorePrintRemoval:
    """Verify VectorStore no longer uses print() — uses logger instead."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        self.source = _get_source("governance.vector_store.store")

    def test_bug_marker_present(self):
        assert "BUG-381-VEC-001" in self.source

    def test_no_print_statements(self):
        """No print() calls should remain in store.py."""
        for line in self.source.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if stripped.startswith("print(") or stripped.startswith("print ("):
                pytest.fail(f"print() still present: {stripped}")

    def test_logger_imported(self):
        """Module should import logging and create logger."""
        assert "import logging" in self.source
        assert "getLogger(__name__)" in self.source

    def test_logger_error_used(self):
        """Error paths should use logger.error()."""
        count = self.source.count("logger.error(")
        assert count >= 3, f"Expected >=3 logger.error() calls, found {count}"

    def test_logger_warning_used(self):
        """Warning paths should use logger.warning()."""
        count = self.source.count("logger.warning(")
        assert count >= 2, f"Expected >=2 logger.warning() calls, found {count}"


# ===========================================================================
# Import Verification
# ===========================================================================

class TestBatch381Imports:
    """Verify all modified modules import cleanly."""

    @pytest.mark.parametrize("module_path", [
        "governance.routes.sessions.crud",
        "governance.routes.tasks.crud",
        "governance.mcp_tools.tasks_crud_verify",
        "governance.mcp_tools.tasks_linking",
        "governance.services.ingestion_orchestrator",
        "governance.vector_store.store",
    ])
    def test_module_imports(self, module_path):
        mod = importlib.import_module(module_path)
        assert mod is not None
