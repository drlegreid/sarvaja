"""
Unit tests for Session Query Consolidation (EPIC-PERF-TELEM-V1 Phase 3).

Verifies that _build_session_from_id uses consolidated queries instead of
19 individual N+1 queries. Target: <=4 query operations.

BDD Scenarios:
  - Single session fetch uses <=4 queries
  - Status correctly inferred from completed-at
  - Consolidated returns identical data (all fields populated)
  - All 4 relation types fetched
  - Missing attributes return None

Created: 2026-03-26
"""

import sys
import time
from unittest.mock import MagicMock

import pytest

# TEST-GUARD-01: Guard for hatch env where typedb-driver is not installed
if "typedb" not in sys.modules and "typedb.driver" not in sys.modules:
    _typedb_mock = MagicMock()
    sys.modules["typedb"] = _typedb_mock
    sys.modules["typedb.driver"] = _typedb_mock.driver

from governance.typedb.queries.sessions.read import SessionReadQueries
from governance.typedb.entities import Session


# ── Test Helpers ─────────────────────────────────────────


def _make_attr_concept(type_name, value):
    """Create a mock attribute concept with type label and value."""
    c = MagicMock()
    c.get_value.return_value = value
    type_obj = MagicMock()
    label_obj = MagicMock()
    label_obj.name = type_name
    type_obj.get_label.return_value = label_obj
    c.get_type.return_value = type_obj
    return c


def _make_result_row(data_dict):
    """Create a mock TypeDB result row from {var_name: value}."""
    row = MagicMock()
    row.column_names.return_value = list(data_dict.keys())
    concepts = {}
    for k, v in data_dict.items():
        concept = MagicMock()
        concept.get_value.return_value = v
        concepts[k] = concept
    row.get.side_effect = lambda k: concepts.get(k)
    return row


class _CountingSessionReader(SessionReadQueries):
    """Session reader with query counting for consolidation tests."""

    def __init__(self):
        self._connected = True
        self._driver = MagicMock()
        self.database = "test-db"
        self._query_count = 0
        self._total_query_ms = 0.0

    def _execute_query(self, query, infer=False):
        """Count queries (old code path fallback)."""
        self._query_count += 1
        return []

    def _concept_to_value(self, concept):
        """Extract value from concept."""
        if concept is None:
            return None
        if hasattr(concept, "get_value"):
            try:
                return concept.get_value()
            except Exception:
                pass
        return str(concept)

    def _record_query_timing(self, t0, query):
        """Track query timing."""
        duration_ms = (time.monotonic() - t0) * 1000
        self._query_count += 1
        self._total_query_ms += duration_ms


def _setup_attr_query_mock(driver, attrs_dict):
    """Configure driver mock for _fetch_all_session_attrs."""

    def transaction_factory(*args, **kwargs):
        tx = MagicMock()

        def query_handler(query_str):
            qr = MagicMock()
            if "has $a" in query_str:
                rows = []
                for type_name, value in attrs_dict.items():
                    row = MagicMock()
                    row.get.return_value = _make_attr_concept(type_name, value)
                    rows.append(row)
                qr.resolve.return_value = iter(rows)
            else:
                qr.resolve.return_value = iter([])
            return qr

        tx.query.side_effect = query_handler
        tx.__enter__ = MagicMock(return_value=tx)
        tx.__exit__ = MagicMock(return_value=False)
        return tx

    driver.transaction.side_effect = transaction_factory


# ── BDD: Single session fetch uses <=4 queries ──────────


class TestQueryCount:
    """Scenario: Single session fetch uses <=4 queries."""

    def test_build_session_uses_at_most_4_queries(self):
        """_build_session_from_id increments _query_count by at most 4."""
        reader = _CountingSessionReader()
        _setup_attr_query_mock(reader._driver, {
            "session-id": "S-1", "session-name": "Test",
            "started-at": "2026-03-01T09:00:00",
        })
        reader._query_count = 0
        reader._build_session_from_id("S-1")
        assert reader._query_count <= 4, (
            f"Expected <=4 queries, got {reader._query_count}"
        )

    def test_fewer_queries_than_original_19(self):
        """Consolidated approach uses dramatically fewer queries."""
        reader = _CountingSessionReader()
        _setup_attr_query_mock(reader._driver, {
            "session-id": "S-1", "session-name": "Test",
            "started-at": "2026-03-01T09:00:00",
            "agent-id": "code-agent",
        })
        reader._query_count = 0
        reader._build_session_from_id("S-1")
        # Original was 19 queries. Must be at most 4 now.
        assert reader._query_count <= 4


# ── BDD: Status correctly inferred from completed-at ────


