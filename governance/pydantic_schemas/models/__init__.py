"""
Pydantic Models Package
=======================
Input and output models for governance operations.

Per RULE-017: Type-Safe Tool Development
Per GAP-FILE-010: Extracted from pydantic_tools.py

Created: 2024-12-28
"""

from .inputs import (
    RuleQueryConfig,
    DependencyConfig,
    TrustScoreRequest,
    ProposalConfig,
    ImpactAnalysisConfig,
    DSMCycleConfig,
)

from .outputs import (
    RuleInfo,
    RuleQueryResult,
    DependencyResult,
    TrustScoreResult,
    ProposalResult,
    ImpactAnalysisResult,
    HealthCheckResult,
)

__all__ = [
    # Input models
    "RuleQueryConfig",
    "DependencyConfig",
    "TrustScoreRequest",
    "ProposalConfig",
    "ImpactAnalysisConfig",
    "DSMCycleConfig",
    # Output models
    "RuleInfo",
    "RuleQueryResult",
    "DependencyResult",
    "TrustScoreResult",
    "ProposalResult",
    "ImpactAnalysisResult",
    "HealthCheckResult",
]
