"""
TypeDB → Kanren Constraint Loader (KAN-004).

Dynamically loads governance rules from TypeDB and converts them
to Kanren facts for constraint validation.

Per RD-KANREN-CONTEXT: Integration with TypeDB for dynamic constraints.
"""

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from kanren import run, var, eq, conde, Relation, facts


# =============================================================================
# Domain Models
# =============================================================================

@dataclass
class RuleConstraint:
    """
    Constraint extracted from TypeDB rule.

    Represents a rule's constraint logic for Kanren validation.
    """
    rule_id: str
    semantic_id: str
    name: str
    category: str
    priority: str
    directive: str
    rule_type: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuleConstraint":
        """Create from TypeDB query result."""
        return cls(
            rule_id=data.get("id", ""),
            semantic_id=data.get("semantic_id", ""),
            name=data.get("name", ""),
            category=data.get("category", ""),
            priority=data.get("priority", "MEDIUM"),
            directive=data.get("directive", ""),
            rule_type=data.get("rule_type", "OPERATIONAL"),
        )


# =============================================================================
# Kanren Relations (Dynamic Facts)
# =============================================================================

# Priority constraint relations
rule_priority = Relation("rule_priority")
category_priority = Relation("category_priority")
critical_rule = Relation("critical_rule")

# Type constraint relations
rule_type_rel = Relation("rule_type")
foundational_rule = Relation("foundational_rule")
operational_rule = Relation("operational_rule")
technical_rule = Relation("technical_rule")

# Category relations
governance_rule = Relation("governance_rule")
testing_rule = Relation("testing_rule")
autonomy_rule = Relation("autonomy_rule")


# =============================================================================
# Loader Functions
# =============================================================================

def load_rules_from_typedb(mcp_result: Optional[str] = None) -> List[RuleConstraint]:
    """
    Load rules from TypeDB MCP result and convert to RuleConstraint objects.

    Args:
        mcp_result: JSON string from governance_query_rules MCP call.
                   If None, returns empty list.

    Returns:
        List of RuleConstraint objects

    Example:
        # Using MCP result
        result = await governance_query_rules(status="ACTIVE")
        rules = load_rules_from_typedb(result)
    """
    if not mcp_result:
        return []

    try:
        data = json.loads(mcp_result) if isinstance(mcp_result, str) else mcp_result
        return [RuleConstraint.from_dict(r) for r in data]
    except (json.JSONDecodeError, TypeError):
        return []


def populate_kanren_facts(rules: List[RuleConstraint]) -> Dict[str, int]:
    """
    Populate Kanren relations with facts from TypeDB rules.

    Creates facts for:
    - rule_priority(rule_id, priority)
    - critical_rule(rule_id) for CRITICAL priority
    - rule_type(rule_id, type)
    - foundational_rule(rule_id), operational_rule(rule_id), etc.
    - category relations

    Args:
        rules: List of RuleConstraint objects

    Returns:
        Dict with counts of facts added by category

    Example:
        rules = load_rules_from_typedb(mcp_result)
        counts = populate_kanren_facts(rules)
        print(f"Added {counts['critical']} critical rules")
    """
    counts = {
        "priority": 0,
        "critical": 0,
        "rule_type": 0,
        "category": 0,
    }

    for rule in rules:
        # Priority facts
        facts(rule_priority, (rule.rule_id, rule.priority))
        counts["priority"] += 1

        # Critical rule facts
        if rule.priority == "CRITICAL":
            facts(critical_rule, (rule.rule_id,))
            counts["critical"] += 1

        # Rule type facts
        if rule.rule_type:
            facts(rule_type_rel, (rule.rule_id, rule.rule_type))
            counts["rule_type"] += 1

            # Type-specific relations
            if rule.rule_type == "FOUNDATIONAL":
                facts(foundational_rule, (rule.rule_id,))
            elif rule.rule_type == "OPERATIONAL":
                facts(operational_rule, (rule.rule_id,))
            elif rule.rule_type == "TECHNICAL":
                facts(technical_rule, (rule.rule_id,))

        # Category facts
        if rule.category:
            if rule.category == "governance":
                facts(governance_rule, (rule.rule_id,))
            elif rule.category == "testing":
                facts(testing_rule, (rule.rule_id,))
            elif rule.category == "autonomy":
                facts(autonomy_rule, (rule.rule_id,))
            counts["category"] += 1

    return counts


# =============================================================================
# Constraint Queries
# =============================================================================

def query_critical_rules() -> Tuple:
    """
    Query all CRITICAL priority rules using Kanren.

    Returns:
        Tuple of rule IDs with CRITICAL priority

    Example:
        critical_ids = query_critical_rules()
        # ('RULE-015', 'RULE-024', ...)
    """
    x = var()
    return run(0, x, critical_rule(x))


def query_rules_by_priority(priority: str) -> Tuple:
    """
    Query rules by priority using Kanren.

    Args:
        priority: Priority level (CRITICAL, HIGH, MEDIUM, LOW)

    Returns:
        Tuple of rule IDs with specified priority
    """
    x = var()
    return run(0, x, rule_priority(x, priority))


