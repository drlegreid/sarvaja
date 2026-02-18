"""
Unit tests for Tab Deep Scan Batch 44 — sessions_linking resource leaks,
transcript.py file handling, detail.py routes, session_bridge logging.

4 resource leaks fixed (BUG-LINK-LEAK-001 × 4). Multiple false positives
verified (transcript NameError, detail.py silent None, completion_rate div).

Per TEST-E2E-01-v1: Tier 1 unit tests for data flow validation.
"""

import inspect


# ── BUG-LINK-LEAK-001: sessions_linking try/finally ──────────────────


class TestSessionsLinkingResourceSafety:
    """Verify sessions_linking.py uses try/finally for client cleanup."""

    def test_has_bugfix_marker(self):
        """BUG-LINK-LEAK-001 marker present in sessions_linking."""
        from governance.mcp_tools import sessions_linking
        source = inspect.getsource(sessions_linking)
        assert "BUG-LINK-LEAK-001" in source

    def test_four_try_finally_blocks(self):
        """All 4 linking functions use try/finally pattern."""
        from governance.mcp_tools import sessions_linking
        source = inspect.getsource(sessions_linking)
        # Count try/finally pairs (each function has one)
        finally_count = source.count("finally:")
        assert finally_count >= 4, f"Expected >=4 finally blocks, got {finally_count}"

    def test_client_close_in_finally(self):
        """client.close() appears after each finally: keyword."""
        from governance.mcp_tools import sessions_linking
        source = inspect.getsource(sessions_linking)
        lines = source.split("\n")
        finally_lines = [i for i, l in enumerate(lines) if "finally:" in l]
        for fl in finally_lines:
            # Check next 2 lines for client.close()
            nearby = "\n".join(lines[fl:fl + 3])
            assert "client.close()" in nearby, f"No client.close() near finally at line {fl}"

    def test_close_count_matches_finally_count(self):
        """Same number of actual client.close() calls as finally: blocks."""
        from governance.mcp_tools import sessions_linking
        source = inspect.getsource(sessions_linking)
        lines = source.split("\n")
        # Count only non-comment lines with client.close()
        close_count = sum(1 for l in lines if "client.close()" in l and not l.strip().startswith("#"))
        finally_count = source.count("finally:")
        assert close_count == finally_count, \
            f"close={close_count} vs finally={finally_count}"

    def test_session_get_tasks_has_finally(self):
        """session_get_tasks function uses try/finally."""
        from governance.mcp_tools import sessions_linking
        source = inspect.getsource(sessions_linking)
        # Find the function and verify it has finally
        func_start = source.index("def session_get_tasks")
        func_end = source.index("def session_link_rule")
        func_source = source[func_start:func_end]
        assert "finally:" in func_source
        assert "client.close()" in func_source


# ── Transcript: two-try-block design is safe ──────────────────────────


class TestTranscriptTwoTryDesign:
    """Verify cc_transcript.py two-try-block design prevents NameError."""

    def test_open_failure_returns_before_finally(self):
        """If open() fails, function returns before reaching finally block."""
        from governance.services.cc_transcript import stream_transcript
        source = inspect.getsource(stream_transcript)
        lines = source.split("\n")

        # Find the first except block (handles PermissionError/IOError)
        first_except = None
        first_return = None
        finally_line = None
        for i, line in enumerate(lines):
            if "PermissionError" in line and first_except is None:
                first_except = i
            if first_except and "return" in line and first_return is None:
                first_return = i
            if "finally:" in line:
                finally_line = i
                break

        assert first_except is not None, "Missing PermissionError handler"
        assert first_return is not None, "Missing return after PermissionError"
        assert finally_line is not None, "Missing finally block"
        assert first_return < finally_line, "return must come before finally"

    def test_finally_has_f_close(self):
        """finally block closes the file handle."""
        from governance.services.cc_transcript import stream_transcript
        source = inspect.getsource(stream_transcript)
        assert "finally:" in source
        assert "f.close()" in source

    def test_stream_returns_empty_for_missing_file(self):
        """Missing file returns empty generator (no crash)."""
        from pathlib import Path
        from governance.services.cc_transcript import stream_transcript
        results = list(stream_transcript(Path("/nonexistent/path.jsonl")))
        assert results == []


# ── Detail routes: proper 404 handling ────────────────────────────────


class TestDetailRoutesNullSafety:
    """Verify detail.py handles None results correctly."""

    def test_session_detail_raises_404(self):
        """get_session_detail returning None → 404."""
        from governance.routes.sessions import detail
        source = inspect.getsource(detail)
        assert "HTTPException(status_code=404" in source

    def test_evidence_rendered_checks_session(self):
        """Evidence route checks session existence."""
        from governance.routes.sessions.detail import session_evidence_rendered
        source = inspect.getsource(session_evidence_rendered)
        assert "if not session:" in source

    def test_evidence_rendered_checks_file_path(self):
        """Evidence route checks file_path existence."""
        from governance.routes.sessions.detail import session_evidence_rendered
        source = inspect.getsource(session_evidence_rendered)
        assert "if not file_path:" in source

    def test_evidence_rendered_checks_file_exists(self):
        """Evidence route checks file exists on disk."""
        from governance.routes.sessions.detail import session_evidence_rendered
        source = inspect.getsource(session_evidence_rendered)
        assert "if not p.exists():" in source


# ── Dashboard log: BUG-LOG-001 serialization ──────────────────────────


class TestDashboardLogSerialization:
    """Verify dashboard_log.py uses default=str."""

    def test_has_bugfix_marker(self):
        from governance.middleware import dashboard_log
        source = inspect.getsource(dashboard_log)
        assert "BUG-LOG-001" in source

    def test_has_default_str(self):
        from governance.middleware import dashboard_log
        source = inspect.getsource(dashboard_log)
        assert "default=str" in source


# ── Cross-layer consistency ──────────────────────────────────────────


class TestCrossLayerConsistencyBatch44:
    """Batch 44 cross-cutting consistency checks."""

    def test_linking_uses_typedb_client(self):
        """sessions_linking imports TypeDBClient."""
        from governance.mcp_tools import sessions_linking
        source = inspect.getsource(sessions_linking)
        assert "TypeDBClient" in source

    def test_linking_has_monitoring(self):
        """sessions_linking has monitoring instrumentation."""
        from governance.mcp_tools import sessions_linking
        source = inspect.getsource(sessions_linking)
        assert "log_monitor_event" in source

    def test_detail_has_logger(self):
        """detail.py has logger configured."""
        from governance.routes.sessions import detail
        assert hasattr(detail, "logger")

    def test_all_linking_functions_registered(self):
        """All 4 linking functions are defined."""
        from governance.mcp_tools import sessions_linking
        source = inspect.getsource(sessions_linking)
        assert "def session_get_tasks" in source
        assert "def session_link_rule" in source
        assert "def session_link_decision" in source
        assert "def session_link_evidence" in source
