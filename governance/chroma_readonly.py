"""
ChromaDB Read-Only Wrapper (P7.5)
Created: 2024-12-25

Provides a ChromaDB-compatible interface that:
- Allows read operations (query, get, list)
- Deprecates write operations (add, update, delete)
- Redirects writes to TypeDB via DataRouter

Per DECISION-003: TypeDB-First Strategy
Per R&D-BACKLOG: P7.5 ChromaDB sunset (read-only)

Usage:
    from governance.chroma_readonly import create_readonly_client

    client = create_readonly_client()
    results = client.query("governance", "rule compliance")
    # Writes are deprecated and redirected to TypeDB
    client.add("rules", ["new rule"], ["RULE-099"])  # -> TypeDB
"""

import re
import json
import warnings
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from dataclasses import dataclass, asdict

from governance.data_router import DataRouter, create_data_router

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent


@dataclass
class DeprecationResult:
    """Result of a deprecated operation."""
    deprecated: bool = True
    operation: str = ""
    redirected: bool = False
    typedb_result: Optional[Dict] = None
    message: str = ""


class ReadOnlyCollection:
    """
    Read-only collection wrapper.

    Provides collection-level operations with read-only enforcement.
    """

    def __init__(
        self,
        name: str,
        parent: 'ChromaReadOnly'
    ):
        self.name = name
        self._parent = parent

    def query(
        self,
        query_texts: List[str] = None,
        n_results: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """Query the collection (allowed)."""
        return self._parent.query(
            collection=self.name,
            query_text=query_texts[0] if query_texts else "",
            n_results=n_results,
            **kwargs
        )

    def get(
        self,
        ids: List[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Get documents by ID (allowed)."""
        return self._parent.get(
            collection=self.name,
            ids=ids or [],
            **kwargs
        )

    def add(
        self,
        documents: List[str] = None,
        ids: List[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Add documents (DEPRECATED - redirects to TypeDB)."""
        return self._parent.add(
            collection=self.name,
            documents=documents or [],
            ids=ids or [],
            **kwargs
        )

    def update(
        self,
        documents: List[str] = None,
        ids: List[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Update documents (DEPRECATED - redirects to TypeDB)."""
        return self._parent.update(
            collection=self.name,
            documents=documents or [],
            ids=ids or [],
            **kwargs
        )

    def delete(
        self,
        ids: List[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Delete documents (DEPRECATED)."""
        return self._parent.delete(
            collection=self.name,
            ids=ids or [],
            **kwargs
        )


class ChromaReadOnly:
    """
    ChromaDB Read-Only Wrapper.

    Provides ChromaDB-compatible interface while:
    - Allowing all read operations
    - Deprecating and redirecting write operations to TypeDB
    - Logging deprecation warnings

    Example:
        client = ChromaReadOnly()
        results = client.query("governance", "rule compliance")

        # Deprecated but redirects to TypeDB:
        client.add("rules", ["new rule"], ["RULE-099"])
    """

    # ID patterns for type detection
    RULE_PATTERN = re.compile(r'^RULE-\d{3}$')
    DECISION_PATTERN = re.compile(r'^DECISION-\d{3}$')
    SESSION_PATTERN = re.compile(r'^SESSION-\d{4}-\d{2}-\d{2}')

    def __init__(
        self,
        chroma_host: str = "localhost",
        chroma_port: int = 8001,
        log_deprecations: bool = True,
        skip_connection: bool = False
    ):
        """
        Initialize ChromaDB Read-Only Wrapper.

        Args:
            chroma_host: ChromaDB host
            chroma_port: ChromaDB port
            log_deprecations: Log deprecation warnings
            skip_connection: Skip actual ChromaDB connection (for testing)
        """
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
            except Exception:
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

    # =========================================================================
    # READ OPERATIONS (Allowed)
    # =========================================================================

    def query(
        self,
        collection: str,
        query_text: str,
        n_results: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Query a collection (allowed).

        Args:
            collection: Collection name
            query_text: Query text
            n_results: Number of results
            **kwargs: Additional query parameters

        Returns:
            Query results
        """
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
            return {'error': str(e)}

    def get(
        self,
        collection: str,
        ids: List[str],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get documents by ID (allowed).

        Args:
            collection: Collection name
            ids: Document IDs
            **kwargs: Additional parameters

        Returns:
            Documents
        """
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
            return {'error': str(e)}

    def list_collections(self) -> List[str]:
        """
        List all collections (allowed).

        Returns:
            List of collection names
        """
        if self.skip_connection:
            return []

        try:
            client = self._get_client()
            if client is None:
                return []

            return [c.name for c in client.list_collections()]

        except Exception:
            return []

    def get_collection(self, name: str) -> ReadOnlyCollection:
        """
        Get a collection wrapper (allowed).

        Args:
            name: Collection name

        Returns:
            ReadOnlyCollection wrapper
        """
        return ReadOnlyCollection(name, self)

    # =========================================================================
    # WRITE OPERATIONS (Deprecated, Redirect to TypeDB)
    # =========================================================================

    def add(
        self,
        collection: str,
        documents: List[str],
        ids: List[str],
        metadatas: List[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Add documents (DEPRECATED - redirects to TypeDB).

        Args:
            collection: Collection name
            documents: Documents to add
            ids: Document IDs
            metadatas: Optional metadata
            **kwargs: Additional parameters

        Returns:
            Deprecation result with redirect info
        """
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
                results.append({'success': False, 'error': str(e)})

        return asdict(DeprecationResult(
            deprecated=True,
            operation='add',
            redirected=True,
            typedb_result={'results': results},
            message=f"Redirected {len(ids)} documents to TypeDB"
        ))

    def update(
        self,
        collection: str,
        documents: List[str],
        ids: List[str],
        metadatas: List[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Update documents (DEPRECATED - redirects to TypeDB).

        Args:
            collection: Collection name
            documents: Updated documents
            ids: Document IDs
            metadatas: Optional metadata
            **kwargs: Additional parameters

        Returns:
            Deprecation result
        """
        self._log_deprecation(
            "update",
            f"Updating {len(documents)} documents in {collection}"
        )

        # For updates, we re-route as adds (TypeDB handles upsert)
        return self.add(collection, documents, ids, metadatas, **kwargs)

    def delete(
        self,
        collection: str,
        ids: List[str],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Delete documents (DEPRECATED - not redirected).

        Note: Delete operations are logged but not redirected to TypeDB.
        TypeDB deletions should be handled explicitly through governance tools.

        Args:
            collection: Collection name
            ids: Document IDs to delete
            **kwargs: Additional parameters

        Returns:
            Deprecation result
        """
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

    # =========================================================================
    # STATUS
    # =========================================================================

    def get_deprecation_status(self) -> Dict[str, Any]:
        """
        Get deprecation status.

        Returns:
            Status dict with deprecation info
        """
        return {
            'writes_deprecated': True,
            'reads_allowed': True,
            'redirect_target': 'typedb',
            'deprecation_date': '2024-12-25',
            'sunset_planned': True,
            'message': 'ChromaDB writes are deprecated. Use TypeDB via DataRouter.'
        }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_readonly_client(
    skip_connection: bool = False,
    log_deprecations: bool = True,
    **kwargs
) -> ChromaReadOnly:
    """
    Factory function to create read-only ChromaDB client.

    Args:
        skip_connection: Skip actual ChromaDB connection
        log_deprecations: Log deprecation warnings
        **kwargs: Additional options

    Returns:
        ChromaReadOnly instance
    """
    return ChromaReadOnly(
        skip_connection=skip_connection,
        log_deprecations=log_deprecations,
        **kwargs
    )


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI for read-only wrapper."""
    import argparse

    parser = argparse.ArgumentParser(description="ChromaDB Read-Only Wrapper")
    parser.add_argument("command", choices=["query", "get", "list", "status"])
    parser.add_argument("--collection", "-c", help="Collection name")
    parser.add_argument("--query", "-q", help="Query text")
    parser.add_argument("--ids", nargs="+", help="Document IDs")
    args = parser.parse_args()

    client = create_readonly_client()

    if args.command == "query" and args.collection and args.query:
        result = client.query(args.collection, args.query)
        print(json.dumps(result, indent=2))

    elif args.command == "get" and args.collection and args.ids:
        result = client.get(args.collection, args.ids)
        print(json.dumps(result, indent=2))

    elif args.command == "list":
        result = client.list_collections()
        print(json.dumps(result, indent=2))

    elif args.command == "status":
        result = client.get_deprecation_status()
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
