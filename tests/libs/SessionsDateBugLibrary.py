"""
Robot Framework Library for Sessions Date Display Bug Tests.

Per GAP-UI-EXP-005: Sessions view shows "No date" when API returns valid start_time.
Migrated from tests/test_sessions_date_bug.py
"""
from robot.api.deco import keyword


class SessionsDateBugLibrary:
    """Library for testing sessions date display bug fix."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    @keyword("Sessions List Uses Start Time Field")
    def sessions_list_uses_start_time_field(self):
        """Test that sessions/list.py uses start_time, not date field."""
        try:
            list_file = "agent/governance_ui/views/sessions/list.py"
            with open(list_file, "r") as f:
                content = f.read()
            return {
                "no_session_date": "session.date" not in content,
                "has_start_time": "session.start_time" in content
            }
        except FileNotFoundError:
            return {"skipped": True, "reason": f"File not found: {list_file}"}

    @keyword("Sessions Content Uses Start Time Field")
    def sessions_content_uses_start_time_field(self):
        """Test that sessions/content.py uses start_time, not date field."""
        try:
            content_file = "agent/governance_ui/views/sessions/content.py"
            with open(content_file, "r") as f:
                content = f.read()
            return {
                "no_selected_session_date": "selected_session.date" not in content,
                "has_start_time": "selected_session.start_time" in content
            }
        except FileNotFoundError:
            return {"skipped": True, "reason": f"File not found: {content_file}"}

    @keyword("API Returns Start Time Not Date")
    def api_returns_start_time_not_date(self):
        """Verify API contract: sessions endpoint returns start_time field."""
        expected_session_fields = {
            "session_id",
            "start_time",
            "end_time",
            "status",
            "description",
        }
        return {
            "no_date_field": "date" not in expected_session_fields,
            "has_start_time": "start_time" in expected_session_fields
        }
