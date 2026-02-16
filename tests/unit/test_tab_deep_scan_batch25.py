"""
Unit tests for Tab Deep Scan Batch 25 — Error state + loading flag consistency.

Covers: BUG-UI-LOAD-002 (monitor loading), BUG-UI-LOAD-003 (monitor error state),
BUG-UI-LOAD-004 (backlog error state), BUG-UI-EXEC-001 (executive error state),
BUG-UI-SESSION-003 (stale error reset).
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect


# ── BUG-UI-LOAD-002: Monitor data error handling ──────────────────────


class TestMonitorDataErrorHandling:
    """load_monitor_data in data_loaders.py must have error handling."""

    def test_has_try_except(self):
        from agent.governance_ui.controllers import data_loaders
        source = inspect.getsource(data_loaders)
        start = source.index("def load_monitor_data(")
        end = source.index("\n    def load_backlog_data", start + 1)
        fn_src = source[start:end]
        assert "try:" in fn_src
        assert "except Exception" in fn_src

    def test_has_error_trace(self):
        from agent.governance_ui.controllers import data_loaders
        source = inspect.getsource(data_loaders)
        start = source.index("def load_monitor_data(")
        end = source.index("\n    def load_backlog_data", start + 1)
        fn_src = source[start:end]
        assert "add_error_trace" in fn_src

    def test_has_bugfix_marker(self):
        from agent.governance_ui.controllers import data_loaders
        source = inspect.getsource(data_loaders)
        assert "BUG-UI-LOAD-002" in source


# ── BUG-UI-LOAD-003: Monitor trigger error state ─────────────────────


class TestMonitorTriggerErrorState:
    """load_monitor_data trigger in monitor.py must set has_error."""

    def test_uses_has_error(self):
        from agent.governance_ui.controllers import monitor
        source = inspect.getsource(monitor)
        start = source.index("def load_monitor_data(")
        fn_src = source[start:]
        assert "has_error = True" in fn_src

    def test_uses_error_message(self):
        from agent.governance_ui.controllers import monitor
        source = inspect.getsource(monitor)
        start = source.index("def load_monitor_data(")
        fn_src = source[start:]
        assert "error_message" in fn_src

    def test_no_status_message_for_errors(self):
        """Errors should use error_message, not status_message."""
        from agent.governance_ui.controllers import monitor
        source = inspect.getsource(monitor)
        start = source.index("def load_monitor_data(")
        fn_src = source[start:]
        # Exception handler should NOT assign state.status_message
        lines = fn_src.splitlines()
        in_except = False
        for line in lines:
            if "except Exception" in line:
                in_except = True
            elif in_except and line.strip() and not line.strip().startswith("#"):
                if "state.status_message" in line:
                    raise AssertionError(
                        f"Error handler uses status_message: {line.strip()}"
                    )
                if "finally:" in line or (line.strip() and not line.startswith(" " * 12)):
                    break

    def test_imports_add_error_trace(self):
        from agent.governance_ui.controllers import monitor
        source = inspect.getsource(monitor)
        assert "add_error_trace" in source

    def test_has_bugfix_marker(self):
        from agent.governance_ui.controllers import monitor
        source = inspect.getsource(monitor)
        assert "BUG-UI-LOAD-003" in source


# ── BUG-UI-LOAD-004: Backlog error state ─────────────────────────────


class TestBacklogErrorState:
    """load_backlog_data must set has_error on failure."""

    def test_has_error_on_exception(self):
        from agent.governance_ui.controllers import data_loaders
        source = inspect.getsource(data_loaders)
        start = source.index("def load_backlog_data(")
        end = source.index("\n    def load_executive_report_data", start + 1)
        fn_src = source[start:end]
        assert "has_error = True" in fn_src

    def test_has_error_message(self):
        from agent.governance_ui.controllers import data_loaders
        source = inspect.getsource(data_loaders)
        start = source.index("def load_backlog_data(")
        end = source.index("\n    def load_executive_report_data", start + 1)
        fn_src = source[start:end]
        assert "error_message" in fn_src

    def test_has_bugfix_marker(self):
        from agent.governance_ui.controllers import data_loaders
        source = inspect.getsource(data_loaders)
        assert "BUG-UI-LOAD-004" in source


# ── BUG-UI-EXEC-001: Executive report error state ────────────────────


class TestExecutiveReportErrorState:
    """Executive report non-200 response must set error state."""

    def test_non_200_sets_has_error(self):
        from agent.governance_ui.controllers import data_loaders
        source = inspect.getsource(data_loaders)
        start = source.index("def load_executive_report_data(")
        fn_src = source[start:]
        # Find the else branch (non-200)
        assert "has_error = True" in fn_src

    def test_non_200_sets_error_message(self):
        from agent.governance_ui.controllers import data_loaders
        source = inspect.getsource(data_loaders)
        start = source.index("def load_executive_report_data(")
        fn_src = source[start:]
        assert "Executive report API error" in fn_src

    def test_has_bugfix_marker(self):
        from agent.governance_ui.controllers import data_loaders
        source = inspect.getsource(data_loaders)
        assert "BUG-UI-EXEC-001" in source


# ── BUG-UI-SESSION-003: Stale error reset on page load ───────────────


class TestSessionsPageErrorReset:
    """load_sessions_page must clear has_error on reload."""

    def test_clears_has_error_at_start(self):
        from agent.governance_ui.controllers import sessions_pagination
        source = inspect.getsource(sessions_pagination)
        start = source.index("def load_sessions_page(")
        end = source.index("\n    @ctrl.trigger", start + 1)
        fn_src = source[start:end]
        # has_error = False must come before the API call
        lines = fn_src.splitlines()
        has_error_clear_line = None
        api_call_line = None
        for i, line in enumerate(lines):
            if "has_error = False" in line and has_error_clear_line is None:
                has_error_clear_line = i
            if "client.get" in line and api_call_line is None:
                api_call_line = i
        assert has_error_clear_line is not None, "has_error = False not found"
        assert api_call_line is not None, "API call not found"
        assert has_error_clear_line < api_call_line, \
            "has_error must be cleared before API call"

    def test_has_bugfix_marker(self):
        from agent.governance_ui.controllers import sessions_pagination
        source = inspect.getsource(sessions_pagination)
        assert "BUG-UI-SESSION-003" in source


# ── Error handling consistency across loaders ─────────────────────────


class TestLoaderErrorConsistency:
    """All loaders must follow consistent error handling patterns."""

    def test_all_loaders_have_try_except(self):
        """Every loader function in data_loaders.py must have try/except."""
        from agent.governance_ui.controllers import data_loaders
        source = inspect.getsource(data_loaders)
        loader_names = [
            "load_trust_data", "load_monitor_data",
            "load_backlog_data", "load_executive_report_data",
        ]
        for name in loader_names:
            start = source.index(f"def {name}(")
            # Find next def or @ctrl or return
            next_def = source.find("\n    def ", start + 1)
            next_ctrl = source.find("\n    @ctrl.", start + 1)
            candidates = [x for x in [next_def, next_ctrl] if x > 0]
            end = min(candidates) if candidates else len(source)
            fn_src = source[start:end]
            assert "except Exception" in fn_src, \
                f"{name} missing exception handler"

    def test_all_loaders_have_error_trace(self):
        """Every loader should call add_error_trace on failure."""
        from agent.governance_ui.controllers import data_loaders
        source = inspect.getsource(data_loaders)
        loader_names = [
            "load_trust_data", "load_monitor_data",
            "load_backlog_data", "load_executive_report_data",
        ]
        for name in loader_names:
            start = source.index(f"def {name}(")
            next_def = source.find("\n    def ", start + 1)
            next_ctrl = source.find("\n    @ctrl.", start + 1)
            candidates = [x for x in [next_def, next_ctrl] if x > 0]
            end = min(candidates) if candidates else len(source)
            fn_src = source[start:end]
            assert "add_error_trace" in fn_src, \
                f"{name} missing add_error_trace"
