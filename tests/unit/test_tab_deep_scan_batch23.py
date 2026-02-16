"""
Unit tests for Tab Deep Scan Batch 23 — Audit navigation + poll error handling.

Covers: BUG-UI-AUDIT-NAV-001 (dead code in navigate_to_entity),
BUG-UI-TESTS-POLL-001 (silent polling exceptions),
audit loader error handling patterns.
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect
import re


# ── BUG-UI-AUDIT-NAV-001: navigate_to_entity dead code removed ────────


class TestNavigateToEntityFix:
    """navigate_to_entity session path must not have dead code."""

    def test_source_has_audit_nav_fix(self):
        from agent.governance_ui.controllers import audit_loaders
        source = inspect.getsource(audit_loaders)
        assert "BUG-UI-AUDIT-NAV-001" in source

    def test_no_dead_set_false_after_select(self):
        """The old dead code `if not show: show = False` must be removed."""
        from agent.governance_ui.controllers import audit_loaders
        source = inspect.getsource(audit_loaders)
        start = source.index("def navigate_to_entity")
        end = source.index("\n    # Reactive filter", start)
        fn_src = source[start:end]
        # Must NOT have the pattern: if not state.show_session_detail: state.show_session_detail = False
        assert "if not state.show_session_detail" not in fn_src

    def test_session_path_uses_select_session(self):
        """Session navigation must delegate to ctrl.select_session."""
        from agent.governance_ui.controllers import audit_loaders
        source = inspect.getsource(audit_loaders)
        start = source.index("def navigate_to_entity")
        end = source.index("\n    # Reactive filter", start)
        fn_src = source[start:end]
        assert "ctrl.select_session(entity_id)" in fn_src

    def test_rule_path_sets_show_detail_true(self):
        from agent.governance_ui.controllers import audit_loaders
        source = inspect.getsource(audit_loaders)
        start = source.index("def navigate_to_entity")
        end = source.index("\n    # Reactive filter", start)
        fn_src = source[start:end]
        assert 'state.show_rule_detail = True' in fn_src

    def test_task_path_sets_show_detail_true(self):
        from agent.governance_ui.controllers import audit_loaders
        source = inspect.getsource(audit_loaders)
        start = source.index("def navigate_to_entity")
        end = source.index("\n    # Reactive filter", start)
        fn_src = source[start:end]
        assert 'state.show_task_detail = True' in fn_src

    def test_decision_path_sets_show_detail_true(self):
        from agent.governance_ui.controllers import audit_loaders
        source = inspect.getsource(audit_loaders)
        start = source.index("def navigate_to_entity")
        end = source.index("\n    # Reactive filter", start)
        fn_src = source[start:end]
        assert 'state.show_decision_detail = True' in fn_src


# ── BUG-UI-TESTS-POLL-001: Polling error handling ─────────────────────


class TestPollingErrorHandling:
    """Poll loops must not silently swallow all exceptions."""

    def test_poll_for_results_no_bare_except_pass(self):
        from agent.governance_ui.controllers import tests
        source = inspect.getsource(tests)
        start = source.index("def poll_for_results")
        end = source.index("\n    @ctrl.trigger(\"run_tests\")")
        fn_src = source[start:end]
        silent = re.findall(r'except\s+Exception\s*:\s*\n\s*pass', fn_src)
        assert len(silent) == 0, f"Found {len(silent)} silent except:pass in poll_for_results"

    def test_poll_for_results_has_consecutive_error_limit(self):
        from agent.governance_ui.controllers import tests
        source = inspect.getsource(tests)
        start = source.index("def poll_for_results")
        end = source.index("\n    @ctrl.trigger(\"run_tests\")")
        fn_src = source[start:end]
        assert "consecutive_errors" in fn_src

    def test_poll_for_regression_no_bare_except_pass(self):
        from agent.governance_ui.controllers import tests
        source = inspect.getsource(tests)
        start = source.index("def poll_for_regression")
        end = source.index("\n    @ctrl.trigger(\"run_regression\")")
        fn_src = source[start:end]
        silent = re.findall(r'except\s+Exception\s*:\s*\n\s*pass', fn_src)
        assert len(silent) == 0, f"Found {len(silent)} silent except:pass in poll_for_regression"

    def test_poll_for_regression_has_consecutive_error_limit(self):
        from agent.governance_ui.controllers import tests
        source = inspect.getsource(tests)
        start = source.index("def poll_for_regression")
        end = source.index("\n    @ctrl.trigger(\"run_regression\")")
        fn_src = source[start:end]
        assert "consecutive_errors" in fn_src

    def test_poll_source_has_bugfix_marker(self):
        from agent.governance_ui.controllers import tests
        source = inspect.getsource(tests)
        assert "BUG-UI-TESTS-POLL-001" in source

    def test_poll_breaks_after_consecutive_errors(self):
        """Poll must break after 5 consecutive errors."""
        from agent.governance_ui.controllers import tests
        source = inspect.getsource(tests)
        start = source.index("def poll_for_results")
        end = source.index("\n    @ctrl.trigger(\"run_tests\")")
        fn_src = source[start:end]
        assert "consecutive_errors >= 5" in fn_src
        assert "break" in fn_src


# ── Audit loader error handling ───────────────────────────────────────


class TestAuditLoaderErrorHandling:
    """Audit loader must handle errors gracefully."""

    def test_load_audit_trail_uses_add_error_trace(self):
        from agent.governance_ui.controllers import audit_loaders
        source = inspect.getsource(audit_loaders)
        assert 'add_error_trace' in source

    def test_audit_loading_always_reset(self):
        """audit_loading must be set to False in finally/after."""
        from agent.governance_ui.controllers import audit_loaders
        source = inspect.getsource(audit_loaders)
        start = source.index("def load_audit_trail")
        end = source.index("\n    @ctrl.trigger(\"load_audit_trail\")")
        fn_src = source[start:end]
        assert "audit_loading = False" in fn_src

    def test_audit_entries_fallback_on_error(self):
        from agent.governance_ui.controllers import audit_loaders
        source = inspect.getsource(audit_loaders)
        assert "audit_entries = []" in source


# ── Tests controller loading state patterns ───────────────────────────


class TestTestsControllerLoadingState:
    """Test controller must manage loading state correctly."""

    def test_load_tests_data_uses_finally(self):
        from agent.governance_ui.controllers import tests
        source = inspect.getsource(tests)
        start = source.index("def load_tests_data")
        end = source.index("\n    @ctrl.trigger(\"load_test_results\")")
        fn_src = source[start:end]
        assert "finally:" in fn_src
        assert "tests_loading = False" in fn_src

    def test_run_tests_resets_on_failure(self):
        from agent.governance_ui.controllers import tests
        source = inspect.getsource(tests)
        start = source.index("def on_run_tests")
        end = source.index("\n    @ctrl.trigger(\"view_test_run\")")
        fn_src = source[start:end]
        # tests_running = False should appear in both error paths
        count = fn_src.count("tests_running = False")
        assert count >= 2, f"Expected >=2 resets, found {count}"

    def test_regression_resets_on_failure(self):
        from agent.governance_ui.controllers import tests
        source = inspect.getsource(tests)
        start = source.index("def _start_regression")
        end = source.index("\n    def poll_for_regression")
        fn_src = source[start:end]
        count = fn_src.count("tests_running = False")
        assert count >= 2, f"Expected >=2 resets, found {count}"

    def test_poll_resets_running_on_exit(self):
        """Both poll functions must reset tests_running on loop exit."""
        from agent.governance_ui.controllers import tests
        source = inspect.getsource(tests)
        # After the for loop exits (max_polls or break), must reset
        start = source.index("def poll_for_results")
        end = source.index("\n    @ctrl.trigger(\"run_tests\")")
        fn_src = source[start:end]
        # Last line before next function should reset
        assert fn_src.rstrip().endswith('state.dirty("tests_running")')
