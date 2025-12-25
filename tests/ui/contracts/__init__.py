# API Contracts Package
# Per UI-FIRST-SPRINT-WORKFLOW.md: Spec-First TDD - API contracts
"""
API contract definitions for Sim.ai Governance Platform.
These define the EXPECTED API behavior before implementation.
"""
from .rules_api import (
    RuleResponse,
    RulesListResponse,
    CreateRuleRequest,
    CreateRuleResponse,
    UpdateRuleRequest,
    UpdateRuleResponse,
    DeleteRuleResponse,
    RULES_API,
    EXAMPLE_RULE,
    EXAMPLE_LIST,
)

__all__ = [
    'RuleResponse',
    'RulesListResponse',
    'CreateRuleRequest',
    'CreateRuleResponse',
    'UpdateRuleRequest',
    'UpdateRuleResponse',
    'DeleteRuleResponse',
    'RULES_API',
    'EXAMPLE_RULE',
    'EXAMPLE_LIST',
]
