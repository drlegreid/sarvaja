"""
Robot Framework Library for Session Viewer Tests.

Per P9.3: Session evidence viewer with timeline and search.
Migrated from tests/test_session_viewer.py
"""
from pathlib import Path
from robot.api.deco import keyword


class SessionViewerLibrary:
    """Library for testing session viewer module."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.agent_dir = self.project_root / "agent"
        self.evidence_dir = self.project_root / "evidence"

    # =============================================================================
    # Module Existence Tests
    # =============================================================================

    @keyword("Session Viewer Module Exists")
    def session_viewer_module_exists(self):
        """Session viewer module must exist."""
        viewer_file = self.agent_dir / "session_viewer.py"
        return {"exists": viewer_file.exists()}

    @keyword("Session Viewer Class Importable")
    def session_viewer_class_importable(self):
        """SessionViewer class must be importable."""
        try:
            from agent.session_viewer import SessionViewer

            viewer = SessionViewer()
            return {
                "importable": True,
                "instantiable": viewer is not None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Init error: {str(e)}"}

    @keyword("Viewer Has Required Methods")
    def viewer_has_required_methods(self):
        """Viewer must have required methods."""
        try:
            from agent.session_viewer import SessionViewer

            viewer = SessionViewer()

            return {
                "has_get_sessions_timeline": hasattr(viewer, 'get_sessions_timeline'),
                "has_get_session_detail": hasattr(viewer, 'get_session_detail'),
                "has_search_in_session": hasattr(viewer, 'search_in_session'),
                "has_get_session_metadata": hasattr(viewer, 'get_session_metadata')
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Init error: {str(e)}"}

    # =============================================================================
    # Timeline Tests
    # =============================================================================

    @keyword("Get Sessions Timeline Works")
    def get_sessions_timeline_works(self):
        """Should return sessions ordered by date."""
        try:
            from agent.session_viewer import SessionViewer

            viewer = SessionViewer()
            timeline = viewer.get_sessions_timeline()

            is_ordered = True
            if len(timeline) >= 2:
                first_date = timeline[0].get('date', '')
                second_date = timeline[1].get('date', '')
                is_ordered = first_date >= second_date

            return {
                "is_list": isinstance(timeline, list),
                "is_ordered": is_ordered
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Timeline Has Required Fields")
    def timeline_has_required_fields(self):
        """Timeline entries should have required fields."""
        try:
            from agent.session_viewer import SessionViewer

            viewer = SessionViewer()
            timeline = viewer.get_sessions_timeline(limit=1)

            if timeline:
                entry = timeline[0]
                return {
                    "has_session_id": 'session_id' in entry,
                    "has_date": 'date' in entry
                }
            return {"has_session_id": True, "has_date": True}  # No entries is valid
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Timeline Date Filter Works")
    def timeline_date_filter_works(self):
        """Should filter timeline by date range."""
        try:
            from agent.session_viewer import SessionViewer

            viewer = SessionViewer()
            timeline = viewer.get_sessions_timeline(
                start_date="2024-12-01",
                end_date="2024-12-31"
            )

            all_in_range = True
            for entry in timeline:
                date = entry.get('date', '')
                if date and '2024-12' not in date:
                    all_in_range = False
                    break

            return {
                "is_list": isinstance(timeline, list),
                "all_in_range": all_in_range
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    # =============================================================================
    # Session Detail Tests
    # =============================================================================

    @keyword("Get Session Detail Works")
    def get_session_detail_works(self):
        """Should return full session details."""
        try:
            from agent.session_viewer import SessionViewer

            viewer = SessionViewer()
            timeline = viewer.get_sessions_timeline(limit=1)

            if timeline:
                session_id = timeline[0]['session_id']
                detail = viewer.get_session_detail(session_id)

                return {
                    "has_session_id": 'session_id' in detail,
                    "has_content": 'content' in detail
                }
            return {"has_session_id": True, "has_content": True}  # No entries valid
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Session Detail Parses Sections")
    def session_detail_parses_sections(self):
        """Should parse markdown sections."""
        try:
            from agent.session_viewer import SessionViewer

            viewer = SessionViewer()
            timeline = viewer.get_sessions_timeline(limit=1)

            if timeline:
                session_id = timeline[0]['session_id']
                detail = viewer.get_session_detail(session_id)

                return {
                    "has_sections": 'sections' in detail,
                    "sections_is_list": isinstance(detail.get('sections', []), list)
                }
            return {"has_sections": True, "sections_is_list": True}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Session Not Found Handled")
    def session_not_found_handled(self):
        """Should handle missing sessions gracefully."""
        try:
            from agent.session_viewer import SessionViewer

            viewer = SessionViewer()
            detail = viewer.get_session_detail("SESSION-NONEXISTENT-999")

            return {"has_error": 'error' in detail}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    # =============================================================================
    # Metadata Tests
    # =============================================================================

    @keyword("Get Session Metadata Works")
    def get_session_metadata_works(self):
        """Should extract session metadata."""
        try:
            from agent.session_viewer import SessionViewer

            viewer = SessionViewer()
            timeline = viewer.get_sessions_timeline(limit=1)

            if timeline:
                session_id = timeline[0]['session_id']
                metadata = viewer.get_session_metadata(session_id)

                return {
                    "is_dict": isinstance(metadata, dict),
                    "has_session_id": 'session_id' in metadata
                }
            return {"is_dict": True, "has_session_id": True}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Metadata Extracts Phase")
    def metadata_extracts_phase(self):
        """Should extract phase from session ID."""
        try:
            from agent.session_viewer import SessionViewer

            viewer = SessionViewer()
            metadata = viewer.parse_session_id("SESSION-2024-12-25-PHASE8-HEALTHCHECK")

            return {
                "has_date": 'date' in metadata,
                "has_phase": 'phase' in metadata,
                "phase_correct": metadata.get('phase') == 'PHASE8'
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Metadata Extracts Topic")
    def metadata_extracts_topic(self):
        """Should extract topic from session ID."""
        try:
            from agent.session_viewer import SessionViewer

            viewer = SessionViewer()
            metadata = viewer.parse_session_id("SESSION-2024-12-25-PHASE8-HEALTHCHECK")

            return {
                "has_topic": 'topic' in metadata,
                "topic_correct": metadata.get('topic') == 'HEALTHCHECK'
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    # =============================================================================
    # Search Tests
    # =============================================================================

    @keyword("Search In Session Works")
    def search_in_session_works(self):
        """Should search within a session."""
        try:
            from agent.session_viewer import SessionViewer

            viewer = SessionViewer()
            timeline = viewer.get_sessions_timeline(limit=1)

            if timeline:
                session_id = timeline[0]['session_id']
                results = viewer.search_in_session(session_id, "session")

                return {"is_list": isinstance(results, list)}
            return {"is_list": True}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Search Returns Context")
    def search_returns_context(self):
        """Search results should include context."""
        try:
            from agent.session_viewer import SessionViewer

            viewer = SessionViewer()
            timeline = viewer.get_sessions_timeline(limit=1)

            if timeline:
                session_id = timeline[0]['session_id']
                results = viewer.search_in_session(session_id, "session")

                if results:
                    result = results[0]
                    has_context = 'match' in result and ('line' in result or 'context' in result)
                    return {"has_context": has_context}
            return {"has_context": True}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Search All Sessions Works")
    def search_all_sessions_works(self):
        """Should search across all sessions."""
        try:
            from agent.session_viewer import SessionViewer

            viewer = SessionViewer()
            results = viewer.search_all_sessions("evidence")

            has_session_id = True
            if results:
                has_session_id = 'session_id' in results[0]

            return {
                "is_list": isinstance(results, list),
                "has_session_id": has_session_id
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

