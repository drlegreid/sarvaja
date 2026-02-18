"""
ChromaDB Scanner
Created: 2024-12-25 (P7.4)
Modularized: 2026-01-02 (RULE-032)

Scans ChromaDB for collections and documents.
"""
from typing import Dict, Any


class ChromaScanner:
    """Scans ChromaDB for collections and document counts."""

    def __init__(
        self,
        chroma_host: str = "localhost",
        chroma_port: int = 8001,
        skip_connection: bool = False
    ):
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self.skip_connection = skip_connection

    def scan(self) -> Dict[str, Any]:
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
                'error': type(e).__name__  # BUG-476-MSC-1: sanitize error info
            }
