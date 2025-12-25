"""
Rules API Contract - Expected request/response schemas.
Per ENTITY-API-UI-MAP.md: Rule entity API specification
Per UI-FIRST-SPRINT-WORKFLOW.md: Spec-First TDD - API contracts

GAP-UI-004: REST API endpoints are currently missing.
This file defines the EXPECTED contracts for implementation.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class RuleStatus(Enum):
    """Rule status values."""
    ACTIVE = "ACTIVE"
    DRAFT = "DRAFT"
    DEPRECATED = "DEPRECATED"


class RuleCategory(Enum):
    """Rule category values."""
    GOVERNANCE = "governance"
    TECHNICAL = "technical"
    OPERATIONAL = "operational"
    STRATEGIC = "strategic"


class RulePriority(Enum):
    """Rule priority values."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================

@dataclass
class CreateRuleRequest:
    """POST /api/rules request body."""
    rule_id: str
    title: str
    directive: str
    category: str = "governance"
    priority: str = "HIGH"


@dataclass
class UpdateRuleRequest:
    """PUT /api/rules/{rule_id} request body."""
    title: Optional[str] = None
    directive: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None


@dataclass
class ListRulesParams:
    """GET /api/rules query parameters."""
    category: Optional[str] = None
    status: Optional[str] = None
    search: Optional[str] = None
    sort_by: Optional[str] = None
    sort_order: str = "asc"
    page: int = 1
    page_size: int = 10


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

@dataclass
class RuleResponse:
    """Single rule response object."""
    rule_id: str
    title: str
    directive: str
    category: str
    priority: str
    status: str
    created_at: str
    updated_at: str

    # Relations
    related_rules: List[str] = field(default_factory=list)
    related_decisions: List[str] = field(default_factory=list)
    related_sessions: List[str] = field(default_factory=list)


@dataclass
class RulesListResponse:
    """GET /api/rules response."""
    rules: List[RuleResponse]
    total: int
    page: int
    page_size: int


@dataclass
class CreateRuleResponse:
    """POST /api/rules response."""
    success: bool
    rule_id: str
    message: Optional[str] = None


@dataclass
class UpdateRuleResponse:
    """PUT /api/rules/{rule_id} response."""
    success: bool
    message: Optional[str] = None


@dataclass
class DeleteRuleResponse:
    """DELETE /api/rules/{rule_id} response."""
    success: bool
    message: Optional[str] = None


# =============================================================================
# API ENDPOINTS CONTRACT
# =============================================================================

RULES_API = {
    "list": {
        "method": "GET",
        "path": "/api/rules",
        "params": ["category", "status", "search", "sort_by", "sort_order", "page", "page_size"],
        "response": RulesListResponse,
        "status_codes": {
            200: "Success - returns list of rules",
            401: "Unauthorized",
            500: "Server error"
        }
    },
    "get": {
        "method": "GET",
        "path": "/api/rules/{rule_id}",
        "response": RuleResponse,
        "status_codes": {
            200: "Success - returns rule",
            404: "Rule not found",
            401: "Unauthorized",
            500: "Server error"
        }
    },
    "create": {
        "method": "POST",
        "path": "/api/rules",
        "request": CreateRuleRequest,
        "response": CreateRuleResponse,
        "status_codes": {
            201: "Created successfully",
            400: "Validation error",
            401: "Unauthorized",
            409: "Rule ID already exists",
            500: "Server error"
        }
    },
    "update": {
        "method": "PUT",
        "path": "/api/rules/{rule_id}",
        "request": UpdateRuleRequest,
        "response": UpdateRuleResponse,
        "status_codes": {
            200: "Updated successfully",
            400: "Validation error",
            401: "Unauthorized",
            404: "Rule not found",
            500: "Server error"
        }
    },
    "delete": {
        "method": "DELETE",
        "path": "/api/rules/{rule_id}",
        "response": DeleteRuleResponse,
        "status_codes": {
            200: "Deleted successfully",
            401: "Unauthorized",
            404: "Rule not found",
            500: "Server error"
        }
    }
}


# =============================================================================
# EXAMPLE DATA (for testing)
# =============================================================================

EXAMPLE_RULE = RuleResponse(
    rule_id="RULE-001",
    title="Session Evidence Logging",
    directive="Every development session MUST produce evidence artifacts...",
    category="governance",
    priority="CRITICAL",
    status="ACTIVE",
    created_at="2024-12-24T00:00:00Z",
    updated_at="2024-12-25T00:00:00Z",
    related_rules=["RULE-006", "RULE-012"],
    related_decisions=["DECISION-001"],
    related_sessions=["SESSION-2024-12-24"]
)

EXAMPLE_LIST = RulesListResponse(
    rules=[EXAMPLE_RULE],
    total=11,
    page=1,
    page_size=10
)
