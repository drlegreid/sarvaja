"""
ChromaDB Read-Only Wrapper (DEPRECATED - use governance.readonly package)
Created: 2024-12-25 (P7.5)
Modularized: 2026-01-02 (RULE-032)

This file is kept for backward compatibility.
Import from governance.readonly instead:

    from governance.readonly import ChromaReadOnly, create_readonly_client

Per DECISION-003: TypeDB-First Strategy
Per R&D-BACKLOG: P7.5 ChromaDB sunset (read-only)
Per RULE-032: Files >300 lines MUST be modularized.
"""
import warnings

# Re-export from modular package for backward compatibility
from governance.readonly import (
    DeprecationResult,
    ReadOnlyCollection,
    ChromaReadOnly,
    create_readonly_client,
)

__all__ = [
    "DeprecationResult",
    "ReadOnlyCollection",
    "ChromaReadOnly",
    "create_readonly_client",
]

# Emit deprecation warning on import
warnings.warn(
    "governance.chroma_readonly is deprecated. "
    "Use 'from governance.readonly import ChromaReadOnly' instead.",
    DeprecationWarning,
    stacklevel=2
)


def main():
    """CLI entry point (deprecated - use python -m governance.readonly)."""
    from governance.readonly.__main__ import main as _main
    _main()


if __name__ == "__main__":
    main()
