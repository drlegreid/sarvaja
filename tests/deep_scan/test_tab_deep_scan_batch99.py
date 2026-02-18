"""Deep scan batch 99: Cross-cutting integration + remaining scripts.

Batch 99 findings: 34 total, 0 confirmed fixes, 34 rejected.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta


# ── Audit store defense ──────────────


class TestAuditStoreRetention:
    """Verify audit store retention policy."""

    def test_retention_removes_old_entries(self):
        import governance.stores.audit as audit_mod

        old_entries = audit_mod._audit_store.copy()
        try:
            audit_mod._audit_store = [
                {"audit_id": "OLD", "timestamp": "2020-01-01T00:00:00", "action_type": "CREATE"},
                {"audit_id": "NEW", "timestamp": datetime.now().isoformat(), "action_type": "UPDATE"},
            ]
            audit_mod._apply_retention(days=7)
            # _apply_retention rebinds global — access via module
            assert len(audit_mod._audit_store) == 1
            assert audit_mod._audit_store[0]["audit_id"] == "NEW"
        finally:
            audit_mod._audit_store = old_entries

    def test_retention_keeps_recent(self):
        import governance.stores.audit as audit_mod

        old_entries = audit_mod._audit_store.copy()
        try:
            audit_mod._audit_store = [
                {"audit_id": "RECENT", "timestamp": datetime.now().isoformat(), "action_type": "CREATE"},
            ]
            audit_mod._apply_retention(days=7)
            assert len(audit_mod._audit_store) == 1
        finally:
            audit_mod._audit_store = old_entries


class TestAuditStoreQuery:
    """Verify audit trail querying."""

    def test_query_by_entity_id(self):
        from governance.stores.audit import query_audit_trail, _audit_store

        old_entries = _audit_store.copy()
        try:
            _audit_store.clear()
            _audit_store.append({
                "entity_id": "TASK-001",
                "entity_type": "task",
                "timestamp": datetime.now().isoformat(),
            })
            _audit_store.append({
                "entity_id": "SESSION-001",
                "entity_type": "session",
                "timestamp": datetime.now().isoformat(),
            })
            result = query_audit_trail(entity_id="TASK-001")
            assert len(result) == 1
            assert result[0]["entity_id"] == "TASK-001"
        finally:
            _audit_store.clear()
            _audit_store.extend(old_entries)

    def test_query_pagination(self):
        from governance.stores.audit import query_audit_trail, _audit_store

        old_entries = _audit_store.copy()
        try:
            _audit_store.clear()
            for i in range(10):
                _audit_store.append({
                    "entity_id": f"TASK-{i:03d}",
                    "timestamp": f"2026-02-15T{10+i}:00:00",
                })
            result = query_audit_trail(limit=3, offset=2)
            assert len(result) == 3
        finally:
            _audit_store.clear()
            _audit_store.extend(old_entries)


# ── Heuristic check return structure defense ──────────────


class TestHeuristicCheckReturnStructure:
    """Verify all heuristic checks return consistent structure."""

    def test_exploratory_self_referential_returns_skip(self):
        from governance.routes.tests.heuristic_checks_exploratory import (
            check_chat_session_count_accuracy,
        )

        result = check_chat_session_count_accuracy("http://localhost:8082")
        assert "status" in result
        assert "violations" in result
        assert result["status"] == "SKIP"

    def test_exploratory_audit_trail_self_ref(self):
        from governance.routes.tests.heuristic_checks_exploratory import (
            check_audit_trail_populated,
        )

        result = check_audit_trail_populated("http://localhost:8082")
        assert result["status"] == "SKIP"
        assert isinstance(result["violations"], list)

    def test_exploratory_mcp_readiness_self_ref(self):
        from governance.routes.tests.heuristic_checks_exploratory import (
            check_mcp_readiness_consistency,
        )

        result = check_mcp_readiness_consistency("http://localhost:8082")
        assert result["status"] == "SKIP"


# ── _is_self_referential defense ──────────────


class TestIsSelfReferential:
    """Verify self-referential detection logic."""

    def test_localhost_detected(self):
        from governance.routes.tests.heuristic_checks_exploratory import _is_self_referential

        assert _is_self_referential("http://localhost:8082") is True

    def test_loopback_detected(self):
        from governance.routes.tests.heuristic_checks_exploratory import _is_self_referential

        assert _is_self_referential("http://127.0.0.1:8082") is True

    def test_trailing_slash_handled(self):
        from governance.routes.tests.heuristic_checks_exploratory import _is_self_referential

        assert _is_self_referential("http://localhost:8082/") is True

    def test_external_not_detected(self):
        from governance.routes.tests.heuristic_checks_exploratory import _is_self_referential

        assert _is_self_referential("http://other-host:8082") is False


# ── Session repair negative duration defense ──────────────


class TestRepairNegativeDuration:
    """Verify negative duration detection and swap logic."""

    def test_negative_duration_detected(self):
        from governance.services.session_repair import detect_negative_durations

        sessions = [
            {
                "session_id": "SESSION-2026-02-15-TEST",
                "start_time": "2026-02-15T17:00:00",
                "end_time": "2026-02-15T09:00:00",  # End before start
            }
        ]
        flagged = detect_negative_durations(sessions)
        assert "SESSION-2026-02-15-TEST" in flagged

    def test_positive_duration_not_flagged(self):
        from governance.services.session_repair import detect_negative_durations

        sessions = [
            {
                "session_id": "SESSION-2026-02-15-OK",
                "start_time": "2026-02-15T09:00:00",
                "end_time": "2026-02-15T17:00:00",
            }
        ]
        flagged = detect_negative_durations(sessions)
        assert len(flagged) == 0


# ── Repair plan completeness defense ──────────────


class TestRepairPlanCompleteness:
    """Verify build_repair_plan generates all fix types."""

    def test_plan_includes_agent_fix(self):
        from governance.services.session_repair import build_repair_plan

        sessions = [{"session_id": "SESSION-2026-02-15-X", "start_time": "", "end_time": ""}]
        plan = build_repair_plan(sessions)
        assert len(plan) == 1
        assert "agent_id" in plan[0]["fixes"]

    def test_plan_includes_timestamp_fix_for_backfilled(self):
        from governance.services.session_repair import build_repair_plan

        sessions = [{
            "session_id": "SESSION-2026-02-15-BACKFILL",
            "description": "Backfilled from evidence file",
            "start_time": "2026-02-15T00:00:00",
            "end_time": "2026-02-15T00:00:00",
            "agent_id": "code-agent",
        }]
        plan = build_repair_plan(sessions)
        assert len(plan) == 1
        assert "timestamp" in plan[0]["fixes"]


# ── Task to response conversion defense ──────────────


class TestTaskToResponseConversion:
    """Verify task_to_response handles TypeDB Task objects."""

    def test_null_safe_linked_fields(self):
        from governance.stores.helpers import task_to_response

        task = MagicMock()
        task.id = "TASK-001"
        task.name = "Test task"
        task.description = "Desc"
        task.phase = "Phase 1"
        task.status = "OPEN"
        task.resolution = None
        task.priority = "HIGH"
        task.task_type = "FEATURE"
        task.agent_id = None
        task.created_at = None
        task.claimed_at = None
        task.completed_at = None
        task.body = None
        task.linked_rules = None  # NULL from TypeDB
        task.linked_sessions = None
        task.linked_commits = None
        task.linked_documents = None
        task.gap_id = None
        task.evidence = None
        task.document_path = None

        resp = task_to_response(task)
        assert resp.linked_rules == []
        assert resp.linked_sessions == []
        assert resp.linked_commits == []
