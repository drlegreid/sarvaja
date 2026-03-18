"""Tests for session sorting and evidence deduplication fixes.

Bug: BUG-SESSION-SORT-001 — Test artifacts sort first due to null timestamps.
Bug: BUG-SESSION-EVIDENCE-DUP-001 — Evidence files appear duplicated.
"""

from unittest.mock import patch, MagicMock

import pytest


class TestSessionSortNullTimestamps:
    """Tests for list_sessions() null-safe sorting."""

    @patch("governance.services.sessions.get_all_sessions_from_typedb")
    def test_null_timestamps_sort_last_desc(self, mock_get):
        """Sessions with null start_time should appear AFTER sessions with timestamps (desc)."""
        from governance.services.sessions import list_sessions

        mock_get.return_value = [
            {"session_id": "S-NULL", "status": "ACTIVE", "start_time": None},
            {"session_id": "S-REAL-2", "status": "COMPLETED", "start_time": "2026-02-15T10:00:00"},
            {"session_id": "S-REAL-1", "status": "COMPLETED", "start_time": "2026-02-14T10:00:00"},
            {"session_id": "S-EMPTY", "status": "ACTIVE", "start_time": ""},
        ]

        result = list_sessions(sort_by="started_at", order="desc", limit=100)
        ids = [s["session_id"] for s in result["items"]]

        # Real sessions with timestamps first, then null/empty last
        assert ids[0] == "S-REAL-2"
        assert ids[1] == "S-REAL-1"
        # Null and empty should be at the end
        assert "S-NULL" in ids[2:]
        assert "S-EMPTY" in ids[2:]

    @patch("governance.services.sessions.get_all_sessions_from_typedb")
    def test_null_timestamps_sort_first_asc(self, mock_get):
        """Sessions with null start_time should appear FIRST when ascending."""
        from governance.services.sessions import list_sessions

        mock_get.return_value = [
            {"session_id": "S-NULL", "status": "ACTIVE", "start_time": None},
            {"session_id": "S-REAL", "status": "COMPLETED", "start_time": "2026-02-15T10:00:00"},
        ]

        result = list_sessions(sort_by="started_at", order="asc", limit=100)
        ids = [s["session_id"] for s in result["items"]]
        # Ascending: nulls first (sort by tuple, False < True)
        assert ids[0] == "S-NULL"
        assert ids[1] == "S-REAL"

    @patch("governance.services.sessions.get_all_sessions_from_typedb")
    def test_real_sessions_sorted_by_timestamp_desc(self, mock_get):
        """Real sessions should be sorted by timestamp in descending order."""
        from governance.services.sessions import list_sessions

        mock_get.return_value = [
            {"session_id": "S-OLD", "status": "COMPLETED", "start_time": "2026-01-01T10:00:00"},
            {"session_id": "S-NEW", "status": "COMPLETED", "start_time": "2026-02-15T10:00:00"},
            {"session_id": "S-MID", "status": "COMPLETED", "start_time": "2026-02-01T10:00:00"},
        ]

        result = list_sessions(sort_by="started_at", order="desc", limit=100)
        ids = [s["session_id"] for s in result["items"]]
        assert ids == ["S-NEW", "S-MID", "S-OLD"]

    @patch("governance.services.sessions.get_all_sessions_from_typedb")
    def test_all_null_timestamps(self, mock_get):
        """All sessions with null timestamps should still return without error."""
        from governance.services.sessions import list_sessions

        mock_get.return_value = [
            {"session_id": "S-1", "status": "ACTIVE", "start_time": None},
            {"session_id": "S-2", "status": "ACTIVE", "start_time": None},
        ]

        result = list_sessions(sort_by="started_at", order="desc", limit=100)
        assert result["total"] == 2

    @patch("governance.services.sessions.get_all_sessions_from_typedb")
    def test_mixed_null_and_empty_sort_together(self, mock_get):
        """Both None and empty string timestamps should sort as 'missing'."""
        from governance.services.sessions import list_sessions

        mock_get.return_value = [
            {"session_id": "S-REAL", "status": "COMPLETED", "start_time": "2026-02-15T10:00:00"},
            {"session_id": "S-NONE", "status": "ACTIVE", "start_time": None},
            {"session_id": "S-EMPTY", "status": "ACTIVE", "start_time": ""},
        ]

        result = list_sessions(sort_by="started_at", order="desc", limit=100)
        ids = [s["session_id"] for s in result["items"]]
        assert ids[0] == "S-REAL"  # Real timestamp first


