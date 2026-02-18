"""Batch 393 — MCP info disclosure, ingestion guards, route protection, TypeQL control chars.

Validates fixes for:
- BUG-391-DEC-001: typedb_error uses type(e).__name__ not str(e)
- BUG-391-DEC-002: chromadb_error uses type(e).__name__ not str(e)
- BUG-391-ING-001: ingest_session_content wrapped in try/except
- BUG-391-ING-002: mine_session_links wrapped in try/except
- BUG-391-ING-003: ingest_session_full wrapped in try/except
- BUG-391-ING-004: ingestion_status wrapped in try/except
- BUG-392-ERR-001: get_session() wrapped in try/except in evidence/rendered
- BUG-392-ERR-002: ingestion_status logger.error has exc_info=True
- BUG-393-CRUD-001: _strip_ctl helper strips control chars before TypeQL escape
"""
import importlib
import inspect


# ── BUG-391-DEC-001/002: decisions.py MCP response sanitization ──────

class TestDecisionsMcpSanitization:
    """governance_health must not leak str(e) in service_status error fields."""

    def _src(self):
        mod = importlib.import_module("governance.mcp_tools.decisions")
        return inspect.getsource(mod)

    def test_typedb_error_uses_type_name(self):
        src = self._src()
        idx = src.index("typedb_error")
        block = src[idx:idx + 500]
        assert "type(e).__name__" in block

    def test_chromadb_error_uses_type_name(self):
        src = self._src()
        idx = src.index("chromadb_error")
        block = src[idx:idx + 1200]
        assert "type(e).__name__" in block

    def test_no_str_e_in_error_assignments(self):
        """No str(e) should appear in error variable assignments."""
        src = self._src()
        bad_lines = [
            line.strip() for line in src.split("\n")
            if ("typedb_error" in line or "chromadb_error" in line)
            and "str(e)" in line
        ]
        assert not bad_lines, f"str(e) in error assignments: {bad_lines}"

    def test_bug_markers_present(self):
        src = self._src()
        for marker in ["BUG-391-DEC-001", "BUG-391-DEC-002"]:
            assert marker in src, f"Missing {marker}"


# ── BUG-391-ING-001..004: ingestion.py service call guards ──────────

class TestIngestionToolGuards:
    """All ingestion MCP tool functions must have try/except around service calls."""

    def _src(self):
        mod = importlib.import_module("governance.mcp_tools.ingestion")
        return inspect.getsource(mod)

    def test_ingest_session_content_has_try_except(self):
        src = self._src()
        idx = src.index("def ingest_session_content")
        block = src[idx:idx + 1800]
        assert "except Exception" in block
        assert "type(e).__name__" in block

    def test_mine_session_links_has_try_except(self):
        src = self._src()
        idx = src.index("def mine_session_links")
        block = src[idx:idx + 1600]
        assert "except Exception" in block
        assert "type(e).__name__" in block

    def test_ingest_session_full_has_try_except(self):
        src = self._src()
        idx = src.index("def ingest_session_full")
        block = src[idx:idx + 1600]
        assert "except Exception" in block
        assert "type(e).__name__" in block

    def test_ingestion_status_has_try_except(self):
        src = self._src()
        idx = src.index("def ingestion_status")
        block = src[idx:idx + 900]
        assert "except Exception" in block
        assert "type(e).__name__" in block

    def test_all_tools_have_exc_info(self):
        """All service call guards must log with exc_info=True."""
        src = self._src()
        # Count exc_info=True occurrences — should be at least 4 (one per tool)
        count = src.count("exc_info=True")
        assert count >= 4, f"Expected >=4 exc_info=True, found {count}"

    def test_has_logger(self):
        src = self._src()
        assert "logger = logging.getLogger" in src

    def test_bug_markers_present(self):
        src = self._src()
        for marker in ["BUG-391-ING-001", "BUG-391-ING-002",
                        "BUG-391-ING-003", "BUG-391-ING-004"]:
            assert marker in src, f"Missing {marker}"


# ── BUG-392-ERR-001/002: detail.py route protection ─────────────────

class TestDetailRouteProtection:
    """session_evidence_rendered must wrap get_session in try/except."""

    def _src(self):
        mod = importlib.import_module("governance.routes.sessions.detail")
        return inspect.getsource(mod)

    def test_get_session_wrapped(self):
        src = self._src()
        idx = src.index("def session_evidence_rendered")
        block = src[idx:idx + 600]
        assert "except Exception" in block
        assert "type(e).__name__" in block

    def test_ingestion_status_has_exc_info(self):
        src = self._src()
        idx = src.index("def ingestion_status")
        block = src[idx:idx + 700]
        assert "exc_info=True" in block

    def test_bug_markers_present(self):
        src = self._src()
        for marker in ["BUG-392-ERR-001", "BUG-392-ERR-002"]:
            assert marker in src, f"Missing {marker}"


# ── BUG-393-CRUD-001: tasks/crud.py control char stripping ──────────

class TestTasksCrudControlCharStripping:
    """_strip_ctl helper must exist and be used at key escape sites."""

    def _src(self):
        mod = importlib.import_module("governance.typedb.queries.tasks.crud")
        return inspect.getsource(mod)

    def test_strip_ctl_helper_exists(self):
        src = self._src()
        assert "def _strip_ctl" in src

    def test_strip_ctl_removes_newline(self):
        from governance.typedb.queries.tasks.crud import _strip_ctl
        assert _strip_ctl("hello\nworld") == "helloworld"

    def test_strip_ctl_removes_carriage_return(self):
        from governance.typedb.queries.tasks.crud import _strip_ctl
        assert _strip_ctl("hello\rworld") == "helloworld"

    def test_strip_ctl_replaces_tab_with_space(self):
        from governance.typedb.queries.tasks.crud import _strip_ctl
        assert _strip_ctl("hello\tworld") == "hello world"

    def test_strip_ctl_removes_null(self):
        from governance.typedb.queries.tasks.crud import _strip_ctl
        assert _strip_ctl("hello\0world") == "helloworld"

    def test_strip_ctl_preserves_normal_text(self):
        from governance.typedb.queries.tasks.crud import _strip_ctl
        assert _strip_ctl("GAP-UI-001") == "GAP-UI-001"

    def test_update_attribute_uses_strip_ctl(self):
        src = self._src()
        idx = src.index("def _update_attribute")
        block = src[idx:idx + 700]
        assert "_strip_ctl" in block

    def test_set_lifecycle_timestamps_uses_strip_ctl(self):
        src = self._src()
        idx = src.index("def _set_lifecycle_timestamps")
        block = src[idx:idx + 500]
        assert "_strip_ctl" in block

    def test_bug_marker_present(self):
        src = self._src()
        assert "BUG-393-CRUD-001" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch393Imports:
    def test_decisions_mcp_importable(self):
        import governance.mcp_tools.decisions
        assert governance.mcp_tools.decisions is not None

    def test_ingestion_mcp_importable(self):
        import governance.mcp_tools.ingestion
        assert governance.mcp_tools.ingestion is not None

    def test_detail_routes_importable(self):
        import governance.routes.sessions.detail
        assert governance.routes.sessions.detail is not None

    def test_tasks_crud_importable(self):
        import governance.typedb.queries.tasks.crud
        assert governance.typedb.queries.tasks.crud is not None
