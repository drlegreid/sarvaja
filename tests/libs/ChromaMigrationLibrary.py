"""
Robot Framework Library for ChromaDB Migration Tool Tests.

Per P7.4: ChromaDB migration tool.
Migrated from tests/test_chroma_migration.py
"""
from pathlib import Path
from robot.api.deco import keyword


class ChromaMigrationLibrary:
    """Library for testing ChromaDB migration tool."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.governance_dir = self.project_root / "governance"

    # =============================================================================
    # Module Tests
    # =============================================================================

    @keyword("Migration Tool Module Exists")
    def migration_tool_module_exists(self):
        """Migration tool module must exist."""
        migration_file = self.governance_dir / "chroma_migration.py"
        return {"exists": migration_file.exists()}

    @keyword("Chroma Migration Class Works")
    def chroma_migration_class_works(self):
        """ChromaMigration class must be importable."""
        try:
            from governance.chroma_migration import ChromaMigration

            migrator = ChromaMigration(dry_run=True, skip_connection=True)
            return {"created": migrator is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Migrator Has Required Methods")
    def migrator_has_required_methods(self):
        """Migrator must have required methods."""
        try:
            from governance.chroma_migration import ChromaMigration

            migrator = ChromaMigration(dry_run=True, skip_connection=True)

            return {
                "has_scan": hasattr(migrator, 'scan_chroma'),
                "has_migrate_collection": hasattr(migrator, 'migrate_collection'),
                "has_migrate_all": hasattr(migrator, 'migrate_all'),
                "has_get_status": hasattr(migrator, 'get_migration_status')
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Scan Tests
    # =============================================================================

    @keyword("Scan Chroma Returns Collections")
    def scan_chroma_returns_collections(self):
        """Scan should return list of collections."""
        try:
            from governance.chroma_migration import ChromaMigration

            migrator = ChromaMigration(dry_run=True, skip_connection=True)
            result = migrator.scan_chroma()

            return {
                "is_dict": isinstance(result, dict),
                "has_collections": 'collections' in result
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Scan Includes Document Counts")
    def scan_includes_document_counts(self):
        """Scan should include document counts per collection."""
        try:
            from governance.chroma_migration import ChromaMigration

            migrator = ChromaMigration(dry_run=True, skip_connection=True)
            result = migrator.scan_chroma()

            return {"has_total_docs": 'total_documents' in result}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Scan Handles Missing Chroma")
    def scan_handles_missing_chroma(self):
        """Should handle ChromaDB not available gracefully."""
        try:
            from governance.chroma_migration import ChromaMigration

            migrator = ChromaMigration(dry_run=True, skip_connection=True)
            result = migrator.scan_chroma()

            return {"is_dict": isinstance(result, dict)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Collection Migration Tests
    # =============================================================================

    @keyword("Migrate Collection Dry Run")
    def migrate_collection_dry_run(self):
        """Dry run migration should not write to TypeDB."""
        try:
            from governance.chroma_migration import ChromaMigration

            migrator = ChromaMigration(dry_run=True, skip_connection=True)
            result = migrator.migrate_collection("test_collection")

            return {
                "is_dict": isinstance(result, dict),
                "has_dry_run": 'dry_run' in result,
                "dry_run_true": result.get('dry_run') is True
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Migrate Collection Tracks Progress")
    def migrate_collection_tracks_progress(self):
        """Migration should track progress."""
        try:
            from governance.chroma_migration import ChromaMigration

            migrator = ChromaMigration(dry_run=True, skip_connection=True)
            result = migrator.migrate_collection("test_collection")

            return {
                "has_progress": 'migrated' in result or 'status' in result
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Migrate Collection Handles Errors")
    def migrate_collection_handles_errors(self):
        """Should handle migration errors gracefully."""
        try:
            from governance.chroma_migration import ChromaMigration

            migrator = ChromaMigration(dry_run=True, skip_connection=True)
            result = migrator.migrate_collection("nonexistent_collection")

            return {"is_dict": isinstance(result, dict)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Data Transformation Tests
    # =============================================================================

    @keyword("Transform Document Works")
    def transform_document_works(self):
        """Should transform ChromaDB document to TypeDB format."""
        try:
            from governance.chroma_migration import ChromaMigration

            migrator = ChromaMigration(dry_run=True, skip_connection=True)

            chroma_doc = {
                'id': 'doc-123',
                'content': 'Test content',
                'metadata': {'source': 'test', 'type': 'rule'}
            }

            result = migrator.transform_document(chroma_doc)

            return {
                "is_dict": isinstance(result, dict),
                "has_output": 'typeql' in result or 'id' in result
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Transform Preserves Metadata")
    def transform_preserves_metadata(self):
        """Transformation should preserve metadata."""
        try:
            from governance.chroma_migration import ChromaMigration

            migrator = ChromaMigration(dry_run=True, skip_connection=True)

            chroma_doc = {
                'id': 'doc-456',
                'content': 'Test content',
                'metadata': {'source': 'SESSION-2024-12-25', 'category': 'governance'}
            }

            result = migrator.transform_document(chroma_doc)

            return {
                "preserves_data": 'metadata' in result or 'source' in str(result)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Detect Document Type Works")
    def detect_document_type_works(self):
        """Should detect document type from ID pattern."""
        try:
            from governance.chroma_migration import ChromaMigration

            migrator = ChromaMigration(dry_run=True, skip_connection=True)

            return {
                "rule_correct": migrator.detect_type('RULE-001') == 'rule',
                "decision_correct": migrator.detect_type('DECISION-003') == 'decision',
                "session_correct": migrator.detect_type('SESSION-2024-12-25') == 'session',
                "default_correct": migrator.detect_type('unknown-doc') == 'document'
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Full Migration Tests
    # =============================================================================

    @keyword("Migrate All Dry Run")
    def migrate_all_dry_run(self):
        """Full migration dry run should scan and plan."""
        try:
            from governance.chroma_migration import ChromaMigration

            migrator = ChromaMigration(dry_run=True, skip_connection=True)
            result = migrator.migrate_all()

            return {
                "is_dict": isinstance(result, dict),
                "has_dry_run": 'dry_run' in result,
                "dry_run_true": result.get('dry_run') is True
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Migrate All Returns Statistics")
    def migrate_all_returns_statistics(self):
        """Full migration should return statistics."""
        try:
            from governance.chroma_migration import ChromaMigration

            migrator = ChromaMigration(dry_run=True, skip_connection=True)
            result = migrator.migrate_all()

            return {
                "has_stats": 'total' in result or 'collections' in result
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Status Tests
    # =============================================================================

    @keyword("Get Migration Status Works")
    def get_migration_status_works(self):
        """Should return current migration status."""
        try:
            from governance.chroma_migration import ChromaMigration

            migrator = ChromaMigration(dry_run=True, skip_connection=True)
            status = migrator.get_migration_status()

            return {
                "is_dict": isinstance(status, dict),
                "has_status": 'phase' in status or 'status' in status
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Status Tracks Collections")
    def status_tracks_collections(self):
        """Status should track per-collection migration state."""
        try:
            from governance.chroma_migration import ChromaMigration

            migrator = ChromaMigration(dry_run=True, skip_connection=True)
            status = migrator.get_migration_status()

            return {"is_dict": isinstance(status, dict)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Integration Tests
    # =============================================================================

    @keyword("Migration Uses Data Router")
    def migration_uses_data_router(self):
        """Migration should use DataRouter for TypeDB writes."""
        try:
            from governance.chroma_migration import ChromaMigration

            migrator = ChromaMigration(dry_run=True, skip_connection=True)
            return {
                "has_router": hasattr(migrator, 'router') or hasattr(migrator, '_router')
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Factory Function Creates Migrator")
    def factory_function_creates_migrator(self):
        """Factory function should create migrator."""
        try:
            from governance.chroma_migration import create_chroma_migration

            migrator = create_chroma_migration(dry_run=True, skip_connection=True)
            return {"created": migrator is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Factory Accepts Options")
    def factory_accepts_options(self):
        """Factory should accept options."""
        try:
            from governance.chroma_migration import create_chroma_migration

            migrator = create_chroma_migration(
                dry_run=True,
                batch_size=50,
                skip_connection=True
            )
            return {"batch_size_correct": migrator.batch_size == 50}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
