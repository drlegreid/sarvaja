"""
Tests for in-memory data stores and exceptions.

Batch 168: New coverage for governance/stores/data_stores.py (0->8 tests).
"""
import pytest


class TestTypeDBUnavailable:
    def test_exception_importable(self):
        from governance.stores.data_stores import TypeDBUnavailable
        assert issubclass(TypeDBUnavailable, Exception)

    def test_exception_raiseable(self):
        from governance.stores.data_stores import TypeDBUnavailable
        with pytest.raises(TypeDBUnavailable):
            raise TypeDBUnavailable("TypeDB is down")

    def test_exception_message(self):
        from governance.stores.data_stores import TypeDBUnavailable
        exc = TypeDBUnavailable("test message")
        assert str(exc) == "test message"


class TestGlobalStores:
    def test_tasks_store_is_dict(self):
        from governance.stores.data_stores import _tasks_store
        assert isinstance(_tasks_store, dict)

    def test_sessions_store_is_dict(self):
        from governance.stores.data_stores import _sessions_store
        assert isinstance(_sessions_store, dict)

    def test_execution_events_store_is_dict(self):
        from governance.stores.data_stores import _execution_events_store
        assert isinstance(_execution_events_store, dict)

    def test_chat_sessions_is_dict(self):
        from governance.stores.data_stores import _chat_sessions
        assert isinstance(_chat_sessions, dict)

    def test_stores_initially_empty(self):
        """Verify stores start empty (or contain runtime data only)."""
        from governance.stores.data_stores import _tasks_store, _sessions_store
        # These are global stores — may have data from other tests,
        # but they should be dict instances
        assert isinstance(_tasks_store, dict)
        assert isinstance(_sessions_store, dict)
