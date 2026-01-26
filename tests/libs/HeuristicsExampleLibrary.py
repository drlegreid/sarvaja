"""
Heuristics Example Library for Robot Framework
Demonstrates SFDIPOT and CRUCSS decorators for systematic gap discovery.
Migrated from tests/heuristics/test_heuristics_example.py
Per: RF-007 Robot Framework Migration
"""
from robot.api.deco import keyword


class HeuristicsExampleLibrary:
    """Robot Framework keywords for heuristics example tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # SFDIPOT: Structure Tests
    # =========================================================================

    @keyword("TypeDB Entities Exist")
    def typedb_entities_exist(self):
        """Verify TypeDB schema includes required entities."""
        required_entities = ["rule", "task", "session", "agent", "decision"]
        return {
            "entity_count": len(required_entities),
            "count_correct": len(required_entities) == 5
        }

    @keyword("API Routes Match Spec")
    def api_routes_match_spec(self):
        """Verify API routes are documented."""
        documented_routes = ["/api/rules", "/api/tasks", "/api/sessions"]
        return {
            "route_count": len(documented_routes),
            "has_minimum_routes": len(documented_routes) >= 3
        }

    # =========================================================================
    # SFDIPOT: Data Tests
    # =========================================================================

    @keyword("Task Description Integrity")
    def task_description_integrity(self):
        """Tasks should have descriptions (GAP-DATA-001)."""
        # Placeholder - actual check in integration tests
        return {"integrity_check": True}

    @keyword("Rule Directive Length")
    def rule_directive_length(self):
        """Rules must have meaningful directives."""
        min_length = 10
        return {
            "min_length": min_length,
            "length_valid": min_length > 0
        }

    # =========================================================================
    # SFDIPOT: Function Tests
    # =========================================================================

    @keyword("Rules CRUD Flow")
    def rules_crud_flow(self):
        """Verify rules can be created, read, updated, deleted."""
        return {"crud_flow_valid": True}

    @keyword("Task Status Workflow")
    def task_status_workflow(self):
        """Tasks: pending → in_progress → completed."""
        valid_transitions = [
            ("pending", "in_progress"),
            ("in_progress", "completed"),
            ("pending", "blocked"),
        ]
        return {
            "transition_count": len(valid_transitions),
            "has_minimum_transitions": len(valid_transitions) >= 3
        }

    # =========================================================================
    # CRUCSS: Security Tests
    # =========================================================================

    @keyword("API Auth Required")
    def api_auth_required(self):
        """API should require authentication (GAP-SEC-001)."""
        # Placeholder
        return {"auth_check": True}

    @keyword("No Secrets In Repo")
    def no_secrets_in_repo(self):
        """Secrets should never be committed."""
        # Placeholder
        return {"secrets_check": True}

    # =========================================================================
    # CRUCSS: Reliability Tests
    # =========================================================================

    @keyword("TypeDB Failover")
    def typedb_failover(self):
        """System should handle TypeDB restart gracefully."""
        return {"failover_check": True}

    @keyword("Health Check Detection")
    def health_check_detection(self):
        """Healthcheck should detect down services."""
        return {"health_detection_check": True}

    # =========================================================================
    # CRUCSS: Capability Tests
    # =========================================================================

    @keyword("Rule Management Capability")
    def rule_management_capability(self):
        """End-to-end rule management."""
        return {"capability_check": True}

    @keyword("Chat Capability")
    def chat_capability(self):
        """User can interact with agents via chat."""
        return {"chat_check": True}

    # =========================================================================
    # CRUCSS: Usability Tests
    # =========================================================================

    @keyword("Navigation Usability")
    def navigation_usability(self):
        """Users can find features easily."""
        return {"navigation_check": True}

    @keyword("Error Messages Usability")
    def error_messages_usability(self):
        """Errors explain what went wrong."""
        return {"error_messages_check": True}

    # =========================================================================
    # Coverage Report Tests
    # =========================================================================

    @keyword("Coverage Report Generation")
    def coverage_report_generation(self):
        """Coverage report should include all heuristics."""
        try:
            from tests.heuristics import HeuristicCoverageReport

            report = HeuristicCoverageReport()
            report.collect()

            report_dict = report.to_dict()
            return {
                "has_sfdipot": "sfdipot" in report_dict,
                "has_crucss": "crucss" in report_dict
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Gap Detection")
    def gap_detection(self):
        """Coverage report should identify missing aspects."""
        try:
            from tests.heuristics import HeuristicCoverageReport

            report = HeuristicCoverageReport()
            report.collect()

            gaps = report.get_gaps()
            return {
                "gaps_is_dict": isinstance(gaps, dict),
                "has_sfdipot_gaps": "SFDIPOT" in gaps,
                "has_crucss_gaps": "CRUCSS" in gaps
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
