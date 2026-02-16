"""
Unit tests for EPIC-UI-VALUE-001: UI Orthogonal Value Audit.

Tests rule applicability, task commits/timestamps, session linked
rules/decisions, and task claim/complete controllers.
"""

from unittest.mock import MagicMock, patch, PropertyMock
import pytest


# ── Rule Applicability in Initial State ─────────────────────

class TestRuleApplicabilityState:
    def test_form_rule_applicability_default(self):
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert 'form_rule_applicability' in state
        assert state['form_rule_applicability'] == 'MANDATORY'


# ── Rules View Headers ──────────────────────────────────────

class TestRulesViewApplicability:
    def test_rules_headers_include_applicability(self):
        """Rules list table should have Applicability column."""
        import importlib
        import inspect
        mod = importlib.import_module("agent.governance_ui.views.rules_view")
        source = inspect.getsource(mod.build_rules_list_view)
        assert "Applicability" in source
        assert "applicability" in source


class TestRuleDetailApplicability:
    def test_detail_view_has_applicability_chip(self):
        """Rule detail view should show applicability chip."""
        import importlib
        import inspect
        mod = importlib.import_module("agent.governance_ui.views.rules_view_detail")
        source = inspect.getsource(mod.build_rule_detail_view)
        assert "rule-applicability" in source
        assert "MANDATORY" in source
        assert "RECOMMENDED" in source
        assert "FORBIDDEN" in source


class TestRuleFormApplicability:
    def test_rule_form_has_applicability_field(self):
        """Rule create/edit form should have applicability selector."""
        import importlib
        import inspect
        mod = importlib.import_module("agent.governance_ui.views.rules_view")
        source = inspect.getsource(mod.build_rule_form_view)
        assert "rule-form-applicability" in source
        assert "MANDATORY" in source
        assert "CONDITIONAL" in source


# ── Task Detail: Commits + Timestamps ───────────────────────

class TestTaskLinkedCommits:
    def test_forms_has_commit_chip(self):
        """Task forms should render linked_commits chips."""
        import importlib
        import inspect
        mod = importlib.import_module("agent.governance_ui.views.tasks.forms")
        source = inspect.getsource(mod.build_task_linked_items)
        assert "linked_commits" in source
        assert "task-commit-chip" in source
        assert "mdi-source-commit" in source

    def test_forms_has_timestamps(self):
        """Task forms should render claimed_at and completed_at."""
        import importlib
        import inspect
        mod = importlib.import_module("agent.governance_ui.views.tasks.forms")
        source = inspect.getsource(mod.build_task_linked_items)
        assert "claimed_at" in source
        assert "completed_at" in source


# ── Task Detail: Claim/Complete Buttons ─────────────────────

class TestTaskClaimCompleteButtons:
    def test_detail_has_claim_button(self):
        """Task detail should have Claim button for OPEN tasks."""
        import importlib
        import inspect
        mod = importlib.import_module("agent.governance_ui.views.tasks.detail")
        source = inspect.getsource(mod.build_task_detail_view)
        assert "task-detail-claim-btn" in source
        assert "claim_selected_task" in source

    def test_detail_has_complete_button(self):
        """Task detail should have Complete button for IN_PROGRESS tasks."""
        import importlib
        import inspect
        mod = importlib.import_module("agent.governance_ui.views.tasks.detail")
        source = inspect.getsource(mod.build_task_detail_view)
        assert "task-detail-complete-btn" in source
        assert "complete_selected_task" in source


# ── Task Controller: Claim/Complete ──────────────────────────