class TestExcludeTestArtifacts:
    """Tests for _is_test_artifact() and exclude_test parameter."""

    def test_is_test_artifact_detects_session_fail(self):
        """SESSION-FAIL is a test artifact."""
        from governance.services.sessions import _is_test_artifact
        assert _is_test_artifact({"session_id": "SESSION-FAIL"}) is True

    def test_is_test_artifact_detects_session_test(self):
        """SESSION-TEST is a test artifact."""
        from governance.services.sessions import _is_test_artifact
        assert _is_test_artifact({"session_id": "SESSION-TEST"}) is True

    def test_is_test_artifact_detects_chat_test_patterns(self):
        """CHAT-TEST patterns should be detected."""
        from governance.services.sessions import _is_test_artifact
        test_ids = [
            "SESSION-2026-02-15-CHAT-TEST",
            "SESSION-2026-02-15-CHAT-FAIL",
            "SESSION-2026-02-15-CHAT-TEST-STORE",
            "SESSION-2026-02-15-CHAT-DELETE-TEST",
            "SESSION-2026-02-15-CHAT-AAAAAAAAAA",
        ]
        for sid in test_ids:
            assert _is_test_artifact({"session_id": sid}) is True, f"Expected {sid} to be test artifact"

    def test_is_test_artifact_detects_integration_patterns(self):
        """Integration test patterns (CHAT-FULL-LIFECYCLE, etc.) should be detected."""
        from governance.services.sessions import _is_test_artifact
        integration_ids = [
            "SESSION-2026-02-14-CHAT-FULL-LIFECYCLE",
            "SESSION-2026-02-15-CHAT-REVIEWING-RULES",
            "SESSION-2026-02-21-CHAT-HELLO",
            "SESSION-2026-02-18-CHAT-VERIFY-SESSION",
            "SESSION-2026-02-15-CHAT-CVP-TEST",
            "SESSION-2026-02-21-CHAT-HEURISTIC-INTEGRITY-CHECK-(ALL)",
            "SESSION-2026-02-18-INTTEST-RULE-LIFECYCLE",
        ]
        for sid in integration_ids:
            assert _is_test_artifact({"session_id": sid}) is True, f"Expected {sid} to be test artifact"

    def test_is_test_artifact_allows_real_sessions(self):
        """Real sessions should not be detected as test artifacts."""
        from governance.services.sessions import _is_test_artifact
        real_ids = [
            "SESSION-2026-02-15-CC-E0E0A53E-60BC",
            "SESSION-2026-01-20-CC-176AB4A6-F892",
            "SESSION-2026-02-15-ASSESS-P0-P6-GAPS-SESSION-2",
            "SESSION-2026-01-02-ANALYSIS-REPORT",
            "SESSION-2026-02-12-CHAT-DASHBOARD-WORK",
        ]
        for sid in real_ids:
            assert _is_test_artifact({"session_id": sid}) is False, f"Expected {sid} to be real session"

    @patch("governance.services.sessions.get_all_sessions_from_typedb")
    def test_exclude_test_filters_artifacts(self, mock_get):
        """exclude_test=True should filter out test sessions."""
        from governance.services.sessions import list_sessions

        mock_get.return_value = [
            {"session_id": "SESSION-FAIL", "status": "ACTIVE", "start_time": "2026-02-15"},
            {"session_id": "SESSION-2026-02-15-CHAT-TEST", "status": "COMPLETED", "start_time": "2026-02-15"},
            {"session_id": "SESSION-2026-02-15-CC-REAL", "status": "COMPLETED", "start_time": "2026-02-15"},
            {"session_id": "SESSION-2026-02-14-CHAT-DASHBOARD-WORK", "status": "COMPLETED", "start_time": "2026-02-14"},
        ]

        result = list_sessions(exclude_test=True, limit=100)
        ids = [s["session_id"] for s in result["items"]]
        assert len(ids) == 2
        assert "SESSION-2026-02-15-CC-REAL" in ids
        assert "SESSION-2026-02-14-CHAT-DASHBOARD-WORK" in ids
        assert "SESSION-FAIL" not in ids

    @patch("governance.services.sessions.get_all_sessions_from_typedb")
    def test_exclude_test_false_keeps_all(self, mock_get):
        """exclude_test=False should keep all sessions."""
        from governance.services.sessions import list_sessions

        mock_get.return_value = [
            {"session_id": "SESSION-FAIL", "status": "ACTIVE", "start_time": "2026-02-15"},
            {"session_id": "SESSION-2026-02-15-CC-REAL", "status": "COMPLETED", "start_time": "2026-02-15"},
        ]

        result = list_sessions(exclude_test=False, limit=100)
        assert result["total"] == 2


