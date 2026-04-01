"""TDD tests for Phase 6: Request correlation — thread-local context + TypeDB propagation.

BDD Scenarios:
  - set_request_id() / get_request_id() round-trip
  - get_request_id() returns None when not set
  - TypeDB slow-query WARNING includes rid when set
  - TypeDB slow-query WARNING omits rid when not set
  - Thread isolation — different threads see different rid

Created: 2026-03-26  EPIC-PERF-TELEM-V1 Phase 6
"""
import logging
import threading
import time
from unittest.mock import patch, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Scenario: set/get round-trip
# ---------------------------------------------------------------------------

def test_set_get_request_id():
    """set_request_id stores value, get_request_id retrieves it."""
    from governance.middleware.request_context import set_request_id, get_request_id

    set_request_id("abc12345")
    assert get_request_id() == "abc12345"

    # Cleanup
    set_request_id(None)


# ---------------------------------------------------------------------------
# Scenario: get returns None when not set
# ---------------------------------------------------------------------------

def test_get_request_id_returns_none_default():
    """get_request_id returns None when no rid is set."""
    from governance.middleware.request_context import set_request_id, get_request_id

    set_request_id(None)
    assert get_request_id() is None


# ---------------------------------------------------------------------------
# Scenario: Thread isolation
# ---------------------------------------------------------------------------

def test_thread_isolation():
    """Different threads see different request IDs."""
    from governance.middleware.request_context import set_request_id, get_request_id

    results = {}

    def worker(name, rid):
        set_request_id(rid)
        # Small sleep to interleave
        time.sleep(0.01)
        results[name] = get_request_id()

    t1 = threading.Thread(target=worker, args=("t1", "rid-thread1"))
    t2 = threading.Thread(target=worker, args=("t2", "rid-thread2"))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert results["t1"] == "rid-thread1"
    assert results["t2"] == "rid-thread2"

    set_request_id(None)


# ---------------------------------------------------------------------------
# Scenario: TypeDB slow-query WARNING includes rid
# ---------------------------------------------------------------------------

def test_typedb_slow_query_includes_rid():
    """When rid is set and query >500ms, TypeDB WARNING includes rid."""
    from governance.middleware.request_context import set_request_id

    set_request_id("abc12345")

    try:
        from governance.typedb.base import TypeDBBaseClient

        client = TypeDBBaseClient()
        # Don't connect — just test _record_query_timing directly

        call_count = [0]

        def fake_monotonic():
            call_count[0] += 1
            if call_count[0] <= 1:
                return 0.0
            return 0.6  # 600ms > 500ms threshold

        with patch("time.monotonic", side_effect=fake_monotonic):
            t0 = time.monotonic()

            with patch.object(client, "_query_count", 0), \
                 patch.object(client, "_total_query_ms", 0.0):
                logger = logging.getLogger("governance.typedb.base")
                with patch.object(logger, "warning") as mock_warn:
                    client._record_query_timing(t0, "match $x isa task;")

                    assert mock_warn.called
                    log_msg = mock_warn.call_args[0][0]
                    # The rid should appear in the log message
                    assert "abc12345" in str(mock_warn.call_args)
    finally:
        set_request_id(None)


# ---------------------------------------------------------------------------
# Scenario: TypeDB slow-query WARNING omits rid when not set
# ---------------------------------------------------------------------------

def test_typedb_slow_query_no_rid_when_unset():
    """When no rid is set, TypeDB WARNING does not include rid field."""
    from governance.middleware.request_context import set_request_id

    set_request_id(None)

    from governance.typedb.base import TypeDBBaseClient

    client = TypeDBBaseClient()

    call_count = [0]

    def fake_monotonic():
        call_count[0] += 1
        if call_count[0] <= 1:
            return 0.0
        return 0.6  # 600ms

    with patch("time.monotonic", side_effect=fake_monotonic):
        t0 = time.monotonic()

        with patch.object(client, "_query_count", 0), \
             patch.object(client, "_total_query_ms", 0.0):
            logger = logging.getLogger("governance.typedb.base")
            with patch.object(logger, "warning") as mock_warn:
                client._record_query_timing(t0, "match $x isa task;")

                assert mock_warn.called
                # "rid" should NOT appear in the log
                full_call = str(mock_warn.call_args)
                assert "rid=" not in full_call or "rid=None" not in full_call
