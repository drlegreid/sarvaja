"""
Rule-related Compliance Checks.

Per DOC-SIZE-01-v1: Extracted from workflow_compliance.py.
Per GOV-RULE-01-v1: Rule governance compliance.

Created: 2026-01-20
"""

import logging
from ..models import ComplianceCheck
from ..api_client import fetch_rules

logger = logging.getLogger(__name__)


def check_active_rules() -> ComplianceCheck:
    """
    Check GOV-RULE-01-v1: System should have active rules.
    """
    try:
        rules = fetch_rules()

        if not rules:
            return ComplianceCheck(
                rule_id="GOV-RULE-01-v1",
                check_name="active_rules",
                status="SKIP",
                message="No rules available (API unreachable or empty)",
                count=0
            )

        active_rules = [r for r in rules if r.get("status") == "ACTIVE"]
        count = len(active_rules)

        if count >= 30:
            return ComplianceCheck(
                rule_id="GOV-RULE-01-v1",
                check_name="active_rules",
                status="PASS",
                message=f"{count} active rules in governance system",
                count=count
            )
        elif count >= 20:
            return ComplianceCheck(
                rule_id="GOV-RULE-01-v1",
                check_name="active_rules",
                status="WARNING",
                message=f"Only {count} active rules (expected 30+)",
                count=count
            )
        else:
            return ComplianceCheck(
                rule_id="GOV-RULE-01-v1",
                check_name="active_rules",
                status="FAIL",
                message=f"Insufficient active rules: {count} (expected 40+)",
                count=count
            )

    except Exception as e:
        # BUG-474-WRC-1: Sanitize logger message + add exc_info for stack trace preservation
        logger.error(f"active_rules check failed: {type(e).__name__}", exc_info=True)
        return ComplianceCheck(
            rule_id="GOV-RULE-01-v1",
            check_name="active_rules",
            status="SKIP",
            message=f"Check failed: {type(e).__name__}"
        )
