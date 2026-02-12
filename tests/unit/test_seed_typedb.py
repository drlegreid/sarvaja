"""
Unit tests for TypeDB Seeder Functions.

Per DOC-SIZE-01-v1: Tests for seed/typedb.py module.
Tests: get_typedb_client, seed_tasks_to_typedb, seed_sessions_to_typedb,
       seed_agents_to_typedb.
"""

import pytest
from unittest.mock import patch, MagicMock

from governance.seed.typedb import (
    get_typedb_client,
    seed_tasks_to_typedb,
    seed_sessions_to_typedb,
    seed_agents_to_typedb,
)


# ---------------------------------------------------------------------------
# get_typedb_client
# ---------------------------------------------------------------------------
class TestGetTypedbClient:
    """Tests for get_typedb_client()."""

    @patch("governance.client.get_client")
    def test_returns_connected_client(self, mock_get):
        client = MagicMock()
        client.is_connected.return_value = True
        mock_get.return_value = client
        assert get_typedb_client() is client

    @patch("governance.client.get_client")
    def test_returns_none_when_not_connected(self, mock_get):
        client = MagicMock()
        client.is_connected.return_value = False
        mock_get.return_value = client
        assert get_typedb_client() is None

    @patch("governance.client.get_client")
    def test_returns_none_on_exception(self, mock_get):
        mock_get.side_effect = Exception("Connection refused")
        assert get_typedb_client() is None

    @patch("governance.client.get_client")
    def test_returns_none_when_client_is_none(self, mock_get):
        mock_get.return_value = None
        assert get_typedb_client() is None


# ---------------------------------------------------------------------------
# seed_tasks_to_typedb
# ---------------------------------------------------------------------------
class TestSeedTasksToTypedb:
    """Tests for seed_tasks_to_typedb()."""

    def test_skips_existing_tasks(self):
        client = MagicMock()
        client.get_task.return_value = MagicMock()  # exists
        count = seed_tasks_to_typedb(client)
        assert count == 0

    def test_inserts_new_tasks(self):
        client = MagicMock()
        client.get_task.return_value = None  # doesn't exist
        client.insert_task.return_value = True
        count = seed_tasks_to_typedb(client)
        assert count > 0

    def test_handles_insert_failure(self):
        client = MagicMock()
        client.get_task.return_value = None
        client.insert_task.return_value = False
        count = seed_tasks_to_typedb(client)
        assert count == 0

    def test_handles_exception(self):
        client = MagicMock()
        client.get_task.side_effect = Exception("DB error")
        count = seed_tasks_to_typedb(client)
        assert count == 0

    def test_passes_task_fields(self):
        client = MagicMock()
        client.get_task.return_value = None
        client.insert_task.return_value = True
        seed_tasks_to_typedb(client)
        call_kwargs = client.insert_task.call_args_list[0][1]
        assert "task_id" in call_kwargs
        assert "name" in call_kwargs
        assert "status" in call_kwargs


# ---------------------------------------------------------------------------
# seed_sessions_to_typedb
# ---------------------------------------------------------------------------
class TestSeedSessionsToTypedb:
    """Tests for seed_sessions_to_typedb()."""

    def test_skips_existing_sessions(self):
        client = MagicMock()
        client.get_session.return_value = MagicMock()
        count = seed_sessions_to_typedb(client)
        assert count == 0

    def test_inserts_new_sessions(self):
        client = MagicMock()
        client.get_session.return_value = None
        client.insert_session.return_value = True
        count = seed_sessions_to_typedb(client)
        assert count > 0

    def test_handles_exception(self):
        client = MagicMock()
        client.get_session.side_effect = Exception("DB error")
        count = seed_sessions_to_typedb(client)
        assert count == 0


# ---------------------------------------------------------------------------
# seed_agents_to_typedb
# ---------------------------------------------------------------------------
class TestSeedAgentsToTypedb:
    """Tests for seed_agents_to_typedb()."""

    def test_skips_existing_agents(self):
        client = MagicMock()
        client.get_agent.return_value = MagicMock()
        count = seed_agents_to_typedb(client)
        assert count == 0

    def test_inserts_new_agents(self):
        client = MagicMock()
        client.get_agent.return_value = None
        client.insert_agent.return_value = True
        count = seed_agents_to_typedb(client)
        assert count == 5  # all 5 agents

    def test_handles_exception(self):
        client = MagicMock()
        client.get_agent.side_effect = Exception("DB error")
        count = seed_agents_to_typedb(client)
        assert count == 0

    def test_passes_trust_score(self):
        client = MagicMock()
        client.get_agent.return_value = None
        client.insert_agent.return_value = True
        seed_agents_to_typedb(client)
        call_kwargs = client.insert_agent.call_args_list[0][1]
        assert "trust_score" in call_kwargs
        assert 0.0 <= call_kwargs["trust_score"] <= 1.0