class TestTaskClaimController:
    def test_claim_task_posts_to_api(self):
        """claim_task should POST to /api/tasks/{id}/claim."""
        from agent.governance_ui.controllers.tasks import register_tasks_controllers

        state = MagicMock()
        ctrl = MagicMock()
        triggers = {}

        def capture_trigger(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator

        ctrl.trigger = capture_trigger
        ctrl.set = capture_trigger

        state.selected_task = {"task_id": "TASK-001", "status": "OPEN"}
        state.tasks = []
        state.tasks_page = 1
        state.tasks_per_page = 20
        state.tasks_pagination = {}

        register_tasks_controllers(state, ctrl, "http://test:8082")
        assert "claim_selected_task" in triggers

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"task_id": "TASK-001", "status": "IN_PROGRESS"}

        with patch("httpx.Client") as mock_client:
            client_inst = MagicMock()
            mock_client.return_value.__enter__ = MagicMock(return_value=client_inst)
            mock_client.return_value.__exit__ = MagicMock(return_value=False)
            client_inst.post.return_value = mock_resp

            triggers["claim_selected_task"]()
            client_inst.post.assert_called_once_with("http://test:8082/api/tasks/TASK-001/claim")

    def test_complete_task_posts_to_api(self):
        """complete_task should POST to /api/tasks/{id}/complete."""
        from agent.governance_ui.controllers.tasks import register_tasks_controllers

        state = MagicMock()
        ctrl = MagicMock()
        triggers = {}

        def capture_trigger(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator

        ctrl.trigger = capture_trigger
        ctrl.set = capture_trigger

        state.selected_task = {"task_id": "TASK-002", "status": "IN_PROGRESS"}
        state.tasks = []
        state.tasks_page = 1
        state.tasks_per_page = 20
        state.tasks_pagination = {}

        register_tasks_controllers(state, ctrl, "http://test:8082")
        assert "complete_selected_task" in triggers

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"task_id": "TASK-002", "status": "DONE"}

        with patch("httpx.Client") as mock_client:
            client_inst = MagicMock()
            mock_client.return_value.__enter__ = MagicMock(return_value=client_inst)
            mock_client.return_value.__exit__ = MagicMock(return_value=False)
            client_inst.post.return_value = mock_resp

            triggers["complete_selected_task"]()
            client_inst.post.assert_called_once_with("http://test:8082/api/tasks/TASK-002/complete")

    def test_claim_no_selected_task(self):
        """claim_task should no-op when no task selected."""
        from agent.governance_ui.controllers.tasks import register_tasks_controllers

        state = MagicMock()
        ctrl = MagicMock()
        triggers = {}

        def capture_trigger(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator

        ctrl.trigger = capture_trigger
        ctrl.set = capture_trigger

        state.selected_task = None
        state.tasks = []
        state.tasks_page = 1
        state.tasks_per_page = 20
        state.tasks_pagination = {}

        register_tasks_controllers(state, ctrl, "http://test:8082")
        # Should not raise
        triggers["claim_selected_task"]()


# ── Rules Controller: Applicability in Form ──────────────────

class TestRulesControllerApplicability:
    def test_edit_rule_sets_applicability(self):
        """edit_rule should populate form_rule_applicability."""
        from agent.governance_ui.controllers.rules import register_rules_controllers

        state = MagicMock()
        ctrl = MagicMock()
        triggers = {}

        def capture_trigger(name):
            def decorator(fn):
                triggers[name] = fn
                return fn
            return decorator

        ctrl.trigger = capture_trigger
        ctrl.set = capture_trigger

        state.rules = []
        state.selected_rule = {
            "id": "R-1",
            "rule_id": "R-1",
            "name": "Test",
            "directive": "Do stuff",
            "category": "governance",
            "priority": "HIGH",
            "applicability": "RECOMMENDED",
        }

        register_rules_controllers(state, ctrl, "http://test:8082")
        triggers["edit_rule"]()

        assert state.form_rule_applicability == "RECOMMENDED"

    def test_submit_includes_applicability(self):
        """submit_rule_form should send applicability in payload."""
        import importlib
        import inspect
        mod = importlib.import_module("agent.governance_ui.controllers.rules")
        source = inspect.getsource(mod.register_rules_controllers)
        assert "applicability" in source
        assert "form_rule_applicability" in source


# ── Session Content: Linked Rules/Decisions ──────────────────

class TestSessionLinkedRulesDecisions:
    def test_content_has_linked_rules_card(self):
        """Session content should render linked rules card."""
        import importlib
        import inspect
        mod = importlib.import_module("agent.governance_ui.views.sessions.content")
        source = inspect.getsource(mod.build_session_info_card)
        assert "session-linked-rules" in source
        assert "linked_rules_applied" in source

    def test_content_has_linked_decisions_card(self):
        """Session content should render linked decisions card."""
        import importlib
        import inspect
        mod = importlib.import_module("agent.governance_ui.views.sessions.content")
        source = inspect.getsource(mod.build_session_info_card)
        assert "session-linked-decisions" in source
        assert "linked_decisions" in source

    def test_content_has_duration(self):
        """Session content should show duration."""
        import importlib
        import inspect
        mod = importlib.import_module("agent.governance_ui.views.sessions.content")
        source = inspect.getsource(mod.build_session_info_card)
        assert "duration" in source
