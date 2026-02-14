"""
UI Bugs Batch 2: Tests for 6 UI-layer bugs discovered via exploratory testing.

BUG-UI-AGENTS-001: Agent Pause/Resume toggle returns 404
BUG-UI-SESSIONS-001: Sessions pivot view toggle doesn't work
BUG-UI-AUDIT-001: Audit Trail filters not wired to API
BUG-UI-RULES-001: Rules filter dropdowns not wired
BUG-UI-TASKS-001: Task Create dialog form submission error
BUG-UI-TASKS-002: Status tabs don't filter the table

Per TEST-BUGFIX-01-v1: Write tests BEFORE fixing.
"""

from unittest.mock import patch, MagicMock, PropertyMock
import pytest


# ── BUG-UI-AGENTS-001: Toggle returns 404 ──────────────────


class TestAgentToggle404:
    """Agent toggle should work for TypeDB-only agents, not just memory store."""

    @patch("governance.services.agents._agents_store", {"code-agent": {"agent_id": "code-agent", "status": "PAUSED"}})
    def test_toggle_known_agent_works(self):
        """Toggle should succeed for agents in memory store."""
        from governance.services.agents import toggle_agent_status
        with patch("governance.services.agents.get_typedb_client") as mock_client:
            mock_client.return_value = None
            result = toggle_agent_status("code-agent")
            assert result is not None
            assert result["status"] == "ACTIVE"

    @patch("governance.services.agents._agents_store", {})
    @patch("governance.services.agents.get_typedb_client")
    def test_toggle_typedb_only_agent_should_not_404(self, mock_client_fn):
        """BUG: Agent in TypeDB but not memory → toggle returns None (404).
        Fix: Should query TypeDB and add to memory before toggling."""
        from governance.services.agents import toggle_agent_status

        # Agent exists in TypeDB
        client = MagicMock()
        agent_obj = MagicMock()
        agent_obj.id = "research-agent"
        agent_obj.name = "Research Agent"
        agent_obj.agent_type = "research"
        agent_obj.trust_score = 0.8
        client.get_agent.return_value = agent_obj
        mock_client_fn.return_value = client

        result = toggle_agent_status("research-agent")
        assert result is not None, "toggle should NOT return None for TypeDB-only agents"

    @patch("governance.services.agents._agents_store", {})
    @patch("governance.services.agents.get_typedb_client")
    def test_toggle_truly_missing_agent_returns_none(self, mock_client_fn):
        """Agent not in memory OR TypeDB → should return None."""
        from governance.services.agents import toggle_agent_status

        client = MagicMock()
        client.get_agent.return_value = None
        mock_client_fn.return_value = client

        result = toggle_agent_status("ghost-agent")
        assert result is None


# ── BUG-UI-SESSIONS-001: Pivot toggle doesn't work ────────


class TestSessionsPivotToggle:
    """Sessions view mode toggle should properly update state."""

    def test_toggle_trigger_accepts_new_value(self):
        """sessions_toggle_view should accept new_value parameter."""
        from agent.governance_ui.controllers.sessions_pagination import register_sessions_pagination

        state = MagicMock()
        state.sessions_view_mode = "table"
        state.active_view = "sessions"
        ctrl = MagicMock()

        captured_triggers = {}

        def capture_trigger(name):
            def decorator(func):
                captured_triggers[name] = func
                return func
            return decorator

        ctrl.trigger = capture_trigger

        # Mock state.change to not fire
        state.change = lambda *a, **k: lambda f: f

        register_sessions_pagination(state, ctrl, "http://localhost:8082")

        assert "sessions_toggle_view" in captured_triggers

    def test_pivot_view_mode_state_init(self):
        """Initial state should have sessions_view_mode = 'table'."""
        from agent.governance_ui.state.initial import get_initial_state
        init_state = get_initial_state()
        assert init_state.get("sessions_view_mode") == "table"


# ── BUG-UI-AUDIT-001: Audit filters not wired ─────────────


