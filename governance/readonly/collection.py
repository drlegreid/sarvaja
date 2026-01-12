"""
Read-Only Collection Wrapper
Created: 2024-12-25 (P7.5)
Modularized: 2026-01-02 (RULE-032)

Provides collection-level operations with read-only enforcement.
"""
from typing import List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from governance.readonly.client import ChromaReadOnly


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
