"""
ChromaDB Migration Package
Created: 2024-12-25 (P7.4)
Modularized: 2026-01-02 (RULE-032)

Migrates existing ChromaDB data to TypeDB.
Supports: rules, decisions, sessions, and generic documents.

Per DECISION-003: TypeDB-First Strategy
Per R&D-BACKLOG: P7.4 ChromaDB migration tool

Usage:
    from governance.migration import ChromaMigration, create_chroma_migration

    migrator = create_chroma_migration(dry_run=True)
    result = migrator.migrate_all()
"""

from governance.migration.models import MigrationResult
from governance.migration.scanner import ChromaScanner
from governance.migration.transformer import DocumentTransformer
from governance.migration.migrator import ChromaMigration, create_chroma_migration

__all__ = [
    "MigrationResult",
    "ChromaScanner",
    "DocumentTransformer",
    "ChromaMigration",
    "create_chroma_migration",
]
