"""
Unit tests for Dashboard State Initialization.

Per DOC-SIZE-01-v1: Tests for extracted dashboard_state_init.py module.
Tests: init_form_and_detail_states, init_dialog_states.
"""

import pytest
from unittest.mock import MagicMock

from agent.governance_ui.dashboard_state_init import (
    init_form_and_detail_states,
    init_dialog_states,
)


class TestInitFormAndDetailStates:
    """Tests for init_form_and_detail_states()."""

    @pytest.fixture
    def state(self):
        return MagicMock()

    def test_sets_backlog_state(self, state):
        init_form_and_detail_states(state)
        assert state.available_tasks == []
        assert state.claimed_tasks == []
        assert state.backlog_agent_id == ""

    def test_sets_rule_form_state(self, state):
        init_form_and_detail_states(state)
        assert state.show_rule_detail is False
        assert state.show_rule_form is False
        assert state.rule_form_mode == "create"
        assert state.rules_search_query == ""

    def test_sets_filter_options(self, state):
        init_form_and_detail_states(state)
        # Should set list values from constants
        assert state.status_options is not None
        assert state.category_options is not None
        assert state.task_status_options is not None
        assert state.task_phase_options is not None

    def test_sets_rule_form_fields(self, state):
        init_form_and_detail_states(state)
        assert state.form_rule_id == ""
        assert state.form_rule_title == ""
        assert state.form_rule_directive == ""
        assert state.form_rule_category == "governance"
        assert state.form_rule_priority == "HIGH"

    def test_sets_task_form_state(self, state):
        init_form_and_detail_states(state)
        assert state.show_task_form is False
        assert state.form_task_id == ""
        assert state.form_task_phase == "P10"

    def test_sets_detail_views(self, state):
        init_form_and_detail_states(state)
        assert state.selected_task is None
        assert state.show_task_detail is False
        assert state.selected_session is None
        assert state.show_session_detail is False
        assert state.selected_decision is None
        assert state.show_decision_detail is False

    def test_sets_chat_state(self, state):
        init_form_and_detail_states(state)
        assert state.chat_messages == []
        assert state.chat_input == ""
        assert state.chat_loading is False

    def test_sets_file_viewer_state(self, state):
        init_form_and_detail_states(state)
        assert state.show_file_viewer is False
        assert state.file_viewer_content == ""

    def test_sets_test_runner_state(self, state):
        init_form_and_detail_states(state)
        assert state.tests_loading is False
        assert state.tests_running is False
        assert state.tests_recent_runs == []


class TestInitDialogStates:
    """Tests for init_dialog_states()."""

    def test_sets_dialog_states(self):
        state = MagicMock()
        init_dialog_states(state)
        assert state.has_error is False
        assert state.show_confirm is False
        assert state.confirm_message == ""