class TestStatusInference:
    """Scenario: Status correctly inferred from completed-at."""

    def test_completed_status_when_completed_at_present(self):
        """Session with completed-at is marked COMPLETED."""
        reader = _CountingSessionReader()
        reader._fetch_all_session_attrs = MagicMock(return_value={
            "session-id": "S-1", "session-name": "Done",
            "started-at": "2026-03-01T09:00:00",
            "completed-at": "2026-03-01T13:00:00",
        })
        reader._fetch_session_relations_batch = MagicMock()

        session = reader._build_session_from_id("S-1")

        assert session is not None
        assert session.status == "COMPLETED"
        assert session.completed_at == "2026-03-01T13:00:00"

    def test_active_status_when_started_no_completed(self):
        """Session with started-at but no completed-at is ACTIVE."""
        reader = _CountingSessionReader()
        reader._fetch_all_session_attrs = MagicMock(return_value={
            "session-id": "S-2", "session-name": "Running",
            "started-at": "2026-03-01T09:00:00",
        })
        reader._fetch_session_relations_batch = MagicMock()

        session = reader._build_session_from_id("S-2")

        assert session is not None
        assert session.status == "ACTIVE"

    def test_unknown_status_when_no_started_no_completed(self):
        """Session without started-at or completed-at is UNKNOWN."""
        reader = _CountingSessionReader()
        reader._fetch_all_session_attrs = MagicMock(return_value={
            "session-id": "S-3", "session-name": "Orphan",
        })
        reader._fetch_session_relations_batch = MagicMock()

        session = reader._build_session_from_id("S-3")

        assert session is not None
        assert session.status == "UNKNOWN"


# ── BDD: Consolidated returns identical data ─────────────


_FULL_SESSION_ATTRS = {
    "session-id": "S-FULL",
    "session-name": "Full Session",
    "session-description": "A complete session",
    "session-file-path": "/tmp/session.jsonl",
    "started-at": "2026-03-01T09:00:00",
    "completed-at": "2026-03-01T13:00:00",
    "agent-id": "code-agent",
    "cc-session-uuid": "uuid-1234",
    "cc-project-slug": "sarvaja",
    "cc-git-branch": "master",
    "cc-external-name": "My Session",
    "cc-tool-count": 42,
    "cc-thinking-chars": 10000,
    "cc-compaction-count": 3,
}


class TestConsolidatedData:
    """Scenario: Consolidated returns identical data to original."""

    def test_all_core_attrs_populated(self):
        """All core session attributes are correctly populated."""
        reader = _CountingSessionReader()
        reader._fetch_all_session_attrs = MagicMock(return_value=_FULL_SESSION_ATTRS)
        reader._fetch_session_relations_batch = MagicMock()

        session = reader._build_session_from_id("S-FULL")

        assert session is not None
        assert session.id == "S-FULL"
        assert session.name == "Full Session"
        assert session.description == "A complete session"
        assert session.file_path == "/tmp/session.jsonl"
        assert session.started_at == "2026-03-01T09:00:00"
        assert session.completed_at == "2026-03-01T13:00:00"
        assert session.agent_id == "code-agent"
        assert session.status == "COMPLETED"

    def test_all_cc_attrs_populated(self):
        """All Claude Code session attributes are correctly populated."""
        reader = _CountingSessionReader()
        reader._fetch_all_session_attrs = MagicMock(return_value=_FULL_SESSION_ATTRS)
        reader._fetch_session_relations_batch = MagicMock()

        session = reader._build_session_from_id("S-FULL")

        assert session.cc_session_uuid == "uuid-1234"
        assert session.cc_project_slug == "sarvaja"
        assert session.cc_git_branch == "master"
        assert session.cc_external_name == "My Session"
        assert session.cc_tool_count == 42
        assert session.cc_thinking_chars == 10000
        assert session.cc_compaction_count == 3

    def test_integer_attrs_coerced(self):
        """CC integer attributes are coerced to int."""
        reader = _CountingSessionReader()
        attrs = dict(_FULL_SESSION_ATTRS)
        attrs["cc-tool-count"] = "55"  # string from TypeDB
        reader._fetch_all_session_attrs = MagicMock(return_value=attrs)
        reader._fetch_session_relations_batch = MagicMock()

        session = reader._build_session_from_id("S-FULL")

        assert session.cc_tool_count == 55
        assert isinstance(session.cc_tool_count, int)


# ── BDD: Missing attributes return None ──────────────────


class TestMissingAttrs:
    """Scenario: Missing attributes return None."""

    def test_optional_attrs_default_none(self):
        """Session with only ID has None for all optional attrs."""
        reader = _CountingSessionReader()
        reader._fetch_all_session_attrs = MagicMock(return_value={
            "session-id": "S-MINIMAL",
        })
        reader._fetch_session_relations_batch = MagicMock()

        session = reader._build_session_from_id("S-MINIMAL")

        assert session is not None
        assert session.name is None
        assert session.description is None
        assert session.file_path is None
        assert session.agent_id is None
        assert session.cc_session_uuid is None
        assert session.cc_tool_count is None


# ── BDD: All 4 relation types fetched ───────────────────


