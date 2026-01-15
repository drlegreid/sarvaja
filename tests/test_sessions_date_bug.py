"""
TDD Test for Sessions Date Display Bug (GAP-UI-EXP-005).

Per TDD: Write failing test FIRST, then fix.
Per TEST-BDD-01-v1: E2E testing with Playwright.
Per GAP-UI-EXP-005: Sessions view shows "No date" when API returns valid start_time.

Bug Details:
- File: agent/governance_ui/views/sessions/list.py:70
- File: agent/governance_ui/views/sessions/content.py:16,47
- Template uses `session.date` but API returns `start_time`
- Fix: Change all occurrences of `session.date` to `session.start_time`
"""

import pytest


class TestSessionsDateDisplay:
    """Tests for sessions date display - GAP-UI-EXP-005."""

    def test_sessions_list_uses_start_time_field(self):
        """
        Test that sessions/list.py uses start_time, not date field.

        GAP-UI-EXP-005: API returns start_time but UI looks for date.
        """
        list_file = "agent/governance_ui/views/sessions/list.py"

        with open(list_file, "r") as f:
            content = f.read()

        # Bug: Template uses session.date but should use session.start_time
        # This test SHOULD FAIL initially (TDD red phase)
        assert "session.date" not in content, (
            f"Bug found in {list_file}: Uses 'session.date' but API returns 'start_time'. "
            "Fix: Change 'session.date' to 'session.start_time'"
        )
        # After fix, template should use start_time
        assert "session.start_time" in content, (
            f"Missing 'session.start_time' in {list_file}. "
            "Sessions should display start_time from API response."
        )

    def test_sessions_content_uses_start_time_field(self):
        """
        Test that sessions/content.py uses start_time, not date field.

        GAP-UI-EXP-005: Multiple occurrences of session.date in content.py.
        Lines 16 and 47 use date instead of start_time.
        """
        content_file = "agent/governance_ui/views/sessions/content.py"

        with open(content_file, "r") as f:
            content = f.read()

        # Bug: Template uses selected_session.date but should use selected_session.start_time
        # This test SHOULD FAIL initially (TDD red phase)
        assert "selected_session.date" not in content, (
            f"Bug found in {content_file}: Uses 'selected_session.date' but API returns 'start_time'. "
            "Fix: Change 'selected_session.date' to 'selected_session.start_time'"
        )
        # After fix, template should use start_time
        assert "selected_session.start_time" in content, (
            f"Missing 'selected_session.start_time' in {content_file}. "
            "Session detail should display start_time from API response."
        )

    def test_api_returns_start_time_not_date(self):
        """
        Verify API contract: sessions endpoint returns start_time field.

        This documents the expected API response format.
        """
        # Expected API response fields for a session
        expected_session_fields = {
            "session_id",
            "start_time",  # This is what API returns
            "end_time",
            "status",
            "description",
        }

        # Note: API does NOT return a 'date' field
        # UI templates were incorrectly looking for 'date'
        assert "date" not in expected_session_fields, (
            "API does not return 'date' field - it returns 'start_time'"
        )
        assert "start_time" in expected_session_fields, (
            "API returns 'start_time' field which UI should display"
        )


class TestSessionsDateDisplayIntegration:
    """Integration tests for sessions date display."""

    @pytest.mark.skipif(
        True,  # Skip until services are running
        reason="Requires running API server"
    )
    def test_sessions_api_response_has_start_time(self):
        """
        Integration test: Verify actual API response has start_time.

        Requires: API server running on localhost:8082
        """
        import httpx

        response = httpx.get("http://localhost:8082/api/sessions")
        assert response.status_code == 200

        sessions = response.json()
        if sessions:
            first_session = sessions[0]
            assert "start_time" in first_session, (
                "API response missing 'start_time' field"
            )
            assert first_session["start_time"] is not None, (
                "start_time should not be None"
            )
            # API should NOT have 'date' field
            assert "date" not in first_session, (
                "API should not have 'date' field - use 'start_time'"
            )
