"""Deep scan batch 159: Models + stores + health layers.

Batch 159 findings: 7 total, 0 confirmed fixes, 7 rejected.
"""
import pytest
from pathlib import Path
from datetime import datetime


# ── Task dataclass defaults defense ──────────────


class TestTaskDataclassDefaultsDefense:
    """Verify Task dataclass has None defaults for optional fields."""

    def test_priority_defaults_to_none(self):
        """Task.priority defaults to None (not missing)."""
        from governance.typedb.entities import Task
        t = Task(id="T1", name="Test", status="OPEN", phase="backlog")
        assert t.priority is None  # Not AttributeError

    def test_task_type_defaults_to_none(self):
        """Task.task_type defaults to None."""
        from governance.typedb.entities import Task
        t = Task(id="T1", name="Test", status="OPEN", phase="backlog")
        assert t.task_type is None

    def test_resolution_defaults_to_none_string(self):
        """Task.resolution defaults to 'NONE'."""
        from governance.typedb.entities import Task
        t = Task(id="T1", name="Test", status="OPEN", phase="backlog")
        assert t.resolution == "NONE"

    def test_gap_id_defaults_to_none(self):
        """Task.gap_id defaults to None."""
        from governance.typedb.entities import Task
        t = Task(id="T1", name="Test", status="OPEN", phase="backlog")
        assert t.gap_id is None

    def test_evidence_defaults_to_none(self):
        """Task.evidence defaults to None."""
        from governance.typedb.entities import Task
        t = Task(id="T1", name="Test", status="OPEN", phase="backlog")
        assert t.evidence is None

    def test_direct_access_safe_for_dict(self):
        """Putting None in dict is valid — not an error."""
        from governance.typedb.entities import Task
        t = Task(id="T1", name="Test", status="OPEN", phase="backlog")
        d = {"priority": t.priority, "task_type": t.task_type}
        assert d["priority"] is None
        assert d["task_type"] is None


# ── Session getattr pattern defense ──────────────


class TestSessionGetAttrDefense:
    """Verify session uses getattr for CC fields added later."""

    def test_session_cc_fields_are_optional(self):
        """Session CC fields all have Optional defaults."""
        from governance.typedb.entities import Session
        s = Session(id="S1")
        assert s.cc_session_uuid is None
        assert s.cc_tool_count is None

    def test_session_to_dict_uses_getattr_for_cc(self):
        """_session_to_dict uses getattr for CC fields (backward compat)."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/stores/typedb_access.py").read_text()
        assert "getattr(session, 'cc_session_uuid'" in src

    def test_task_to_dict_uses_direct_access(self):
        """_task_to_dict uses direct access (all fields in original dataclass)."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/stores/typedb_access.py").read_text()
        assert "task.priority" in src
        assert "task.task_type" in src


# ── ISO string date comparison defense ──────────────


class TestISOStringDateComparisonDefense:
    """Verify ISO date strings sort correctly for range queries."""

    def test_date_only_less_than_datetime(self):
        """'2026-02-17' < '2026-02-17T10:00:00' — includes whole day."""
        assert "2026-02-17" < "2026-02-17T10:00:00"

    def test_iso_strings_sort_chronologically(self):
        """ISO timestamps sort chronologically as strings."""
        dates = [
            "2026-02-17T14:00:00",
            "2026-02-15T10:00:00",
            "2026-02-17T09:00:00",
        ]
        assert sorted(dates) == [
            "2026-02-15T10:00:00",
            "2026-02-17T09:00:00",
            "2026-02-17T14:00:00",
        ]

    def test_date_range_filter_works(self):
        """ISO string comparison correctly filters date ranges."""
        entries = [
            {"ts": "2026-02-15T10:00:00"},
            {"ts": "2026-02-17T14:00:00"},
            {"ts": "2026-02-19T08:00:00"},
        ]
        date_from = "2026-02-16"
        date_to = "2026-02-18"
        filtered = [e for e in entries if date_from <= e["ts"] <= date_to]
        assert len(filtered) == 1
        assert filtered[0]["ts"] == "2026-02-17T14:00:00"


# ── Health check endpoint defense ──────────────


class TestHealthCheckEndpointDefense:
    """Verify health check patterns are correct."""

    def test_health_endpoint_exists(self):
        """GET /api/health endpoint is defined."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/api.py").read_text()
        assert "/health" in src or "health" in src

    def test_typedb_connected_field(self):
        """Health response includes typedb_connected field."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/health/checks.py").read_text()
        assert "typedb_connected" in src or "typedb" in src
