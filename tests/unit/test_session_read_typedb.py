"""
Unit tests for TypeDB Session Read Queries.

Batch 126: Tests for governance/typedb/queries/sessions/read.py
- get_all_sessions: batch fetch with attributes + relationships
- _batch_fetch_session_attributes: attribute mapping + status inference
- _batch_fetch_session_relationships: rules, decisions, evidence, tasks
- _build_session_from_id: single session hydration
- get_session: exists check + build
- get_tasks_for_session: linked task query
"""

from unittest.mock import MagicMock

from governance.typedb.queries.sessions.read import SessionReadQueries


def _make_client(query_results=None):
    """Create a mock client with SessionReadQueries mixed in."""

    class MockClient(SessionReadQueries):
        pass

    client = MockClient()
    # Default: return empty list for any query
    client._execute_query = MagicMock(return_value=query_results or [])
    return client


# ── get_all_sessions ─────────────────────────────────────


class TestGetAllSessions:
    """Tests for get_all_sessions() method."""

    def test_empty_results(self):
        client = _make_client([])
        assert client.get_all_sessions() == []

    def test_returns_session_objects(self):
        client = _make_client()
        # First call: session IDs; subsequent calls: attributes/relationships
        client._execute_query = MagicMock(side_effect=[
            [{"id": "S-1"}, {"id": "S-2"}],  # get_all_sessions query
            # _batch_fetch_session_attributes: 8 attr queries + 3 CC int + 1 completed-at
            [], [], [], [], [],  # name, desc, path, started_at, agent_id
            [], [], [],  # cc_session_uuid, cc_project_slug, cc_git_branch
            [], [], [],  # cc_tool_count, cc_thinking_chars, cc_compaction_count
            [],  # completed-at
            # _batch_fetch_session_relationships: 4 queries
            [], [], [], [],  # rules, decisions, evidence, tasks
        ])

        sessions = client.get_all_sessions()
        assert len(sessions) == 2
        assert sessions[0].id == "S-1"
        assert sessions[1].id == "S-2"

    def test_sets_completed_status(self):
        client = _make_client()
        client._execute_query = MagicMock(side_effect=[
            [{"id": "S-1"}, {"id": "S-2"}],
            [], [], [], [], [],  # 5 attr queries
            [], [], [],  # cc_session_uuid, cc_project_slug, cc_git_branch
            [], [], [],  # cc_tool_count, cc_thinking_chars, cc_compaction_count
            [{"id": "S-1", "v": "2026-02-11T10:00:00"}],  # completed-at: only S-1
            [], [], [], [],  # relationships
        ])

        sessions = client.get_all_sessions()
        session_map = {s.id: s for s in sessions}
        assert session_map["S-1"].status == "COMPLETED"
        assert session_map["S-2"].status == "ACTIVE"

    def test_populates_attributes(self):
        client = _make_client()
        client._execute_query = MagicMock(side_effect=[
            [{"id": "S-1"}],
            [{"id": "S-1", "v": "Session One"}],  # name
            [{"id": "S-1", "v": "Test session"}],  # description
            [],  # file_path
            [{"id": "S-1", "v": "2026-02-11T08:00:00"}],  # started_at
            [{"id": "S-1", "v": "code-agent"}],  # agent_id
            [], [], [],  # cc_session_uuid, cc_project_slug, cc_git_branch
            [], [], [],  # cc_tool_count, cc_thinking_chars, cc_compaction_count
            [],  # completed-at
            [], [], [], [],  # relationships
        ])

        sessions = client.get_all_sessions()
        s = sessions[0]
        assert s.name == "Session One"
        assert s.description == "Test session"
        assert s.agent_id == "code-agent"

    def test_populates_relationships(self):
        client = _make_client()
        client._execute_query = MagicMock(side_effect=[
            [{"id": "S-1"}],
            [], [], [], [], [],  # 5 attr queries
            [], [], [],  # cc_session_uuid, cc_project_slug, cc_git_branch
            [], [], [],  # cc_tool_count, cc_thinking_chars, cc_compaction_count
            [],  # completed-at
            [{"sid": "S-1", "rid": "RULE-001"}],  # rules
            [{"sid": "S-1", "did": "DEC-001"}],  # decisions
            [{"sid": "S-1", "src": "evidence/test.md"}],  # evidence
            [{"sid": "S-1", "t": "mock"}],  # tasks
        ])

        sessions = client.get_all_sessions()
        s = sessions[0]
        assert "RULE-001" in s.linked_rules_applied
        assert "DEC-001" in s.linked_decisions
        assert "evidence/test.md" in s.evidence_files
        assert s.tasks_completed == 1

    def test_attribute_query_error_silenced(self):
        """Attribute query errors should not break the overall fetch."""
        client = _make_client()
        call_count = [0]

        def side_effect(q):
            call_count[0] += 1
            if call_count[0] == 1:
                return [{"id": "S-1"}]
            # 8 string attr queries + 3 CC int queries = 11 queries (calls 2-12)
            if call_count[0] <= 12:
                raise Exception("TypeDB attr error")
            if call_count[0] == 13:
                return []  # completed-at
            return []

        client._execute_query = MagicMock(side_effect=side_effect)
        sessions = client.get_all_sessions()
        assert len(sessions) == 1
        assert sessions[0].status == "ACTIVE"

    def test_filters_none_session_ids(self):
        client = _make_client()
        client._execute_query = MagicMock(side_effect=[
            [{"id": "S-1"}, {"id": None}, {"other": "val"}],
            [], [], [], [], [],  # 5 attr queries
            [], [], [],  # cc string attrs
            [], [], [],  # cc int attrs
            [],  # completed-at
            [], [], [], [],  # relationships
        ])
        sessions = client.get_all_sessions()
        assert len(sessions) == 1


