"""
Migration Data Models
Created: 2024-12-25 (P7.4)
Modularized: 2026-01-02 (RULE-032)

Dataclasses for migration results and state.
"""
from typing import List
from dataclasses import dataclass


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
