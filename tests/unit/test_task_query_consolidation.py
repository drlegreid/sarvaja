"""
Unit tests for Task Query Consolidation (EPIC-PERF-TELEM-V1 Phase 2).

Verifies that _build_task_from_id uses consolidated queries instead of
28 individual N+1 queries. Target: <=5 query operations.

BDD Scenarios:
  - Single task fetch uses <=5 queries
  - Consolidated returns identical data to original
  - Missing attributes return None without error
  - All 5 relation types fetched

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

from governance.typedb.queries.tasks.read import TaskReadQueries
from governance.typedb.entities import Task


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


class _CountingTaskReader(TaskReadQueries):
    """Task reader with query counting for consolidation tests.

    Provides _execute_query (for old code path) and
    _record_query_timing + _concept_to_value (for new code path).
    """

    def __init__(self):
        self._connected = True
        self._driver = MagicMock()
        self.database = "test-db"
        self._query_count = 0
        self._total_query_ms = 0.0

    def _execute_query(self, query, infer=False):
        """Count queries and return generic results (old code path)."""
        self._query_count += 1
        return [{"name": "Test", "status": "OPEN", "phase": "P1"}]

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
        """Track query timing (new code path)."""
        duration_ms = (time.monotonic() - t0) * 1000
        self._query_count += 1
        self._total_query_ms += duration_ms


def _setup_attr_query_mock(driver, attrs_dict):
    """Configure driver mock for _fetch_all_entity_attrs."""

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


# ── BDD: Single task fetch uses <=5 queries ──────────────


class TestQueryCount:
    """Scenario: Single task fetch uses <=5 queries."""

    def test_build_task_uses_at_most_5_queries(self):
        """_build_task_from_id increments _query_count by at most 5."""
        reader = _CountingTaskReader()
        # Mock driver for new code path
        _setup_attr_query_mock(reader._driver, {
            "task-id": "T-1", "task-name": "Test",
            "task-status": "OPEN", "phase": "P1",
        })
        reader._query_count = 0
        reader._build_task_from_id("T-1")
        assert reader._query_count <= 5, (
            f"Expected <=5 queries, got {reader._query_count}"
        )


# ── BDD: Consolidated returns identical data ─────────────


_FULL_ATTRS = {
    "task-id": "T-1", "task-name": "Test Task",
    "task-status": "OPEN", "phase": "P1",
    "task-body": "body text", "task-resolution": "NONE",
    "gap-reference": "GAP-001", "agent-id": "code-agent",
    "task-evidence": "ev.json",
    "task-completed-at": "2026-03-01",
    "task-created-at": "2026-02-01",
    "task-claimed-at": "2026-02-15",
    "task-business": "biz", "task-design": "design",
    "task-architecture": "arch", "task-test": "test plan",
    "item-type": "task", "document-path": "docs/foo.md",
    "task-priority": "HIGH", "task-type": "feature",
    "task-summary": "summary", "resolution-notes": "notes",
    "task-layer": "api", "task-concern": "perf",
    "task-method": "automated",
}


class TestConsolidatedData:
    """Scenario: Consolidated returns identical data to original."""

    def test_all_optional_attrs_populated(self):
        """All 22 optional attributes are correctly populated."""
        reader = _CountingTaskReader()
        reader._fetch_all_entity_attrs = MagicMock(return_value=_FULL_ATTRS)
        reader._fetch_task_relations_batch = MagicMock()

        task = reader._build_task_from_id("T-1")

        assert task is not None
        assert task.id == "T-1"
        assert task.name == "Test Task"
        assert task.status == "OPEN"
        assert task.phase == "P1"
        assert task.body == "body text"
        assert task.resolution == "NONE"
        assert task.gap_id == "GAP-001"
        assert task.agent_id == "code-agent"
        assert task.evidence == "ev.json"
        assert task.completed_at == "2026-03-01"
        assert task.created_at == "2026-02-01"
        assert task.claimed_at == "2026-02-15"
        assert task.business == "biz"
        assert task.design == "design"
        assert task.architecture == "arch"
        assert task.test_section == "test plan"
        assert task.item_type == "task"
        assert task.document_path == "docs/foo.md"
        assert task.priority == "HIGH"
        assert task.task_type == "feature"
        assert task.summary == "summary"
        assert task.resolution_notes == "notes"
        assert task.layer == "api"
        assert task.concern == "perf"
        assert task.method == "automated"


# ── BDD: Missing attributes return None ──────────────────


class TestMissingAttrs:
    """Scenario: Missing attributes return None."""

    def test_optional_attrs_default_none(self):
        """Task with only core fields has None for all optional attrs."""
        reader = _CountingTaskReader()
        attrs = {
            "task-id": "T-2", "task-name": "Minimal",
            "task-status": "OPEN", "phase": "P1",
        }
        reader._fetch_all_entity_attrs = MagicMock(return_value=attrs)
        reader._fetch_task_relations_batch = MagicMock()

        task = reader._build_task_from_id("T-2")

        assert task is not None
        assert task.name == "Minimal"
        for attr in ("body", "agent_id", "priority", "layer", "concern",
                     "method", "summary", "evidence", "gap_id"):
            assert getattr(task, attr) is None, f"{attr} should be None"


# ── BDD: All 5 relation types fetched ────────────────────


class TestRelationsFetched:
    """Scenario: All 5 relation types fetched."""

    def test_all_five_relation_types_populated(self):
        """Task with rules, sessions, commits, documents, workspace."""
        reader = _CountingTaskReader()
        reader._fetch_all_entity_attrs = MagicMock(return_value={
            "task-id": "T-3", "task-name": "Linked",
            "task-status": "OPEN", "phase": "P1",
        })

        def populate_rels(tid, task):
            task.linked_rules = ["RULE-001", "RULE-002"]
            task.linked_sessions = ["S-1"]
            task.linked_commits = ["abc123", "def456", "789ghi"]
            task.linked_documents = ["docs/foo.md"]
            task.workspace_id = "WS-1"

        reader._fetch_task_relations_batch = MagicMock(side_effect=populate_rels)

        task = reader._build_task_from_id("T-3")

        assert task.linked_rules == ["RULE-001", "RULE-002"]
        assert task.linked_sessions == ["S-1"]
        assert len(task.linked_commits) == 3
        assert task.linked_documents == ["docs/foo.md"]
        assert task.workspace_id == "WS-1"


# ── Edge cases ───────────────────────────────────────────


class TestEdgeCases:

    def test_task_not_found_returns_none(self):
        """Nonexistent task returns None."""
        reader = _CountingTaskReader()
        reader._fetch_all_entity_attrs = MagicMock(return_value=None)
        assert reader._build_task_from_id("NONEXIST") is None

    def test_backslash_in_id_escaped(self):
        """Task ID with backslash is properly escaped."""
        reader = _CountingTaskReader()
        reader._fetch_all_entity_attrs = MagicMock(return_value={
            "task-id": "T-1\\test", "task-name": "Esc",
            "task-status": "OPEN", "phase": "P1",
        })
        reader._fetch_task_relations_batch = MagicMock()
        task = reader._build_task_from_id("T-1\\test")
        assert task is not None
        call_arg = reader._fetch_all_entity_attrs.call_args[0][0]
        assert "\\\\" in call_arg  # backslash was double-escaped


# ── Low-level: _fetch_all_entity_attrs ───────────────────


class TestFetchAllEntityAttrs:

    def test_returns_attr_dict(self):
        """Returns dict mapping TypeDB attr type labels to values."""
        reader = _CountingTaskReader()
        _setup_attr_query_mock(reader._driver, {
            "task-name": "My Task", "task-status": "OPEN",
            "phase": "P1", "task-body": "body text",
        })
        attrs = reader._fetch_all_entity_attrs("T-1")
        assert attrs is not None
        assert attrs["task-name"] == "My Task"
        assert attrs["task-body"] == "body text"

    def test_returns_none_when_empty(self):
        """Returns None when task has no attributes (not found)."""
        reader = _CountingTaskReader()
        _setup_attr_query_mock(reader._driver, {})
        attrs = reader._fetch_all_entity_attrs("NONE")
        assert attrs is None

    def test_increments_query_count_by_one(self):
        """Single query operation for all attributes."""
        reader = _CountingTaskReader()
        _setup_attr_query_mock(reader._driver, {
            "task-id": "T-1", "task-name": "X",
            "task-status": "OPEN", "phase": "P1",
        })
        reader._query_count = 0
        reader._fetch_all_entity_attrs("T-1")
        assert reader._query_count == 1


# ── Low-level: _fetch_task_relations_batch ───────────────


class TestFetchTaskRelationsBatch:

    def test_populates_all_five_relations(self):
        """Batch relation fetch populates all 5 relation types on task."""
        reader = _CountingTaskReader()
        task = Task(id="T-1", name="Test", status="OPEN", phase="P1")

        def transaction_factory(*args, **kwargs):
            tx = MagicMock()
            call_idx = [0]
            responses = [
                [_make_result_row({"rid": "RULE-001"})],
                [_make_result_row({"sid": "S-1"})],
                [_make_result_row({"sha": "abc"})],
                [_make_result_row({"dpath": "docs/f.md"})],
                [_make_result_row({"wid": "WS-1"})],
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
        reader._fetch_task_relations_batch("T-1", task)

        assert task.linked_rules == ["RULE-001"]
        assert task.linked_sessions == ["S-1"]
        assert task.linked_commits == ["abc"]
        assert task.linked_documents == ["docs/f.md"]
        assert task.workspace_id == "WS-1"

    def test_increments_query_count_by_one(self):
        """Single query operation for all relations (batch)."""
        reader = _CountingTaskReader()
        task = Task(id="T-1", name="Test", status="OPEN", phase="P1")
        _setup_attr_query_mock(reader._driver, {})  # empty responses
        reader._query_count = 0
        reader._fetch_task_relations_batch("T-1", task)
        assert reader._query_count == 1


# ── Backward compat: get_task delegates to _build_task_from_id ───


class TestGetTaskDelegates:

    def test_get_task_calls_build(self):
        """get_task(id) still returns the same Task."""
        reader = _CountingTaskReader()
        reader._fetch_all_entity_attrs = MagicMock(return_value={
            "task-id": "T-99", "task-name": "Via get_task",
            "task-status": "DONE", "phase": "P2",
        })
        reader._fetch_task_relations_batch = MagicMock()

        task = reader.get_task("T-99")
        assert task is not None
        assert task.name == "Via get_task"
        assert task.status == "DONE"
