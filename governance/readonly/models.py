"""
Read-Only Data Models
Created: 2024-12-25 (P7.5)
Modularized: 2026-01-02 (RULE-032)

Dataclasses for deprecation results.
"""
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class DeprecationResult:
    """Result of a deprecated operation."""
    deprecated: bool = True
    operation: str = ""
    redirected: bool = False
    typedb_result: Optional[Dict] = None
    message: str = ""
