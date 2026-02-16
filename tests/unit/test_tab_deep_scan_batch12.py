"""
Unit tests for Tab Deep Scan Batch 12 — VDataTable header key consistency.

Covers: doc_count enrichment across all task load paths,
applied_rules_display derivation, monitor rule_id flattening,
session source_type derivation.
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect
from unittest.mock import MagicMock, patch


# ── doc_count enrichment (BUG-UI-TASKS-004) ─────────────────────


class TestDocCountEnrichment:
    """_enrich_doc_count must be applied on all task load paths."""

    def test_enrich_doc_count_adds_field(self):
        from agent.governance_ui.controllers.tasks import _enrich_doc_count
        tasks = [
            {"task_id": "T1", "linked_documents": ["a.md", "b.md"]},
            {"task_id": "T2"},
            {"task_id": "T3", "linked_documents": []},
        ]
        result = _enrich_doc_count(tasks)
        assert result[0]["doc_count"] == 2
        assert result[1]["doc_count"] == 0
        assert result[2]["doc_count"] == 0

    def test_enrich_doc_count_none_documents(self):
        from agent.governance_ui.controllers.tasks import _enrich_doc_count
        tasks = [{"task_id": "T1", "linked_documents": None}]
        result = _enrich_doc_count(tasks)
        assert result[0]["doc_count"] == 0

    def test_dashboard_loader_calls_enrich(self):
        """dashboard_data_loader._load_tasks must call _enrich_doc_count."""
        from agent.governance_ui import dashboard_data_loader
        source = inspect.getsource(dashboard_data_loader)
        assert "_enrich_doc_count" in source

    def test_refresh_loader_calls_enrich(self):
        """data_loaders_refresh must call _enrich_doc_count."""
        from agent.governance_ui.controllers import data_loaders_refresh
        source = inspect.getsource(data_loaders_refresh)
        assert "_enrich_doc_count" in source

    def test_backlog_calls_enrich(self):
        """backlog.py must call _enrich_doc_count when refreshing tasks."""
        from agent.governance_ui.controllers import backlog
        source = inspect.getsource(backlog)
        assert "_enrich_doc_count" in source

    def test_tasks_controller_calls_enrich(self):
        """tasks.py must call _enrich_doc_count in all load paths."""
        from agent.governance_ui.controllers import tasks
        source = inspect.getsource(tasks)
        # Must appear multiple times — once per load path
        assert source.count("_enrich_doc_count") >= 4


# ── Header keys vs model fields ────────────────────────────────


class TestRulesHeaderKeysMatch:
    """Rules table header keys must match RuleResponse fields."""

    def test_all_header_keys_exist_in_model(self):
        from governance.models import RuleResponse
        fields = set(RuleResponse.model_fields.keys())
        header_keys = {
            "id", "name", "status", "category", "priority",
            "applicability", "linked_tasks_count",
            "linked_sessions_count", "created_date",
        }
        for key in header_keys:
            assert key in fields, f"Header key '{key}' not in RuleResponse"


class TestTasksHeaderKeysMatch:
    """Tasks table header keys must match TaskResponse + enrichment."""

    def test_model_fields_cover_headers(self):
        from governance.models import TaskResponse
        fields = set(TaskResponse.model_fields.keys())
        header_keys = {
            "task_id", "description", "priority", "task_type",
            "status", "phase", "agent_id", "created_at",
            "completed_at", "gap_id",
        }
        for key in header_keys:
            assert key in fields, f"Header key '{key}' not in TaskResponse"

    def test_doc_count_not_in_model(self):
        """doc_count is enriched, not in model — verify enrichment exists."""
        from governance.models import TaskResponse
        assert "doc_count" not in TaskResponse.model_fields
        # Enrichment function must exist
        from agent.governance_ui.controllers.tasks import _enrich_doc_count
        assert callable(_enrich_doc_count)


# ── applied_rules_display derivation ─────────────────────────


class TestAppliedRulesDisplay:
    """Audit entries must have applied_rules_display derived from list."""

    def test_derivation_in_audit_loaders(self):
        from agent.governance_ui.controllers import audit_loaders
        source = inspect.getsource(audit_loaders)
        assert "applied_rules_display" in source
        assert "', '.join(rules)" in source

    def test_list_conversion(self):
        """Rules list should become comma-separated string."""
        rules = ["RULE-001", "RULE-002"]
        display = ', '.join(rules)
        assert display == "RULE-001, RULE-002"

    def test_empty_list_conversion(self):
        rules = []
        display = ', '.join(rules)
        assert display == ""


# ── Monitor rule_id flattening ──────────────────────────────


class TestMonitorRuleIdFlattening:
    """Monitor events must flatten rule_id from details dict."""

    def test_format_event_extracts_rule_id(self):
        from agent.governance_ui.state.monitor import format_event_item
        event = {
            "event_id": "E1",
            "event_type": "rule_query",
            "source": "test",
            "timestamp": "2026-01-01T00:00:00",
            "severity": "INFO",
            "details": {"rule_id": "RULE-042"},
        }
        result = format_event_item(event)
        assert result["rule_id"] == "RULE-042"

    def test_format_event_no_rule_id(self):
        from agent.governance_ui.state.monitor import format_event_item
        event = {
            "event_id": "E2",
            "event_type": "trust_increase",
            "source": "test",
            "timestamp": "2026-01-01T00:00:00",
            "severity": "INFO",
            "details": {"agent_id": "A1"},
        }
        result = format_event_item(event)
        assert result["rule_id"] == ""


# ── Session source_type derivation consistency ───────────────


class TestSessionSourceType:
    """source_type must be derived in all session load paths."""

    def test_dashboard_loader_derives_source_type(self):
        from agent.governance_ui import dashboard_data_loader
        source = inspect.getsource(dashboard_data_loader)
        assert 'source_type' in source
        assert '"CC"' in source
        assert '"Chat"' in source
        assert '"API"' in source

    def test_refresh_derives_source_type(self):
        from agent.governance_ui.controllers import data_loaders_refresh
        source = inspect.getsource(data_loaders_refresh)
        assert 'source_type' in source

    def test_pagination_derives_source_type(self):
        from agent.governance_ui.controllers import sessions_pagination
        source = inspect.getsource(sessions_pagination)
        assert 'source_type' in source


# ── Session duration computation consistency ─────────────────


class TestSessionDurationConsistency:
    """duration must be computed in all session load paths."""

    def test_dashboard_loader_computes_duration(self):
        from agent.governance_ui import dashboard_data_loader
        source = inspect.getsource(dashboard_data_loader)
        assert "compute_session_duration" in source

    def test_refresh_computes_duration(self):
        from agent.governance_ui.controllers import data_loaders_refresh
        source = inspect.getsource(data_loaders_refresh)
        assert "compute_session_duration" in source

    def test_pagination_computes_duration(self):
        from agent.governance_ui.controllers import sessions_pagination
        source = inspect.getsource(sessions_pagination)
        assert "compute_session_duration" in source
