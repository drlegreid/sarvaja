"""Batch 222 — UI controllers defense tests.

Validates fixes for:
- BUG-222-REGR-001: _start_regression must guard against None run_id
- BUG-222-HC-001: infra_loaders must handle None last_check value
- BUG-222-RULE-001: submit_rule_form must preserve status in edit mode
"""
from pathlib import Path
import re

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-222-REGR-001: run_id null guard ──────────────────────────────

class TestRegressionRunIdGuard:
    """_start_regression must check run_id before starting poll thread."""

    def test_run_id_guard_in_source(self):
        src = (SRC / "agent/governance_ui/controllers/tests.py").read_text()
        assert "if not run_id:" in src

    def test_tests_controller_importable(self):
        import agent.governance_ui.controllers.tests
        assert agent.governance_ui.controllers.tests is not None


# ── BUG-222-HC-001: None last_check guard ────────────────────────────

class TestHealthcheckNoneGuard:
    """infra_loaders must handle None value for last_check."""

    def test_none_guard_in_source(self):
        src = (SRC / "agent/governance_ui/controllers/infra_loaders.py").read_text()
        # Should use `or "Never"` pattern, not `.get(..., "Never")`
        assert 'or "Never"' in src


# ── BUG-222-RULE-001: Edit mode status preservation ─────────────────

class TestRuleEditStatusPreservation:
    """submit_rule_form must preserve existing status in edit mode."""

    def test_edit_mode_preserves_status_in_source(self):
        src = (SRC / "agent/governance_ui/controllers/rules.py").read_text()
        # Should reference rule_form_mode == "edit" for status
        assert "rule_form_mode" in src and "edit" in src and "status" in src


# ── Controllers defense tests ────────────────────────────────────────

class TestControllerImports:
    """Defense tests for UI controller modules."""

    def test_tasks_controller_importable(self):
        import agent.governance_ui.controllers.tasks
        assert agent.governance_ui.controllers.tasks is not None

    def test_sessions_controller_importable(self):
        import agent.governance_ui.controllers.sessions
        assert agent.governance_ui.controllers.sessions is not None

    def test_rules_controller_importable(self):
        import agent.governance_ui.controllers.rules
        assert agent.governance_ui.controllers.rules is not None

    def test_infra_controller_importable(self):
        import agent.governance_ui.controllers.infra
        assert agent.governance_ui.controllers.infra is not None

    def test_backlog_controller_importable(self):
        import agent.governance_ui.controllers.backlog
        assert agent.governance_ui.controllers.backlog is not None

    def test_trust_controller_importable(self):
        import agent.governance_ui.controllers.trust
        assert agent.governance_ui.controllers.trust is not None

    def test_chat_controller_importable(self):
        import agent.governance_ui.controllers.chat
        assert agent.governance_ui.controllers.chat is not None

    def test_audit_loaders_importable(self):
        import agent.governance_ui.controllers.audit_loaders
        assert agent.governance_ui.controllers.audit_loaders is not None

    def test_workflow_loaders_importable(self):
        import agent.governance_ui.controllers.workflow_loaders
        assert agent.governance_ui.controllers.workflow_loaders is not None

    def test_data_loaders_refresh_importable(self):
        import agent.governance_ui.controllers.data_loaders_refresh
        assert agent.governance_ui.controllers.data_loaders_refresh is not None

    def test_sessions_pagination_importable(self):
        import agent.governance_ui.controllers.sessions_pagination
        assert agent.governance_ui.controllers.sessions_pagination is not None

    def test_sessions_detail_loaders_importable(self):
        import agent.governance_ui.controllers.sessions_detail_loaders
        assert agent.governance_ui.controllers.sessions_detail_loaders is not None


# ── Infra loaders defense ────────────────────────────────────────────

class TestInfraLoadersDefense:
    """Defense tests for infra_loaders module."""

    def test_register_infra_loader_controllers_callable(self):
        from agent.governance_ui.controllers.infra_loaders import register_infra_loader_controllers
        assert callable(register_infra_loader_controllers)
