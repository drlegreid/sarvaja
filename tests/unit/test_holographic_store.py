"""
Unit tests for HolographicTestStore.

Per EPIC-TEST-COMPRESS-001 + FH-001: Multi-resolution test evidence.
"""

import pytest
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from tests.evidence.holographic_store import (
    HolographicTestStore,
    EvidenceRecord,
    get_global_store,
    reset_global_store,
)


class TestEvidenceRecord:
    """Tests for EvidenceRecord dataclass."""

    def test_creates_evidence_hash(self):
        """Evidence hash is auto-generated."""
        evidence = EvidenceRecord(
            test_id="test_1",
            name="test_1",
            status="passed",
        )
        assert evidence.evidence_hash is not None
        assert len(evidence.evidence_hash) == 16

    def test_to_summary_dict(self):
        """to_summary_dict returns level 1-2 fields."""
        evidence = EvidenceRecord(
            test_id="test_1",
            name="test_1",
            status="passed",
            category="unit",
            duration_ms=100.0,
            fixtures={"input": "secret"},  # Should not appear
        )
        summary = evidence.to_summary_dict()

        assert summary["test_id"] == "test_1"
        assert summary["status"] == "passed"
        assert "fixtures" not in summary

    def test_to_full_dict_includes_fixtures(self):
        """to_full_dict includes all fields."""
        evidence = EvidenceRecord(
            test_id="test_1",
            name="test_1",
            status="passed",
            fixtures={"input": "data"},
        )
        full = evidence.to_full_dict()

        assert "fixtures" in full
        assert full["fixtures"]["input"] == "data"


class TestHolographicTestStore:
    """Tests for HolographicTestStore."""

    def test_push_event_basic(self):
        """push_event adds event and returns hash."""
        store = HolographicTestStore()

        hash1 = store.push_event(
            test_id="test_1",
            name="test_1",
            status="passed",
        )

        assert hash1 is not None
        assert store.count == 1

    def test_push_event_with_fixtures(self):
        """push_event stores fixtures at level 3."""
        store = HolographicTestStore()

        store.push_event(
            test_id="test_api",
            name="test_api",
            status="passed",
            fixtures={"request": {"method": "GET", "url": "/api/users"}},
            response_data={"users": [{"id": 1}]},
        )

        result = store.query(zoom=3, test_id="test_api")
        evidence = result["evidence"]

        assert evidence["fixtures"]["request"]["method"] == "GET"
        assert evidence["response_data"]["users"][0]["id"] == 1

    def test_query_zoom_0_oneline(self):
        """Zoom 0 returns one-line summary."""
        store = HolographicTestStore()
        store.push_event("t1", "t1", "passed")
        store.push_event("t2", "t2", "passed")
        store.push_event("t3", "t3", "failed", error_message="Error")

        result = store.query(zoom=0)

        assert result["zoom"] == 0
        assert result["total"] == 3
        assert result["passed"] == 2
        assert result["failed"] == 1
        assert "2/3" in result["summary"] or "Tests:" in result["summary"]

    def test_query_zoom_1_compact(self):
        """Zoom 1 returns compact summary with failures."""
        store = HolographicTestStore()
        store.push_event("t1", "t1", "passed")
        store.push_event("t2", "t2", "failed", error_message="AssertionError")

        result = store.query(zoom=1)

        assert result["zoom"] == 1
        assert "stats" in result
        assert result["stats"]["failed"] == 1
        assert len(result["failures"]) == 1
        assert "AssertionError" in result["failures"][0].get("error", "")

    def test_query_zoom_2_list(self):
        """Zoom 2 returns per-test list."""
        store = HolographicTestStore()
        store.push_event("t1", "test_one", "passed", duration_ms=100)
        store.push_event("t2", "test_two", "passed", duration_ms=200)

        result = store.query(zoom=2)

        assert result["zoom"] == 2
        assert result["count"] == 2
        assert len(result["tests"]) == 2
        assert result["tests"][0]["name"] == "test_one"

    def test_query_zoom_3_full_single(self):
        """Zoom 3 with test_id returns single full detail."""
        store = HolographicTestStore()
        store.push_event(
            "tests/test_auth.py::test_login",
            "test_login",
            "passed",
            fixtures={"user": "admin"},
        )

        result = store.query(zoom=3, test_id="test_login")

        assert result["zoom"] == 3
        assert "evidence" in result
        assert result["evidence"]["fixtures"]["user"] == "admin"

    def test_query_filter_by_category(self):
        """Query can filter by category."""
        store = HolographicTestStore()
        store.push_event("t1", "t1", "passed", category="unit")
        store.push_event("t2", "t2", "passed", category="e2e")
        store.push_event("t3", "t3", "passed", category="unit")

        result = store.query(zoom=0, category="unit")

        assert result["total"] == 2

    def test_query_filter_by_status(self):
        """Query can filter by status."""
        store = HolographicTestStore()
        store.push_event("t1", "t1", "passed")
        store.push_event("t2", "t2", "failed", error_message="Err")
        store.push_event("t3", "t3", "skipped")

        result = store.query(zoom=0, status="failed")

        assert result["total"] == 1
        assert result["failed"] == 1

    def test_get_by_hash(self):
        """get_by_hash retrieves specific evidence."""
        store = HolographicTestStore()
        hash1 = store.push_event("t1", "t1", "passed")
        hash2 = store.push_event("t2", "t2", "failed", error_message="Err")

        evidence = store.get_by_hash(hash2)

        assert evidence is not None
        assert evidence.test_id == "t2"
        assert evidence.status == "failed"

    def test_get_by_hash_not_found(self):
        """get_by_hash returns None for invalid hash."""
        store = HolographicTestStore()
        store.push_event("t1", "t1", "passed")

        result = store.get_by_hash("invalid_hash_123")

        assert result is None

    def test_clear(self):
        """clear removes all events."""
        store = HolographicTestStore()
        store.push_event("t1", "t1", "passed")
        store.push_event("t2", "t2", "passed")

        count = store.clear()

        assert count == 2
        assert store.count == 0

    def test_persist_and_load(self):
        """Events can be persisted and loaded."""
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "evidence.json"

            # Create and persist
            store1 = HolographicTestStore(persist_path=path)
            store1.push_event("t1", "t1", "passed")
            store1.push_event("t2", "t2", "failed", error_message="Err")

            # Load into new store
            store2 = HolographicTestStore()
            count = store2.load(path)

            assert count == 2
            assert store2.count == 2

    def test_thread_safety(self):
        """Store is thread-safe for concurrent pushes."""
        import threading

        store = HolographicTestStore()
        errors = []

        def push_many(start):
            try:
                for i in range(100):
                    store.push_event(f"t{start}_{i}", f"test_{start}_{i}", "passed")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=push_many, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert store.count == 500


class TestGlobalStore:
    """Tests for global store functions."""

    def test_get_global_store_creates_singleton(self):
        """get_global_store returns same instance."""
        reset_global_store()

        store1 = get_global_store()
        store2 = get_global_store()

        assert store1 is store2

    def test_reset_global_store(self):
        """reset_global_store clears the singleton."""
        reset_global_store()
        store1 = get_global_store()
        store1.push_event("t1", "t1", "passed")

        reset_global_store()
        store2 = get_global_store()

        assert store2.count == 0
