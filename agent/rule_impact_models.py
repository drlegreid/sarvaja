"""
Rule Impact Analyzer Models.

Per DOC-SIZE-01-v1: Extracted from rule_impact.py (549 lines).
Dataclasses for impact analysis results and graph structures.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class ImpactResult:
    """Result of impact analysis."""
    rule_id: str
    change_type: str
    affected: List[str]
    impact_score: float
    warnings: List[str]


@dataclass
class GraphNode:
    """Node in dependency graph."""
    rule_id: str
    name: str
    priority: str
    category: str


@dataclass
class GraphEdge:
    """Edge in dependency graph."""
    source: str
    target: str
    relationship: str
