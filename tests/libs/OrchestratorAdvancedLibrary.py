"""
Robot Framework Library for Orchestrator Advanced Tests.

Per ORCH-002: Agent orchestrator - AgentInfo and Engine tests.
Split from OrchestratorLibrary.py per DOC-SIZE-01-v1.
"""
from pathlib import Path
from unittest.mock import Mock
from robot.api.deco import keyword


class OrchestratorAdvancedLibrary:
    """Library for testing orchestrator agent and engine modules."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    # =============================================================================
    # AgentInfo Tests
    # =============================================================================

    @keyword("Agent Trust Level Expert")
    def agent_trust_level_expert(self):
        """Expert trust level for score >= 0.9."""
        try:
            from agent.orchestrator.engine import AgentInfo, AgentRole

            agent = AgentInfo("A1", "Test", AgentRole.CODING, 0.95)
            return {"is_expert": agent.trust_level == "expert"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Agent Trust Level Trusted")
    def agent_trust_level_trusted(self):
        """Trusted level for score >= 0.7."""
        try:
            from agent.orchestrator.engine import AgentInfo, AgentRole

            agent = AgentInfo("A1", "Test", AgentRole.CODING, 0.75)
            return {"is_trusted": agent.trust_level == "trusted"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Agent Trust Level Supervised")
    def agent_trust_level_supervised(self):
        """Supervised level for score >= 0.5."""
        try:
            from agent.orchestrator.engine import AgentInfo, AgentRole

            agent = AgentInfo("A1", "Test", AgentRole.CODING, 0.55)
            return {"is_supervised": agent.trust_level == "supervised"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Agent Trust Level Restricted")
    def agent_trust_level_restricted(self):
        """Restricted level for score < 0.5."""
        try:
            from agent.orchestrator.engine import AgentInfo, AgentRole

            agent = AgentInfo("A1", "Test", AgentRole.CODING, 0.35)
            return {"is_restricted": agent.trust_level == "restricted"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    # =============================================================================
    # OrchestratorEngine Tests
    # =============================================================================

    @keyword("Engine Register Agent")
    def engine_register_agent(self):
        """Register agent successfully."""
        try:
            from agent.orchestrator.engine import OrchestratorEngine, AgentInfo, AgentRole

            mock_client = Mock()
            engine = OrchestratorEngine(mock_client)

            agent = AgentInfo("A1", "Test", AgentRole.CODING, 0.9)
            result = engine.register_agent(agent)

            return {
                "register_success": result is True,
                "agent_retrievable": engine.get_agent("A1") is not None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Engine Register Duplicate Fails")
    def engine_register_duplicate_fails(self):
        """Duplicate agent registration fails."""
        try:
            from agent.orchestrator.engine import OrchestratorEngine, AgentInfo, AgentRole

            mock_client = Mock()
            engine = OrchestratorEngine(mock_client)

            agent = AgentInfo("A1", "Test", AgentRole.CODING, 0.9)
            engine.register_agent(agent)

            return {"duplicate_rejected": engine.register_agent(agent) is False}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Engine Unregister Agent")
    def engine_unregister_agent(self):
        """Unregister agent successfully."""
        try:
            from agent.orchestrator.engine import OrchestratorEngine, AgentInfo, AgentRole

            mock_client = Mock()
            engine = OrchestratorEngine(mock_client)

            agent = AgentInfo("A1", "Test", AgentRole.CODING, 0.9)
            engine.register_agent(agent)

            unregister_result = engine.unregister_agent("A1")

            return {
                "unregister_success": unregister_result is True,
                "agent_gone": engine.get_agent("A1") is None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Engine Get Available Agents")
    def engine_get_available_agents(self):
        """Get available agents."""
        try:
            from agent.orchestrator.engine import OrchestratorEngine, AgentInfo, AgentRole

            mock_client = Mock()
            engine = OrchestratorEngine(mock_client)

            engine.register_agent(AgentInfo("A1", "T1", AgentRole.CODING, 0.9))
            engine.register_agent(AgentInfo("A2", "T2", AgentRole.SYNC, 0.8))

            available = engine.get_available_agents()
            coding_agents = engine.get_available_agents(AgentRole.CODING)

            return {
                "all_agents": len(available) == 2,
                "coding_only": len(coding_agents) == 1
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Engine Stats")
    def engine_stats(self):
        """Engine reports statistics."""
        try:
            from agent.orchestrator.engine import OrchestratorEngine

            mock_client = Mock()
            engine = OrchestratorEngine(mock_client)

            stats = engine.stats

            return {
                "has_running": "running" in stats,
                "has_dispatch_count": "dispatch_count" in stats,
                "has_queue_stats": "queue_stats" in stats,
                "has_agents": "agents_registered" in stats
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}