class TestRelationsFetched:
    """Scenario: All 4 relation types fetched."""

    def test_all_four_relation_types_populated(self):
        """Session with rules, decisions, evidence, tasks."""
        reader = _CountingSessionReader()
        reader._fetch_all_session_attrs = MagicMock(return_value={
            "session-id": "S-LINKED",
            "session-name": "Linked",
            "started-at": "2026-03-01T09:00:00",
        })

        def populate_rels(sid, session):
            session.linked_rules_applied = ["RULE-001", "RULE-002"]
            session.linked_decisions = ["DEC-001"]
            session.evidence_files = ["evidence/test.json"]
            session.tasks_completed = 3

        reader._fetch_session_relations_batch = MagicMock(side_effect=populate_rels)

        session = reader._build_session_from_id("S-LINKED")

        assert session.linked_rules_applied == ["RULE-001", "RULE-002"]
        assert session.linked_decisions == ["DEC-001"]
        assert session.evidence_files == ["evidence/test.json"]
        assert session.tasks_completed == 3


# ── Edge cases ───────────────────────────────────────────


class TestEdgeCases:

    def test_session_not_found_returns_none(self):
        """Nonexistent session returns None."""
        reader = _CountingSessionReader()
        reader._fetch_all_session_attrs = MagicMock(return_value=None)
        assert reader._build_session_from_id("NONEXIST") is None

    def test_backslash_in_id_escaped(self):
        """Session ID with backslash is properly escaped."""
        reader = _CountingSessionReader()
        reader._fetch_all_session_attrs = MagicMock(return_value={
            "session-id": "S-1\\test",
            "session-name": "Escaped",
        })
        reader._fetch_session_relations_batch = MagicMock()
        session = reader._build_session_from_id("S-1\\test")
        assert session is not None
        call_arg = reader._fetch_all_session_attrs.call_args[0][0]
        assert "\\\\" in call_arg  # backslash was double-escaped

    def test_get_session_delegates_to_build(self):
        """get_session() still returns the same Session."""
        reader = _CountingSessionReader()
        reader._fetch_all_session_attrs = MagicMock(return_value={
            "session-id": "S-99",
            "session-name": "Via get_session",
            "started-at": "2026-03-01T09:00:00",
        })
        reader._fetch_session_relations_batch = MagicMock()

        session = reader.get_session("S-99")
        assert session is not None
        assert session.name == "Via get_session"


# ── Low-level: _fetch_all_session_attrs ──────────────────


class TestFetchAllSessionAttrs:

    def test_returns_attr_dict(self):
        """Returns dict mapping TypeDB attr type labels to values."""
        reader = _CountingSessionReader()
        _setup_attr_query_mock(reader._driver, {
            "session-name": "My Session", "started-at": "2026-03-01",
            "agent-id": "code-agent",
        })
        attrs = reader._fetch_all_session_attrs("S-1")
        assert attrs is not None
        assert attrs["session-name"] == "My Session"
        assert attrs["agent-id"] == "code-agent"

    def test_returns_none_when_empty(self):
        """Returns None when session has no attributes (not found)."""
        reader = _CountingSessionReader()
        _setup_attr_query_mock(reader._driver, {})
        attrs = reader._fetch_all_session_attrs("NONE")
        assert attrs is None

    def test_increments_query_count_by_one(self):
        """Single query operation for all attributes."""
        reader = _CountingSessionReader()
        _setup_attr_query_mock(reader._driver, {
            "session-id": "S-1", "session-name": "X",
        })
        reader._query_count = 0
        reader._fetch_all_session_attrs("S-1")
        assert reader._query_count == 1


# ── Low-level: _fetch_session_relations_batch ────────────


class TestFetchSessionRelationsBatch:

    def test_populates_all_four_relations(self):
        """Batch relation fetch populates all 4 relation types on session."""
        reader = _CountingSessionReader()
        session = Session(id="S-1")

        def transaction_factory(*args, **kwargs):
            tx = MagicMock()
            call_idx = [0]
            responses = [
                [_make_result_row({"rid": "RULE-001"})],     # rules
                [_make_result_row({"did": "DEC-001"})],      # decisions
                [_make_result_row({"src": "ev/test.json"})],  # evidence
                [_make_result_row({"t": "task-iid"})],       # tasks (count)
            ]

            def query_handler(q):
                qr = MagicMock()
                idx = call_idx[0]
                call_idx[0] += 1
                if idx < len(responses):
                    qr.resolve.return_value = iter(responses[idx])
                else:
                    qr.resolve.return_value = iter([])
                return qr

            tx.query.side_effect = query_handler
            tx.__enter__ = MagicMock(return_value=tx)
            tx.__exit__ = MagicMock(return_value=False)
            return tx

        reader._driver.transaction.side_effect = transaction_factory
        reader._fetch_session_relations_batch("S-1", session)

        assert session.linked_rules_applied == ["RULE-001"]
        assert session.linked_decisions == ["DEC-001"]
        assert session.evidence_files == ["ev/test.json"]
        assert session.tasks_completed == 1

    def test_increments_query_count_by_one(self):
        """Single transaction for all relations."""
        reader = _CountingSessionReader()
        session = Session(id="S-1")
        _setup_attr_query_mock(reader._driver, {})
        reader._query_count = 0
        reader._fetch_session_relations_batch("S-1", session)
        assert reader._query_count == 1
