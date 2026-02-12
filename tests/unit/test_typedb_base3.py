"""
Unit tests for TypeDB 3.x Base Client.

Batch 124: Tests for governance/typedb/base3.py
- TypeDB3BaseClient: init, connect, close, is_connected, health_check
- execute_query: read/write transactions, error handling
- _process_results / _concept_to_value: result conversion
- define_schema / insert_data: schema and data operations
- get_typedb3_client: factory function
"""

import os
import sys
from unittest.mock import patch, MagicMock

import pytest


_MOD = "governance.typedb.base3"


def _make_typedb_mocks():
    """Create mock typedb.driver module with expected classes."""
    mock_typedb = MagicMock()
    mock_typedb.TypeDB = MagicMock()
    mock_typedb.Credentials = MagicMock()
    mock_typedb.DriverOptions = MagicMock()
    mock_typedb.TransactionType = MagicMock()
    mock_typedb.TransactionType.READ = "READ"
    mock_typedb.TransactionType.WRITE = "WRITE"
    mock_typedb.TransactionType.SCHEMA = "SCHEMA"
    return mock_typedb


# ── __init__ ─────────────────────────────────────────────


class TestTypeDB3BaseClientInit:
    """Tests for constructor defaults and overrides."""

    def test_default_values(self):
        from governance.typedb.base3 import TypeDB3BaseClient
        client = TypeDB3BaseClient()
        assert client.host is not None
        assert client.port is not None
        assert client.database is not None
        assert client._driver is None
        assert client._connected is False

    def test_custom_values(self):
        from governance.typedb.base3 import TypeDB3BaseClient
        client = TypeDB3BaseClient(host="myhost", port=9999, database="mydb")
        assert client.host == "myhost"
        assert client.port == 9999
        assert client.database == "mydb"

    @patch.dict(os.environ, {"TYPEDB_HOST": "envhost", "TYPEDB_PORT": "2729",
                              "TYPEDB_DATABASE": "envdb"})
    def test_env_var_defaults(self):
        # Module-level constants read at import time, so reimport
        import importlib
        import governance.typedb.base3 as mod
        importlib.reload(mod)
        client = mod.TypeDB3BaseClient()
        assert client.host == "envhost"
        assert client.port == 2729
        assert client.database == "envdb"
        # Reload again to restore defaults
        importlib.reload(mod)


# ── connect ──────────────────────────────────────────────


class TestConnect:
    """Tests for connect() method."""

    def test_successful_connect(self):
        mock_typedb = _make_typedb_mocks()
        mock_driver = MagicMock()
        mock_typedb.TypeDB.driver.return_value = mock_driver

        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            from governance.typedb.base3 import TypeDB3BaseClient
            client = TypeDB3BaseClient(host="localhost", port=1729, database="test")
            result = client.connect()
            assert result is True
            assert client._connected is True
            assert client._driver is mock_driver
            mock_typedb.Credentials.assert_called_once()
            mock_typedb.DriverOptions.assert_called_once()

    def test_import_error_returns_false(self):
        from governance.typedb.base3 import TypeDB3BaseClient
        client = TypeDB3BaseClient()
        # Remove typedb.driver from sys.modules to trigger ImportError
        saved = sys.modules.pop("typedb.driver", None)
        saved_parent = sys.modules.pop("typedb", None)
        try:
            # Ensure fresh import fails
            with patch.dict(sys.modules, {}, clear=False):
                # Force ImportError by making typedb.driver unavailable
                if "typedb" in sys.modules:
                    del sys.modules["typedb"]
                if "typedb.driver" in sys.modules:
                    del sys.modules["typedb.driver"]
                result = client.connect()
                assert result is False
                assert client._connected is False
        finally:
            if saved is not None:
                sys.modules["typedb.driver"] = saved
            if saved_parent is not None:
                sys.modules["typedb"] = saved_parent

    def test_connection_exception_returns_false(self):
        mock_typedb = _make_typedb_mocks()
        mock_typedb.TypeDB.driver.side_effect = Exception("Connection refused")

        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            from governance.typedb.base3 import TypeDB3BaseClient
            client = TypeDB3BaseClient()
            result = client.connect()
            assert result is False
            assert client._connected is False

    @patch.dict(os.environ, {"TYPEDB_USERNAME": "myuser", "TYPEDB_PASSWORD": "mypass"})
    def test_credentials_from_env(self):
        mock_typedb = _make_typedb_mocks()
        mock_typedb.TypeDB.driver.return_value = MagicMock()

        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            from governance.typedb.base3 import TypeDB3BaseClient
            client = TypeDB3BaseClient()
            client.connect()
            mock_typedb.Credentials.assert_called_once_with("myuser", "mypass")


# ── close / is_connected ────────────────────────────────


