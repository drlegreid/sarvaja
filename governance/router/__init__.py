"""
Data Router Package
Created: 2024-12-25 (P7.3)
Modularized: 2026-01-02 (RULE-032)

Routes new data to TypeDB with optional embedding generation.
Supports: rules, decisions, sessions.

Per DECISION-003: TypeDB-First Strategy
Per RULE-001: Session Evidence Logging

Usage:
    from governance.router import DataRouter, create_data_router

    router = create_data_router()
    router.route_rule(rule_id="RULE-023", name="New Rule", directive="Do the thing")
    router.route_decision(decision_id="DECISION-005", name="New Decision", context="Why")
    router.route_session(session_id="SESSION-2024-12-25-PHASE9", content="Evidence...")
"""

from governance.router.models import RouteResult
from governance.router.rules import RuleRoutingMixin
from governance.router.decisions import DecisionRoutingMixin
from governance.router.sessions import SessionRoutingMixin
from governance.router.batch import BatchRoutingMixin
from governance.router.router import DataRouter, create_data_router

__all__ = [
    "RouteResult",
    "RuleRoutingMixin",
    "DecisionRoutingMixin",
    "SessionRoutingMixin",
    "BatchRoutingMixin",
    "DataRouter",
    "create_data_router",
]
