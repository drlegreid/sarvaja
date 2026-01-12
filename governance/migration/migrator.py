"""
ChromaDB Migrator
Created: 2024-12-25 (P7.4)
Modularized: 2026-01-02 (RULE-032)

Main migration logic for ChromaDB to TypeDB.
"""
from typing import Dict, Any, List
from datetime import datetime
from dataclasses import asdict
from pathlib import Path

from governance.data_router import DataRouter, create_data_router
from governance.migration.models import MigrationResult
from governance.migration.scanner import ChromaScanner
from governance.migration.transformer import DocumentTransformer

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
EVIDENCE_DIR = PROJECT_ROOT / "evidence"


class ChromaMigration:
    """
    Migrates ChromaDB data to TypeDB.

    Features:
    - Scans ChromaDB collections
    - Transforms documents to TypeDB format
    - Uses DataRouter for TypeDB writes
    - Tracks migration progress
    - Supports dry run mode

    Example:
        migrator = ChromaMigration(dry_run=True)
        scan = migrator.scan_chroma()
        print(f"Found {scan['total_documents']} documents")
        result = migrator.migrate_all()
    """

    def __init__(
        self,
        dry_run: bool = True,
        chroma_host: str = "localhost",
        chroma_port: int = 8001,
        batch_size: int = 100,
        embed: bool = True,
        skip_connection: bool = False
    ):
        """
        Initialize ChromaDB Migration tool.

        Args:
            dry_run: If True, don't write to TypeDB
            chroma_host: ChromaDB host
            chroma_port: ChromaDB port
            batch_size: Documents per batch
            embed: Generate embeddings during migration
            skip_connection: Skip actual ChromaDB connection (for testing)
        """
        self.dry_run = dry_run
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self.batch_size = batch_size
        self.embed = embed
        self.skip_connection = skip_connection

        # Initialize components
        self._router = create_data_router(dry_run=dry_run, embed=embed)
        self._scanner = ChromaScanner(chroma_host, chroma_port, skip_connection)
        self._transformer = DocumentTransformer()

        # Track migration state
        self._migration_state: Dict[str, Any] = {
            'phase': 'idle',
            'started': None,
            'completed': None,
            'collections': {}
        }

    @property
    def router(self) -> DataRouter:
        """Get the data router."""
        return self._router

    def scan_chroma(self) -> Dict[str, Any]:
        """Scan ChromaDB for collections and document counts."""
        return self._scanner.scan()

    def transform_document(self, chroma_doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform ChromaDB document to TypeDB format (delegates to transformer).

        Args:
            chroma_doc: ChromaDB document dict

        Returns:
            Transformed document for TypeDB
        """
        return self._transformer.transform(chroma_doc)

    def detect_type(self, doc_id: str) -> str:
        """
        Detect document type from ID pattern (delegates to transformer).

        Args:
            doc_id: Document ID

        Returns:
            Type string: 'rule', 'decision', 'session', or 'document'
        """
        return self._transformer.detect_type(doc_id)

    def migrate_collection(self, collection_name: str) -> Dict[str, Any]:
        """
        Migrate a single ChromaDB collection to TypeDB.

        Args:
            collection_name: Name of collection to migrate

        Returns:
            Migration result dict
        """
        migrated = 0
        failed = 0
        skipped = 0
        errors: List[str] = []

        self._migration_state['phase'] = 'migrating'
        self._migration_state['collections'][collection_name] = {
            'status': 'in_progress',
            'started': datetime.now().isoformat()
        }

        try:
            if self.dry_run:
                # Dry run - just scan and count
                scan = self.scan_chroma()
                for coll in scan.get('collections', []):
                    if coll['name'] == collection_name:
                        migrated = coll['count']
                        break

                return asdict(MigrationResult(
                    success=True,
                    collection=collection_name,
                    migrated=migrated,
                    failed=0,
                    skipped=0,
                    dry_run=True,
                    errors=[]
                ))

            # Real migration
            import chromadb

            client = chromadb.HttpClient(
                host=self.chroma_host,
                port=self.chroma_port
            )

            collection = client.get_collection(collection_name)
            docs = collection.get(include=['documents', 'metadatas'])

            for i, doc_id in enumerate(docs['ids']):
                try:
                    chroma_doc = {
                        'id': doc_id,
                        'content': docs['documents'][i] if docs.get('documents') else '',
                        'metadata': docs['metadatas'][i] if docs.get('metadatas') else {}
                    }

                    transformed = self._transformer.transform(chroma_doc)
                    doc_type = transformed['type']

                    # Route to TypeDB using DataRouter
                    if doc_type == 'rule':
                        result = self._router.route_rule(
                            rule_id=doc_id,
                            name=transformed['metadata'].get('name', doc_id),
                            directive=transformed['content']
                        )
                    elif doc_type == 'decision':
                        result = self._router.route_decision(
                            decision_id=doc_id,
                            name=transformed['metadata'].get('name', doc_id),
                            context=transformed['content']
                        )
                    elif doc_type == 'session':
                        result = self._router.route_session(
                            session_id=doc_id,
                            content=transformed['content']
                        )
                    else:
                        # Skip generic documents for now
                        skipped += 1
                        continue

                    if result.get('success'):
                        migrated += 1
                    else:
                        failed += 1
                        errors.append(result.get('error', 'Unknown error'))

                except Exception as e:
                    failed += 1
                    errors.append(f"{doc_id}: {str(e)}")

            self._migration_state['collections'][collection_name] = {
                'status': 'completed',
                'migrated': migrated,
                'failed': failed
            }

            return asdict(MigrationResult(
                success=failed == 0,
                collection=collection_name,
                migrated=migrated,
                failed=failed,
                skipped=skipped,
                dry_run=False,
                errors=errors[:10]  # Limit error list
            ))

        except ImportError:
            return asdict(MigrationResult(
                success=False,
                collection=collection_name,
                migrated=0,
                failed=0,
                skipped=0,
                dry_run=self.dry_run,
                errors=['chromadb not installed']
            ))
        except Exception as e:
            return asdict(MigrationResult(
                success=False,
                collection=collection_name,
                migrated=migrated,
                failed=failed + 1,
                skipped=skipped,
                dry_run=self.dry_run,
                errors=[str(e)]
            ))

    def migrate_all(self) -> Dict[str, Any]:
        """
        Migrate all ChromaDB collections to TypeDB.

        Returns:
            Full migration result dict
        """
        self._migration_state['phase'] = 'scanning'
        self._migration_state['started'] = datetime.now().isoformat()

        # Scan ChromaDB
        scan = self.scan_chroma()

        if 'error' in scan:
            return {
                'success': False,
                'dry_run': self.dry_run,
                'error': scan['error'],
                'total': 0,
                'collections': []
            }

        total_migrated = 0
        total_failed = 0
        collection_results = []

        for coll_info in scan.get('collections', []):
            coll_name = coll_info['name']
            result = self.migrate_collection(coll_name)
            collection_results.append(result)
            total_migrated += result.get('migrated', 0)
            total_failed += result.get('failed', 0)

        self._migration_state['phase'] = 'completed'
        self._migration_state['completed'] = datetime.now().isoformat()

        return {
            'success': total_failed == 0,
            'dry_run': self.dry_run,
            'total': total_migrated,
            'failed': total_failed,
            'collections': collection_results
        }

    def get_migration_status(self) -> Dict[str, Any]:
        """
        Get current migration status.

        Returns:
            Status dict with phase and collection states
        """
        return {
            'phase': self._migration_state['phase'],
            'started': self._migration_state.get('started'),
            'completed': self._migration_state.get('completed'),
            'collections': self._migration_state.get('collections', {}),
            'dry_run': self.dry_run
        }


def create_chroma_migration(
    dry_run: bool = True,
    batch_size: int = 100,
    **kwargs
) -> ChromaMigration:
    """
    Factory function to create ChromaDB migrator.

    Args:
        dry_run: Don't write to TypeDB
        batch_size: Documents per batch
        **kwargs: Additional options

    Returns:
        ChromaMigration instance
    """
    return ChromaMigration(dry_run=dry_run, batch_size=batch_size, **kwargs)
