"""
Governance Module
Provides rule inference and knowledge reasoning for platform-gai.
Abstract layer over TypeDB - can be swapped for other inference engines.
Created: 2024-12-24 (DECISION-003)
"""

from .client import TypeDBClient, Rule, Decision, InferenceResult
from .client import get_client, quick_health

# Schema and data files location
import os
SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "schema.tql")
DATA_FILE = os.path.join(os.path.dirname(__file__), "data.tql")

__all__ = [
    "TypeDBClient",
    "Rule",
    "Decision",
    "InferenceResult",
    "get_client",
    "quick_health",
    "SCHEMA_FILE",
    "DATA_FILE",
]
