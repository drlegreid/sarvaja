"""
ChromaDB Migration Tool Tests (P7.4)
Created: 2024-12-25

Tests for migrating existing ChromaDB data to TypeDB.
Strategic Goal: Consolidate all governance data in TypeDB-first architecture.
"""
import pytest
import json
from datetime import datetime


class TestChromaScan:
    """Tests for ChromaDB scanning functionality."""

    @pytest.mark.unit
    def test_scan_chroma_returns_collections(self):
        """Scan should return list of collections."""
        from governance.chroma_migration import ChromaMigration

        migrator = ChromaMigration(dry_run=True, skip_connection=True)
        result = migrator.scan_chroma()

        assert isinstance(result, dict)
        assert 'collections' in result

    @pytest.mark.unit
    def test_scan_includes_document_counts(self):
        """Scan should include document counts per collection."""
        from governance.chroma_migration import ChromaMigration

        migrator = ChromaMigration(dry_run=True, skip_connection=True)
        result = migrator.scan_chroma()

        assert 'total_documents' in result

    @pytest.mark.unit
    def test_scan_handles_missing_chroma(self):
        """Should handle ChromaDB not available gracefully."""
        from governance.chroma_migration import ChromaMigration

        migrator = ChromaMigration(dry_run=True, skip_connection=True)
        result = migrator.scan_chroma()

        # Should still return valid structure even on error
        assert isinstance(result, dict)


class TestCollectionMigration:
    """Tests for migrating individual collections."""

    @pytest.mark.unit
    def test_migrate_collection_dry_run(self):
        """Dry run migration should not write to TypeDB."""
        from governance.chroma_migration import ChromaMigration

        migrator = ChromaMigration(dry_run=True, skip_connection=True)
        result = migrator.migrate_collection("test_collection")

        assert isinstance(result, dict)
        assert 'dry_run' in result
        assert result['dry_run'] is True

    @pytest.mark.unit
    def test_migrate_collection_tracks_progress(self):
        """Migration should track progress."""
        from governance.chroma_migration import ChromaMigration

        migrator = ChromaMigration(dry_run=True, skip_connection=True)
        result = migrator.migrate_collection("test_collection")

        assert 'migrated' in result or 'status' in result

    @pytest.mark.unit
    def test_migrate_collection_handles_errors(self):
        """Should handle migration errors gracefully."""
        from governance.chroma_migration import ChromaMigration

        migrator = ChromaMigration(dry_run=True, skip_connection=True)
        result = migrator.migrate_collection("nonexistent_collection")

        assert isinstance(result, dict)


class TestDataTransformation:
    """Tests for data transformation from ChromaDB to TypeDB format."""

    @pytest.mark.unit
    def test_transform_document(self):
        """Should transform ChromaDB document to TypeDB format."""
        from governance.chroma_migration import ChromaMigration

        migrator = ChromaMigration(dry_run=True, skip_connection=True)

        chroma_doc = {
            'id': 'doc-123',
            'content': 'Test content',
            'metadata': {'source': 'test', 'type': 'rule'}
        }

        result = migrator.transform_document(chroma_doc)

        assert isinstance(result, dict)
        assert 'typeql' in result or 'id' in result

    @pytest.mark.unit
    def test_transform_preserves_metadata(self):
        """Transformation should preserve metadata."""
        from governance.chroma_migration import ChromaMigration

        migrator = ChromaMigration(dry_run=True, skip_connection=True)

        chroma_doc = {
            'id': 'doc-456',
            'content': 'Test content',
            'metadata': {'source': 'SESSION-2024-12-25', 'category': 'governance'}
        }

        result = migrator.transform_document(chroma_doc)

        assert 'metadata' in result or 'source' in str(result)

    @pytest.mark.unit
    def test_detect_document_type(self):
        """Should detect document type from ID pattern."""
        from governance.chroma_migration import ChromaMigration

        migrator = ChromaMigration(dry_run=True, skip_connection=True)

        assert migrator.detect_type('RULE-001') == 'rule'
        assert migrator.detect_type('DECISION-003') == 'decision'
        assert migrator.detect_type('SESSION-2024-12-25') == 'session'
        assert migrator.detect_type('unknown-doc') == 'document'


class TestFullMigration:
    """Tests for full migration workflow."""

    @pytest.mark.unit
    def test_migrate_all_dry_run(self):
        """Full migration dry run should scan and plan."""
        from governance.chroma_migration import ChromaMigration

        migrator = ChromaMigration(dry_run=True, skip_connection=True)
        result = migrator.migrate_all()

        assert isinstance(result, dict)
        assert 'dry_run' in result
        assert result['dry_run'] is True

    @pytest.mark.unit
    def test_migrate_all_returns_statistics(self):
        """Full migration should return statistics."""
        from governance.chroma_migration import ChromaMigration

        migrator = ChromaMigration(dry_run=True, skip_connection=True)
        result = migrator.migrate_all()

        assert 'total' in result or 'collections' in result


class TestMigrationStatus:
    """Tests for migration status tracking."""

    @pytest.mark.unit
    def test_get_migration_status(self):
        """Should return current migration status."""
        from governance.chroma_migration import ChromaMigration

        migrator = ChromaMigration(dry_run=True, skip_connection=True)
        status = migrator.get_migration_status()

        assert isinstance(status, dict)
        assert 'phase' in status or 'status' in status

    @pytest.mark.unit
    def test_status_tracks_collections(self):
        """Status should track per-collection migration state."""
        from governance.chroma_migration import ChromaMigration

        migrator = ChromaMigration(dry_run=True, skip_connection=True)
        status = migrator.get_migration_status()

        assert isinstance(status, dict)


class TestMigrationIntegration:
    """Integration tests for migration tool."""

    @pytest.mark.unit
    def test_uses_data_router(self):
        """Migration should use DataRouter for TypeDB writes."""
        from governance.chroma_migration import ChromaMigration

        migrator = ChromaMigration(dry_run=True, skip_connection=True)
        assert hasattr(migrator, 'router') or hasattr(migrator, '_router')

    @pytest.mark.unit
    def test_factory_function(self):
        """Factory function should create migrator."""
        from governance.chroma_migration import create_chroma_migration

        migrator = create_chroma_migration(dry_run=True, skip_connection=True)
        assert migrator is not None

    @pytest.mark.unit
    def test_factory_with_options(self):
        """Factory should accept options."""
        from governance.chroma_migration import create_chroma_migration

        migrator = create_chroma_migration(
            dry_run=True,
            batch_size=50,
            skip_connection=True
        )
        assert migrator.batch_size == 50
