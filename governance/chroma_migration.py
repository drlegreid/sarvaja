"""
ChromaDB Migration Tool (DEPRECATED - use governance.migration package)
Created: 2024-12-25 (P7.4)
Modularized: 2026-01-02 (RULE-032)

This file is kept for backward compatibility.
Import from governance.migration instead:

    from governance.migration import ChromaMigration, create_chroma_migration

Per DECISION-003: TypeDB-First Strategy
Per R&D-BACKLOG: P7.4 ChromaDB migration tool
Per RULE-032: Files >300 lines MUST be modularized.
"""
import warnings

# Re-export from modular package for backward compatibility
from governance.migration import (
    MigrationResult,
    ChromaScanner,
    DocumentTransformer,
    ChromaMigration,
    create_chroma_migration,
)

__all__ = [
    "MigrationResult",
    "ChromaScanner",
    "DocumentTransformer",
    "ChromaMigration",
    "create_chroma_migration",
]

# Emit deprecation warning on import
warnings.warn(
    "governance.chroma_migration is deprecated. "
    "Use 'from governance.migration import ChromaMigration' instead.",
    DeprecationWarning,
    stacklevel=2
)


def main():
    """CLI entry point (deprecated - use python -m governance.migration)."""
    from governance.migration.__main__ import main as _main
    _main()


if __name__ == "__main__":
    main()
