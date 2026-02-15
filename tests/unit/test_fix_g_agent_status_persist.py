"""Tests for Fix G: Agent Status Persistence.

Validates that agent status toggles are persisted to metrics file
and restored on startup (survives container restarts).
"""
from unittest.mock import patch, MagicMock
import json
import os
import pytest


def test_persist_agent_status_writes_to_metrics():
    """_persist_agent_status writes status to metrics file."""
    from governance.services.agents import _persist_agent_status

    saved_data = {}

    def mock_save(metrics):
        saved_data.update(metrics)

    with patch("governance.services.agents._load_agent_metrics", return_value={}):
        with patch("governance.services.agents._save_agent_metrics", side_effect=mock_save):
            _persist_agent_status("code-agent", "ACTIVE")

    assert saved_data["code-agent"]["status"] == "ACTIVE"


def test_persist_agent_status_preserves_existing_metrics():
    """_persist_agent_status preserves existing metrics (tasks_executed, etc)."""
    from governance.services.agents import _persist_agent_status

    saved_data = {}
    existing = {"code-agent": {"tasks_executed": 42, "last_active": "2026-02-15"}}

    def mock_save(metrics):
        saved_data.update(metrics)

    with patch("governance.services.agents._load_agent_metrics", return_value=existing):
        with patch("governance.services.agents._save_agent_metrics", side_effect=mock_save):
            _persist_agent_status("code-agent", "ACTIVE")

    assert saved_data["code-agent"]["status"] == "ACTIVE"
    assert saved_data["code-agent"]["tasks_executed"] == 42
    assert saved_data["code-agent"]["last_active"] == "2026-02-15"


def test_persist_agent_status_handles_save_failure():
    """_persist_agent_status handles save errors gracefully."""
    from governance.services.agents import _persist_agent_status

    with patch("governance.services.agents._load_agent_metrics", return_value={}):
        with patch("governance.services.agents._save_agent_metrics", side_effect=IOError("disk full")):
            # Should not raise
            _persist_agent_status("code-agent", "ACTIVE")


def test_toggle_calls_persist():
    """toggle_agent_status calls _persist_agent_status."""
    from governance.services.agents import toggle_agent_status
    from governance.stores import _agents_store

    # Ensure agent exists in memory
    _agents_store["test-agent-g"] = {
        "agent_id": "test-agent-g",
        "name": "Test",
        "agent_type": "custom",
        "status": "PAUSED",
        "trust_score": 0.8,
        "tasks_executed": 0,
        "capabilities": [],
        "recent_sessions": [],
        "active_tasks": [],
    }

    with patch("governance.services.agents._persist_agent_status") as mock_persist:
        with patch("governance.services.agents.get_typedb_client", return_value=None):
            toggle_agent_status("test-agent-g")

    mock_persist.assert_called_once_with("test-agent-g", "ACTIVE")

    # Toggle back
    with patch("governance.services.agents._persist_agent_status") as mock_persist:
        with patch("governance.services.agents.get_typedb_client", return_value=None):
            toggle_agent_status("test-agent-g")

    mock_persist.assert_called_once_with("test-agent-g", "PAUSED")

    # Cleanup
    _agents_store.pop("test-agent-g", None)


def test_build_agents_store_restores_persisted_status():
    """_build_agents_store restores persisted status from metrics."""
    from governance.stores.agents import _build_agents_store

    metrics = {
        "code-agent": {"tasks_executed": 5, "status": "ACTIVE"},
    }

    with patch("governance.stores.agents._load_agent_metrics", return_value=metrics):
        with patch("governance.stores.agents._load_workflow_configs", return_value={}):
            store = _build_agents_store()

    assert store["code-agent"]["status"] == "ACTIVE"


def test_build_agents_store_defaults_when_no_persisted_status():
    """_build_agents_store uses default_status when no persisted status."""
    from governance.stores.agents import _build_agents_store

    metrics = {
        "code-agent": {"tasks_executed": 5},  # No "status" key
    }

    with patch("governance.stores.agents._load_agent_metrics", return_value=metrics):
        with patch("governance.stores.agents._load_workflow_configs", return_value={}):
            store = _build_agents_store()

    # Should fall back to default_status from _AGENT_BASE_CONFIG
    assert store["code-agent"]["status"] == "PAUSED"


def test_persist_new_agent_creates_entry():
    """_persist_agent_status creates new entry for unknown agent."""
    from governance.services.agents import _persist_agent_status

    saved_data = {}

    def mock_save(metrics):
        saved_data.update(metrics)

    with patch("governance.services.agents._load_agent_metrics", return_value={}):
        with patch("governance.services.agents._save_agent_metrics", side_effect=mock_save):
            _persist_agent_status("brand-new-agent", "ACTIVE")

    assert "brand-new-agent" in saved_data
    assert saved_data["brand-new-agent"]["status"] == "ACTIVE"
