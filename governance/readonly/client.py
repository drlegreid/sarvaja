"""ChromaDB Read-Only Client. Redirects writes to TypeDB. Created: 2024-12-25."""
import logging
import re
import warnings
from typing import Dict, Any, List

logger = logging.getLogger(__name__)
from dataclasses import asdict

from governance.data_router import DataRouter, create_data_router
from governance.readonly.models import DeprecationResult
from governance.readonly.collection import ReadOnlyCollection

class ChromaReadOnly:
    """ChromaDB wrapper: reads allowed, writes deprecated and redirected to TypeDB."""

    # ID patterns for type detection
    RULE_PATTERN = re.compile(r'^RULE-\d{3}$')
    DECISION_PATTERN = re.compile(r'^DECISION-\d{3}$')
    SESSION_PATTERN = re.compile(r'^SESSION-\d{4}-\d{2}-\d{2}')

    def __init__(self, chroma_host: str = "localhost", chroma_port: int = 8001,
                 log_deprecations: bool = True, skip_connection: bool = False):
        """Initialize ChromaDB Read-Only Wrapper."""
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self.log_deprecations = log_deprecations
        self.skip_connection = skip_connection

        # Initialize router for TypeDB redirects
        self._router = create_data_router(dry_run=skip_connection, embed=True)

        # ChromaDB client (lazy loaded)
        self._client = None

    @property
    def router(self) -> DataRouter:
        """Get the data router."""
        return self._router

    def _get_client(self):
        """Get or create ChromaDB client."""
        if self.skip_connection:
            return None

        if self._client is None:
            try:
                import chromadb
                self._client = chromadb.HttpClient(
                    host=self.chroma_host,
                    port=self.chroma_port
                )
            except ImportError:
                return None
            except Exception as e:
                # BUG-477-RCL-1: Sanitize debug/info logger
                logger.debug(f"ChromaDB connection failed: {type(e).__name__}")
                return None

        return self._client

    def _log_deprecation(self, operation: str, message: str):
        """Log deprecation warning."""
        if self.log_deprecations:
            warnings.warn(
                f"ChromaDB {operation} is deprecated: {message}. "
                f"Use TypeDB via DataRouter instead.",
                DeprecationWarning,
                stacklevel=3
            )

    def _detect_type(self, doc_id: str) -> str:
        """Detect document type from ID pattern."""
        if self.RULE_PATTERN.match(doc_id):
            return 'rule'
        elif self.DECISION_PATTERN.match(doc_id):
            return 'decision'
        elif self.SESSION_PATTERN.match(doc_id):
            return 'session'
        else:
            return 'document'

    def query(self, collection: str, query_text: str, n_results: int = 10,
              **kwargs) -> Dict[str, Any]:
        """Query a collection (allowed)."""
        if self.skip_connection:
            return {
                'ids': [],
                'documents': [],
                'metadatas': [],
                'distances': []
            }

        try:
            client = self._get_client()
            if client is None:
                return {'error': 'ChromaDB not available'}

            coll = client.get_collection(collection)
            results = coll.query(
                query_texts=[query_text],
                n_results=n_results,
                **kwargs
            )

            return {
                'ids': results.get('ids', [[]])[0],
                'documents': results.get('documents', [[]])[0],
                'metadatas': results.get('metadatas', [[]])[0],
                'distances': results.get('distances', [[]])[0]
            }

        except Exception as e:
            logger.warning(f"ChromaDB query failed: {type(e).__name__}", exc_info=True)
            return {'error': type(e).__name__}  # BUG-476-RCL-1

    def get(self, collection: str, ids: List[str], **kwargs) -> Dict[str, Any]:
        """Get documents by ID (allowed)."""
        if self.skip_connection:
            return {
                'ids': ids,
                'documents': [],
                'metadatas': []
            }

        try:
            client = self._get_client()
            if client is None:
                return {'error': 'ChromaDB not available'}

            coll = client.get_collection(collection)
            results = coll.get(ids=ids, **kwargs)

            return results

        except Exception as e:
            logger.warning(f"ChromaDB get failed: {type(e).__name__}", exc_info=True)
            return {'error': type(e).__name__}  # BUG-476-RCL-2

    def list_collections(self) -> List[str]:
        """List all collections (allowed)."""
        if self.skip_connection:
            return []

        try:
            client = self._get_client()
            if client is None:
                return []

            return [c.name for c in client.list_collections()]

        except Exception as e:
            # BUG-477-RCL-2: Sanitize debug/info logger
            logger.debug(f"Failed to list ChromaDB collections: {type(e).__name__}")
            return []

    def get_collection(self, name: str) -> ReadOnlyCollection:
        """Get a collection wrapper (allowed)."""
        return ReadOnlyCollection(name, self)

    def add(self, collection: str, documents: List[str], ids: List[str],
            metadatas: List[Dict] = None, **kwargs) -> Dict[str, Any]:
        """Add documents (DEPRECATED - redirects to TypeDB)."""
        self._log_deprecation(
            "add",
            f"Adding {len(documents)} documents to {collection}"
        )

        # Redirect to TypeDB via DataRouter
        results = []
        for i, doc_id in enumerate(ids):
            doc_type = self._detect_type(doc_id)
            content = documents[i] if i < len(documents) else ""
            metadata = metadatas[i] if metadatas and i < len(metadatas) else {}

            try:
                if doc_type == 'rule':
                    result = self._router.route_rule(
                        rule_id=doc_id,
                        name=metadata.get('name', doc_id),
                        directive=content
                    )
                elif doc_type == 'decision':
                    result = self._router.route_decision(
                        decision_id=doc_id,
                        name=metadata.get('name', doc_id),
                        context=content
                    )
                elif doc_type == 'session':
                    result = self._router.route_session(
                        session_id=doc_id,
                        content=content
                    )
                else:
                    result = {'success': True, 'skipped': True, 'type': 'generic'}

                results.append(result)

            except Exception as e:
                logger.warning(f"ChromaDB add redirect failed: {type(e).__name__}", exc_info=True)
                results.append({'success': False, 'error': type(e).__name__})  # BUG-476-RCL-3

        return asdict(DeprecationResult(
            deprecated=True,
            operation='add',
            redirected=True,
            typedb_result={'results': results},
            message=f"Redirected {len(ids)} documents to TypeDB"
        ))

    def update(self, collection: str, documents: List[str], ids: List[str],
               metadatas: List[Dict] = None, **kwargs) -> Dict[str, Any]:
        """Update documents (DEPRECATED - redirects to TypeDB)."""
        self._log_deprecation(
            "update",
            f"Updating {len(documents)} documents in {collection}"
        )

        # For updates, we re-route as adds (TypeDB handles upsert)
        return self.add(collection, documents, ids, metadatas, **kwargs)

    def delete(self, collection: str, ids: List[str], **kwargs) -> Dict[str, Any]:
        """Delete documents (DEPRECATED - logged but not redirected)."""
        self._log_deprecation(
            "delete",
            f"Deleting {len(ids)} documents from {collection}"
        )

        return asdict(DeprecationResult(
            deprecated=True,
            operation='delete',
            redirected=False,
            typedb_result=None,
            message=f"Delete of {len(ids)} documents not executed. "
                    f"Use governance tools for TypeDB deletions."
        ))

    def get_deprecation_status(self) -> Dict[str, Any]:
        """Get deprecation status."""
        return {
            'writes_deprecated': True,
            'reads_allowed': True,
            'redirect_target': 'typedb',
            'deprecation_date': '2024-12-25',
            'sunset_planned': True,
            'message': 'ChromaDB writes are deprecated. Use TypeDB via DataRouter.'
        }

def create_readonly_client(skip_connection: bool = False, log_deprecations: bool = True,
                           **kwargs) -> ChromaReadOnly:
    """Factory function to create read-only ChromaDB client."""
    return ChromaReadOnly(
        skip_connection=skip_connection,
        log_deprecations=log_deprecations,
        **kwargs
    )
