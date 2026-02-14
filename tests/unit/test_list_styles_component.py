"""
Tests for list styles component.

Per UI-LIST-01: Consistent list styling across dashboard views.
Batch 165: New coverage for components/list_styles.py (0->8 tests).
"""
import inspect

import pytest


class TestListStylesComponents:
    def test_inject_list_styles_callable(self):
        from agent.governance_ui.components.list_styles import inject_list_styles
        assert callable(inject_list_styles)

    def test_exported_in_all(self):
        from agent.governance_ui.components import list_styles
        assert "inject_list_styles" in list_styles.__all__


class TestListStylesContent:
    def test_has_zebra_striping(self):
        from agent.governance_ui.components import list_styles
        source = inspect.getsource(list_styles)
        assert "nth-child(even)" in source

    def test_has_dark_theme_support(self):
        from agent.governance_ui.components import list_styles
        source = inspect.getsource(list_styles)
        assert "v-theme--dark" in source

    def test_has_hover_state(self):
        from agent.governance_ui.components import list_styles
        source = inspect.getsource(list_styles)
        assert "hover" in source

    def test_styles_rules_list(self):
        from agent.governance_ui.components import list_styles
        source = inspect.getsource(list_styles)
        assert "rules-list" in source

    def test_styles_tasks_list(self):
        from agent.governance_ui.components import list_styles
        source = inspect.getsource(list_styles)
        assert "tasks-list" in source

    def test_styles_sessions_list(self):
        from agent.governance_ui.components import list_styles
        source = inspect.getsource(list_styles)
        assert "sessions-list" in source
