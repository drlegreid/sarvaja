"""
Unit tests for Compat - Task CRUD Exports.

Per DOC-SIZE-01-v1: Tests for compat/tasks.py module.
Tests: _json_serializer, governance_create_task, governance_get_task,
       governance_update_task, governance_delete_task.
"""

import json
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from governance.compat.tasks import _json_serializer


class TestJsonSerializer:
    """Tests for _json_serializer()."""

    def test_datetime(self):
        dt = datetime(2026, 2, 11, 10, 0, 0)
        result = _json_serializer(dt)
        assert result == "2026-02-11T10:00:00"

    def test_isoformat_duck_type(self):
        class FakeDate:
            def isoformat(self):
                return "2026-01-01"
        result = _json_serializer(FakeDate())
        assert result == "2026-01-01"

    def test_typedb_datetime_type(self):
        class Datetime:
            def __str__(self):
                return "2026-02-11"
        result = _json_serializer(Datetime())
        assert result == "2026-02-11"

    def test_unsupported_raises(self):
        with pytest.raises(TypeError, match="not JSON serializable"):
            _json_serializer(set())


class TestGovernanceCreateTask:
    """Tests for governance_create_task()."""

    @patch("governance.compat.tasks.get_typedb_client")
    def test_success(self, mock_get):
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.insert_task.return_value = True
        mock_get.return_value = mock_client

        from governance.compat.tasks import governance_create_task
        result = json.loads(governance_create_task("T-1", "Test Task"))
        assert result["task_id"] == "T-1"
        assert "message" in result
        mock_client.close.assert_called_once()

    @patch("governance.compat.tasks.get_typedb_client")
    def test_connect_fail(self, mock_get):
        mock_client = MagicMock()
        mock_client.connect.return_value = False
        mock_get.return_value = mock_client

        from governance.compat.tasks import governance_create_task
        result = json.loads(governance_create_task("T-1", "Test"))
        assert "error" in result

    @patch("governance.compat.tasks.get_typedb_client")
    def test_insert_fail(self, mock_get):
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.insert_task.return_value = False
        mock_get.return_value = mock_client

        from governance.compat.tasks import governance_create_task
        result = json.loads(governance_create_task("T-1", "Test"))
        assert "error" in result


class TestGovernanceGetTask:
    """Tests for governance_get_task()."""

    @patch("governance.compat.tasks.get_typedb_client")
    def test_found(self, mock_get):
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_task = MagicMock()
        mock_task.__dataclass_fields__ = {}
        mock_client.get_task.return_value = mock_task
        mock_get.return_value = mock_client

        with patch("governance.compat.tasks.asdict", return_value={"id": "T-1"}):
            from governance.compat.tasks import governance_get_task
            result = json.loads(governance_get_task("T-1"))
            assert result["id"] == "T-1"

    @patch("governance.compat.tasks.get_typedb_client")
    def test_not_found(self, mock_get):
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.get_task.return_value = None
        mock_get.return_value = mock_client

        from governance.compat.tasks import governance_get_task
        result = json.loads(governance_get_task("T-999"))
        assert "error" in result


class TestGovernanceUpdateTask:
    """Tests for governance_update_task()."""

    def test_no_fields_error(self):
        from governance.compat.tasks import governance_update_task
        result = json.loads(governance_update_task("T-1"))
        assert "error" in result
        assert "No update fields" in result["error"]

    @patch("governance.compat.tasks.get_typedb_client")
    def test_success(self, mock_get):
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.update_task.return_value = True
        mock_client.get_task.return_value = None  # task lookup after update
        mock_get.return_value = mock_client

        from governance.compat.tasks import governance_update_task
        result = json.loads(governance_update_task("T-1", status="DONE"))
        assert "message" in result

    @patch("governance.compat.tasks.get_typedb_client")
    def test_update_fail(self, mock_get):
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.update_task.return_value = False
        mock_get.return_value = mock_client

        from governance.compat.tasks import governance_update_task
        result = json.loads(governance_update_task("T-1", status="DONE"))
        assert "error" in result


class TestGovernanceDeleteTask:
    """Tests for governance_delete_task()."""

    @patch("governance.compat.tasks.get_typedb_client")
    def test_success(self, mock_get):
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.delete_task.return_value = True
        mock_get.return_value = mock_client

        from governance.compat.tasks import governance_delete_task
        result = json.loads(governance_delete_task("T-1"))
        assert result["deleted"] is True

    @patch("governance.compat.tasks.get_typedb_client")
    def test_delete_fail(self, mock_get):
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.delete_task.return_value = False
        mock_get.return_value = mock_client

        from governance.compat.tasks import governance_delete_task
        result = json.loads(governance_delete_task("T-1"))
        assert "error" in result
