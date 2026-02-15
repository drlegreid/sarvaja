"""Tests for Fix F: CC Session Auto-Ingestion on dashboard startup.

Validates that _auto_ingest_cc_sessions() calls ingest_all() for each
CC project discovered during _load_projects().
"""
from unittest.mock import patch, MagicMock, call
from pathlib import Path
import pytest


def test_auto_ingest_calls_ingest_all():
    """_auto_ingest_cc_sessions calls ingest_all with correct params."""
    from agent.governance_ui.dashboard_data_loader import _auto_ingest_cc_sessions

    cc_proj = {
        "project_id": "PROJ-SARVAJA-PLATFORM",
        "name": "Sarvaja Platform",
        "path": "/home/user/sarvaja/platform",
        "cc_directory": "/home/user/.claude/projects/-home-user-sarvaja-platform",
        "session_count": 5,
    }

    with patch("governance.services.cc_session_ingestion.ingest_all", return_value=[{"session_id": "S1"}]) as mock_ingest:
        _auto_ingest_cc_sessions(cc_proj)

    mock_ingest.assert_called_once()
    args = mock_ingest.call_args
    assert args.kwargs["project_id"] == "PROJ-SARVAJA-PLATFORM"
    assert args.kwargs["project_slug"] == "sarvaja-platform"
    assert args.kwargs["dry_run"] is False


def test_auto_ingest_skips_when_no_cc_directory():
    """_auto_ingest_cc_sessions does nothing when cc_directory is missing."""
    from agent.governance_ui.dashboard_data_loader import _auto_ingest_cc_sessions

    cc_proj = {
        "project_id": "PROJ-TEST",
        "name": "Test",
        "path": "/test",
    }

    with patch("governance.services.cc_session_ingestion.ingest_all") as mock_ingest:
        _auto_ingest_cc_sessions(cc_proj)

    mock_ingest.assert_not_called()


def test_auto_ingest_handles_ingest_failure():
    """_auto_ingest_cc_sessions handles ingest_all failures gracefully."""
    from agent.governance_ui.dashboard_data_loader import _auto_ingest_cc_sessions

    cc_proj = {
        "project_id": "PROJ-FAIL",
        "cc_directory": "/nonexistent",
    }

    with patch("governance.services.cc_session_ingestion.ingest_all", side_effect=Exception("boom")):
        # Should not raise
        _auto_ingest_cc_sessions(cc_proj)


def test_auto_ingest_called_for_each_cc_project():
    """_load_projects calls _auto_ingest_cc_sessions for each CC project."""
    from agent.governance_ui.dashboard_data_loader import _load_projects

    state = MagicMock()
    client = MagicMock()

    def mock_get(url, **kwargs):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"items": []}
        return resp

    client.get = mock_get

    cc_projects = [
        {"project_id": "PROJ-A", "name": "A", "path": "/a", "cc_directory": "/cc/a", "session_count": 3},
        {"project_id": "PROJ-B", "name": "B", "path": "/b", "cc_directory": "/cc/b", "session_count": 1},
    ]

    with patch("governance.services.cc_session_scanner.discover_cc_projects", return_value=cc_projects):
        with patch("governance.services.workspace_registry.detect_project_type", return_value="generic"):
            with patch("agent.governance_ui.dashboard_data_loader._auto_ingest_cc_sessions") as mock_auto:
                _load_projects(state, client, "http://localhost:8082")

    # Should be called once per CC project
    assert mock_auto.call_count == 2
    project_ids = [c.args[0]["project_id"] for c in mock_auto.call_args_list]
    assert "PROJ-A" in project_ids
    assert "PROJ-B" in project_ids


def test_auto_ingest_returns_count():
    """_auto_ingest_cc_sessions logs ingested session count."""
    from agent.governance_ui.dashboard_data_loader import _auto_ingest_cc_sessions

    cc_proj = {
        "project_id": "PROJ-TEST",
        "cc_directory": "/test",
    }

    results = [
        {"session_id": "S1"},
        {"session_id": "S2"},
        {"session_id": "S3"},
    ]
    with patch("governance.services.cc_session_ingestion.ingest_all", return_value=results):
        # Should not raise, just logs
        _auto_ingest_cc_sessions(cc_proj)


def test_ingest_session_idempotent():
    """ingest_session skips already-existing sessions."""
    from governance.services.cc_session_ingestion import ingest_session

    mock_meta = {
        "slug": "test",
        "session_uuid": "uuid-1",
        "git_branch": "main",
        "first_ts": "2026-02-15T10:00:00",
        "last_ts": "2026-02-15T11:00:00",
        "user_count": 5,
        "assistant_count": 5,
        "tool_use_count": 10,
        "thinking_chars": 100,
        "compaction_count": 0,
        "models": [],
        "file_path": "/tmp/test.jsonl",
        "file_size": 1000,
    }

    with patch("governance.services.cc_session_ingestion._scan_jsonl_metadata", return_value=mock_meta):
        with patch("governance.services.cc_session_ingestion.session_service") as mock_svc:
            mock_svc.get_session.return_value = {"session_id": "SESSION-EXISTING"}  # Already exists
            result = ingest_session(Path("/tmp/test.jsonl"))

    assert result is None  # Skipped


def test_ingest_all_uses_discover_log_files():
    """ingest_all uses discover_log_files to find JSONL files."""
    from governance.services.cc_session_ingestion import ingest_all

    mock_file = MagicMock(spec=Path)
    mock_file.stat.return_value.st_size = 1000

    mock_dir = MagicMock(spec=Path)
    mock_dir.is_dir.return_value = True

    with patch("governance.services.cc_session_ingestion.discover_log_files", return_value=[mock_file]) as mock_discover:
        with patch("governance.services.cc_session_ingestion.ingest_session", return_value=None):
            with patch("governance.services.cc_session_ingestion._derive_project_slug", return_value="test"):
                results = ingest_all(directory=mock_dir, project_slug="test")

    mock_discover.assert_called_once()
    assert results == []
