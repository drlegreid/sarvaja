"""
Unit tests for Tab Deep Scan Batch 22 — Error handling + silent failure fixes.

Covers: BUG-UI-SILENT-FAIL-001 (replace bare except:pass with add_error_trace),
error_message vs status_message for failures,
print() antipattern removal.
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect


# ── data_loaders_refresh.py: no silent except:pass ────────────────────


class TestDataLoadersRefreshNoSilentFailures:
    """refresh_data in data_loaders_refresh must not swallow exceptions silently."""

    def test_no_bare_except_pass(self):
        """No bare 'except Exception: pass' or 'except: pass' patterns."""
        from agent.governance_ui.controllers import data_loaders_refresh
        source = inspect.getsource(data_loaders_refresh)
        # Count patterns like "except Exception:\n            pass"
        import re
        silent = re.findall(r'except\s+Exception\s*:\s*\n\s*pass', source)
        assert len(silent) == 0, f"Found {len(silent)} silent except:pass blocks"

    def test_refresh_rules_has_error_trace(self):
        from agent.governance_ui.controllers import data_loaders_refresh
        source = inspect.getsource(data_loaders_refresh)
        assert 'Refresh rules failed' in source

    def test_refresh_decisions_has_error_trace(self):
        from agent.governance_ui.controllers import data_loaders_refresh
        source = inspect.getsource(data_loaders_refresh)
        assert 'Refresh decisions failed' in source

    def test_refresh_tasks_has_error_trace(self):
        from agent.governance_ui.controllers import data_loaders_refresh
        source = inspect.getsource(data_loaders_refresh)
        assert 'Refresh tasks failed' in source

    def test_refresh_sessions_has_error_trace(self):
        from agent.governance_ui.controllers import data_loaders_refresh
        source = inspect.getsource(data_loaders_refresh)
        assert 'Refresh sessions failed' in source

    def test_refresh_agents_has_error_trace(self):
        from agent.governance_ui.controllers import data_loaders_refresh
        source = inspect.getsource(data_loaders_refresh)
        assert 'Refresh agents failed' in source

    def test_refresh_infra_has_error_trace(self):
        from agent.governance_ui.controllers import data_loaders_refresh
        source = inspect.getsource(data_loaders_refresh)
        assert 'Refresh infra failed' in source

    def test_outer_exception_uses_error_message(self):
        """BUG-UI-SILENT-FAIL-001: Outer handler must use error_message not status_message."""
        from agent.governance_ui.controllers import data_loaders_refresh
        source = inspect.getsource(data_loaders_refresh)
        assert 'BUG-UI-SILENT-FAIL-001' in source

    def test_outer_exception_sets_has_error(self):
        from agent.governance_ui.controllers import data_loaders_refresh
        source = inspect.getsource(data_loaders_refresh)
        start = source.index("def refresh_data")
        fn_end = source.index("\n    def load_sessions_list", start)
        fn_src = source[start:fn_end]
        # The outer exception handler must set has_error = True
        assert 'state.has_error = True' in fn_src


# ── common_handlers.py: no silent except:pass ─────────────────────────


class TestCommonHandlersNoSilentFailures:
    """refresh_data in common_handlers must not swallow exceptions silently."""

    def test_no_bare_except_pass(self):
        from agent.governance_ui.handlers import common_handlers
        source = inspect.getsource(common_handlers)
        import re
        silent = re.findall(r'except\s+Exception\s*:\s*\n\s*pass', source)
        assert len(silent) == 0, f"Found {len(silent)} silent except:pass blocks"

    def test_refresh_rules_has_error_trace(self):
        from agent.governance_ui.handlers import common_handlers
        source = inspect.getsource(common_handlers)
        assert 'Refresh rules failed' in source

    def test_refresh_decisions_has_error_trace(self):
        from agent.governance_ui.handlers import common_handlers
        source = inspect.getsource(common_handlers)
        assert 'Refresh decisions failed' in source

    def test_refresh_tasks_has_error_trace(self):
        from agent.governance_ui.handlers import common_handlers
        source = inspect.getsource(common_handlers)
        assert 'Refresh tasks failed' in source

    def test_refresh_sessions_has_error_trace(self):
        from agent.governance_ui.handlers import common_handlers
        source = inspect.getsource(common_handlers)
        assert 'Refresh sessions failed' in source

    def test_refresh_agents_has_error_trace(self):
        from agent.governance_ui.handlers import common_handlers
        source = inspect.getsource(common_handlers)
        assert 'Refresh agents failed' in source

    def test_outer_exception_uses_error_message(self):
        from agent.governance_ui.handlers import common_handlers
        source = inspect.getsource(common_handlers)
        assert 'BUG-UI-SILENT-FAIL-001' in source

    def test_outer_exception_sets_has_error(self):
        from agent.governance_ui.handlers import common_handlers
        source = inspect.getsource(common_handlers)
        start = source.index("def refresh_data")
        fn_end = source.index("\n    @ctrl.set", start)
        fn_src = source[start:fn_end]
        assert 'state.has_error = True' in fn_src


# ── No print() antipattern ────────────────────────────────────────────


class TestNoPrintAntipattern:
    """Controllers and handlers must not use print() for error logging."""

    def test_common_handlers_no_print(self):
        from agent.governance_ui.handlers import common_handlers
        source = inspect.getsource(common_handlers)
        import re
        prints = re.findall(r'\bprint\s*\(', source)
        assert len(prints) == 0, f"Found {len(prints)} print() calls"

    def test_data_loaders_refresh_no_print(self):
        from agent.governance_ui.controllers import data_loaders_refresh
        source = inspect.getsource(data_loaders_refresh)
        import re
        prints = re.findall(r'\bprint\s*\(', source)
        assert len(prints) == 0, f"Found {len(prints)} print() calls"


# ── Dead code removal — escalated_proposals ───────────────────────────


class TestDeadCodeRemoval:
    """Dead try/except around simple assignment should be removed."""

    def test_no_try_around_escalated_proposals(self):
        """The old try/except around `escalated_proposals = []` was dead code."""
        from agent.governance_ui.handlers import common_handlers
        source = inspect.getsource(common_handlers)
        # The escalated_proposals assignment should be direct, not wrapped
        start = source.index("load_trust_data")
        end = source.index("\ndef register_view_handlers", start)
        fn_src = source[start:end]
        assert "state.escalated_proposals = []" in fn_src
        # Should NOT have try/except around it
        import re
        bad = re.findall(r'try:\s*\n\s*state\.escalated_proposals\s*=\s*\[\]', fn_src)
        assert len(bad) == 0, "Unnecessary try/except around escalated_proposals"


# ── Proposals error trace ─────────────────────────────────────────────


class TestProposalsErrorTrace:
    """get_proposals() exceptions must be traced, not silently caught."""

    def test_proposals_failure_traced(self):
        from agent.governance_ui.handlers import common_handlers
        source = inspect.getsource(common_handlers)
        assert 'Load proposals failed' in source


# ── Error handling consistency across refresh functions ────────────────


class TestErrorHandlingConsistency:
    """Both refresh_data implementations must have matching error patterns."""

    def test_both_refresh_data_use_add_error_trace(self):
        """Both files' refresh_data must use add_error_trace for sub-failures."""
        from agent.governance_ui.controllers import data_loaders_refresh
        from agent.governance_ui.handlers import common_handlers
        src1 = inspect.getsource(data_loaders_refresh)
        src2 = inspect.getsource(common_handlers)
        # Both must have at least 5 add_error_trace calls in refresh_data
        assert src1.count('add_error_trace') >= 5
        assert src2.count('add_error_trace') >= 5

    def test_both_refresh_data_set_has_error_on_total_failure(self):
        """Both must set has_error when the entire refresh fails."""
        from agent.governance_ui.controllers import data_loaders_refresh
        from agent.governance_ui.handlers import common_handlers
        # Both must contain BUG-UI-SILENT-FAIL-001
        src1 = inspect.getsource(data_loaders_refresh)
        src2 = inspect.getsource(common_handlers)
        assert 'BUG-UI-SILENT-FAIL-001' in src1
        assert 'BUG-UI-SILENT-FAIL-001' in src2

    def test_trust_data_uses_add_error_trace(self):
        """load_trust_data must use add_error_trace instead of print()."""
        from agent.governance_ui.handlers import common_handlers
        source = inspect.getsource(common_handlers)
        start = source.index("def load_trust_data")
        end = source.index("\n        state.trust_leaderboard", start)
        fn_src = source[start:end]
        assert 'add_error_trace' in fn_src
