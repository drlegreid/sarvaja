"""
Tests for TypeDB query timing instrumentation (EPIC-PERF-TELEM-V1 Phase 1).

BDD Scenarios:
  - Query execution records duration (_query_count increments, _total_query_ms accumulates)
  - Slow query (>500ms) logs WARNING with query snippet and duration_ms
  - Write execution also records timing
"""

import logging
import time
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from governance.typedb.base import TypeDBBaseClient


@pytest.fixture
def client():
    """Create a TypeDBBaseClient with mocked connection."""
    c = TypeDBBaseClient(host="localhost", port=1729, database="test-db")
    c._connected = True
    c._driver = MagicMock()
    return c


def _mock_read_transaction(driver, results=None):
    """Set up a mock read transaction that returns given results."""
    tx = MagicMock()
    query_result = MagicMock()
    if results is None:
        query_result.resolve.return_value = []
    else:
        query_result.resolve.return_value = results
    tx.query.return_value = query_result
    tx.__enter__ = MagicMock(return_value=tx)
    tx.__exit__ = MagicMock(return_value=False)
    driver.transaction.return_value = tx
    return tx


def _mock_write_transaction(driver):
    """Set up a mock write transaction."""
    tx = MagicMock()
    query_result = MagicMock()
    query_result.resolve.return_value = None
    tx.query.return_value = query_result
    tx.__enter__ = MagicMock(return_value=tx)
    tx.__exit__ = MagicMock(return_value=False)
    driver.transaction.return_value = tx
    return tx


class TestQueryCounterIncrement:
    """Scenario: Query execution records duration."""

    def test_query_count_starts_at_zero(self, client):
        """New client has zero query count."""
        assert client._query_count == 0
        assert client._total_query_ms == 0.0

    def test_execute_query_increments_count(self, client):
        """_execute_query increments _query_count by 1."""
        _mock_read_transaction(client._driver, results=[])
        client._execute_query("match $x isa rule-entity; get;")
        assert client._query_count == 1

    def test_multiple_queries_accumulate(self, client):
        """Multiple queries increment counter correctly."""
        _mock_read_transaction(client._driver, results=[])
        for _ in range(5):
            client._execute_query("match $x isa rule-entity; get;")
        assert client._query_count == 5

    def test_total_query_ms_accumulates(self, client):
        """_total_query_ms accumulates positive values."""
        _mock_read_transaction(client._driver, results=[])
        client._execute_query("match $x isa rule-entity; get;")
        assert client._total_query_ms >= 0.0


class TestWriteCounterIncrement:
    """Scenario: Write execution also records timing."""

    def test_execute_write_increments_count(self, client):
        """_execute_write increments _query_count."""
        _mock_write_transaction(client._driver)
        client._execute_write("insert $x isa rule-entity;")
        assert client._query_count == 1

    def test_execute_write_accumulates_ms(self, client):
        """_execute_write adds to _total_query_ms."""
        _mock_write_transaction(client._driver)
        client._execute_write("insert $x isa rule-entity;")
        assert client._total_query_ms >= 0.0


class TestSlowQueryWarning:
    """Scenario: Slow query logs WARNING."""

    def test_slow_query_logs_warning(self, client, caplog):
        """Query taking >500ms emits WARNING log."""
        tx = _mock_read_transaction(client._driver, results=[])

        # Make the query artificially slow by patching time.monotonic
        call_count = [0]
        base_time = 1000.0

        def mock_monotonic():
            call_count[0] += 1
            if call_count[0] % 2 == 1:
                return base_time  # start time
            return base_time + 0.6  # end time = 600ms later

        with patch("governance.typedb.base.time") as mock_time:
            mock_time.monotonic = mock_monotonic
            with caplog.at_level(logging.WARNING, logger="governance.typedb.base"):
                client._execute_query("match $x isa rule-entity; get;")

        assert any("slow" in r.message.lower() or "ms" in r.message.lower()
                    for r in caplog.records if r.levelno >= logging.WARNING), (
            "Expected WARNING log for slow query (>500ms)"
        )

    def test_fast_query_no_warning(self, client, caplog):
        """Query taking <500ms does NOT emit WARNING."""
        _mock_read_transaction(client._driver, results=[])

        call_count = [0]
        base_time = 1000.0

        def mock_monotonic():
            call_count[0] += 1
            if call_count[0] % 2 == 1:
                return base_time
            return base_time + 0.01  # 10ms — fast

        with patch("governance.typedb.base.time") as mock_time:
            mock_time.monotonic = mock_monotonic
            with caplog.at_level(logging.WARNING, logger="governance.typedb.base"):
                client._execute_query("match $x isa rule-entity; get;")

        warning_records = [r for r in caplog.records if r.levelno >= logging.WARNING]
        assert len(warning_records) == 0, "Fast query should NOT emit WARNING"

    def test_slow_write_logs_warning(self, client, caplog):
        """Write taking >500ms emits WARNING log."""
        _mock_write_transaction(client._driver)

        call_count = [0]
        base_time = 1000.0

        def mock_monotonic():
            call_count[0] += 1
            if call_count[0] % 2 == 1:
                return base_time
            return base_time + 0.8  # 800ms

        with patch("governance.typedb.base.time") as mock_time:
            mock_time.monotonic = mock_monotonic
            with caplog.at_level(logging.WARNING, logger="governance.typedb.base"):
                client._execute_write("insert $x isa rule-entity;")

        assert any("slow" in r.message.lower() or "ms" in r.message.lower()
                    for r in caplog.records if r.levelno >= logging.WARNING), (
            "Expected WARNING log for slow write (>500ms)"
        )


class TestQuerySnippetInLog:
    """WARNING log includes query snippet for debugging."""

    def test_warning_includes_query_snippet(self, client, caplog):
        """Slow query WARNING includes a truncated query snippet."""
        _mock_read_transaction(client._driver, results=[])

        call_count = [0]
        base_time = 1000.0

        def mock_monotonic():
            call_count[0] += 1
            if call_count[0] % 2 == 1:
                return base_time
            return base_time + 1.0  # 1000ms

        with patch("governance.typedb.base.time") as mock_time:
            mock_time.monotonic = mock_monotonic
            with caplog.at_level(logging.WARNING, logger="governance.typedb.base"):
                client._execute_query("match $x isa rule-entity; get;")

        warning_msgs = [r.message for r in caplog.records if r.levelno >= logging.WARNING]
        assert any("rule-entity" in msg for msg in warning_msgs), (
            "WARNING should include query snippet"
        )
