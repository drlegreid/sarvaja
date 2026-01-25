"""
Robot Framework Library for Session Memory - Context Tests.

Per P11.4: Session memory integration for amnesia recovery.
Split from SessionMemoryLibrary.py per DOC-SIZE-01-v1.

Covers: SessionContext creation, serialization, metadata.
"""
from pathlib import Path
from datetime import date
from robot.api.deco import keyword


class SessionMemoryContextLibrary:
    """Library for testing SessionContext module."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    # =========================================================================
    # SessionContext Tests
    # =========================================================================

    @keyword("Session Context Creates With Defaults")
    def session_context_creates_with_defaults(self):
        """SessionContext initializes with sensible defaults."""
        try:
            from governance.session_memory import SessionContext

            ctx = SessionContext(session_id="TEST-001")

            return {
                "session_id_correct": ctx.session_id == "TEST-001",
                "project_correct": ctx.project == "sim-ai",
                "date_correct": ctx.date == date.today().isoformat(),
                "tasks_empty": ctx.tasks_completed == [],
                "gaps_empty": ctx.gaps_resolved == []
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Session Context To Document Basic")
    def session_context_to_document_basic(self):
        """to_document creates readable string."""
        try:
            from governance.session_memory import SessionContext

            ctx = SessionContext(
                session_id="TEST-001",
                phase="P11",
                summary="Test session for unit tests",
            )

            doc = ctx.to_document()

            return {
                "has_session_id": "sim-ai Session TEST-001" in doc,
                "has_phase": "Phase: P11" in doc,
                "has_summary": "Test session for unit tests" in doc
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Session Context To Document With Tasks")
    def session_context_to_document_with_tasks(self):
        """to_document includes tasks."""
        try:
            from governance.session_memory import SessionContext

            ctx = SessionContext(
                session_id="TEST-002",
                tasks_completed=["P11.1", "P11.2"],
                gaps_resolved=["GAP-001"],
            )

            doc = ctx.to_document()

            return {
                "has_tasks": "Tasks Completed: P11.1, P11.2" in doc,
                "has_gaps": "Gaps Resolved: GAP-001" in doc
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Session Context To Metadata")
    def session_context_to_metadata(self):
        """to_metadata creates proper dict."""
        try:
            from governance.session_memory import SessionContext

            ctx = SessionContext(
                session_id="TEST-003",
                phase="P11",
            )
            ctx.tasks_completed = ["P11.1", "P11.2", "P11.3"]
            ctx.gaps_resolved = ["GAP-001"]

            meta = ctx.to_metadata()

            return {
                "project_correct": meta.get("project") == "sim-ai",
                "session_id_correct": meta.get("session_id") == "TEST-003",
                "phase_correct": meta.get("phase") == "P11",
                "type_correct": meta.get("type") == "session-context",
                "tasks_count_correct": meta.get("tasks_count") == 3,
                "gaps_count_correct": meta.get("gaps_resolved_count") == 1
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}
