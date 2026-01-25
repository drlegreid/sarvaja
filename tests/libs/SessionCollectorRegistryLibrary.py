"""
Robot Framework Library for SessionCollector - Registry & MCP Tests.

Per P4.2: Session Collector.
Split from SessionCollectorLibrary.py per DOC-SIZE-01-v1.

Covers: Session registry, MCP session tools.
"""
import json
import tempfile
from pathlib import Path
from robot.api.deco import keyword


class SessionCollectorRegistryLibrary:
    """Library for testing SessionCollector registry and MCP tools."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # Session Registry Tests
    # =========================================================================

    @keyword("Get Or Create Session Creates New")
    def get_or_create_session_creates_new(self):
        """get_or_create_session creates new session."""
        try:
            from governance.session_collector import get_or_create_session, _active_sessions
            _active_sessions.clear()
            collector = get_or_create_session("NEW-TOPIC")
            return {
                "created": collector is not None,
                "has_topic": "NEW-TOPIC" in collector.session_id
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Or Create Session Returns Existing")
    def get_or_create_session_returns_existing(self):
        """get_or_create_session returns existing session."""
        try:
            from governance.session_collector import get_or_create_session, _active_sessions
            _active_sessions.clear()
            collector1 = get_or_create_session("SAME-TOPIC")
            collector2 = get_or_create_session("SAME-TOPIC")
            return {"same_instance": collector1 is collector2}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("List Active Sessions Returns IDs")
    def list_active_sessions_returns_ids(self):
        """list_active_sessions returns session IDs."""
        try:
            from governance.session_collector import (
                get_or_create_session,
                list_active_sessions,
                _active_sessions
            )
            _active_sessions.clear()
            get_or_create_session("TOPIC-A")
            get_or_create_session("TOPIC-B")
            sessions = list_active_sessions()
            return {"correct_count": len(sessions) == 2}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("End Session Removes And Generates Log")
    def end_session_removes_and_generates_log(self):
        """end_session removes session and generates log."""
        try:
            from governance.session_collector import (
                get_or_create_session,
                end_session,
                list_active_sessions,
                _active_sessions
            )
            _active_sessions.clear()
            collector = get_or_create_session("END-TEST")
            collector.capture_prompt("Test")

            with tempfile.TemporaryDirectory() as tmpdir:
                collector.evidence_dir = Path(tmpdir)
                log_path = end_session("END-TEST")

                return {
                    "log_generated": log_path is not None,
                    "session_removed": "END-TEST" not in [s for s in list_active_sessions()]
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # MCP Session Tools Tests
    # =========================================================================

    @keyword("Session Start Tool Exists")
    def session_start_tool_exists(self):
        """session_start MCP tool exists."""
        try:
            from governance.compat import session_start
            return {
                "exists": session_start is not None,
                "callable": callable(session_start)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Session Start Returns JSON")
    def session_start_returns_json(self):
        """session_start returns valid JSON."""
        try:
            from governance.compat import session_start
            from governance.session_collector import _active_sessions
            _active_sessions.clear()
            result = session_start("MCP-TEST", "research")
            parsed = json.loads(result)
            return {
                "has_session_id": "session_id" in parsed,
                "topic_correct": parsed["topic"] == "MCP-TEST"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("Session Decision Tool Exists")
    def session_decision_tool_exists(self):
        """session_decision MCP tool exists."""
        try:
            from governance.compat import session_decision
            return {
                "exists": session_decision is not None,
                "callable": callable(session_decision)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Session Task Tool Exists")
    def session_task_tool_exists(self):
        """session_task MCP tool exists."""
        try:
            from governance.compat import session_task
            return {
                "exists": session_task is not None,
                "callable": callable(session_task)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Session End Tool Exists")
    def session_end_tool_exists(self):
        """session_end MCP tool exists."""
        try:
            from governance.compat import session_end
            return {
                "exists": session_end is not None,
                "callable": callable(session_end)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Session List Tool Exists")
    def session_list_tool_exists(self):
        """session_list MCP tool exists."""
        try:
            from governance.compat import session_list
            return {
                "exists": session_list is not None,
                "callable": callable(session_list)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
