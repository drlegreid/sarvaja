"""
Applicability Enforcement Framework.

Per EPIC-GOV-RULES-V3 P4: Runtime enforcement for MANDATORY/RECOMMENDED/
FORBIDDEN/CONDITIONAL rule applicability levels.

Strategy pattern: applicability level -> enforcement handler.
SRP: Enforcement logic separate from rule CRUD.
DRY: Reuses fetch_rules() from api_client.

Created: 2026-03-25
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .api_client import fetch_rules

logger = logging.getLogger(__name__)

# Valid applicability levels
APPLICABILITY_LEVELS = ("MANDATORY", "RECOMMENDED", "FORBIDDEN", "CONDITIONAL")


# ---------------------------------------------------------------------------
# ComplianceResult dataclass
# ---------------------------------------------------------------------------

@dataclass
class ComplianceResult:
    """Result of an applicability enforcement check."""
    level: str  # MANDATORY_BLOCK | RECOMMENDED_WARN | FORBIDDEN_BLOCK | CONDITIONAL_DELEGATE | PASS
    rule_id: str
    message: str
    action: str
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def is_blocking(self) -> bool:
        """Whether this result blocks the action."""
        return self.level in ("MANDATORY_BLOCK", "FORBIDDEN_BLOCK")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level,
            "rule_id": self.rule_id,
            "message": self.message,
            "action": self.action,
            "is_blocking": self.is_blocking,
            "timestamp": self.timestamp.isoformat(),
        }


# ---------------------------------------------------------------------------
# Strategy handlers (one per applicability level)
# ---------------------------------------------------------------------------

def _handle_mandatory(rule: Dict, context: Dict) -> ComplianceResult:
    """MANDATORY: block if non-compliant, pass if compliant."""
    compliant = context.get("compliant", False)
    if compliant:
        return ComplianceResult(
            level="PASS", rule_id=rule.get("semantic_id") or rule["id"],
            message=f"MANDATORY rule {rule['id']} satisfied",
            action=context.get("action", "unknown"),
        )
    return ComplianceResult(
        level="MANDATORY_BLOCK", rule_id=rule.get("semantic_id") or rule["id"],
        message=f"MANDATORY rule {rule['id']} violated — action blocked",
        action=context.get("action", "unknown"),
    )


def _handle_recommended(rule: Dict, context: Dict) -> ComplianceResult:
    """RECOMMENDED: warn if non-compliant, pass if compliant."""
    compliant = context.get("compliant", False)
    if compliant:
        return ComplianceResult(
            level="PASS", rule_id=rule.get("semantic_id") or rule["id"],
            message=f"RECOMMENDED rule {rule['id']} satisfied",
            action=context.get("action", "unknown"),
        )
    return ComplianceResult(
        level="RECOMMENDED_WARN", rule_id=rule.get("semantic_id") or rule["id"],
        message=f"RECOMMENDED rule {rule['id']} not met — warning only",
        action=context.get("action", "unknown"),
    )


def _handle_forbidden(rule: Dict, context: Dict) -> ComplianceResult:
    """FORBIDDEN: always block non-compliant actions."""
    compliant = context.get("compliant", False)
    if compliant:
        return ComplianceResult(
            level="PASS", rule_id=rule.get("semantic_id") or rule["id"],
            message=f"FORBIDDEN rule {rule['id']} — action is allowed",
            action=context.get("action", "unknown"),
        )
    return ComplianceResult(
        level="FORBIDDEN_BLOCK", rule_id=rule.get("semantic_id") or rule["id"],
        message=f"FORBIDDEN rule {rule['id']} — action blocked",
        action=context.get("action", "unknown"),
    )


def _handle_conditional(rule: Dict, context: Dict) -> ComplianceResult:
    """CONDITIONAL: delegate to context-specific evaluation."""
    return ComplianceResult(
        level="CONDITIONAL_DELEGATE",
        rule_id=rule.get("semantic_id") or rule["id"],
        message=f"CONDITIONAL rule {rule['id']} — requires context evaluation",
        action=context.get("action", "unknown"),
    )


# ---------------------------------------------------------------------------
# check_rule_compliance() — single-rule enforcement
# ---------------------------------------------------------------------------

# Strategy map: applicability -> handler
_STRATEGY_MAP: Dict[str, Callable] = {
    "MANDATORY": _handle_mandatory,
    "RECOMMENDED": _handle_recommended,
    "FORBIDDEN": _handle_forbidden,
    "CONDITIONAL": _handle_conditional,
}


def check_rule_compliance(action: str, context: Dict[str, Any]) -> ComplianceResult:
    """
    Check a single rule's applicability enforcement.

    Args:
        action: The action being performed (e.g., "file_create", "git_force_push").
        context: Dict with at minimum 'rule_id' and 'compliant' keys.

    Returns:
        ComplianceResult with enforcement level and message.
    """
    rule_id = context.get("rule_id", "")
    rules = fetch_rules()

    # Find the target rule
    rule = next(
        (r for r in rules
         if r.get("id") == rule_id or r.get("semantic_id") == rule_id),
        None,
    )
    if not rule:
        return ComplianceResult(
            level="PASS", rule_id=rule_id,
            message=f"Rule {rule_id} not found — no enforcement",
            action=action,
        )

    applicability = rule.get("applicability")
    handler = _STRATEGY_MAP.get(applicability, _handle_recommended)
    context["action"] = action
    return handler(rule, context)


# ---------------------------------------------------------------------------
# ComplianceChecker — aggregated enforcement with registration
# ---------------------------------------------------------------------------

class ComplianceChecker:
    """
    Aggregated compliance checker with strategy pattern.

    Provides enforcement summary across all rules and supports
    registering runtime check functions for specific rules.
    """

    def __init__(self) -> None:
        self.strategies: Dict[str, Callable] = dict(_STRATEGY_MAP)
        self._registered_checks: Dict[str, Callable] = {}

    def register_check(self, rule_id: str, check_fn: Callable) -> None:
        """Register a runtime check function for a specific rule."""
        self._registered_checks[rule_id] = check_fn

    def get_enforcement_summary(
        self, rules: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Build enforcement summary across all active rules.

        Args:
            rules: Pre-fetched rules list. If None, falls back to fetch_rules().
                   Pass rules from service layer when called from inside the
                   container to avoid self-calling REST deadlock.

        Returns dict with counts per applicability level,
        total, and list of unimplemented mandatory rules.
        """
        if rules is None:
            rules = fetch_rules()
        active_rules = [r for r in rules if r.get("status") == "ACTIVE"]

        counts: Dict[str, int] = {
            "mandatory": 0,
            "recommended": 0,
            "forbidden": 0,
            "conditional": 0,
            "unspecified": 0,
        }
        unimplemented_mandatory: List[Dict[str, str]] = []

        for rule in active_rules:
            applicability = rule.get("applicability")
            if applicability == "MANDATORY":
                counts["mandatory"] += 1
                rule_id = rule.get("semantic_id") or rule.get("id", "")
                if rule_id not in self._registered_checks:
                    unimplemented_mandatory.append({
                        "rule_id": rule_id,
                        "name": rule.get("name", ""),
                    })
            elif applicability == "RECOMMENDED":
                counts["recommended"] += 1
            elif applicability == "FORBIDDEN":
                counts["forbidden"] += 1
            elif applicability == "CONDITIONAL":
                counts["conditional"] += 1
            else:
                counts["unspecified"] += 1

        return {
            **counts,
            "total": len(active_rules),
            "unimplemented_mandatory": unimplemented_mandatory,
        }
