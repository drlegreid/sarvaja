"""
Unit tests for ChromaDB Migrator.

Per DOC-SIZE-01-v1: Tests for migration/migrator.py module.
Tests: ChromaMigration — init, scan_chroma, transform_document, detect_type,
       migrate_collection, migrate_all, get_migration_status,
       create_chroma_migration.
"""

from unittest.mock import patch, MagicMock

import pytest


_P_ROUTER = "governance.migration.migrator.create_data_router"
_P_SCANNER = "governance.migration.migrator.ChromaScanner"
_P_TRANSFORMER = "governance.migration.migrator.DocumentTransformer"


@pytest.fixture()
def migrator():
    with patch(_P_ROUTER) as mock_router, \
         patch(_P_SCANNER) as mock_scanner, \
         patch(_P_TRANSFORMER) as mock_transformer:
        mock_router.return_value = MagicMock()
        mock_scanner.return_value = MagicMock()
        mock_transformer.return_value = MagicMock()
        from governance.migration.migrator import ChromaMigration
        m = ChromaMigration(dry_run=True)
        yield m


class TestInit:
    def test_defaults(self, migrator):
        assert migrator.dry_run is True
        assert migrator.batch_size == 100
        assert migrator._migration_state["phase"] == "idle"

    def test_custom_params(self):
        with patch(_P_ROUTER), patch(_P_SCANNER), patch(_P_TRANSFORMER):
            from governance.migration.migrator import ChromaMigration
            m = ChromaMigration(dry_run=False, batch_size=50, chroma_port=9999)
            assert m.dry_run is False
            assert m.batch_size == 50
            assert m.chroma_port == 9999


class TestRouter:
    def test_property(self, migrator):
        assert migrator.router is migrator._router


class TestScanChroma:
    def test_delegates(self, migrator):
        migrator._scanner.scan.return_value = {"collections": []}
        result = migrator.scan_chroma()
        migrator._scanner.scan.assert_called_once()
        assert result == {"collections": []}


class TestTransformDocument:
    def test_delegates(self, migrator):
        migrator._transformer.transform.return_value = {"type": "rule"}
        result = migrator.transform_document({"id": "R-1", "content": "test"})
        assert result["type"] == "rule"


class TestDetectType:
    def test_delegates(self, migrator):
        migrator._transformer.detect_type.return_value = "decision"
        assert migrator.detect_type("DECISION-001") == "decision"


class TestMigrateCollection:
    def test_dry_run(self, migrator):
        migrator._scanner.scan.return_value = {
            "collections": [{"name": "test-coll", "count": 5}]
        }
        result = migrator.migrate_collection("test-coll")
        assert result["dry_run"] is True
        assert result["success"] is True
        assert result["migrated"] == 5

    def test_dry_run_collection_not_found(self, migrator):
        migrator._scanner.scan.return_value = {
            "collections": [{"name": "other", "count": 3}]
        }
        result = migrator.migrate_collection("nonexistent")
        assert result["migrated"] == 0
        assert result["success"] is True

    def test_import_error(self, migrator):
        migrator.dry_run = False
        with patch("builtins.__import__", side_effect=ImportError("no chromadb")):
            result = migrator.migrate_collection("test")
        assert result["success"] is False
        assert "chromadb not installed" in result["errors"]

    def test_scan_exception(self, migrator):
        migrator.dry_run = False
        # Simulate general exception by patching chromadb import
        with patch.dict("sys.modules", {"chromadb": MagicMock(
            HttpClient=MagicMock(side_effect=Exception("connection error"))
        )}):
            result = migrator.migrate_collection("test")
        assert result["success"] is False

    def test_state_tracking(self, migrator):
        migrator._scanner.scan.return_value = {
            "collections": [{"name": "coll", "count": 2}]
        }
        migrator.migrate_collection("coll")
        assert migrator._migration_state["phase"] == "migrating"
        assert "coll" in migrator._migration_state["collections"]


class TestMigrateAll:
    def test_scan_error(self, migrator):
        migrator._scanner.scan.return_value = {"error": "connection refused"}
        result = migrator.migrate_all()
        assert result["success"] is False
        assert result["error"] == "connection refused"

    def test_success(self, migrator):
        migrator._scanner.scan.return_value = {
            "collections": [{"name": "coll1", "count": 3}]
        }
        result = migrator.migrate_all()
        assert result["dry_run"] is True
        assert result["total"] == 3
        assert migrator._migration_state["phase"] == "completed"

    def test_multiple_collections(self, migrator):
        migrator._scanner.scan.return_value = {
            "collections": [
                {"name": "coll1", "count": 2},
                {"name": "coll2", "count": 3},
            ]
        }
        result = migrator.migrate_all()
        assert result["total"] == 5
        assert len(result["collections"]) == 2

    def test_empty_collections(self, migrator):
        migrator._scanner.scan.return_value = {"collections": []}
        result = migrator.migrate_all()
        assert result["success"] is True
        assert result["total"] == 0


class TestGetMigrationStatus:
    def test_idle(self, migrator):
        status = migrator.get_migration_status()
        assert status["phase"] == "idle"
        assert status["dry_run"] is True

    def test_after_migration(self, migrator):
        migrator._scanner.scan.return_value = {"collections": []}
        migrator.migrate_all()
        status = migrator.get_migration_status()
        assert status["phase"] == "completed"
        assert status["started"] is not None
        assert status["completed"] is not None


class TestFactory:
    def test_create(self):
        with patch(_P_ROUTER), patch(_P_SCANNER), patch(_P_TRANSFORMER):
            from governance.migration.migrator import create_chroma_migration
            m = create_chroma_migration(dry_run=True, batch_size=50)
            assert m.dry_run is True
            assert m.batch_size == 50