class TestCloseAndConnected:
    """Tests for close() and is_connected()."""

    def test_close_with_driver(self):
        from governance.typedb.base3 import TypeDB3BaseClient
        client = TypeDB3BaseClient()
        client._driver = MagicMock()
        client._connected = True
        client.close()
        client._driver.close.assert_called_once()
        assert client._connected is False

    def test_close_without_driver(self):
        from governance.typedb.base3 import TypeDB3BaseClient
        client = TypeDB3BaseClient()
        client.close()  # Should not raise

    def test_is_connected_false_by_default(self):
        from governance.typedb.base3 import TypeDB3BaseClient
        client = TypeDB3BaseClient()
        assert client.is_connected() is False

    def test_is_connected_true_after_connect(self):
        from governance.typedb.base3 import TypeDB3BaseClient
        client = TypeDB3BaseClient()
        client._connected = True
        assert client.is_connected() is True


# ── health_check ─────────────────────────────────────────


class TestHealthCheck:
    """Tests for health_check() method."""

    def test_not_connected(self):
        from governance.typedb.base3 import TypeDB3BaseClient
        client = TypeDB3BaseClient()
        result = client.health_check()
        assert result["healthy"] is False
        assert "Not connected" in result["error"]

    def test_healthy_with_target_db(self):
        from governance.typedb.base3 import TypeDB3BaseClient
        client = TypeDB3BaseClient(database="mydb")
        client._connected = True
        mock_db1 = MagicMock()
        mock_db1.name = "mydb"
        mock_db2 = MagicMock()
        mock_db2.name = "other"
        client._driver = MagicMock()
        client._driver.databases.all.return_value = [mock_db1, mock_db2]

        result = client.health_check()
        assert result["healthy"] is True
        assert result["database_exists"] is True
        assert "mydb" in result["databases"]
        assert result["driver_version"] == "3.x"

    def test_healthy_db_not_found(self):
        from governance.typedb.base3 import TypeDB3BaseClient
        client = TypeDB3BaseClient(database="missing")
        client._connected = True
        client._driver = MagicMock()
        client._driver.databases.all.return_value = []

        result = client.health_check()
        assert result["healthy"] is True
        assert result["database_exists"] is False

    def test_exception_returns_unhealthy(self):
        from governance.typedb.base3 import TypeDB3BaseClient
        client = TypeDB3BaseClient()
        client._connected = True
        client._driver = MagicMock()
        client._driver.databases.all.side_effect = Exception("timeout")

        result = client.health_check()
        assert result["healthy"] is False
        assert "timeout" in result["error"]


# ── execute_query ────────────────────────────────────────


class TestExecuteQuery:
    """Tests for execute_query() method."""

    def test_not_connected_raises(self):
        from governance.typedb.base3 import TypeDB3BaseClient
        client = TypeDB3BaseClient()
        with pytest.raises(RuntimeError, match="Not connected"):
            client.execute_query("match $r isa rule;")

    def test_read_query(self):
        mock_typedb = _make_typedb_mocks()
        mock_tx = MagicMock()
        mock_answer = MagicMock()
        mock_answer.column_names.return_value = ["name"]
        mock_concept = MagicMock()
        mock_concept.get_value.return_value = "test-rule"
        mock_answer.get.return_value = mock_concept
        mock_tx.query.return_value.resolve.return_value = [mock_answer]
        mock_tx.__enter__ = MagicMock(return_value=mock_tx)
        mock_tx.__exit__ = MagicMock(return_value=False)

        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            from governance.typedb.base3 import TypeDB3BaseClient
            client = TypeDB3BaseClient()
            client._connected = True
            client._driver = MagicMock()
            client._driver.transaction.return_value = mock_tx

            results = client.execute_query("match $r isa rule;", read_only=True)
            assert len(results) == 1
            assert results[0]["name"] == "test-rule"
            client._driver.transaction.assert_called_once_with(
                client.database, "READ"
            )

    def test_write_query(self):
        mock_typedb = _make_typedb_mocks()
        mock_tx = MagicMock()
        mock_tx.query.return_value.resolve.return_value = None
        mock_tx.__enter__ = MagicMock(return_value=mock_tx)
        mock_tx.__exit__ = MagicMock(return_value=False)

        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            from governance.typedb.base3 import TypeDB3BaseClient
            client = TypeDB3BaseClient()
            client._connected = True
            client._driver = MagicMock()
            client._driver.transaction.return_value = mock_tx

            results = client.execute_query("insert $r isa rule;", read_only=False)
            assert results == []
            client._driver.transaction.assert_called_once_with(
                client.database, "WRITE"
            )

    def test_query_exception_raises_runtime_error(self):
        mock_typedb = _make_typedb_mocks()
        mock_tx = MagicMock()
        mock_tx.query.side_effect = Exception("TypeQL parse error")
        mock_tx.__enter__ = MagicMock(return_value=mock_tx)
        mock_tx.__exit__ = MagicMock(return_value=False)

        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            from governance.typedb.base3 import TypeDB3BaseClient
            client = TypeDB3BaseClient()
            client._connected = True
            client._driver = MagicMock()
            client._driver.transaction.return_value = mock_tx

            with pytest.raises(RuntimeError, match="Query execution failed"):
                client.execute_query("bad query")

    def test_null_result_returns_empty(self):
        mock_typedb = _make_typedb_mocks()
        mock_tx = MagicMock()
        mock_tx.query.return_value.resolve.return_value = None
        mock_tx.__enter__ = MagicMock(return_value=mock_tx)
        mock_tx.__exit__ = MagicMock(return_value=False)

        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            from governance.typedb.base3 import TypeDB3BaseClient
            client = TypeDB3BaseClient()
            client._connected = True
            client._driver = MagicMock()
            client._driver.transaction.return_value = mock_tx

            results = client.execute_query("match $r isa rule;")
            assert results == []


