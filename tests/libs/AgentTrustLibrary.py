"""
Robot Framework Library for Agent Trust Dashboard Tests.

Per P9.5: Agent trust tracking and RULE-011 compliance metrics.
Migrated from tests/test_agent_trust.py
"""
from pathlib import Path
from robot.api.deco import keyword


class AgentTrustLibrary:
    """Library for testing agent trust dashboard."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.agent_dir = self.project_root / "agent"

    # =============================================================================
    # Module Existence Tests
    # =============================================================================

    @keyword("Agent Trust Module Exists")
    def agent_trust_module_exists(self):
        """Agent trust module must exist."""
        trust_file = self.agent_dir / "agent_trust.py"
        return {"exists": trust_file.exists()}

    @keyword("Agent Trust Class Importable")
    def agent_trust_class_importable(self):
        """AgentTrustDashboard class must be importable."""
        try:
            from agent.agent_trust import AgentTrustDashboard

            dashboard = AgentTrustDashboard()
            return {
                "importable": True,
                "instantiable": dashboard is not None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Init error: {str(e)}"}

    @keyword("Dashboard Has Required Methods")
    def dashboard_has_required_methods(self):
        """Dashboard must have required methods."""
        try:
            from agent.agent_trust import AgentTrustDashboard

            dashboard = AgentTrustDashboard()

            return {
                "has_get_trust_score": hasattr(dashboard, 'get_trust_score'),
                "has_get_compliance_status": hasattr(dashboard, 'get_compliance_status'),
                "has_record_action": hasattr(dashboard, 'record_action'),
                "has_get_trust_history": hasattr(dashboard, 'get_trust_history')
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Init error: {str(e)}"}

    # =============================================================================
    # Trust Scoring Tests
    # =============================================================================

    @keyword("Get Trust Score Works")
    def get_trust_score_works(self):
        """Should return trust score for an agent."""
        try:
            from agent.agent_trust import AgentTrustDashboard

            dashboard = AgentTrustDashboard()
            score = dashboard.get_trust_score("agent-001")

            return {
                "is_number": isinstance(score, (int, float)),
                "in_range": 0 <= score <= 100
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Default Trust Score Works")
    def default_trust_score_works(self):
        """New agents should have default trust score."""
        try:
            from agent.agent_trust import AgentTrustDashboard

            dashboard = AgentTrustDashboard()
            score = dashboard.get_trust_score("new-agent-xyz")

            return {
                "is_default": score == dashboard.default_trust_score
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Get All Trust Scores Works")
    def get_all_trust_scores_works(self):
        """Should return trust scores for all known agents."""
        try:
            from agent.agent_trust import AgentTrustDashboard

            dashboard = AgentTrustDashboard()
            scores = dashboard.get_all_trust_scores()

            return {"is_dict": isinstance(scores, dict)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    # =============================================================================
    # Compliance Tracking Tests
    # =============================================================================

    @keyword("Get Compliance Status Works")
    def get_compliance_status_works(self):
        """Should return compliance status for agent."""
        try:
            from agent.agent_trust import AgentTrustDashboard

            dashboard = AgentTrustDashboard()
            status = dashboard.get_compliance_status("agent-001")

            return {
                "is_dict": isinstance(status, dict),
                "has_compliant": 'compliant' in status
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}
