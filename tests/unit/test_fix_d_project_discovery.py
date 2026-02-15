"""Tests for Fix D: Project auto-discovery from CC directories.

Validates discover_cc_projects() scanner and auto-creation in _load_projects().
"""
from unittest.mock import MagicMock, patch
from pathlib import Path
import pytest


def test_discover_cc_projects_returns_list():
    """discover_cc_projects returns list from CC directory structure."""
    from governance.services.cc_session_scanner import discover_cc_projects

    mock_dir = MagicMock(spec=Path)
    mock_dir.is_dir.return_value = True
    mock_dir.name = "-home-user-Documents-sarvaja-platform"

    mock_jsonl = MagicMock(spec=Path)
    mock_dir.glob.return_value = [mock_jsonl] * 3  # 3 JSONL files

    with patch("governance.services.cc_session_scanner.DEFAULT_CC_DIR") as mock_cc:
        mock_cc.is_dir.return_value = True
        mock_cc.iterdir.return_value = [mock_dir]
        mock_dir.is_dir.return_value = True

        result = discover_cc_projects()

    assert len(result) == 1
    assert result[0]["project_id"] == "PROJ-SARVAJA-PLATFORM"
    assert result[0]["session_count"] == 3
    assert result[0]["name"] == "Sarvaja Platform"


def test_discover_cc_projects_skips_empty_dirs():
    """discover_cc_projects skips directories with no JSONL files."""
    from governance.services.cc_session_scanner import discover_cc_projects

    mock_dir = MagicMock(spec=Path)
    mock_dir.is_dir.return_value = True
    mock_dir.name = "-home-user-empty-project"
    mock_dir.glob.return_value = []  # No JSONL

    with patch("governance.services.cc_session_scanner.DEFAULT_CC_DIR") as mock_cc:
        mock_cc.is_dir.return_value = True
        mock_cc.iterdir.return_value = [mock_dir]

        result = discover_cc_projects()

    assert len(result) == 0


def test_discover_cc_projects_no_cc_dir():
    """discover_cc_projects returns empty list when CC dir doesn't exist."""
    from governance.services.cc_session_scanner import discover_cc_projects

    with patch("governance.services.cc_session_scanner.DEFAULT_CC_DIR") as mock_cc:
        mock_cc.is_dir.return_value = False
        result = discover_cc_projects()

    assert result == []


def test_load_projects_auto_creates_missing():
    """_load_projects creates missing CC-discovered projects via API."""
    from agent.governance_ui.dashboard_data_loader import _load_projects

    state = MagicMock()

    def mock_get(url, **kwargs):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"items": [
            {"project_id": "PROJ-SARVAJA-PLATFORM", "name": "Sarvaja Platform"},
        ]}
        return resp

    def mock_post(url, **kwargs):
        resp = MagicMock()
        resp.status_code = 201
        body = kwargs.get("json", {})
        resp.json.return_value = body
        return resp

    client = MagicMock()
    client.get = mock_get
    client.post = mock_post

    cc_projects = [
        {"project_id": "PROJ-SARVAJA-PLATFORM", "name": "Sarvaja", "path": "/home/user/sarvaja", "session_count": 10},
        {"project_id": "PROJ-TIC-TAC-TOE", "name": "Tic Tac Toe", "path": "/home/user/tic-tac-toe", "session_count": 2},
    ]

    with patch("governance.services.cc_session_scanner.discover_cc_projects", return_value=cc_projects):
        _load_projects(state, client, "http://localhost:8082")

    # Should have 2 projects: existing + auto-created
    assert len(state.projects) == 2
    ids = [p.get("project_id") for p in state.projects]
    assert "PROJ-SARVAJA-PLATFORM" in ids
    assert "PROJ-TIC-TAC-TOE" in ids


def test_load_projects_handles_api_failure_gracefully():
    """_load_projects handles API failure without crashing."""
    from agent.governance_ui.dashboard_data_loader import _load_projects

    state = MagicMock()
    client = MagicMock()
    client.get.side_effect = Exception("Connection refused")

    _load_projects(state, client, "http://localhost:8082")

    assert state.projects == []