# ── _build_session_from_id ───────────────────────────────


class TestBuildSessionFromId:
    """Tests for _build_session_from_id() method."""

    def test_minimal_session(self):
        client = _make_client()
        # All queries return empty (no optional attrs)
        client._execute_query = MagicMock(return_value=[])

        session = client._build_session_from_id("S-1")
        assert session.id == "S-1"
        assert session.status == "ACTIVE"
        assert session.tasks_completed == 0

    def test_completed_session(self):
        client = _make_client()
        call_count = [0]

        def side_effect(q):
            call_count[0] += 1
            if "completed-at" in q:
                return [{"end": "2026-02-11T12:00:00"}]
            return []

        client._execute_query = MagicMock(side_effect=side_effect)
        session = client._build_session_from_id("S-1")
        assert session.status == "COMPLETED"
        assert session.completed_at == "2026-02-11T12:00:00"

    def test_populates_all_optional_attrs(self):
        client = _make_client()

        def side_effect(q):
            if "session-name" in q:
                return [{"name": "My Session"}]
            if "session-description" in q:
                return [{"desc": "A description"}]
            if "session-file-path" in q:
                return [{"path": "/tmp/session.jsonl"}]
            if "started-at" in q:
                return [{"start": "2026-02-11T08:00:00"}]
            if "agent-id" in q:
                return [{"agent": "research-agent"}]
            return []

        client._execute_query = MagicMock(side_effect=side_effect)
        session = client._build_session_from_id("S-1")
        assert session.name == "My Session"
        assert session.description == "A description"
        assert session.file_path == "/tmp/session.jsonl"
        assert session.agent_id == "research-agent"

    def test_populates_relationships(self):
        client = _make_client()

        def side_effect(q):
            if "session-applied-rule" in q:
                return [{"rid": "R-1"}, {"rid": "R-2"}]
            if "session-decision" in q:
                return [{"did": "D-1"}]
            if "has-evidence" in q:
                return [{"src": "evidence/test.md"}]
            if "completed-in" in q:
                return [{"t": "mock1"}, {"t": "mock2"}]
            return []

        client._execute_query = MagicMock(side_effect=side_effect)
        session = client._build_session_from_id("S-1")
        assert session.linked_rules_applied == ["R-1", "R-2"]
        assert session.linked_decisions == ["D-1"]
        assert session.evidence_files == ["evidence/test.md"]
        assert session.tasks_completed == 2


# ── get_session ──────────────────────────────────────────


class TestGetSession:
    """Tests for get_session() method."""

    def test_not_found(self):
        client = _make_client([])
        result = client.get_session("MISSING")
        assert result is None

    def test_found_returns_session(self):
        client = _make_client()
        call_count = [0]

        def side_effect(q):
            call_count[0] += 1
            if call_count[0] == 1:
                return [{"s": "exists"}]  # existence check
            return []

        client._execute_query = MagicMock(side_effect=side_effect)
        result = client.get_session("S-1")
        assert result is not None
        assert result.id == "S-1"


# ── get_tasks_for_session ────────────────────────────────


