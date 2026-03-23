"""
Tests for UI-NAV-01-v1: Entity Navigation Context.

Per UI-NAV-01-v1: Verify navigation context preservation between entities.
"""

import pytest


@pytest.mark.unit
class TestNavigationContextState:
    """Verify navigation context state variables exist."""

    def test_nav_source_view_in_initial_state(self):
        """Verify nav_source_view is in initial state."""
        from agent.governance_ui.state.initial import get_initial_state

        state = get_initial_state()
        assert "nav_source_view" in state
        assert state["nav_source_view"] is None

    def test_nav_source_id_in_initial_state(self):
        """Verify nav_source_id is in initial state."""
        from agent.governance_ui.state.initial import get_initial_state

        state = get_initial_state()
        assert "nav_source_id" in state
        assert state["nav_source_id"] is None

    def test_nav_source_label_in_initial_state(self):
        """Verify nav_source_label is in initial state."""
        from agent.governance_ui.state.initial import get_initial_state

        state = get_initial_state()
        assert "nav_source_label" in state
        assert state["nav_source_label"] is None


@pytest.mark.unit
class TestNavigationTriggers:
    """Verify navigation triggers are registered."""

    def test_navigate_to_task_registered(self):
        """Verify navigate_to_task trigger is registered."""
        from agent.governance_ui.controllers.tasks import register_tasks_controllers

        registered_triggers = []

        class MockState:
            def __setattr__(self, name, value):
                pass

            def __getattr__(self, name):
                if name == "tasks":
                    return []
                return None

            def change(self, var_name):
                def decorator(fn):
                    return fn
                return decorator

        class MockCtrl:
            def set(self, name):
                def decorator(func):
                    return func
                return decorator

            def trigger(self, name):
                def decorator(func):
                    registered_triggers.append(name)
                    return func
                return decorator

        register_tasks_controllers(MockState(), MockCtrl(), "http://localhost:8082")

        assert "navigate_to_task" in registered_triggers

    def test_navigate_back_to_source_registered(self):
        """Verify navigate_back_to_source trigger is registered."""
        from agent.governance_ui.controllers.tasks import register_tasks_controllers

        registered_triggers = []

        class MockState:
            def __setattr__(self, name, value):
                pass

            def __getattr__(self, name):
                if name == "tasks":
                    return []
                return None

            def change(self, var_name):
                def decorator(fn):
                    return fn
                return decorator

        class MockCtrl:
            def set(self, name):
                def decorator(func):
                    return func
                return decorator

            def trigger(self, name):
                def decorator(func):
                    registered_triggers.append(name)
                    return func
                return decorator

        register_tasks_controllers(MockState(), MockCtrl(), "http://localhost:8082")

        assert "navigate_back_to_source" in registered_triggers


@pytest.mark.unit
class TestSessionTasksView:
    """Verify session tasks view passes navigation context."""

    def test_session_tasks_click_has_source_context(self):
        """Verify session tasks click includes navigation source."""
        import inspect
        from agent.governance_ui.views.sessions import tasks

        source = inspect.getsource(tasks)

        # Should pass source_view='sessions'
        assert "'sessions'" in source
        # Should reference selected_session for source_id
        assert "selected_session.session_id" in source


@pytest.mark.unit
class TestTaskDetailView:
    """Verify task detail view has back-to-source button."""

    def test_back_to_source_button_exists(self):
        """Verify back-to-source button in task detail."""
        import inspect
        from agent.governance_ui.views.tasks import detail

        source = inspect.getsource(detail)

        # Should have back-to-source testid
        assert "task-detail-back-to-source" in source
        # Should navigate back using nav_source_view (inline JS)
        assert "nav_source_view" in source

    def test_conditional_back_buttons(self):
        """Verify both back buttons with correct conditions."""
        import inspect
        from agent.governance_ui.views.tasks import detail

        source = inspect.getsource(detail)

        # Should have conditional for nav_source_view
        assert 'v_if="nav_source_view"' in source
        assert 'v_if="!nav_source_view"' in source


@pytest.mark.unit
class TestRulesViewNavigation:
    """Verify rules view task click has navigation context."""

    def test_implementing_tasks_click_has_source_context(self):
        """Verify implementing tasks click includes navigation source."""
        import inspect
        # Per DOC-SIZE-01-v1: detail view extracted to rules_view_detail
        from agent.governance_ui.views import rules_view_detail

        source = inspect.getsource(rules_view_detail)

        # Should pass source_view='rules'
        assert "'rules'" in source
        # Should reference selected_rule for source_id
        assert "selected_rule.rule_id" in source
