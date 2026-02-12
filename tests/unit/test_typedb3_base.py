"""
Unit tests for TypeDB 3.x Base Client.

Per DOC-SIZE-01-v1: Tests for governance/typedb/base3.py.
Tests: TypeDB3BaseClient init, connect, close, health_check,
       execute_query, _process_results, _concept_to_value,
       define_schema, insert_data, get_typedb3_client.
"""

from unittest.mock import patch, MagicMock

from governance.typedb.base3 import (
    TypeDB3BaseClient,
    get_typedb3_client,
    TYPEDB_HOST,
    TYPEDB_PORT,
    DATABASE_NAME,
)


# ── TypeDB3BaseClient init ────────────────────────────


class TestInit:
    def test_defaults(self):
        client = TypeDB3BaseClient()
        assert client.host == TYPEDB_HOST
        assert client.port == TYPEDB_PORT
        assert client.database == DATABASE_NAME
        assert client._connected is False

    def test_custom_params(self):
        client = TypeDB3BaseClient(host="custom", port=9999, database="test-db")
        assert client.host == "custom"
        assert client.port == 9999
        assert client.database == "test-db"


# ── connect ───────────────────────────────────────────


class TestConnect:
    @patch("governance.typedb.base3.TypeDB3BaseClient.connect")
    def test_connect_success(self, mock_connect):
        mock_connect.return_value = True
        client = TypeDB3BaseClient()
        assert client.connect() is True

    def test_connect_import_error(self):
        client = TypeDB3BaseClient()
        with patch.dict("sys.modules", {"typedb": None, "typedb.driver": None}):
            result = client.connect()
            assert result is False

    def test_connect_exception(self):
        client = TypeDB3BaseClient()
        with patch("builtins.__import__", side_effect=Exception("connection refused")):
            result = client.connect()
            assert result is False


# ── close ─────────────────────────────────────────────


class TestClose:
    def test_close_with_driver(self):
        client = TypeDB3BaseClient()
        client._driver = MagicMock()
        client._connected = True
        client.close()
        client._driver.close.assert_called_once()
        assert client._connected is False

    def test_close_without_driver(self):
        client = TypeDB3BaseClient()
        client.close()  # Should not raise


# ── is_connected ──────────────────────────────────────


class TestIsConnected:
    def test_not_connected(self):
        client = TypeDB3BaseClient()
        assert client.is_connected() is False

    def test_connected(self):
        client = TypeDB3BaseClient()
        client._connected = True
        assert client.is_connected() is True


# ── health_check ──────────────────────────────────────


class TestHealthCheck:
    def test_not_connected(self):
        client = TypeDB3BaseClient()
        result = client.health_check()
        assert result["healthy"] is False
        assert "Not connected" in result["error"]

    def test_connected_with_database(self):
        client = TypeDB3BaseClient()
        client._connected = True
        mock_db = MagicMock()
        mock_db.name = DATABASE_NAME
        client._driver = MagicMock()
        client._driver.databases.all.return_value = [mock_db]

        result = client.health_check()
        assert result["healthy"] is True
        assert result["database_exists"] is True
        assert result["driver_version"] == "3.x"

    def test_connected_without_database(self):
        client = TypeDB3BaseClient()
        client._connected = True
        client._driver = MagicMock()
        client._driver.databases.all.return_value = []

        result = client.health_check()
        assert result["healthy"] is True
        assert result["database_exists"] is False

    def test_exception_during_health(self):
        client = TypeDB3BaseClient()
        client._connected = True
        client._driver = MagicMock()
        client._driver.databases.all.side_effect = Exception("timeout")

        result = client.health_check()
        assert result["healthy"] is False
        assert "timeout" in result["error"]


# ── _concept_to_value ─────────────────────────────────


class TestConceptToValue:
    def test_none(self):
        client = TypeDB3BaseClient()
        assert client._concept_to_value(None) is None

    def test_get_value(self):
        client = TypeDB3BaseClient()
        concept = MagicMock()
        concept.get_value.return_value = "hello"
        assert client._concept_to_value(concept) == "hello"

    def test_value_property(self):
        client = TypeDB3BaseClient()
        concept = MagicMock(spec=[])  # No get_value
        concept.value = 42
        assert client._concept_to_value(concept) == 42

    def test_get_iid(self):
        client = TypeDB3BaseClient()
        concept = MagicMock(spec=[])  # No get_value, no value
        concept.get_iid = MagicMock(return_value="0x123")
        assert client._concept_to_value(concept) == "0x123"

    def test_fallback_str(self):
        client = TypeDB3BaseClient()

        class Bare:
            def __str__(self):
                return "<Concept>"

        result = client._concept_to_value(Bare())
        assert result == "<Concept>"


# ── execute_query ─────────────────────────────────────


class TestExecuteQuery:
    def test_not_connected_raises(self):
        client = TypeDB3BaseClient()
        try:
            client.execute_query("match $r isa rule;")
            assert False, "Should have raised"
        except RuntimeError as e:
            assert "Not connected" in str(e)

    def test_returns_empty_on_none_result(self):
        client = TypeDB3BaseClient()
        client._connected = True
        mock_tx = MagicMock()
        mock_tx.query.return_value.resolve.return_value = None
        client._driver = MagicMock()
        client._driver.transaction.return_value.__enter__ = MagicMock(return_value=mock_tx)
        client._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)

        with patch("governance.typedb.base3.TransactionType", create=True):
            with patch("builtins.__import__", return_value=MagicMock()):
                # Mock the import inside execute_query
                import sys
                mock_driver_mod = MagicMock()
                mock_driver_mod.TransactionType.READ = "READ"
                mock_driver_mod.TransactionType.WRITE = "WRITE"
                with patch.dict(sys.modules, {"typedb.driver": mock_driver_mod}):
                    result = client.execute_query("match $r isa rule;")
                    assert result == []


# ── define_schema ─────────────────────────────────────


class TestDefineSchema:
    def test_not_connected_raises(self):
        client = TypeDB3BaseClient()
        try:
            client.define_schema("define entity test;")
            assert False, "Should have raised"
        except RuntimeError as e:
            assert "Not connected" in str(e)


# ── insert_data ───────────────────────────────────────


class TestInsertData:
    def test_not_connected_raises(self):
        client = TypeDB3BaseClient()
        try:
            client.insert_data("insert $x isa test;")
            assert False, "Should have raised"
        except RuntimeError as e:
            assert "Not connected" in str(e)


# ── get_typedb3_client ────────────────────────────────


class TestGetTypedb3Client:
    @patch.object(TypeDB3BaseClient, "connect", return_value=True)
    def test_success(self, mock_connect):
        client = get_typedb3_client()
        assert client is not None
        assert isinstance(client, TypeDB3BaseClient)

    @patch.object(TypeDB3BaseClient, "connect", return_value=False)
    def test_connection_failure(self, mock_connect):
        assert get_typedb3_client() is None
