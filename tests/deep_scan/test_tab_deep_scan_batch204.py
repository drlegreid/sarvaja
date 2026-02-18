"""Batch 204 — MCP tool handler defense tests.

Validates fixes for:
- BUG-204-TYPEQL-001: TypeQL escaping in session_get_tasks
- BUG-204-ENCODING-001: read_text encoding in ingestion checkpoint listing
- BUG-204-OFFSET-001: Negative offset guard in tasks_list
"""
from pathlib import Path


SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-204-TYPEQL-001: TypeQL escaping ──────────────────────────────

class TestSessionLinkingTypeQLEscape:
    """session_get_tasks must escape session_id for TypeQL safety."""

    def test_session_get_tasks_escapes_session_id(self):
        """The query in session_get_tasks must escape session_id."""
        src = (SRC / "governance/mcp_tools/sessions_linking.py").read_text()
        in_func = False
        found_escape = False
        for line in src.splitlines():
            if "def session_get_tasks" in line:
                in_func = True
            elif in_func and line.strip().startswith("def "):
                break
            elif in_func and "replace" in line and "escape" in line.lower() or (in_func and 'replace(' in line and 'session_id' in line):
                found_escape = True
        assert found_escape, "session_get_tasks must escape session_id before TypeQL interpolation"


# ── BUG-204-ENCODING-001: Checkpoint read_text encoding ──────────────

class TestIngestionCheckpointEncoding:
    """Checkpoint listing must specify encoding on read_text."""

    def test_checkpoint_read_text_has_encoding(self):
        """ingestion.py must use read_text(encoding='utf-8')."""
        src = (SRC / "governance/mcp_tools/ingestion.py").read_text()
        assert 'read_text(encoding="utf-8")' in src or "read_text(encoding='utf-8')" in src

    def test_checkpoint_catches_unicode_error(self):
        """Checkpoint listing must catch UnicodeDecodeError."""
        src = (SRC / "governance/mcp_tools/ingestion.py").read_text()
        assert "UnicodeDecodeError" in src


# ── BUG-204-OFFSET-001: Negative offset guard ───────────────────────

class TestTasksListOffsetGuard:
    """tasks_list must guard against negative offset."""

    def test_tasks_list_has_offset_guard(self):
        """tasks_list must use max(0, offset) or similar guard."""
        src = (SRC / "governance/mcp_tools/tasks_crud.py").read_text()
        in_func = False
        found_guard = False
        for line in src.splitlines():
            if "def tasks_list" in line:
                in_func = True
            elif in_func and line.strip().startswith("def "):
                break
            elif in_func and "max(0" in line and "offset" in line:
                found_guard = True
        assert found_guard, "tasks_list must guard against negative offset"


# ── MCP tools importability ──────────────────────────────────────────

class TestMCPToolsImportable:
    """Key MCP tool modules should be importable."""

    def test_sessions_linking_importable(self):
        from governance.mcp_tools import sessions_linking
        assert hasattr(sessions_linking, "register_session_linking_tools")

    def test_ingestion_importable(self):
        from governance.mcp_tools import ingestion
        assert hasattr(ingestion, "register_ingestion_tools")

    def test_tasks_crud_importable(self):
        from governance.mcp_tools import tasks_crud
        assert hasattr(tasks_crud, "register_task_crud_tools")

    def test_common_format_mcp_result(self):
        from governance.mcp_tools.common import format_mcp_result
        result = format_mcp_result({"test": True})
        assert "test" in result  # Output format varies (json vs toon)
