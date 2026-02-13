"""
Unit tests for TypeDB Schema and Data Loader.

Batch 154: Tests for governance/loader.py
- connect: driver creation with credentials
- create_database: database creation/deletion
- load_schema / load_schema_modular: schema loading
- load_data: data insertion
- verify_load: entity count verification
- main: orchestration
"""

import importlib
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import pytest


# loader.py has a top-level import that calls exit(1) if typedb.driver is missing.
# We must mock the import before importing the module.
_mock_typedb = MagicMock()
_mock_typedb.TypeDB = MagicMock()
_mock_typedb.Credentials = MagicMock()
_mock_typedb.DriverOptions = MagicMock()
_mock_typedb.TransactionType = MagicMock()
_mock_typedb.TransactionType.SCHEMA = "SCHEMA"
_mock_typedb.TransactionType.WRITE = "WRITE"
_mock_typedb.TransactionType.READ = "READ"


@pytest.fixture(autouse=True)
def _mock_typedb_driver():
    with patch.dict("sys.modules", {"typedb.driver": _mock_typedb}):
        yield


def _import_loader():
    """Import loader with mocked typedb driver."""
    if "governance.loader" in sys.modules:
        return importlib.reload(sys.modules["governance.loader"])
    import governance.loader as mod
    return mod


# ── connect ──────────────────────────────────────────────

class TestConnect:
    def test_returns_driver(self):
        mod = _import_loader()
        driver = mod.connect()
        assert driver is _mock_typedb.TypeDB.driver.return_value

    def test_calls_typedb_driver(self):
        mod = _import_loader()
        _mock_typedb.TypeDB.driver.reset_mock()
        mod.connect()
        _mock_typedb.TypeDB.driver.assert_called_once()


# ── create_database ──────────────────────────────────────

class TestCreateDatabase:
    def test_creates_new_database(self):
        mod = _import_loader()
        driver = MagicMock()
        mock_db = MagicMock()
        mock_db.name = "other-db"
        driver.databases.all.return_value = [mock_db]

        mod.create_database(driver)
        driver.databases.create.assert_called_once_with(mod.DATABASE_NAME)

    def test_deletes_existing_database(self):
        mod = _import_loader()
        driver = MagicMock()
        mock_db = MagicMock()
        mock_db.name = mod.DATABASE_NAME
        driver.databases.all.return_value = [mock_db]

        mod.create_database(driver)
        driver.databases.get.return_value.delete.assert_called_once()
        driver.databases.create.assert_called_once()


# ── load_schema ──────────────────────────────────────────

class TestLoadSchema:
    def test_loads_monolithic_schema(self):
        mod = _import_loader()
        driver = MagicMock()
        tx = MagicMock()
        driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        driver.transaction.return_value.__exit__ = MagicMock(return_value=False)

        with patch("builtins.open", mock_open(read_data="define\nattribute name;")):
            mod.load_schema(driver)

        tx.query.assert_called_once()
        tx.commit.assert_called_once()

    def test_modular_schema_flag(self, tmp_path):
        mod = _import_loader()
        orig_modular = mod.USE_MODULAR_SCHEMA
        orig_dir = mod.SCHEMA_DIR
        try:
            mod.USE_MODULAR_SCHEMA = True
            schema_dir = tmp_path / "schema"
            schema_dir.mkdir()
            (schema_dir / "01_core.tql").write_text("define\nattribute name, value string;")
            (schema_dir / "02_extra.tql").write_text("define\nattribute desc, value string;")
            mod.SCHEMA_DIR = schema_dir

            driver = MagicMock()
            tx = MagicMock()
            driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
            driver.transaction.return_value.__exit__ = MagicMock(return_value=False)

            mod.load_schema(driver)
            tx.query.assert_called_once()
            combined = tx.query.call_args[0][0]
            assert "01_core.tql" in combined
            assert "02_extra.tql" in combined
        finally:
            mod.USE_MODULAR_SCHEMA = orig_modular
            mod.SCHEMA_DIR = orig_dir


# ── load_schema_modular ──────────────────────────────────

class TestLoadSchemaModular:
    def test_missing_dir_raises(self):
        mod = _import_loader()
        orig = mod.SCHEMA_DIR
        try:
            mod.SCHEMA_DIR = Path("/nonexistent/schema")
            with pytest.raises(FileNotFoundError):
                mod.load_schema_modular(MagicMock())
        finally:
            mod.SCHEMA_DIR = orig

    def test_empty_dir_raises(self, tmp_path):
        mod = _import_loader()
        schema_dir = tmp_path / "schema"
        schema_dir.mkdir()
        orig = mod.SCHEMA_DIR
        try:
            mod.SCHEMA_DIR = schema_dir
            with pytest.raises(FileNotFoundError):
                mod.load_schema_modular(MagicMock())
        finally:
            mod.SCHEMA_DIR = orig


# ── load_data ────────────────────────────────────────────

class TestLoadData:
    def test_loads_data_file(self):
        mod = _import_loader()
        driver = MagicMock()
        tx = MagicMock()
        driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        driver.transaction.return_value.__exit__ = MagicMock(return_value=False)

        with patch("builtins.open", mock_open(read_data="insert $r isa rule;")):
            mod.load_data(driver)

        tx.query.assert_called_once()
        tx.commit.assert_called_once()


# ── verify_load ──────────────────────────────────────────

class TestVerifyLoad:
    def _make_results(self, rules=30, decisions=4, agents=3):
        """Generate side_effect list for tx.query().resolve()."""
        return [
            [MagicMock()] * rules,      # rules
            [MagicMock()] * decisions,   # decisions
            [MagicMock()] * agents,      # agents
            [], [], [], [], [], [], [], [],  # other entity types
        ]

    def test_returns_true_when_sufficient(self):
        mod = _import_loader()
        driver = MagicMock()
        tx = MagicMock()
        driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        driver.transaction.return_value.__exit__ = MagicMock(return_value=False)
        tx.query.return_value.resolve.side_effect = self._make_results(30, 4, 3)
        assert mod.verify_load(driver) is True

    def test_returns_false_insufficient_rules(self):
        mod = _import_loader()
        driver = MagicMock()
        tx = MagicMock()
        driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        driver.transaction.return_value.__exit__ = MagicMock(return_value=False)
        tx.query.return_value.resolve.side_effect = self._make_results(5, 4, 3)
        assert mod.verify_load(driver) is False

    def test_returns_false_wrong_decisions(self):
        mod = _import_loader()
        driver = MagicMock()
        tx = MagicMock()
        driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        driver.transaction.return_value.__exit__ = MagicMock(return_value=False)
        tx.query.return_value.resolve.side_effect = self._make_results(30, 2, 3)
        assert mod.verify_load(driver) is False


# ── main ─────────────────────────────────────────────────

class TestMain:
    def test_exception_returns_one(self):
        mod = _import_loader()
        with patch.object(mod, "connect", side_effect=Exception("conn failed")):
            result = mod.main()
        assert result == 1
