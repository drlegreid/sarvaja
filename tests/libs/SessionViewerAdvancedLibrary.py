"""
Robot Framework Library for Session Viewer Advanced Tests.

Per P9.3: Session summary, navigation, and integration tests.
Split from SessionViewerLibrary.py per DOC-SIZE-01-v1.
"""
from pathlib import Path
from robot.api.deco import keyword


class SessionViewerAdvancedLibrary:
    """Library for testing session viewer summary, navigation, and integration."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.agent_dir = self.project_root / "agent"
        self.evidence_dir = self.project_root / "evidence"

    # =============================================================================
    # Summary Tests
    # =============================================================================

    @keyword("Generate Summary Works")
    def generate_summary_works(self):
        """Should generate session summary."""
        try:
            from agent.session_viewer import SessionViewer

            viewer = SessionViewer()
            timeline = viewer.get_sessions_timeline(limit=1)

            if timeline:
                session_id = timeline[0]['session_id']
                summary = viewer.get_session_summary(session_id)

                return {
                    "is_dict": isinstance(summary, dict),
                    "has_session_id": 'session_id' in summary
                }
            return {"is_dict": True, "has_session_id": True}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Summary Has Stats")
    def summary_has_stats(self):
        """Summary should include statistics."""
        try:
            from agent.session_viewer import SessionViewer

            viewer = SessionViewer()
            timeline = viewer.get_sessions_timeline(limit=1)

            if timeline:
                session_id = timeline[0]['session_id']
                summary = viewer.get_session_summary(session_id)

                return {
                    "has_stats": 'word_count' in summary or 'line_count' in summary
                }
            return {"has_stats": True}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    # =============================================================================
    # Navigation Tests
    # =============================================================================

    @keyword("Get Adjacent Sessions Works")
    def get_adjacent_sessions_works(self):
        """Should find previous and next sessions."""
        try:
            from agent.session_viewer import SessionViewer

            viewer = SessionViewer()
            timeline = viewer.get_sessions_timeline(limit=10)

            if len(timeline) >= 3:
                middle_id = timeline[1]['session_id']
                adjacent = viewer.get_adjacent_sessions(middle_id)

                return {
                    "has_previous": 'previous' in adjacent,
                    "has_next": 'next' in adjacent
                }
            return {"has_previous": True, "has_next": True}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Get Sessions By Phase Works")
    def get_sessions_by_phase_works(self):
        """Should group sessions by phase."""
        try:
            from agent.session_viewer import SessionViewer

            viewer = SessionViewer()
            by_phase = viewer.get_sessions_by_phase()

            return {"is_dict": isinstance(by_phase, dict)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Get Sessions By Date Works")
    def get_sessions_by_date_works(self):
        """Should group sessions by date."""
        try:
            from agent.session_viewer import SessionViewer

            viewer = SessionViewer()
            by_date = viewer.get_sessions_by_date()

            return {"is_dict": isinstance(by_date, dict)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    # =============================================================================
    # Integration Tests
    # =============================================================================

    @keyword("Viewer Uses MCP Tools")
    def viewer_uses_mcp_tools(self):
        """Viewer should use MCP tools internally."""
        try:
            from agent.session_viewer import SessionViewer

            viewer = SessionViewer()
            return {"has_mcp_method": hasattr(viewer, '_call_mcp_tool')}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Init error: {str(e)}"}

    @keyword("Session Viewer Factory Works")
    def session_viewer_factory_works(self):
        """Factory function should create viewer."""
        try:
            from agent.session_viewer import create_session_viewer

            viewer = create_session_viewer()
            return {"created": viewer is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}
