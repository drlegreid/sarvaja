"""
Tests for UI-AUDIT-007: Executive Report dropdown fix.

Per TDD: Write tests for session dropdown loading.
Per GAP-UI-AUDIT-2026-01-18: Fix Executive Report dropdown.

Tests verify:
1. load_sessions_list function exists in loaders
2. Sessions API endpoint works
3. Sessions data format is correct
"""

import pytest
from unittest.mock import MagicMock, patch


@pytest.mark.unit
class TestSessionsListLoader:
    """Verify sessions list loader exists and works."""

    def test_load_sessions_list_in_loaders(self):
        """Verify load_sessions_list is exported from loaders."""
        import inspect
        from agent.governance_ui.controllers import data_loaders

        source = inspect.getsource(data_loaders)

        # Function should be defined
        assert "def load_sessions_list" in source
        # Should be in returned dict
        assert "'load_sessions_list'" in source

    def test_sessions_list_trigger_exists(self):
        """Verify load_sessions_list trigger is registered."""
        import inspect
        from agent.governance_ui.controllers import data_loaders

        source = inspect.getsource(data_loaders)

        # Trigger should be registered
        assert '@ctrl.trigger("load_sessions_list")' in source

    def test_governance_dashboard_calls_sessions_loader(self):
        """Verify executive view loads sessions."""
        import inspect
        from agent import governance_dashboard

        source = inspect.getsource(governance_dashboard)

        # Should call load_sessions_list when executive view is shown
        assert "load_sessions_list()" in source
        assert "load_sessions_list = loaders" in source


@pytest.mark.integration
class TestSessionsAPIIntegration:
    """Test sessions API endpoint works for dropdown."""

    def test_sessions_api_returns_list(self):
        """API returns a list of sessions."""
        import httpx

        response = httpx.get(
            "http://localhost:8082/api/sessions?limit=100",
            timeout=10.0
        )

        assert response.status_code == 200
        data = response.json()

        # Should have items array or be a list directly
        if isinstance(data, dict):
            assert "items" in data
            sessions = data["items"]
        else:
            sessions = data

        assert isinstance(sessions, list)

    def test_sessions_have_session_id(self):
        """Sessions have session_id for dropdown."""
        import httpx

        response = httpx.get(
            "http://localhost:8082/api/sessions?limit=10",
            timeout=10.0
        )

        assert response.status_code == 200
        data = response.json()
        sessions = data.get("items", data) if isinstance(data, dict) else data

        # Each session should have session_id
        if sessions:
            for session in sessions:
                assert "session_id" in session, "Session missing session_id"
