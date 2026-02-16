"""
Unit tests for session_persistence.py (GAP-SESSION-TRANSCRIPT-001).

Tests disk-backed persistence for _sessions_store tool_calls/thoughts.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from governance.stores.session_persistence import (
    persist_session,
    load_persisted_sessions,
    cleanup_persisted,
    _PERSIST_KEYS,
)


@pytest.fixture
def store_dir(tmp_path):
    """Override _STORE_DIR to use tmp directory."""
    d = tmp_path / "session_store"
    d.mkdir()
    with patch("governance.stores.session_persistence._STORE_DIR", d):
        yield d


class TestPersistSession:
    def test_writes_json_file(self, store_dir):
        data = {
            "tool_calls": [{"tool_name": "Bash", "timestamp": "2026-02-15T10:00:00"}],
            "thoughts": [{"thought": "test", "timestamp": "2026-02-15T10:00:01"}],
        }
        persist_session("SESSION-TEST", data)

        path = store_dir / "SESSION-TEST.json"
        assert path.exists()
        loaded = json.loads(path.read_text())
        assert len(loaded["tool_calls"]) == 1
        assert loaded["tool_calls"][0]["tool_name"] == "Bash"

    def test_only_persists_relevant_keys(self, store_dir):
        data = {
            "session_id": "SESSION-TEST",
            "start_time": "2026-02-15T10:00:00",
            "status": "ACTIVE",
            "tool_calls": [{"tool_name": "Read"}],
            "thoughts": [],
            "topic": "my-topic",
        }
        persist_session("SESSION-TEST", data)

        loaded = json.loads((store_dir / "SESSION-TEST.json").read_text())
        assert "tool_calls" in loaded
        assert "topic" in loaded
        assert "session_id" not in loaded  # Metadata, not persisted
        assert "start_time" not in loaded
        assert "status" not in loaded

    def test_skips_empty_data(self, store_dir):
        persist_session("SESSION-EMPTY", {"tool_calls": [], "thoughts": []})
        # Empty lists are falsy, so nothing should be written
        assert not (store_dir / "SESSION-EMPTY.json").exists()

    def test_atomic_write(self, store_dir):
        """Uses tmp file + rename for atomicity."""
        data = {"tool_calls": [{"tool_name": "test"}]}
        persist_session("SESSION-ATOMIC", data)

        # No .tmp files should remain
        tmp_files = list(store_dir.glob("*.tmp"))
        assert len(tmp_files) == 0
        assert (store_dir / "SESSION-ATOMIC.json").exists()

    def test_overwrites_existing(self, store_dir):
        data1 = {"tool_calls": [{"tool_name": "first"}]}
        persist_session("SESSION-OW", data1)

        data2 = {"tool_calls": [{"tool_name": "first"}, {"tool_name": "second"}]}
        persist_session("SESSION-OW", data2)

        loaded = json.loads((store_dir / "SESSION-OW.json").read_text())
        assert len(loaded["tool_calls"]) == 2

    def test_sanitizes_session_id(self, store_dir):
        data = {"tool_calls": [{"tool_name": "test"}]}
        persist_session("SESSION-../../../etc/passwd", data)
        # Should not create file outside store_dir
        assert not Path("/etc/passwd.json").exists()
        assert (store_dir / "SESSION-______etc_passwd.json").exists()

    def test_creates_directory_if_missing(self, tmp_path):
        new_dir = tmp_path / "new" / "nested" / "dir"
        with patch("governance.stores.session_persistence._STORE_DIR", new_dir):
            persist_session("S-1", {"tool_calls": [{"tool_name": "t"}]})
        assert (new_dir / "S-1.json").exists()

    def test_silently_handles_write_error(self, store_dir):
        """Should not raise even if write fails."""
        with patch("governance.stores.session_persistence._STORE_DIR", Path("/nonexistent/readonly")):
            # Should not raise
            persist_session("S-1", {"tool_calls": [{"tool_name": "t"}]})


class TestLoadPersistedSessions:
    def test_loads_into_empty_store(self, store_dir):
        # Write a session file
        (store_dir / "SESSION-LOADED.json").write_text(json.dumps({
            "tool_calls": [{"tool_name": "Bash", "result": "ok"}],
            "thoughts": [{"thought": "test"}],
        }))

        store = {}
        count = load_persisted_sessions(store)

        assert count == 1
        assert "SESSION-LOADED" in store
        assert len(store["SESSION-LOADED"]["tool_calls"]) == 1
        assert len(store["SESSION-LOADED"]["thoughts"]) == 1

    def test_merges_with_existing_entry(self, store_dir):
        """If session already in store (from TypeDB), merge arrays."""
        (store_dir / "SESSION-MERGE.json").write_text(json.dumps({
            "tool_calls": [{"tool_name": "persisted"}],
        }))

        store = {
            "SESSION-MERGE": {
                "session_id": "SESSION-MERGE",
                "status": "COMPLETED",
            }
        }
        load_persisted_sessions(store)

        assert store["SESSION-MERGE"]["status"] == "COMPLETED"  # Preserved
        assert len(store["SESSION-MERGE"]["tool_calls"]) == 1

    def test_does_not_overwrite_existing_tool_calls(self, store_dir):
        """If store already has tool_calls (from active session), keep them."""
        (store_dir / "SESSION-ACTIVE.json").write_text(json.dumps({
            "tool_calls": [{"tool_name": "old-persisted"}],
        }))

        store = {
            "SESSION-ACTIVE": {
                "session_id": "SESSION-ACTIVE",
                "tool_calls": [{"tool_name": "fresh-from-memory"}],
            }
        }
        load_persisted_sessions(store)

        # Memory data takes priority
        assert store["SESSION-ACTIVE"]["tool_calls"][0]["tool_name"] == "fresh-from-memory"

    def test_missing_directory_returns_zero(self, tmp_path):
        with patch("governance.stores.session_persistence._STORE_DIR", tmp_path / "nonexistent"):
            count = load_persisted_sessions({})
        assert count == 0

    def test_skips_malformed_json(self, store_dir):
        (store_dir / "SESSION-BAD.json").write_text("not valid json{{{")
        (store_dir / "SESSION-GOOD.json").write_text(json.dumps({
            "tool_calls": [{"tool_name": "ok"}],
        }))

        store = {}
        count = load_persisted_sessions(store)
        assert count == 1  # Only good one loaded
        assert "SESSION-GOOD" in store
        assert "SESSION-BAD" not in store

    def test_restores_bridge_fields(self, store_dir):
        (store_dir / "SESSION-BRIDGE.json").write_text(json.dumps({
            "tool_calls": [{"tool_name": "t"}],
            "topic": "my-topic",
            "session_type": "chat",
            "intent": "debugging",
        }))

        store = {}
        load_persisted_sessions(store)
        assert store["SESSION-BRIDGE"]["topic"] == "my-topic"
        assert store["SESSION-BRIDGE"]["session_type"] == "chat"

    def test_multiple_sessions(self, store_dir):
        for i in range(5):
            (store_dir / f"SESSION-{i}.json").write_text(json.dumps({
                "tool_calls": [{"tool_name": f"tool-{i}"}],
            }))

        store = {}
        count = load_persisted_sessions(store)
        assert count == 5
        assert len(store) == 5


class TestCleanupPersisted:
    def test_removes_file(self, store_dir):
        path = store_dir / "SESSION-DONE.json"
        path.write_text("{}")
        cleanup_persisted("SESSION-DONE")
        assert not path.exists()

    def test_no_error_if_missing(self, store_dir):
        cleanup_persisted("SESSION-NONEXISTENT")  # Should not raise
