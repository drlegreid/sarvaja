"""
Tests for audit trail dashboard view.

Per RD-DEBUG-AUDIT Phase 4: Dashboard view for audit history.
Batch 160: New coverage for views/audit_view.py (0→12 tests).
"""
import inspect

import pytest


class TestAuditViewComponents:
    def test_build_audit_view_callable(self):
        from agent.governance_ui.views.audit_view import build_audit_view
        assert callable(build_audit_view)

    def test_build_audit_header_callable(self):
        from agent.governance_ui.views.audit_view import build_audit_header
        assert callable(build_audit_header)

    def test_build_audit_summary_callable(self):
        from agent.governance_ui.views.audit_view import build_audit_summary
        assert callable(build_audit_summary)

    def test_build_audit_filters_callable(self):
        from agent.governance_ui.views.audit_view import build_audit_filters
        assert callable(build_audit_filters)

    def test_build_audit_table_callable(self):
        from agent.governance_ui.views.audit_view import build_audit_table
        assert callable(build_audit_table)

    def test_build_action_breakdown_callable(self):
        from agent.governance_ui.views.audit_view import build_action_breakdown
        assert callable(build_action_breakdown)


class TestAuditViewContent:
    def test_has_dashboard_testid(self):
        from agent.governance_ui.views import audit_view
        source = inspect.getsource(audit_view)
        assert "audit-dashboard" in source

    def test_has_refresh_button(self):
        from agent.governance_ui.views import audit_view
        source = inspect.getsource(audit_view)
        assert "audit-refresh-btn" in source

    def test_has_total_card(self):
        from agent.governance_ui.views import audit_view
        source = inspect.getsource(audit_view)
        assert "audit-total-card" in source

    def test_has_filter_entity_type(self):
        from agent.governance_ui.views import audit_view
        source = inspect.getsource(audit_view)
        assert "audit-filter-entity-type" in source

    def test_has_entries_table(self):
        from agent.governance_ui.views import audit_view
        source = inspect.getsource(audit_view)
        assert "audit-entries-table" in source

    def test_has_action_breakdown(self):
        from agent.governance_ui.views import audit_view
        source = inspect.getsource(audit_view)
        assert "audit-action-breakdown-card" in source
