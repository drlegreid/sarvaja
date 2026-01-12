"""
Data Router Models
Created: 2024-12-25 (P7.3)
Modularized: 2026-01-02 (RULE-032)

Dataclasses for routing operations.
"""
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class RouteResult:
    """Result of a routing operation."""
    success: bool
    destination: str
    item_type: str
    item_id: str
    embedded: bool = False
    error: Optional[str] = None
    metadata: Optional[Dict] = None
    evidence_file: Optional[str] = None
