"""Common Utilities for MCP Tools. Per RULE-012: DSP Semantic Code Structure."""
import os
import warnings
import logging
from dataclasses import dataclass
from functools import wraps

logger = logging.getLogger(__name__)

def warn_deprecated(old_name: str, new_name: str) -> None:
    """Log deprecation warning for old tool name. Per RD-MCP-TOOL-NAMING Phase 3."""
    msg = f"MCP tool '{old_name}' deprecated. Use '{new_name}' instead. Removal: 2026-01-31."
    logger.warning(msg)

# TypeDB configuration (from environment or defaults)
TYPEDB_HOST = os.getenv("TYPEDB_HOST", "localhost")
TYPEDB_PORT = int(os.getenv("TYPEDB_PORT", "1729"))
DATABASE_NAME = "sim-ai-governance"


@dataclass
class TrustScore:
    """Agent trust score calculation result."""
    agent_id: str
    agent_name: str
    trust_score: float
    compliance_rate: float
    accuracy_rate: float
    tenure_days: int
    vote_weight: float  # Derived from trust_score


def calculate_vote_weight(trust_score: float) -> float:
    """
    Calculate vote weight based on trust score (RULE-011).

    Pure function: same input -> same output.

    Low trust agents (< 0.5) have vote-weight = trust-score
    High trust agents (>= 0.5) have vote-weight = 1.0
    """
    return 1.0 if trust_score >= 0.5 else trust_score


def get_typedb_client():
    """
    Factory function to create TypeDB client.

    Returns:
        TypeDBClient instance
    """
    from governance.client import TypeDBClient
    return TypeDBClient(host=TYPEDB_HOST, port=TYPEDB_PORT, database=DATABASE_NAME)