class TestSessionSearch:
    """Tests for server-side keyword search (GAP-SESSION-SEARCH-001)."""

    @patch("governance.services.sessions.get_all_sessions_from_typedb")
    def test_search_by_session_id(self, mock_get):
        """Search should match session_id substring."""
        from governance.services.sessions import list_sessions

        mock_get.return_value = [
            {"session_id": "SESSION-2026-02-15-CC-ABC", "status": "COMPLETED", "start_time": "2026-02-15"},
            {"session_id": "SESSION-2026-02-14-CHAT-HELLO", "status": "COMPLETED", "start_time": "2026-02-14"},
        ]

        result = list_sessions(search="CC-ABC", limit=100)
        assert result["total"] == 1
        assert result["items"][0]["session_id"] == "SESSION-2026-02-15-CC-ABC"

    @patch("governance.services.sessions.get_all_sessions_from_typedb")
    def test_search_by_description(self, mock_get):
        """Search should match description substring."""
        from governance.services.sessions import list_sessions

        mock_get.return_value = [
            {"session_id": "S-1", "status": "COMPLETED", "start_time": "2026-02-15",
             "description": "Implementing dark mode toggle"},
            {"session_id": "S-2", "status": "COMPLETED", "start_time": "2026-02-14",
             "description": "Bug fix for auth"},
        ]

        result = list_sessions(search="dark mode", limit=100)
        assert result["total"] == 1
        assert result["items"][0]["session_id"] == "S-1"

    @patch("governance.services.sessions.get_all_sessions_from_typedb")
    def test_search_case_insensitive(self, mock_get):
        """Search should be case-insensitive."""
        from governance.services.sessions import list_sessions

        mock_get.return_value = [
            {"session_id": "SESSION-CHAT-HELLO", "status": "COMPLETED", "start_time": "2026-02-15"},
        ]

        result = list_sessions(search="chat-hello", limit=100)
        assert result["total"] == 1

    @patch("governance.services.sessions.get_all_sessions_from_typedb")
    def test_search_by_project_slug(self, mock_get):
        """Search should match cc_project_slug."""
        from governance.services.sessions import list_sessions

        mock_get.return_value = [
            {"session_id": "S-1", "status": "COMPLETED", "start_time": "2026-02-15",
             "cc_project_slug": "sarvaja-platform"},
            {"session_id": "S-2", "status": "COMPLETED", "start_time": "2026-02-14",
             "cc_project_slug": "other-project"},
        ]

        result = list_sessions(search="sarvaja", limit=100)
        assert result["total"] == 1
        assert result["items"][0]["session_id"] == "S-1"

    @patch("governance.services.sessions.get_all_sessions_from_typedb")
    def test_search_by_git_branch(self, mock_get):
        """Search should match cc_git_branch."""
        from governance.services.sessions import list_sessions

        mock_get.return_value = [
            {"session_id": "S-1", "status": "COMPLETED", "start_time": "2026-02-15",
             "cc_git_branch": "feature/dark-mode"},
            {"session_id": "S-2", "status": "COMPLETED", "start_time": "2026-02-14",
             "cc_git_branch": "master"},
        ]

        result = list_sessions(search="dark-mode", limit=100)
        assert result["total"] == 1

    @patch("governance.services.sessions.get_all_sessions_from_typedb")
    def test_search_none_returns_all(self, mock_get):
        """search=None should not filter anything."""
        from governance.services.sessions import list_sessions

        mock_get.return_value = [
            {"session_id": "S-1", "status": "COMPLETED", "start_time": "2026-02-15"},
            {"session_id": "S-2", "status": "COMPLETED", "start_time": "2026-02-14"},
        ]

        result = list_sessions(search=None, limit=100)
        assert result["total"] == 2

    @patch("governance.services.sessions.get_all_sessions_from_typedb")
    def test_search_combined_with_filters(self, mock_get):
        """Search should work together with status and exclude_test filters."""
        from governance.services.sessions import list_sessions

        mock_get.return_value = [
            {"session_id": "SESSION-CHAT-TEST", "status": "COMPLETED", "start_time": "2026-02-15",
             "description": "test session"},
            {"session_id": "SESSION-2026-CC-ABC", "status": "COMPLETED", "start_time": "2026-02-15",
             "description": "real CC work"},
            {"session_id": "SESSION-2026-CC-DEF", "status": "ACTIVE", "start_time": "2026-02-14",
             "description": "active CC session"},
        ]

        result = list_sessions(
            search="CC", status="COMPLETED", exclude_test=True, limit=100
        )
        assert result["total"] == 1
        assert result["items"][0]["session_id"] == "SESSION-2026-CC-ABC"

    @patch("governance.services.sessions.get_all_sessions_from_typedb")
    def test_search_no_match_returns_empty(self, mock_get):
        """Search with no matches should return empty items."""
        from governance.services.sessions import list_sessions

        mock_get.return_value = [
            {"session_id": "S-1", "status": "COMPLETED", "start_time": "2026-02-15"},
        ]

        result = list_sessions(search="nonexistent-term", limit=100)
        assert result["total"] == 0
        assert result["items"] == []


