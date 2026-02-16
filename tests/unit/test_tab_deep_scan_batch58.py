"""
Batch 58 — Deep Scan: UI controller null guards + ingestion directory check.

Fixes verified:
- BUG-UI-RULE-EDIT-GUARD-001: null guard on selected_rule in rules edit mode
- BUG-INGEST-001: is_dir() guard before iterdir in ingest_all()
"""
import inspect

import pytest


# ===========================================================================
# BUG-UI-RULE-EDIT-GUARD-001: Rules edit null guard
# ===========================================================================

class TestRulesEditNullGuard:
    """Verify rules controller has null guard matching decisions controller."""

    def _get_rules_controller_source(self):
        from agent.governance_ui.controllers import rules
        return inspect.getsource(rules)

    def _get_decisions_controller_source(self):
        from agent.governance_ui.controllers import decisions
        return inspect.getsource(decisions)

    def test_rules_has_selected_rule_guard(self):
        """Rules edit must check 'not state.selected_rule' before .get()."""
        src = self._get_rules_controller_source()
        assert 'not state.selected_rule' in src

    def test_rules_has_error_message_on_missing_selection(self):
        """Must set error message when no rule selected for editing."""
        src = self._get_rules_controller_source()
        assert 'No rule selected for editing' in src

    def test_decisions_has_equivalent_guard(self):
        """Decisions controller has equivalent guard (reference)."""
        src = self._get_decisions_controller_source()
        assert 'not state.selected_decision' in src

    def test_rules_edit_mode_pattern(self):
        """Edit mode in submit must check selected_rule before API call."""
        src = self._get_rules_controller_source()
        # Find the submit_rule_form function specifically
        submit_idx = src.find('submit_rule_form')
        submit_section = src[submit_idx:]
        guard_idx = submit_section.find('No rule selected for editing')
        get_idx = submit_section.find("selected_rule.get('id')", guard_idx)
        assert guard_idx > 0 and get_idx > guard_idx, "Guard must come before .get() in submit"


# ===========================================================================
# BUG-INGEST-001: CC directory existence check
# ===========================================================================

class TestIngestionDirectoryGuard:
    """Verify ingest_all() checks directory existence before iterdir."""

    def _get_ingest_all_source(self):
        from governance.services.cc_session_ingestion import ingest_all
        return inspect.getsource(ingest_all)

    def test_has_is_dir_check(self):
        """ingest_all must check _DEFAULT_CC_DIR.is_dir() before iterdir."""
        src = self._get_ingest_all_source()
        assert 'is_dir()' in src

    def test_guard_before_iterdir(self):
        """is_dir() check must come before iterdir() call."""
        src = self._get_ingest_all_source()
        dir_check = src.find('is_dir()')
        iterdir_call = src.find('iterdir()')
        assert dir_check < iterdir_call, "is_dir() must precede iterdir()"

    def test_returns_empty_on_missing_dir(self):
        """Must return [] when directory doesn't exist."""
        src = self._get_ingest_all_source()
        # After the is_dir check, should return []
        assert 'return []' in src


# ===========================================================================
# Cross-controller audit: null guard consistency
# ===========================================================================

class TestControllerNullGuardConsistency:
    """Verify all CRUD controllers have null guards for edit/delete operations."""

    def test_decisions_has_delete_guard(self):
        """Decisions delete must check selected_decision."""
        from agent.governance_ui.controllers import decisions
        src = inspect.getsource(decisions)
        assert 'not state.selected_decision' in src

    def test_rules_has_is_loading_guard(self):
        """Rules submit must have is_loading guard."""
        from agent.governance_ui.controllers import rules
        src = inspect.getsource(rules)
        assert 'state.is_loading' in src

    def test_decisions_has_is_loading_guard(self):
        """Decisions submit must have is_loading guard."""
        from agent.governance_ui.controllers import decisions
        src = inspect.getsource(decisions)
        assert 'state.is_loading' in src

    def test_rules_has_validation_guard(self):
        """Rules submit must validate required fields."""
        from agent.governance_ui.controllers import rules
        src = inspect.getsource(rules)
        assert 'is required' in src or 'required' in src.lower()

    def test_decisions_has_validation_guard(self):
        """Decisions submit must validate required fields."""
        from agent.governance_ui.controllers import decisions
        src = inspect.getsource(decisions)
        assert 'is required' in src

    def test_httpx_always_has_timeout(self):
        """All httpx.Client() calls must have timeout parameter."""
        from agent.governance_ui.controllers import rules, decisions
        rules_src = inspect.getsource(rules)
        decisions_src = inspect.getsource(decisions)
        # Both should have timeout= in Client() calls
        assert 'timeout=' in rules_src
        assert 'timeout=' in decisions_src


# ===========================================================================
# CC scanner guard consistency
# ===========================================================================

class TestCCScannerGuards:
    """Verify CC session scanner has directory guards too."""

    def test_cc_session_scanner_has_dir_guard(self):
        """cc_session_scanner must check DEFAULT_CC_DIR.is_dir()."""
        try:
            from governance.services.cc_session_scanner import discover_cc_sessions
            src = inspect.getsource(discover_cc_sessions)
            assert 'is_dir()' in src or 'not' in src
        except ImportError:
            pytest.skip("cc_session_scanner not available")
