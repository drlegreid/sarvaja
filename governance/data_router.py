"""
Data Router (DEPRECATED - use governance.router package)
Created: 2024-12-25 (P7.3)
Modularized: 2026-01-02 (RULE-032)

This file is kept for backward compatibility.
Import from governance.router instead:

    from governance.router import DataRouter, create_data_router

Per DECISION-003: TypeDB-First Strategy
Per RULE-032: Files >300 lines MUST be modularized.
"""
import warnings

# Re-export from modular package for backward compatibility
from governance.router import (
    RouteResult,
    RuleRoutingMixin,
    DecisionRoutingMixin,
    SessionRoutingMixin,
    BatchRoutingMixin,
    DataRouter,
    create_data_router,
)

__all__ = [
    "RouteResult",
    "RuleRoutingMixin",
    "DecisionRoutingMixin",
    "SessionRoutingMixin",
    "BatchRoutingMixin",
    "DataRouter",
    "create_data_router",
]

# Emit deprecation warning on import
warnings.warn(
    "governance.data_router is deprecated. "
    "Use 'from governance.router import DataRouter' instead.",
    DeprecationWarning,
    stacklevel=2
)


def main():
    """CLI entry point (deprecated - use python -m governance.router)."""
    from governance.router.__main__ import main as _main
    _main()


if __name__ == "__main__":
    main()
