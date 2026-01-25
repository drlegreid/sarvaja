"""
Robot Framework Library for Kanren Trust & Supervisor Tests.

Per KAN-002: Kanren Constraint Engine - Trust Level Module.
Split from KanrenConstraintsLibrary.py per DOC-SIZE-01-v1.

Covers: Trust Level, Supervisor Requirements, Can Execute Priority, Validate Agent.
"""
from robot.api.deco import keyword


class KanrenTrustLibrary:
    """Library for testing Kanren trust level constraints."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def _check_kanren_available(self):
        """Check if kanren is installed."""
        try:
            from governance.kanren_constraints import trust_level
            return True
        except ImportError:
            return False

    # =========================================================================
    # Trust Level Tests (RULE-011)
    # =========================================================================

    @keyword("Trust Level Expert")
    def trust_level_expert(self):
        """Score >= 0.9 is expert."""
        try:
            from governance.kanren_constraints import trust_level
            return {
                "level_95": trust_level(0.95) == "expert",
                "level_90": trust_level(0.90) == "expert",
                "level_100": trust_level(1.0) == "expert"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Trust Level Trusted")
    def trust_level_trusted(self):
        """Score >= 0.7 and < 0.9 is trusted."""
        try:
            from governance.kanren_constraints import trust_level
            return {
                "level_89": trust_level(0.89) == "trusted",
                "level_75": trust_level(0.75) == "trusted",
                "level_70": trust_level(0.70) == "trusted"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Trust Level Supervised")
    def trust_level_supervised(self):
        """Score >= 0.5 and < 0.7 is supervised."""
        try:
            from governance.kanren_constraints import trust_level
            return {
                "level_69": trust_level(0.69) == "supervised",
                "level_55": trust_level(0.55) == "supervised",
                "level_50": trust_level(0.50) == "supervised"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Trust Level Restricted")
    def trust_level_restricted(self):
        """Score < 0.5 is restricted."""
        try:
            from governance.kanren_constraints import trust_level
            return {
                "level_49": trust_level(0.49) == "restricted",
                "level_25": trust_level(0.25) == "restricted",
                "level_0": trust_level(0.0) == "restricted"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Supervisor Requirements Tests
    # =========================================================================

    @keyword("Restricted Requires Supervisor")
    def restricted_requires_supervisor(self):
        """Restricted agents need supervisor."""
        try:
            from governance.kanren_constraints import requires_supervisor
            result = requires_supervisor("restricted")
            return {
                "has_result": len(result) > 0,
                "requires": result[0] is True
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Supervised Requires Supervisor")
    def supervised_requires_supervisor(self):
        """Supervised agents need supervisor."""
        try:
            from governance.kanren_constraints import requires_supervisor
            result = requires_supervisor("supervised")
            return {
                "has_result": len(result) > 0,
                "requires": result[0] is True
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Trusted No Supervisor")
    def trusted_no_supervisor(self):
        """Trusted agents don't need supervisor."""
        try:
            from governance.kanren_constraints import requires_supervisor
            result = requires_supervisor("trusted")
            return {
                "has_result": len(result) > 0,
                "no_supervisor": result[0] is False
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Expert No Supervisor")
    def expert_no_supervisor(self):
        """Expert agents don't need supervisor."""
        try:
            from governance.kanren_constraints import requires_supervisor
            result = requires_supervisor("expert")
            return {
                "has_result": len(result) > 0,
                "no_supervisor": result[0] is False
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Can Execute Priority Tests
    # =========================================================================

    @keyword("Critical Expert Can Execute")
    def critical_expert_can_execute(self):
        """Expert can execute CRITICAL tasks."""
        try:
            from governance.kanren_constraints import can_execute_priority
            result = can_execute_priority("expert", "CRITICAL")
            return {
                "has_result": len(result) > 0,
                "can_execute": result[0] is True
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Critical Trusted Can Execute")
    def critical_trusted_can_execute(self):
        """Trusted can execute CRITICAL tasks."""
        try:
            from governance.kanren_constraints import can_execute_priority
            result = can_execute_priority("trusted", "CRITICAL")
            return {
                "has_result": len(result) > 0,
                "can_execute": result[0] is True
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Critical Supervised Cannot Execute")
    def critical_supervised_cannot_execute(self):
        """Supervised cannot execute CRITICAL tasks."""
        try:
            from governance.kanren_constraints import can_execute_priority
            result = can_execute_priority("supervised", "CRITICAL")
            return {
                "has_result": len(result) > 0,
                "cannot_execute": result[0] is False
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Critical Restricted Cannot Execute")
    def critical_restricted_cannot_execute(self):
        """Restricted cannot execute CRITICAL tasks."""
        try:
            from governance.kanren_constraints import can_execute_priority
            result = can_execute_priority("restricted", "CRITICAL")
            return {
                "has_result": len(result) > 0,
                "cannot_execute": result[0] is False
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("High Supervised Can Execute")
    def high_supervised_can_execute(self):
        """Supervised can execute HIGH tasks."""
        try:
            from governance.kanren_constraints import can_execute_priority
            result = can_execute_priority("supervised", "HIGH")
            return {
                "has_result": len(result) > 0,
                "can_execute": result[0] is True
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("High Restricted Cannot Execute")
    def high_restricted_cannot_execute(self):
        """Restricted cannot execute HIGH tasks."""
        try:
            from governance.kanren_constraints import can_execute_priority
            result = can_execute_priority("restricted", "HIGH")
            return {
                "has_result": len(result) > 0,
                "cannot_execute": result[0] is False
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Medium All Can Execute")
    def medium_all_can_execute(self):
        """All trust levels can execute MEDIUM tasks."""
        try:
            from governance.kanren_constraints import can_execute_priority
            results = {}
            for trust in ["expert", "trusted", "supervised", "restricted"]:
                result = can_execute_priority(trust, "MEDIUM")
                results[f"{trust}_can"] = len(result) > 0 and result[0] is True
            return results
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Low All Can Execute")
    def low_all_can_execute(self):
        """All trust levels can execute LOW tasks."""
        try:
            from governance.kanren_constraints import can_execute_priority
            results = {}
            for trust in ["expert", "trusted", "supervised", "restricted"]:
                result = can_execute_priority(trust, "LOW")
                results[f"{trust}_can"] = len(result) > 0 and result[0] is True
            return results
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Validate Agent For Task Tests
    # =========================================================================

    @keyword("Validate Expert Critical")
    def validate_expert_critical(self):
        """Quick validation for expert + CRITICAL."""
        try:
            from governance.kanren_constraints import validate_agent_for_task
            result = validate_agent_for_task("AGENT-001", 0.95, "CRITICAL")
            return {"valid": result["valid"] is True}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Validate Restricted Critical")
    def validate_restricted_critical(self):
        """Quick validation for restricted + CRITICAL."""
        try:
            from governance.kanren_constraints import validate_agent_for_task
            result = validate_agent_for_task("AGENT-002", 0.35, "CRITICAL")
            return {"invalid": result["valid"] is False}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
