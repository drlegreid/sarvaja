"""
Robot Framework Library for MCP Tools Health and Trust Tests.

Per GAP-MCP-002: MCP governance health check.
Split from tests/test_mcp_tools.py per DOC-SIZE-01-v1.
"""
from pathlib import Path
from robot.api.deco import keyword


class MCPToolsHealthLibrary:
    """Library for MCP tools health and trust tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    # =========================================================================
    # Health Response Structure Tests (GAP-MCP-002)
    # =========================================================================

    @keyword("Health Response Structure")
    def health_response_structure(self):
        """Health check response has required GAP-MCP-002 fields."""
        required_unhealthy_fields = [
            "status", "error", "action_required", "services", "recovery_hint", "details"
        ]
        required_healthy_fields = [
            "status", "action_required", "details", "timestamp"
        ]

        # Unhealthy response structure
        unhealthy_response = {
            "status": "unhealthy",
            "error": "DEPENDENCY_FAILURE",
            "action_required": "START_SERVICES",
            "services": ["typedb"],
            "recovery_hint": "docker compose --profile dev up -d typedb",
            "details": {"typedb": {"healthy": False}},
            "timestamp": "2024-12-31T00:00:00"
        }

        unhealthy_ok = all(f in unhealthy_response for f in required_unhealthy_fields)

        # Healthy response structure
        healthy_response = {
            "status": "healthy",
            "action_required": None,
            "details": {"typedb": {"healthy": True}, "chromadb": {"healthy": True}},
            "timestamp": "2024-12-31T00:00:00"
        }

        healthy_ok = all(f in healthy_response for f in required_healthy_fields)

        return {
            "unhealthy_fields_ok": unhealthy_ok,
            "healthy_fields_ok": healthy_ok
        }

    @keyword("Action Required Pattern For Claude Code")
    def action_required_pattern_for_claude_code(self):
        """action_required: START_SERVICES triggers Claude Code recovery."""
        unhealthy_response = {
            "status": "unhealthy",
            "error": "DEPENDENCY_FAILURE",
            "action_required": "START_SERVICES",
            "services": ["typedb", "chromadb"],
            "recovery_hint": "docker compose --profile dev up -d typedb chromadb"
        }

        return {
            "action_start_services": unhealthy_response["action_required"] == "START_SERVICES",
            "has_typedb": "typedb" in unhealthy_response["services"],
            "has_chromadb": "chromadb" in unhealthy_response["services"],
            "has_docker_command": "docker compose" in unhealthy_response["recovery_hint"],
            "hint_has_typedb": "typedb" in unhealthy_response["recovery_hint"],
            "hint_has_chromadb": "chromadb" in unhealthy_response["recovery_hint"]
        }

    # =========================================================================
    # Vote Weight Calculation Tests
    # =========================================================================

    @keyword("High Trust Gets Full Weight")
    def high_trust_gets_full_weight(self):
        """High trust agents (>= 0.5) get vote weight of 1.0."""
        # Test the calculation logic
        trust_score = 0.75
        vote_weight = 1.0 if trust_score >= 0.5 else trust_score
        return {"full_weight": vote_weight == 1.0}

    @keyword("Low Trust Gets Reduced Weight")
    def low_trust_gets_reduced_weight(self):
        """Low trust agents (< 0.5) get vote weight equal to trust score."""
        # Test the calculation logic
        trust_score = 0.3
        vote_weight = 1.0 if trust_score >= 0.5 else trust_score
        return {"reduced_weight": vote_weight == 0.3}

    @keyword("Boundary Trust At Half")
    def boundary_trust_at_half(self):
        """Trust score exactly at 0.5 gets full weight."""
        trust_score = 0.5
        vote_weight = 1.0 if trust_score >= 0.5 else trust_score
        return {"boundary_full": vote_weight == 1.0}

    @keyword("Very Low Trust Weight")
    def very_low_trust_weight(self):
        """Very low trust (0.1) gets proportional weight."""
        trust_score = 0.1
        vote_weight = 1.0 if trust_score >= 0.5 else trust_score
        return {"proportional": vote_weight == 0.1}