# ── _process_results ─────────────────────────────────────


class TestProcessResults:
    """Tests for _process_results() method."""

    def test_empty_iterator(self):
        from governance.typedb.base3 import TypeDB3BaseClient
        client = TypeDB3BaseClient()
        assert client._process_results([]) == []

    def test_multiple_rows(self):
        from governance.typedb.base3 import TypeDB3BaseClient
        client = TypeDB3BaseClient()

        row1 = MagicMock()
        row1.column_names.return_value = ["id", "name"]
        c1 = MagicMock()
        c1.get_value.return_value = "R1"
        c2 = MagicMock()
        c2.get_value.return_value = "Rule One"
        row1.get.side_effect = lambda k: {"id": c1, "name": c2}[k]

        row2 = MagicMock()
        row2.column_names.return_value = ["id", "name"]
        c3 = MagicMock()
        c3.get_value.return_value = "R2"
        c4 = MagicMock()
        c4.get_value.return_value = "Rule Two"
        row2.get.side_effect = lambda k: {"id": c3, "name": c4}[k]

        results = client._process_results([row1, row2])
        assert len(results) == 2
        assert results[0]["id"] == "R1"
        assert results[1]["name"] == "Rule Two"

    def test_non_iterable_result(self):
        from governance.typedb.base3 import TypeDB3BaseClient
        client = TypeDB3BaseClient()
        # Some query types don't return iterables — should return empty
        result = client._process_results(42)
        assert result == []


# ── _concept_to_value ────────────────────────────────────


class TestConceptToValue:
    """Tests for _concept_to_value() method."""

    def test_none_concept(self):
        from governance.typedb.base3 import TypeDB3BaseClient
        client = TypeDB3BaseClient()
        assert client._concept_to_value(None) is None

    def test_get_value_method(self):
        from governance.typedb.base3 import TypeDB3BaseClient
        client = TypeDB3BaseClient()
        concept = MagicMock(spec=["get_value"])
        concept.get_value.return_value = "hello"
        assert client._concept_to_value(concept) == "hello"

    def test_get_value_exception_falls_through(self):
        from governance.typedb.base3 import TypeDB3BaseClient
        client = TypeDB3BaseClient()
        concept = MagicMock(spec=["get_value", "value"])
        concept.get_value.side_effect = Exception("broken")
        concept.value = "fallback"
        assert client._concept_to_value(concept) == "fallback"

    def test_value_property(self):
        from governance.typedb.base3 import TypeDB3BaseClient
        client = TypeDB3BaseClient()
        concept = MagicMock(spec=["value"])
        concept.value = 42
        assert client._concept_to_value(concept) == 42

    def test_get_iid_method(self):
        from governance.typedb.base3 import TypeDB3BaseClient
        client = TypeDB3BaseClient()
        concept = MagicMock(spec=["get_iid"])
        concept.get_iid.return_value = "IID-12345"
        assert client._concept_to_value(concept) == "IID-12345"

    def test_get_iid_exception_falls_to_iid(self):
        from governance.typedb.base3 import TypeDB3BaseClient
        client = TypeDB3BaseClient()
        concept = MagicMock(spec=["get_iid", "iid"])
        concept.get_iid.side_effect = Exception("broken")
        concept.iid = "IID-99"
        assert client._concept_to_value(concept) == "IID-99"

    def test_iid_property(self):
        from governance.typedb.base3 import TypeDB3BaseClient
        client = TypeDB3BaseClient()
        concept = MagicMock(spec=["iid"])
        concept.iid = "IID-ABC"
        assert client._concept_to_value(concept) == "IID-ABC"

    def test_last_fallback_str(self):
        from governance.typedb.base3 import TypeDB3BaseClient
        client = TypeDB3BaseClient()

        class Opaque:
            """Object with no get_value/value/get_iid/iid attributes."""
            def __str__(self):
                return "<unknown>"

        concept = Opaque()
        assert client._concept_to_value(concept) == "<unknown>"


