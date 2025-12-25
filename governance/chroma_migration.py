"""
ChromaDB Migration Tool (P7.4)
Created: 2024-12-25

Migrates existing ChromaDB data to TypeDB.
Supports: rules, decisions, sessions, and generic documents.

Per DECISION-003: TypeDB-First Strategy
Per R&D-BACKLOG: P7.4 ChromaDB migration tool

Usage:
    migrator = ChromaMigration(dry_run=True)
    result = migrator.migrate_all()
"""

import re
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict

from governance.data_router import DataRouter, create_data_router

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
EVIDENCE_DIR = PROJECT_ROOT / "evidence"


@dataclass
class MigrationResult:
    """Result of a migration operation."""
    success: bool
    collection: str
    migrated: int
    failed: int
    skipped: int
    dry_run: bool
    errors: List[str]


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

    # ID patterns for type detection
    RULE_PATTERN = re.compile(r'^RULE-\d{3}$')
    DECISION_PATTERN = re.compile(r'^DECISION-\d{3}$')
    SESSION_PATTERN = re.compile(r'^SESSION-\d{4}-\d{2}-\d{2}')

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

        # Initialize router for TypeDB writes
        self._router = create_data_router(dry_run=dry_run, embed=embed)

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

    # =========================================================================
    # CHROMA SCANNING
    # =========================================================================

    def scan_chroma(self) -> Dict[str, Any]:
        """
        Scan ChromaDB for collections and document counts.

        Returns:
            Dict with collections and document counts
        """
        # Skip connection for testing
        if self.skip_connection:
            return {
                'collections': [],
                'total_documents': 0,
                'chroma_host': self.chroma_host,
                'chroma_port': self.chroma_port,
                'skipped': True
            }

        try:
            import chromadb

            client = chromadb.HttpClient(
                host=self.chroma_host,
                port=self.chroma_port
            )

            collections_info = []
            total_docs = 0

            for collection in client.list_collections():
                count = collection.count()
                collections_info.append({
                    'name': collection.name,
                    'count': count
                })
                total_docs += count

            return {
                'collections': collections_info,
                'total_documents': total_docs,
                'chroma_host': self.chroma_host,
                'chroma_port': self.chroma_port
            }

        except ImportError:
            return {
                'collections': [],
                'total_documents': 0,
                'error': 'chromadb not installed'
            }
        except Exception as e:
            return {
                'collections': [],
                'total_documents': 0,
                'error': str(e)
            }

    # =========================================================================
    # DOCUMENT TRANSFORMATION
    # =========================================================================

    def detect_type(self, doc_id: str) -> str:
        """
        Detect document type from ID pattern.

        Args:
            doc_id: Document ID

        Returns:
            Type string: 'rule', 'decision', 'session', or 'document'
        """
        if self.RULE_PATTERN.match(doc_id):
            return 'rule'
        elif self.DECISION_PATTERN.match(doc_id):
            return 'decision'
        elif self.SESSION_PATTERN.match(doc_id):
            return 'session'
        else:
            return 'document'

    def transform_document(self, chroma_doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform ChromaDB document to TypeDB format.

        Args:
            chroma_doc: ChromaDB document dict

        Returns:
            Transformed document for TypeDB
        """
        doc_id = chroma_doc.get('id', 'unknown')
        content = chroma_doc.get('content', chroma_doc.get('document', ''))
        metadata = chroma_doc.get('metadata', {})
        doc_type = self.detect_type(doc_id)

        result = {
            'id': doc_id,
            'content': content,
            'type': doc_type,
            'metadata': metadata,
            'source': 'chromadb_migration'
        }

        # Generate TypeQL based on type
        if doc_type == 'rule':
            result['typeql'] = self._generate_rule_typeql(doc_id, content, metadata)
        elif doc_type == 'decision':
            result['typeql'] = self._generate_decision_typeql(doc_id, content, metadata)
        elif doc_type == 'session':
            result['typeql'] = self._generate_session_typeql(doc_id, content, metadata)
        else:
            result['typeql'] = self._generate_document_typeql(doc_id, content, metadata)

        return result

    def _generate_rule_typeql(
        self,
        rule_id: str,
        content: str,
        metadata: Dict
    ) -> str:
        """Generate TypeQL for rule."""
        name = metadata.get('name', content[:50] if content else 'Migrated Rule')
        directive = metadata.get('directive', content)
        return f'''
            insert $r isa rule-entity,
                has id "{self._escape(rule_id)}",
                has name "{self._escape(name)}",
                has directive "{self._escape(directive)}",
                has category "migrated",
                has priority "MEDIUM",
                has status "ACTIVE",
                has created-date {datetime.now().isoformat()};
        '''

    def _generate_decision_typeql(
        self,
        decision_id: str,
        content: str,
        metadata: Dict
    ) -> str:
        """Generate TypeQL for decision."""
        name = metadata.get('name', content[:50] if content else 'Migrated Decision')
        return f'''
            insert $d isa decision,
                has decision-id "{self._escape(decision_id)}",
                has decision-name "{self._escape(name)}",
                has decision-context "{self._escape(content[:500] if content else '')}",
                has decision-status "ACTIVE",
                has decision-date {datetime.now().isoformat()};
        '''

    def _generate_session_typeql(
        self,
        session_id: str,
        content: str,
        metadata: Dict
    ) -> str:
        """Generate TypeQL for session."""
        # Sessions are primarily stored as embeddings, not in TypeDB directly
        return f'''
            # Session {session_id} - stored as embedding
            # Content length: {len(content)} chars
        '''

    def _generate_document_typeql(
        self,
        doc_id: str,
        content: str,
        metadata: Dict
    ) -> str:
        """Generate TypeQL for generic document."""
        return f'''
            insert $doc isa vector-document,
                has id "{self._escape(doc_id)}",
                has content "{self._escape(content[:1000] if content else '')}",
                has source-type "migrated",
                has source "{self._escape(metadata.get('source', 'chromadb'))}",
                has created-date {datetime.now().isoformat()};
        '''

    @staticmethod
    def _escape(text: str) -> str:
        """Escape text for TypeQL string literals."""
        if not text:
            return ""
        return text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')

    # =========================================================================
    # COLLECTION MIGRATION
    # =========================================================================

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

                    transformed = self.transform_document(chroma_doc)
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

    # =========================================================================
    # FULL MIGRATION
    # =========================================================================

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

    # =========================================================================
    # STATUS TRACKING
    # =========================================================================

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


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

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


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI for ChromaDB migration."""
    import argparse

    parser = argparse.ArgumentParser(description="ChromaDB Migration Tool")
    parser.add_argument("command", choices=["scan", "migrate", "status"])
    parser.add_argument("--collection", "-c", help="Specific collection to migrate")
    parser.add_argument("--dry-run", "-n", action="store_true", default=True)
    parser.add_argument("--execute", "-x", action="store_true", help="Actually execute migration")
    args = parser.parse_args()

    dry_run = not args.execute
    migrator = create_chroma_migration(dry_run=dry_run)

    if args.command == "scan":
        result = migrator.scan_chroma()
        print(json.dumps(result, indent=2))

    elif args.command == "migrate":
        if args.collection:
            result = migrator.migrate_collection(args.collection)
        else:
            result = migrator.migrate_all()
        print(json.dumps(result, indent=2))

    elif args.command == "status":
        result = migrator.get_migration_status()
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