class TestEvidenceDeduplication:
    """Tests for evidence file deduplication in TypeDB queries."""

    def test_batch_fetch_deduplicates_evidence(self):
        """_batch_fetch_session_relationships should not produce duplicate evidence."""
        from governance.typedb.queries.sessions.read import SessionReadQueries

        class MockClient(SessionReadQueries):
            def _execute_query(self, query):
                if "has-evidence" in query:
                    return [
                        {"sid": "S-1", "src": "evidence/SESSION-A.md"},
                        {"sid": "S-1", "src": "evidence/SESSION-A.md"},
                        {"sid": "S-1", "src": "evidence/SESSION-A.md"},
                        {"sid": "S-1", "src": "evidence/SESSION-B.md"},
                    ]
                return []

        client = MockClient()
        session = MagicMock()
        session.evidence_files = None
        session.linked_rules_applied = None
        session.linked_decisions = None
        session.tasks_completed = 0
        session_map = {"S-1": session}

        client._batch_fetch_session_relationships(session_map)

        assert len(session.evidence_files) == 2
        assert "evidence/SESSION-A.md" in session.evidence_files
        assert "evidence/SESSION-B.md" in session.evidence_files

    def test_build_session_deduplicates_evidence(self):
        """_build_session_from_id should deduplicate evidence files."""
        from governance.typedb.queries.sessions.read import SessionReadQueries

        class MockClient(SessionReadQueries):
            def __init__(self):
                self._call_count = 0

            def _execute_query(self, query):
                if "has evidence-source" in query:
                    return [
                        {"src": "evidence/FILE.md"},
                        {"src": "evidence/FILE.md"},
                        {"src": "evidence/FILE.md"},
                    ]
                if "session-name" in query:
                    return [{"name": "Test"}]
                if "session-description" in query:
                    return [{"desc": "Desc"}]
                if "session-file-path" in query:
                    return []
                if "started-at" in query:
                    return [{"start": "2026-01-01"}]
                if "completed-at" in query:
                    return [{"end": "2026-01-01"}]
                if "agent-id" in query:
                    return []
                if "session-id" in query and "select $s" in query:
                    return [{}]  # Session exists
                if "task-name" in query:
                    return [{"name": "Test", "status": "ACTIVE", "phase": "P10"}]
                if "rule-id" in query:
                    return []
                if "decision-id" in query:
                    return []
                if "completed-task" in query:
                    return []
                if "cc-session-uuid" in query or "cc-project-slug" in query or "cc-git-branch" in query:
                    return []
                if "cc-tool-count" in query or "cc-thinking-chars" in query or "cc-compaction-count" in query:
                    return []
                return []

        client = MockClient()
        session = client._build_session_from_id("TEST-SESSION")

        assert session is not None
        assert len(session.evidence_files) == 1
        assert session.evidence_files[0] == "evidence/FILE.md"

    def test_batch_fetch_skips_none_evidence(self):
        """Should skip None evidence sources."""
        from governance.typedb.queries.sessions.read import SessionReadQueries

        class MockClient(SessionReadQueries):
            def _execute_query(self, query):
                if "has-evidence" in query:
                    return [
                        {"sid": "S-1", "src": None},
                        {"sid": "S-1", "src": "evidence/REAL.md"},
                    ]
                return []

        client = MockClient()
        session = MagicMock()
        session.evidence_files = None
        session.linked_rules_applied = None
        session.linked_decisions = None
        session.tasks_completed = 0
        session_map = {"S-1": session}

        client._batch_fetch_session_relationships(session_map)

        assert len(session.evidence_files) == 1
        assert session.evidence_files[0] == "evidence/REAL.md"