def query_foundational_rules() -> Tuple:
    """
    Query all FOUNDATIONAL type rules.

    Per RULE-011: Foundational rules are trust anchors.

    Returns:
        Tuple of foundational rule IDs
    """
    x = var()
    return run(0, x, foundational_rule(x))


def query_governance_rules() -> Tuple:
    """
    Query all governance category rules.

    Returns:
        Tuple of governance rule IDs
    """
    x = var()
    return run(0, x, governance_rule(x))


def rule_requires_evidence(rule_id: str) -> Tuple:
    """
    Check if a rule requires evidence based on priority.

    Per RULE-028: CRITICAL and HIGH priority rules require evidence.

    Args:
        rule_id: The rule ID to check

    Returns:
        Tuple with True/False result
    """
    x = var()
    priority_var = var()

    return run(1, x, conde(
        # Rule is CRITICAL → requires evidence
        [rule_priority(rule_id, priority_var),
         eq(priority_var, "CRITICAL"),
         eq(x, True)],
        # Rule is HIGH → requires evidence
        [rule_priority(rule_id, priority_var),
         eq(priority_var, "HIGH"),
         eq(x, True)],
        # Default → no evidence required
        [eq(x, False)]
    ))


# =============================================================================
# Validation Functions
# =============================================================================

def validate_rule_compliance(
    rule_id: str,
    has_evidence: bool,
    agent_trust: float
) -> Dict[str, Any]:
    """
    Validate if an agent can comply with a rule.

    Combines:
    - Rule priority requirements
    - Evidence requirements
    - Trust level validation

    Args:
        rule_id: Rule to validate compliance for
        has_evidence: Whether evidence is available
        agent_trust: Agent's trust score (0.0-1.0)

    Returns:
        Dict with compliance status and details
    """
    from .trust import trust_level, can_execute_priority

    # Get rule priority from facts
    priority_results = run(1, var(), rule_priority(rule_id, var()))

    if not priority_results:
        # Unknown rule - assume MEDIUM priority
        priority = "MEDIUM"
    else:
        # Extract priority from the relation
        p_var = var()
        priority_result = run(1, p_var, rule_priority(rule_id, p_var))
        priority = priority_result[0] if priority_result else "MEDIUM"

    # Check trust level
    trust = trust_level(agent_trust)
    can_execute = can_execute_priority(trust, priority)

    # Check evidence requirement
    evidence_req = rule_requires_evidence(rule_id)
    needs_evidence = evidence_req[0] if evidence_req else False

    # Validate
    compliant = True
    violations = []

    if not (len(can_execute) > 0 and can_execute[0]):
        compliant = False
        violations.append(f"Trust level '{trust}' cannot execute {priority} priority")

    if needs_evidence and not has_evidence:
        compliant = False
        violations.append(f"Rule {rule_id} requires evidence")

    return {
        "compliant": compliant,
        "rule_id": rule_id,
        "priority": priority,
        "trust_level": trust,
        "requires_evidence": needs_evidence,
        "has_evidence": has_evidence,
        "violations": violations,
    }


# =============================================================================
# Integration Helper
# =============================================================================

class TypeDBKanrenBridge:
    """
    Bridge between TypeDB MCP and Kanren constraint engine.

    Manages the lifecycle of loading rules and validating constraints.

    Example:
        bridge = TypeDBKanrenBridge()
        bridge.load_from_mcp(mcp_result)
        result = bridge.validate_rule("RULE-011", has_evidence=True, agent_trust=0.85)
    """

    def __init__(self):
        self._rules: List[RuleConstraint] = []
        self._loaded = False

    def load_from_mcp(self, mcp_result: str) -> Dict[str, int]:
        """
        Load rules from MCP result and populate Kanren facts.

        Args:
            mcp_result: JSON string from governance_query_rules

        Returns:
            Dict with counts of facts added
        """
        self._rules = load_rules_from_typedb(mcp_result)
        counts = populate_kanren_facts(self._rules)
        self._loaded = True
        return counts

    def is_loaded(self) -> bool:
        """Check if rules have been loaded."""
        return self._loaded

    def get_rules(self) -> List[RuleConstraint]:
        """Get loaded rules."""
        return self._rules

    def validate_rule(
        self,
        rule_id: str,
        has_evidence: bool = False,
        agent_trust: float = 0.7
    ) -> Dict[str, Any]:
        """
        Validate compliance with a rule.

        Args:
            rule_id: Rule to validate
            has_evidence: Whether evidence is available
            agent_trust: Agent's trust score

        Returns:
            Dict with compliance status
        """
        if not self._loaded:
            return {
                "compliant": False,
                "rule_id": rule_id,
                "violations": ["Rules not loaded - call load_from_mcp first"]
            }

        return validate_rule_compliance(rule_id, has_evidence, agent_trust)

    def get_critical_rules(self) -> Tuple:
        """Get all CRITICAL priority rules."""
        return query_critical_rules()

    def get_rules_by_category(self, category: str) -> List[RuleConstraint]:
        """Get rules filtered by category."""
        return [r for r in self._rules if r.category == category]
