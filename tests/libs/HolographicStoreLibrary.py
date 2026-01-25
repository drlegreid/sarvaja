"""
RF-004: Robot Framework Library for Holographic Test Store.

Wraps tests/evidence/holographic_store.py for Robot Framework tests.
Per EPIC-TEST-COMPRESS-001 + FH-001: Multi-resolution test evidence.
"""

import sys
import tempfile
import threading
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class HolographicStoreLibrary:
    """Robot Framework library for Holographic Test Store testing."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # EvidenceRecord Tests
    # =========================================================================

    def evidence_record_creates_hash(self) -> Dict[str, Any]:
        """Evidence hash is auto-generated."""
        from tests.evidence.holographic_store import EvidenceRecord

        evidence = EvidenceRecord(
            test_id="test_1",
            name="test_1",
            status="passed",
        )
        return {
            "has_hash": evidence.evidence_hash is not None,
            "hash_length": len(evidence.evidence_hash) if evidence.evidence_hash else 0
        }

    def evidence_record_to_summary_dict(self) -> Dict[str, Any]:
        """to_summary_dict returns level 1-2 fields."""
        from tests.evidence.holographic_store import EvidenceRecord

        evidence = EvidenceRecord(
            test_id="test_1",
            name="test_1",
            status="passed",
            category="unit",
            duration_ms=100.0,
            fixtures={"input": "secret"},
        )
        summary = evidence.to_summary_dict()
        return {
            "has_test_id": summary["test_id"] == "test_1",
            "has_status": summary["status"] == "passed",
            "no_fixtures": "fixtures" not in summary
        }

    def evidence_record_to_full_dict(self) -> Dict[str, Any]:
        """to_full_dict includes all fields."""
        from tests.evidence.holographic_store import EvidenceRecord

        evidence = EvidenceRecord(
            test_id="test_1",
            name="test_1",
            status="passed",
            fixtures={"input": "data"},
        )
        full = evidence.to_full_dict()
        return {
            "has_fixtures": "fixtures" in full,
            "fixtures_input": full.get("fixtures", {}).get("input")
        }

    # =========================================================================
    # HolographicTestStore Tests
    # =========================================================================

    def push_event_basic(self) -> Dict[str, Any]:
        """push_event adds event and returns hash."""
        from tests.evidence.holographic_store import HolographicTestStore

        store = HolographicTestStore()
        hash1 = store.push_event(
            test_id="test_1",
            name="test_1",
            status="passed",
        )
        return {
            "has_hash": hash1 is not None,
            "count": store.count
        }

    def push_event_with_fixtures(self) -> Dict[str, Any]:
        """push_event stores fixtures at level 3."""
        from tests.evidence.holographic_store import HolographicTestStore

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
        return {
            "method": evidence["fixtures"]["request"]["method"],
            "user_id": evidence["response_data"]["users"][0]["id"]
        }

    def query_zoom_0_oneline(self) -> Dict[str, Any]:
        """Zoom 0 returns one-line summary."""
        from tests.evidence.holographic_store import HolographicTestStore

        store = HolographicTestStore()
        store.push_event("t1", "t1", "passed")
        store.push_event("t2", "t2", "passed")
        store.push_event("t3", "t3", "failed", error_message="Error")

        result = store.query(zoom=0)
        return {
            "zoom": result["zoom"],
            "total": result["total"],
            "passed": result["passed"],
            "failed": result["failed"],
            "has_summary": "summary" in result
        }

    def query_zoom_1_compact(self) -> Dict[str, Any]:
        """Zoom 1 returns compact summary with failures."""
        from tests.evidence.holographic_store import HolographicTestStore

        store = HolographicTestStore()
        store.push_event("t1", "t1", "passed")
        store.push_event("t2", "t2", "failed", error_message="AssertionError")

        result = store.query(zoom=1)
        return {
            "zoom": result["zoom"],
            "has_stats": "stats" in result,
            "failed": result["stats"]["failed"],
            "failure_count": len(result["failures"]),
            "has_assertion_error": "AssertionError" in result["failures"][0].get("error", "") if result["failures"] else False
        }

    def query_zoom_2_list(self) -> Dict[str, Any]:
        """Zoom 2 returns per-test list."""
        from tests.evidence.holographic_store import HolographicTestStore

        store = HolographicTestStore()
        store.push_event("t1", "test_one", "passed", duration_ms=100)
        store.push_event("t2", "test_two", "passed", duration_ms=200)

        result = store.query(zoom=2)
        return {
            "zoom": result["zoom"],
            "count": result["count"],
            "test_count": len(result["tests"]),
            "first_name": result["tests"][0]["name"] if result["tests"] else None
        }

    def query_zoom_3_full_single(self) -> Dict[str, Any]:
        """Zoom 3 with test_id returns single full detail."""
        from tests.evidence.holographic_store import HolographicTestStore

        store = HolographicTestStore()
        store.push_event(
            "tests/test_auth.py::test_login",
            "test_login",
            "passed",
            fixtures={"user": "admin"},
        )

        result = store.query(zoom=3, test_id="test_login")
        return {
            "zoom": result["zoom"],
            "has_evidence": "evidence" in result,
            "fixtures_user": result["evidence"]["fixtures"]["user"] if "evidence" in result else None
        }

    def query_filter_by_category(self) -> Dict[str, Any]:
        """Query can filter by category."""
        from tests.evidence.holographic_store import HolographicTestStore

        store = HolographicTestStore()
        store.push_event("t1", "t1", "passed", category="unit")
        store.push_event("t2", "t2", "passed", category="e2e")
        store.push_event("t3", "t3", "passed", category="unit")

        result = store.query(zoom=0, category="unit")
        return {
            "total": result["total"]
        }

    def query_filter_by_status(self) -> Dict[str, Any]:
        """Query can filter by status."""
        from tests.evidence.holographic_store import HolographicTestStore

        store = HolographicTestStore()
        store.push_event("t1", "t1", "passed")
        store.push_event("t2", "t2", "failed", error_message="Err")
        store.push_event("t3", "t3", "skipped")

        result = store.query(zoom=0, status="failed")
        return {
            "total": result["total"],
            "failed": result["failed"]
        }

    def get_by_hash(self) -> Dict[str, Any]:
        """get_by_hash retrieves specific evidence."""
        from tests.evidence.holographic_store import HolographicTestStore

        store = HolographicTestStore()
        hash1 = store.push_event("t1", "t1", "passed")
        hash2 = store.push_event("t2", "t2", "failed", error_message="Err")

        evidence = store.get_by_hash(hash2)
        return {
            "found": evidence is not None,
            "test_id": evidence.test_id if evidence else None,
            "status": evidence.status if evidence else None
        }

    def get_by_hash_not_found(self) -> Dict[str, Any]:
        """get_by_hash returns None for invalid hash."""
        from tests.evidence.holographic_store import HolographicTestStore

        store = HolographicTestStore()
        store.push_event("t1", "t1", "passed")
        result = store.get_by_hash("invalid_hash_123")
        return {
            "is_none": result is None
        }

    def clear(self) -> Dict[str, Any]:
        """clear removes all events."""
        from tests.evidence.holographic_store import HolographicTestStore

        store = HolographicTestStore()
        store.push_event("t1", "t1", "passed")
        store.push_event("t2", "t2", "passed")

        count = store.clear()
        return {
            "cleared_count": count,
            "store_count": store.count
        }

    def persist_and_load(self) -> Dict[str, Any]:
        """Events can be persisted and loaded."""
        from tests.evidence.holographic_store import HolographicTestStore

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "evidence.json"

            store1 = HolographicTestStore(persist_path=path)
            store1.push_event("t1", "t1", "passed")
            store1.push_event("t2", "t2", "failed", error_message="Err")

            store2 = HolographicTestStore()
            count = store2.load(path)

            return {
                "loaded_count": count,
                "store_count": store2.count
            }

    def thread_safety(self) -> Dict[str, Any]:
        """Store is thread-safe for concurrent pushes."""
        from tests.evidence.holographic_store import HolographicTestStore

        store = HolographicTestStore()
        errors = []

        def push_many(start):
            try:
                for i in range(100):
                    store.push_event(f"t{start}_{i}", f"test_{start}_{i}", "passed")
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=push_many, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        return {
            "no_errors": len(errors) == 0,
            "count": store.count
        }

    # =========================================================================
    # Global Store Tests
    # =========================================================================

    def global_store_singleton(self) -> Dict[str, Any]:
        """get_global_store returns same instance."""
        from tests.evidence.holographic_store import get_global_store, reset_global_store

        reset_global_store()
        store1 = get_global_store()
        store2 = get_global_store()
        return {
            "is_same": store1 is store2
        }

    def reset_global_store(self) -> Dict[str, Any]:
        """reset_global_store clears the singleton."""
        from tests.evidence.holographic_store import get_global_store, reset_global_store

        reset_global_store()
        store1 = get_global_store()
        store1.push_event("t1", "t1", "passed")

        reset_global_store()
        store2 = get_global_store()

        return {
            "count_after_reset": store2.count
        }