class TestGetTasksForSession:
    """Tests for get_tasks_for_session() method."""

    def test_returns_task_dicts(self):
        client = _make_client([
            {"tid": "T-1", "name": "Task One", "status": "OPEN"},
            {"tid": "T-2", "name": "Task Two", "status": "CLOSED"},
        ])
        result = client.get_tasks_for_session("S-1")
        assert len(result) == 2
        assert result[0]["task_id"] == "T-1"
        assert result[1]["status"] == "CLOSED"

    def test_empty_results(self):
        client = _make_client([])
        result = client.get_tasks_for_session("S-1")
        assert result == []

    def test_query_contains_session_id(self):
        client = _make_client([])
        client.get_tasks_for_session("SESSION-2026-02-11-TEST")
        query = client._execute_query.call_args[0][0]
        assert "SESSION-2026-02-11-TEST" in query
        assert "completed-in" in query


# ── CC Field Read Tests (SESSION-CC-01-v1) ─────────────


class TestBatchFetchCCAttributes:
    """Tests for CC field queries in _batch_fetch_session_attributes."""

    def test_cc_string_attrs_populated(self):
        client = _make_client()
        client._execute_query = MagicMock(side_effect=[
            [{"id": "S-1"}],
            [], [], [], [], [],  # 5 base attrs
            [{"id": "S-1", "v": "abc-123"}],  # cc_session_uuid
            [{"id": "S-1", "v": "sarvaja-platform"}],  # cc_project_slug
            [{"id": "S-1", "v": "master"}],  # cc_git_branch
            [], [], [],  # cc int attrs
            [],  # completed-at
            [], [], [], [],  # relationships
        ])
        sessions = client.get_all_sessions()
        s = sessions[0]
        assert s.cc_session_uuid == "abc-123"
        assert s.cc_project_slug == "sarvaja-platform"
        assert s.cc_git_branch == "master"

    def test_cc_int_attrs_populated(self):
        client = _make_client()
        client._execute_query = MagicMock(side_effect=[
            [{"id": "S-1"}],
            [], [], [], [], [],  # 5 base attrs
            [], [], [],  # cc string attrs
            [{"id": "S-1", "v": 42}],  # cc_tool_count
            [{"id": "S-1", "v": 15000}],  # cc_thinking_chars
            [{"id": "S-1", "v": 3}],  # cc_compaction_count
            [],  # completed-at
            [], [], [], [],  # relationships
        ])
        sessions = client.get_all_sessions()
        s = sessions[0]
        assert s.cc_tool_count == 42
        assert s.cc_thinking_chars == 15000
        assert s.cc_compaction_count == 3

    def test_cc_attrs_default_none(self):
        client = _make_client()
        client._execute_query = MagicMock(side_effect=[
            [{"id": "S-1"}],
            [], [], [], [], [],  # 5 base attrs
            [], [], [],  # cc string attrs (empty)
            [], [], [],  # cc int attrs (empty)
            [],  # completed-at
            [], [], [], [],  # relationships
        ])
        sessions = client.get_all_sessions()
        s = sessions[0]
        assert s.cc_session_uuid is None
        assert s.cc_project_slug is None
        assert s.cc_tool_count is None


class TestBuildSessionCCAttributes:
    """Tests for CC field queries in _build_session_from_id."""

    def test_cc_fields_populated(self):
        client = _make_client()

        def side_effect(q):
            if "cc-session-uuid" in q:
                return [{"v": "uuid-abc-123"}]
            if "cc-project-slug" in q:
                return [{"v": "my-project"}]
            if "cc-git-branch" in q:
                return [{"v": "feature-x"}]
            if "cc-tool-count" in q:
                return [{"v": 55}]
            if "cc-thinking-chars" in q:
                return [{"v": 20000}]
            if "cc-compaction-count" in q:
                return [{"v": 2}]
            return []

        client._execute_query = MagicMock(side_effect=side_effect)
        session = client._build_session_from_id("S-1")
        assert session.cc_session_uuid == "uuid-abc-123"
        assert session.cc_project_slug == "my-project"
        assert session.cc_git_branch == "feature-x"
        assert session.cc_tool_count == 55
        assert session.cc_thinking_chars == 20000
        assert session.cc_compaction_count == 2

    def test_cc_fields_none_when_missing(self):
        client = _make_client()
        client._execute_query = MagicMock(return_value=[])
        session = client._build_session_from_id("S-1")
        assert session.cc_session_uuid is None
        assert session.cc_project_slug is None
        assert session.cc_tool_count is None
