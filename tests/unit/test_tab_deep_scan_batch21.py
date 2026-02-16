"""
Unit tests for Tab Deep Scan Batch 21 — select_task/rule pre-clear + form close fix.

Covers: select_task pre-clear (BUG-UI-STALE-DETAIL-004),
select_rule pre-clear (BUG-UI-STALE-DETAIL-005),
create_task form close only on success (BUG-UI-FORMCLOSE-002),
navigate_to_task clears prior edit state.
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect
from unittest.mock import MagicMock, patch


# ── BUG-UI-STALE-DETAIL-004: select_task pre-clear ────────────────────


class TestSelectTaskPreClear:
    """select_task must clear prior task detail state before loading new task."""

    def test_source_has_stale_detail_004(self):
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        assert "BUG-UI-STALE-DETAIL-004" in source

    def test_clears_edit_mode_before_load(self):
        """Edit mode from prior task must be cleared."""
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        start = source.index("def select_task")
        end = source.index("\n    def _auto_load", start + 1)
        fn_src = source[start:end]
        # edit_task_mode = False must appear before the try block
        clear_pos = fn_src.index("edit_task_mode = False")
        try_pos = fn_src.index("try:")
        assert clear_pos < try_pos

    def test_clears_execution_log_before_load(self):
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        start = source.index("def select_task")
        end = source.index("\n    def _auto_load", start + 1)
        fn_src = source[start:end]
        assert "task_execution_log = []" in fn_src

    def test_clears_execution_visibility(self):
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        start = source.index("def select_task")
        end = source.index("\n    def _auto_load", start + 1)
        fn_src = source[start:end]
        assert "show_task_execution = False" in fn_src

    def test_clears_nav_source(self):
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        start = source.index("def select_task")
        end = source.index("\n    def _auto_load", start + 1)
        fn_src = source[start:end]
        assert "nav_source_view = None" in fn_src
        assert "nav_source_id = None" in fn_src
        assert "nav_source_label = None" in fn_src


# ── BUG-UI-STALE-DETAIL-005: select_rule pre-clear ────────────────────


class TestSelectRulePreClear:
    """select_rule must clear prior rule detail state before loading."""

    def test_source_has_stale_detail_005(self):
        from agent.governance_ui.controllers import rules
        source = inspect.getsource(rules)
        assert "BUG-UI-STALE-DETAIL-005" in source

    def test_clears_implementing_tasks(self):
        from agent.governance_ui.controllers import rules
        source = inspect.getsource(rules)
        start = source.index("def select_rule")
        end = source.index("\n    @", start + 1)
        fn_src = source[start:end]
        assert "rule_implementing_tasks = []" in fn_src

    def test_clears_implementing_tasks_loading(self):
        from agent.governance_ui.controllers import rules
        source = inspect.getsource(rules)
        start = source.index("def select_rule")
        end = source.index("\n    @", start + 1)
        fn_src = source[start:end]
        assert "rule_implementing_tasks_loading = False" in fn_src

    def test_clear_before_loop(self):
        """Pre-clear must happen before the for-loop that sets new rule."""
        from agent.governance_ui.controllers import rules
        source = inspect.getsource(rules)
        start = source.index("def select_rule")
        end = source.index("\n    @", start + 1)
        fn_src = source[start:end]
        clear_pos = fn_src.index("rule_implementing_tasks = []")
        loop_pos = fn_src.index("for rule in state.rules")
        assert clear_pos < loop_pos


# ── BUG-UI-FORMCLOSE-002: create_task form close on success only ──────


class TestCreateTaskFormCloseOnSuccess:
    """create_task form must only close on API success, not on error."""

    def test_source_has_formclose_002(self):
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        assert "BUG-UI-FORMCLOSE-002" in source

    def test_form_close_inside_success_branch(self):
        """show_task_form = False must be inside status_code == 201 branch."""
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        start = source.index("def create_task")
        end = source.index("\n    @ctrl.trigger(\"attach_document\")")
        fn_src = source[start:end]
        # show_task_form = False must appear after 201 check, not at function level
        success_line_idx = None
        form_close_line_idx = None
        for i, line in enumerate(fn_src.splitlines()):
            if "status_code == 201:" in line:
                success_line_idx = i
            if "show_task_form = False" in line:
                form_close_line_idx = i
        assert success_line_idx is not None, "201 check not found"
        assert form_close_line_idx is not None, "form close not found"
        assert form_close_line_idx > success_line_idx, "form close must be after 201 check"
        # Verify the form close is indented deeper (inside the if block)
        form_close_line = fn_src.splitlines()[form_close_line_idx]
        success_line = fn_src.splitlines()[success_line_idx]
        assert len(form_close_line) - len(form_close_line.lstrip()) > len(success_line) - len(success_line.lstrip())

    @patch("agent.governance_ui.controllers.tasks.httpx")
    @patch("agent.governance_ui.controllers.tasks.register_tasks_navigation")
    def test_form_stays_open_on_api_error(self, mock_nav, mock_httpx):
        """Form must stay open when API returns non-201."""
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.text = "Bad Request"
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_resp
        mock_httpx.Client.return_value = mock_client

        state = MagicMock()
        state.is_loading = False
        state.form_task_id = "TEST-001"
        state.form_task_description = "Test task"
        state.form_task_phase = "P10"
        state.form_task_type = None
        state.form_task_agent = ""
        state.form_task_body = ""
        state.form_task_priority = None
        state.has_error = False
        state.active_view = "tasks"
        ctrl = MagicMock()
        triggers = {}

        def trigger(name):
            def dec(fn):
                triggers[name] = fn
                return fn
            return dec

        ctrl.trigger = trigger
        ctrl.set = trigger
        state.change = lambda name: lambda fn: fn

        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        register_tasks_controllers(state, ctrl, "http://localhost:8082")
        triggers["create_task"]()

        # Form must stay open — show_task_form should NOT have been set to False
        assert state.has_error is True
        assert state.is_loading is False

    @patch("agent.governance_ui.controllers.tasks.httpx")
    @patch("agent.governance_ui.controllers.tasks.register_tasks_navigation")
    def test_form_closes_on_success(self, mock_nav, mock_httpx):
        """Form must close when API returns 201."""
        mock_resp = MagicMock()
        mock_resp.status_code = 201

        mock_list_resp = MagicMock()
        mock_list_resp.status_code = 200
        mock_list_resp.json.return_value = {"items": [], "pagination": {}}

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_resp
        mock_client.get.return_value = mock_list_resp
        mock_httpx.Client.return_value = mock_client

        state = MagicMock()
        state.is_loading = False
        state.form_task_id = "TEST-001"
        state.form_task_description = "Test task"
        state.form_task_phase = "P10"
        state.form_task_type = None
        state.form_task_agent = ""
        state.form_task_body = ""
        state.form_task_priority = None
        state.has_error = False
        state.tasks = []
        state.active_view = "tasks"
        ctrl = MagicMock()
        triggers = {}

        def trigger(name):
            def dec(fn):
                triggers[name] = fn
                return fn
            return dec

        ctrl.trigger = trigger
        ctrl.set = trigger
        state.change = lambda name: lambda fn: fn

        from agent.governance_ui.controllers.tasks import register_tasks_controllers
        register_tasks_controllers(state, ctrl, "http://localhost:8082")
        triggers["create_task"]()

        assert state.show_task_form is False


# ── navigate_to_task clears prior task state ──────────────────────────


class TestNavigateToTaskClearsPriorState:
    """navigate_to_task must clear prior task edit/execution state."""

    def test_source_has_stale_detail_fix(self):
        from agent.governance_ui.controllers import tasks_navigation
        source = inspect.getsource(tasks_navigation)
        assert "BUG-UI-STALE-DETAIL-004" in source

    def test_clears_edit_mode(self):
        from agent.governance_ui.controllers import tasks_navigation
        source = inspect.getsource(tasks_navigation)
        start = source.index("def navigate_to_task")
        end = source.index("\n    @ctrl.trigger(\"navigate_back_to_source\")")
        fn_src = source[start:end]
        assert "edit_task_mode = False" in fn_src

    def test_clears_execution_log(self):
        from agent.governance_ui.controllers import tasks_navigation
        source = inspect.getsource(tasks_navigation)
        start = source.index("def navigate_to_task")
        end = source.index("\n    @ctrl.trigger(\"navigate_back_to_source\")")
        fn_src = source[start:end]
        assert "task_execution_log = []" in fn_src

    def test_clears_execution_visibility(self):
        from agent.governance_ui.controllers import tasks_navigation
        source = inspect.getsource(tasks_navigation)
        start = source.index("def navigate_to_task")
        end = source.index("\n    @ctrl.trigger(\"navigate_back_to_source\")")
        fn_src = source[start:end]
        assert "show_task_execution = False" in fn_src


# ── Close handlers reset all relevant state ───────────────────────────


class TestCloseHandlersCompleteness:
    """close_*_detail handlers must reset all related state."""

    def test_close_task_detail_resets_edit_mode(self):
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        start = source.index("def close_task_detail")
        end = source.index("\n    @", start + 1)
        fn_src = source[start:end]
        assert "edit_task_mode = False" in fn_src
        assert "task_execution_log = []" in fn_src
        assert "show_task_execution = False" in fn_src
        assert "nav_source_view = None" in fn_src

    def test_close_rule_detail_resets_implementing_tasks(self):
        from agent.governance_ui.controllers import rules
        source = inspect.getsource(rules)
        start = source.index("def close_rule_detail")
        end = source.index("\n    @", start + 1)
        fn_src = source[start:end]
        assert "rule_implementing_tasks = []" in fn_src
        assert "rule_implementing_tasks_loading = False" in fn_src

    def test_close_decision_detail_resets_state(self):
        from agent.governance_ui.controllers import decisions
        source = inspect.getsource(decisions)
        start = source.index("def close_decision_detail")
        end = source.index("\n    @", start + 1)
        fn_src = source[start:end]
        assert "show_decision_detail = False" in fn_src
        assert "selected_decision = None" in fn_src


# ── Pre-clear consistency across all entity selectors ─────────────────


class TestPreClearConsistency:
    """All entity select handlers should pre-clear stale state."""

    def test_select_session_has_pre_clear(self):
        from agent.governance_ui.controllers import sessions
        source = inspect.getsource(sessions)
        start = source.index("def select_session")
        end = source.index("\n    @", start + 1)
        fn_src = source[start:end]
        assert "BUG-UI-STALE-DETAIL-003" in fn_src

    def test_select_task_has_pre_clear(self):
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        start = source.index("def select_task")
        end = source.index("\n    def _auto_load", start + 1)
        fn_src = source[start:end]
        assert "BUG-UI-STALE-DETAIL-004" in fn_src

    def test_select_rule_has_pre_clear(self):
        from agent.governance_ui.controllers import rules
        source = inspect.getsource(rules)
        start = source.index("def select_rule")
        end = source.index("\n    @", start + 1)
        fn_src = source[start:end]
        assert "BUG-UI-STALE-DETAIL-005" in fn_src

    def test_formclose_002_pattern_tasks(self):
        """create_task has form-close-on-success-only pattern."""
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        assert "BUG-UI-FORMCLOSE-002" in source