# ── define_schema ────────────────────────────────────────


class TestDefineSchema:
    """Tests for define_schema() method."""

    def test_not_connected_raises(self):
        from governance.typedb.base3 import TypeDB3BaseClient
        client = TypeDB3BaseClient()
        with pytest.raises(RuntimeError, match="Not connected"):
            client.define_schema("define person sub entity;")

    def test_successful_schema_definition(self):
        mock_typedb = _make_typedb_mocks()
        mock_tx = MagicMock()
        mock_tx.query.return_value.resolve.return_value = None
        mock_tx.__enter__ = MagicMock(return_value=mock_tx)
        mock_tx.__exit__ = MagicMock(return_value=False)

        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            from governance.typedb.base3 import TypeDB3BaseClient
            client = TypeDB3BaseClient()
            client._connected = True
            client._driver = MagicMock()
            client._driver.transaction.return_value = mock_tx

            result = client.define_schema("define person sub entity;")
            assert result is True
            client._driver.transaction.assert_called_once_with(
                client.database, "SCHEMA"
            )
            mock_tx.commit.assert_called_once()

    def test_schema_exception_raises(self):
        mock_typedb = _make_typedb_mocks()
        mock_tx = MagicMock()
        mock_tx.query.side_effect = Exception("Schema error")
        mock_tx.__enter__ = MagicMock(return_value=mock_tx)
        mock_tx.__exit__ = MagicMock(return_value=False)

        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            from governance.typedb.base3 import TypeDB3BaseClient
            client = TypeDB3BaseClient()
            client._connected = True
            client._driver = MagicMock()
            client._driver.transaction.return_value = mock_tx

            with pytest.raises(RuntimeError, match="Schema definition failed"):
                client.define_schema("bad schema")


# ── insert_data ──────────────────────────────────────────


class TestInsertData:
    """Tests for insert_data() method."""

    def test_not_connected_raises(self):
        from governance.typedb.base3 import TypeDB3BaseClient
        client = TypeDB3BaseClient()
        with pytest.raises(RuntimeError, match="Not connected"):
            client.insert_data("insert $p isa person;")

    def test_successful_insert(self):
        mock_typedb = _make_typedb_mocks()
        mock_tx = MagicMock()
        mock_tx.query.return_value.resolve.return_value = None
        mock_tx.__enter__ = MagicMock(return_value=mock_tx)
        mock_tx.__exit__ = MagicMock(return_value=False)

        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            from governance.typedb.base3 import TypeDB3BaseClient
            client = TypeDB3BaseClient()
            client._connected = True
            client._driver = MagicMock()
            client._driver.transaction.return_value = mock_tx

            result = client.insert_data("insert $p isa person;")
            assert result is True
            client._driver.transaction.assert_called_once_with(
                client.database, "WRITE"
            )
            mock_tx.commit.assert_called_once()

    def test_insert_exception_raises(self):
        mock_typedb = _make_typedb_mocks()
        mock_tx = MagicMock()
        mock_tx.query.side_effect = Exception("Insert error")
        mock_tx.__enter__ = MagicMock(return_value=mock_tx)
        mock_tx.__exit__ = MagicMock(return_value=False)

        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            from governance.typedb.base3 import TypeDB3BaseClient
            client = TypeDB3BaseClient()
            client._connected = True
            client._driver = MagicMock()
            client._driver.transaction.return_value = mock_tx

            with pytest.raises(RuntimeError, match="Insert failed"):
                client.insert_data("bad insert")


# ── get_typedb3_client ───────────────────────────────────


class TestGetTypedb3Client:
    """Tests for factory function."""

    @patch(f"{_MOD}.TypeDB3BaseClient")
    def test_successful_connect_returns_client(self, mock_cls):
        from governance.typedb.base3 import get_typedb3_client
        mock_instance = MagicMock()
        mock_instance.connect.return_value = True
        mock_cls.return_value = mock_instance

        result = get_typedb3_client()
        assert result is mock_instance
        mock_instance.connect.assert_called_once()

    @patch(f"{_MOD}.TypeDB3BaseClient")
    def test_failed_connect_returns_none(self, mock_cls):
        from governance.typedb.base3 import get_typedb3_client
        mock_instance = MagicMock()
        mock_instance.connect.return_value = False
        mock_cls.return_value = mock_instance

        result = get_typedb3_client()
        assert result is None
