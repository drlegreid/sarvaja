"""
ChromaDB Read-Only Package
Created: 2024-12-25 (P7.5)
Modularized: 2026-01-02 (RULE-032)

Provides a ChromaDB-compatible interface that:
- Allows read operations (query, get, list)
- Deprecates write operations (add, update, delete)
- Redirects writes to TypeDB via DataRouter

Per DECISION-003: TypeDB-First Strategy
Per R&D-BACKLOG: P7.5 ChromaDB sunset (read-only)

Usage:
    from governance.readonly import create_readonly_client

    client = create_readonly_client()
    results = client.query("governance", "rule compliance")
    # Writes are deprecated and redirected to TypeDB
    client.add("rules", ["new rule"], ["RULE-099"])  # -> TypeDB
"""

from governance.readonly.models import DeprecationResult
from governance.readonly.collection import ReadOnlyCollection
from governance.readonly.client import ChromaReadOnly, create_readonly_client

__all__ = [
    "DeprecationResult",
    "ReadOnlyCollection",
    "ChromaReadOnly",
    "create_readonly_client",
]