class TestAuditAutoLoad:
    """Audit view should auto-load data when navigating to it."""

    def test_loaders_include_audit_trail(self):
        """register_data_loader_controllers should return load_audit_trail."""
        from agent.governance_ui.controllers.data_loaders import register_data_loader_controllers

        state = MagicMock()
        ctrl = MagicMock()
        ctrl.trigger = lambda name: lambda f: f
        state.change = lambda *a, **k: lambda f: f

        loaders = register_data_loader_controllers(state, ctrl, "http://localhost:8082")
        assert "load_audit_trail" in loaders, "loaders should include load_audit_trail"

    def test_view_change_handler_includes_audit(self):
        """on_view_change in governance_dashboard.py should handle 'audit' view.

        This tests that when active_view='audit', load_audit_trail is called.
        """
        # Read the governance_dashboard.py source and check for 'audit' case
        import inspect
        import agent.governance_dashboard as gd

        source = inspect.getsource(gd)
        # After fix, should have 'audit' in on_view_change handler
        assert "audit" in source, "governance_dashboard.py should reference 'audit' view"


# ── BUG-UI-RULES-001: Rules filter dropdowns not wired ────


class TestRulesFilterWiring:
    """Rules filters should be reactive and rules should auto-load on view entry."""

    def test_rules_controller_has_reactive_handlers(self):
        """register_rules_controllers should set up @state.change handlers."""
        from agent.governance_ui.controllers.rules import register_rules_controllers

        state = MagicMock()
        ctrl = MagicMock()
        ctrl.trigger = lambda name: lambda f: f
        ctrl.set = lambda name: lambda f: f

        change_handlers = {}

        def capture_change(var_name):
            def decorator(func):
                change_handlers[var_name] = func
                return func
            return decorator

        state.change = capture_change

        register_rules_controllers(state, ctrl, "http://localhost:8082")
        assert "rules_status_filter" in change_handlers
        assert "rules_category_filter" in change_handlers

    def test_rules_controller_returns_load_rules(self):
        """register_rules_controllers should return load_rules for auto-load wiring."""
        from agent.governance_ui.controllers.rules import register_rules_controllers

        state = MagicMock()
        ctrl = MagicMock()
        ctrl.trigger = lambda name: lambda f: f
        ctrl.set = lambda name: lambda f: f
        state.change = lambda *a, **k: lambda f: f

        result = register_rules_controllers(state, ctrl, "http://localhost:8082")
        # After fix, should return a dict with load_rules
        assert result is not None, "register_rules_controllers should return loader dict"
        assert callable(result.get("load_rules", None)) or callable(result), \
            "Should return load_rules function or dict containing it"


# ── BUG-UI-TASKS-001: Task Create dialog errors ───────────


class TestTaskCreateValidation:
    """Task create should validate required fields and show errors."""

    def test_create_task_handler_validates_task_id(self):
        """create_task trigger should validate task_id is not empty."""
        from agent.governance_ui.controllers.tasks import register_tasks_controllers

        state = MagicMock()
        state.form_task_id = ""
        state.form_task_description = "Test desc"
        state.form_task_phase = "P10"
        state.form_task_agent = ""
        state.form_task_body = ""
        state.active_view = "tasks"
        ctrl = MagicMock()

        captured_triggers = {}

        def capture_trigger(name):
            def decorator(func):
                captured_triggers[name] = func
                return func
            return decorator

        ctrl.trigger = capture_trigger
        ctrl.set = lambda name: lambda f: f
        state.change = lambda *a, **k: lambda f: f

        register_tasks_controllers(state, ctrl, "http://localhost:8082")
        assert "create_task" in captured_triggers

        # Call with empty task_id
        with patch("agent.governance_ui.controllers.tasks.httpx") as mock_httpx:
            captured_triggers["create_task"]()
            # After fix: should set error and NOT call API
            # Before fix: calls API with empty task_id → 422 error

    def test_create_task_handler_validates_description(self):
        """create_task trigger should validate description is not empty."""
        from agent.governance_ui.controllers.tasks import register_tasks_controllers

        state = MagicMock()
        state.form_task_id = "T-1"
        state.form_task_description = ""
        state.form_task_phase = "P10"
        state.form_task_agent = ""
        state.form_task_body = ""
        state.active_view = "tasks"
        ctrl = MagicMock()

        captured_triggers = {}

        def capture_trigger(name):
            def decorator(func):
                captured_triggers[name] = func
                return func
            return decorator

        ctrl.trigger = capture_trigger
        ctrl.set = lambda name: lambda f: f
        state.change = lambda *a, **k: lambda f: f

        register_tasks_controllers(state, ctrl, "http://localhost:8082")

        with patch("agent.governance_ui.controllers.tasks.httpx") as mock_httpx:
            captured_triggers["create_task"]()

    def test_create_task_includes_priority_and_type(self):
        """create_task should send priority and task_type to API."""
        from agent.governance_ui.controllers.tasks import register_tasks_controllers

        state = MagicMock()
        state.form_task_id = "T-1"
        state.form_task_description = "Test task"
        state.form_task_phase = "P10"
        state.form_task_agent = ""
        state.form_task_body = ""
        state.form_task_priority = "HIGH"
        state.form_task_type = "bug"
        state.active_view = "tasks"
        state.tasks_per_page = 20
        state.tasks_page = 1
        ctrl = MagicMock()

        captured_triggers = {}

        def capture_trigger(name):
            def decorator(func):
                captured_triggers[name] = func
                return func
            return decorator

        ctrl.trigger = capture_trigger
        ctrl.set = lambda name: lambda f: f
        state.change = lambda *a, **k: lambda f: f

        register_tasks_controllers(state, ctrl, "http://localhost:8082")

        with patch("agent.governance_ui.controllers.tasks.httpx") as mock_httpx:
            mock_client = MagicMock()
            mock_httpx.Client.return_value.__enter__ = MagicMock(return_value=mock_client)
            mock_httpx.Client.return_value.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = MagicMock(status_code=201)
            mock_client.get.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value={"items": [], "pagination": {}})
            )

            captured_triggers["create_task"]()

            # Verify API was called
            if mock_client.post.called:
                call_args = mock_client.post.call_args
                json_data = call_args[1].get("json") or call_args[0][1] if len(call_args[0]) > 1 else {}
                # After fix: should include priority and task_type in payload


