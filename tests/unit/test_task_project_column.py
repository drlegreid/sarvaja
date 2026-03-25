"""Tests for FIX-HIER-001: Project column from workspace→project_id relation.

Project column is derived from workspace data, NOT from task_id string parsing.
The controller enrichment fetches workspace list once, builds a map, and adds
project_name to each task dict.
"""

import pytest
from unittest.mock import patch, MagicMock
import httpx


# ── Enrichment function tests ────────────────────────────────────────


class TestEnrichProjectName:
    """Test _enrich_project_name adds project_name from workspace map."""

    def test_basic_enrichment(self):
        from agent.governance_ui.controllers.tasks import _enrich_project_name
        tasks = [
            {"task_id": "T-1", "workspace_id": "WS-AAA"},
            {"task_id": "T-2", "workspace_id": "WS-BBB"},
        ]
        ws_map = {"WS-AAA": "sarvaja-platform", "WS-BBB": "gamedev"}
        result = _enrich_project_name(tasks, ws_map)
        assert result[0]["project_name"] == "sarvaja-platform"
        assert result[1]["project_name"] == "gamedev"

    def test_missing_workspace_id(self):
        from agent.governance_ui.controllers.tasks import _enrich_project_name
        tasks = [
            {"task_id": "T-1", "workspace_id": None},
            {"task_id": "T-2"},  # no workspace_id key at all
        ]
        ws_map = {"WS-AAA": "sarvaja-platform"}
        result = _enrich_project_name(tasks, ws_map)
        assert result[0]["project_name"] == ""
        assert result[1]["project_name"] == ""

    def test_unknown_workspace_id(self):
        from agent.governance_ui.controllers.tasks import _enrich_project_name
        tasks = [{"task_id": "T-1", "workspace_id": "WS-UNKNOWN"}]
        ws_map = {"WS-AAA": "sarvaja-platform"}
        result = _enrich_project_name(tasks, ws_map)
        assert result[0]["project_name"] == ""

    def test_empty_tasks(self):
        from agent.governance_ui.controllers.tasks import _enrich_project_name
        result = _enrich_project_name([], {"WS-AAA": "proj"})
        assert result == []

    def test_empty_map(self):
        from agent.governance_ui.controllers.tasks import _enrich_project_name
        tasks = [{"task_id": "T-1", "workspace_id": "WS-AAA"}]
        result = _enrich_project_name(tasks, {})
        assert result[0]["project_name"] == ""

    def test_mutates_in_place(self):
        """Enrichment modifies task dicts in place (same pattern as other enrichers)."""
        from agent.governance_ui.controllers.tasks import _enrich_project_name
        tasks = [{"task_id": "T-1", "workspace_id": "WS-AAA"}]
        ws_map = {"WS-AAA": "sarvaja-platform"}
        result = _enrich_project_name(tasks, ws_map)
        assert result is tasks  # same list object
        assert tasks[0]["project_name"] == "sarvaja-platform"


class TestFetchWorkspaceProjectMap:
    """Test _fetch_workspace_project_map HTTP fetch + map building."""

    @patch("agent.governance_ui.controllers.tasks.httpx.Client")
    def test_builds_map_from_api(self, mock_client_cls):
        from agent.governance_ui.controllers.tasks import _fetch_workspace_project_map
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [
            {"workspace_id": "WS-AAA", "project_id": "sarvaja", "name": "Sarvaja Dev"},
            {"workspace_id": "WS-BBB", "project_id": "gamedev", "name": "Gamedev"},
        ]
        mock_client = MagicMock()
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = _fetch_workspace_project_map("http://localhost:8082")
        assert result == {"WS-AAA": "sarvaja", "WS-BBB": "gamedev"}

    @patch("agent.governance_ui.controllers.tasks.httpx.Client")
    def test_api_failure_returns_empty(self, mock_client_cls):
        from agent.governance_ui.controllers.tasks import _fetch_workspace_project_map
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_client = MagicMock()
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = _fetch_workspace_project_map("http://localhost:8082")
        assert result == {}

    @patch("agent.governance_ui.controllers.tasks.httpx.Client")
    def test_network_error_returns_empty(self, mock_client_cls):
        from agent.governance_ui.controllers.tasks import _fetch_workspace_project_map
        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.ConnectError("refused")
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = _fetch_workspace_project_map("http://localhost:8082")
        assert result == {}

    @patch("agent.governance_ui.controllers.tasks.httpx.Client")
    def test_workspace_without_project_id(self, mock_client_cls):
        from agent.governance_ui.controllers.tasks import _fetch_workspace_project_map
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [
            {"workspace_id": "WS-AAA", "name": "No Project"},  # missing project_id
        ]
        mock_client = MagicMock()
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = _fetch_workspace_project_map("http://localhost:8082")
        assert result == {"WS-AAA": ""}


# ── Column definition tests ──────────────────────────────────────────


class TestProjectColumnInHeaders:
    """Verify Project column present in headers with correct position."""

    def test_initial_state_has_project_column(self):
        """FIX-HIER-001: Project column present in initial.py."""
        from agent.governance_ui.state.initial import get_initial_state
        headers = get_initial_state()["tasks_headers"]
        keys = [h["key"] for h in headers]
        assert "project_name" in keys

    def test_project_column_before_workspace(self):
        """Project is first column — entity hierarchy: Project > Workspace."""
        from agent.governance_ui.state.initial import get_initial_state
        headers = get_initial_state()["tasks_headers"]
        keys = [h["key"] for h in headers]
        proj_idx = keys.index("project_name")
        ws_idx = keys.index("workspace_id")
        assert proj_idx < ws_idx

    def test_column_count_is_15(self):
        """15 columns: Project + EPIC-TASK-TAXONOMY-V2 Layer/Concern/Method."""
        from agent.governance_ui.state.initial import get_initial_state
        headers = get_initial_state()["tasks_headers"]
        assert len(headers) == 15

    def test_project_column_sortable(self):
        """Project column should be sortable."""
        from agent.governance_ui.state.initial import get_initial_state
        headers = get_initial_state()["tasks_headers"]
        proj = next(h for h in headers if h["key"] == "project_name")
        assert proj["sortable"] is True

    def test_project_column_title(self):
        """Project column title is 'Project'."""
        from agent.governance_ui.state.initial import get_initial_state
        headers = get_initial_state()["tasks_headers"]
        proj = next(h for h in headers if h["key"] == "project_name")
        assert proj["title"] == "Project"
