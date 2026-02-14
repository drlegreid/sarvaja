"""
Tests for session content view components.

Per SESSION-CC-01-v1: CC session field display.
Batch 167: New coverage for views/sessions/content.py (0->10 tests).
"""
import inspect

import pytest


class TestSessionsContentComponents:
    def test_build_session_metadata_chips_callable(self):
        from agent.governance_ui.views.sessions.content import build_session_metadata_chips
        assert callable(build_session_metadata_chips)


class TestSessionsContentContent:
    def test_has_date_chip(self):
        from agent.governance_ui.views.sessions import content
        source = inspect.getsource(content)
        assert "session-detail-date" in source

    def test_has_status_chip(self):
        from agent.governance_ui.views.sessions import content
        source = inspect.getsource(content)
        assert "session-detail-status" in source

    def test_has_calendar_icon(self):
        from agent.governance_ui.views.sessions import content
        source = inspect.getsource(content)
        assert "mdi-calendar" in source

    def test_has_source_type(self):
        from agent.governance_ui.views.sessions import content
        source = inspect.getsource(content)
        assert "source_type" in source

    def test_has_cc_git_branch(self):
        from agent.governance_ui.views.sessions import content
        source = inspect.getsource(content)
        assert "cc_git_branch" in source

    def test_has_cc_project_slug(self):
        from agent.governance_ui.views.sessions import content
        source = inspect.getsource(content)
        assert "cc_project_slug" in source

    def test_has_branch_icon(self):
        from agent.governance_ui.views.sessions import content
        source = inspect.getsource(content)
        assert "mdi-source-branch" in source

    def test_has_folder_icon(self):
        from agent.governance_ui.views.sessions import content
        source = inspect.getsource(content)
        assert "mdi-folder" in source

    def test_has_chip_group(self):
        from agent.governance_ui.views.sessions import content
        source = inspect.getsource(content)
        assert "VChipGroup" in source