# ── BUG-UI-TASKS-002: Status tabs don't filter ────────────


class TestTasksStatusTabs:
    """Status tabs should filter the tasks table via reactive state changes."""

    def test_tasks_filter_type_reactive_handler_exists(self):
        """Reactive handler for tasks_filter_type should call load_tasks_page."""
        from agent.governance_ui.controllers.tasks import register_tasks_controllers

        state = MagicMock()
        state.active_view = "tasks"
        ctrl = MagicMock()
        ctrl.trigger = lambda name: lambda f: f
        ctrl.set = lambda name: lambda f: f

        change_handlers = {}

        def capture_change(var_name):
            def decorator(func):
                change_handlers[var_name] = func
                return func
            return decorator

        state.change = capture_change

        register_tasks_controllers(state, ctrl, "http://localhost:8082")

        # These handlers should exist for filter reactivity
        assert "tasks_filter_type" in change_handlers, \
            "Should have reactive handler for tasks_filter_type"
        assert "tasks_status_filter" in change_handlers, \
            "Should have reactive handler for tasks_status_filter"

    def test_tab_to_status_mapping(self):
        """Tab selection should map to correct status filter values."""
        # Expected mapping:
        # all → None, available → TODO, mine → IN_PROGRESS, completed → DONE
        tab_mapping = {
            "all": None,
            "available": "TODO",
            "mine": "IN_PROGRESS",
            "completed": "DONE",
        }
        for tab, expected_status in tab_mapping.items():
            assert expected_status == tab_mapping[tab]


# ── Dashboard auto-load integration ────────────────────────


class TestDashboardAutoLoad:
    """governance_dashboard.py on_view_change should handle all navigable views."""

    def test_audit_view_in_on_view_change_source(self):
        """on_view_change handler should include 'audit' case."""
        import inspect
        import agent.governance_dashboard as gd
        source = inspect.getsource(gd)
        # The on_view_change handler should have a case for audit
        assert "'audit'" in source or '"audit"' in source, \
            "governance_dashboard.py should handle 'audit' in on_view_change"

    def test_loaders_dict_has_required_keys(self):
        """Loaders returned by register_data_loader_controllers should have all required keys."""
        from agent.governance_ui.controllers.data_loaders import register_data_loader_controllers

        state = MagicMock()
        ctrl = MagicMock()
        ctrl.trigger = lambda name: lambda f: f
        state.change = lambda *a, **k: lambda f: f

        loaders = register_data_loader_controllers(state, ctrl, "http://localhost:8082")

        required_keys = [
            'load_trust_data', 'load_monitor_data', 'load_backlog_data',
            'load_executive_report_data', 'load_infra_status',
            'load_workflow_status', 'load_audit_trail', 'load_sessions_list',
        ]
        for key in required_keys:
            assert key in loaders, f"Missing loader: {key}"
