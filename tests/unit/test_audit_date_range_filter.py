"""TDD Tests for Cycle 11-12: Audit Timestamp Range Filter.

Gap: GAP-AUDIT-RANGE-001
Problem: No date range filter on audit trail — can only browse latest N.
Solution: Add date_from/date_to query params, state vars, and filter UI.
"""
from unittest.mock import patch, MagicMock

import pytest


class TestAuditStoreSupportsDateRange:
    """query_audit_trail accepts date_from and date_to params."""

    def test_query_audit_trail_has_date_params(self):
        """query_audit_trail signature includes date_from and date_to."""
        import inspect
        from governance.stores.audit import query_audit_trail
        sig = inspect.signature(query_audit_trail)
        assert "date_from" in sig.parameters
        assert "date_to" in sig.parameters

    def test_date_from_filters_old_entries(self):
        """Entries before date_from are excluded."""
        from governance.stores.audit import query_audit_trail, _audit_store

        original = _audit_store.copy()
        _audit_store.clear()

        try:
            _audit_store.append({
                "audit_id": "A-OLD", "entity_id": "T-OLD", "entity_type": "task",
                "action_type": "CREATE", "actor_id": "agent",
                "timestamp": "2026-02-10T10:00:00", "correlation_id": "C-1",
                "applied_rules": [], "metadata": {},
            })
            _audit_store.append({
                "audit_id": "A-NEW", "entity_id": "T-NEW", "entity_type": "task",
                "action_type": "CREATE", "actor_id": "agent",
                "timestamp": "2026-02-15T10:00:00", "correlation_id": "C-2",
                "applied_rules": [], "metadata": {},
            })

            results = query_audit_trail(date_from="2026-02-14")
            entity_ids = [e["entity_id"] for e in results]
            assert "T-NEW" in entity_ids
            assert "T-OLD" not in entity_ids
        finally:
            _audit_store.clear()
            _audit_store.extend(original)

    def test_date_to_filters_future_entries(self):
        """Entries after date_to are excluded."""
        from governance.stores.audit import query_audit_trail, _audit_store

        original = _audit_store.copy()
        _audit_store.clear()

        try:
            _audit_store.append({
                "audit_id": "A-E", "entity_id": "T-EARLY", "entity_type": "task",
                "action_type": "CREATE", "actor_id": "agent",
                "timestamp": "2026-02-10T10:00:00", "correlation_id": "C-3",
                "applied_rules": [], "metadata": {},
            })
            _audit_store.append({
                "audit_id": "A-L", "entity_id": "T-LATE", "entity_type": "task",
                "action_type": "CREATE", "actor_id": "agent",
                "timestamp": "2026-02-15T10:00:00", "correlation_id": "C-4",
                "applied_rules": [], "metadata": {},
            })

            results = query_audit_trail(date_to="2026-02-12")
            entity_ids = [e["entity_id"] for e in results]
            assert "T-EARLY" in entity_ids
            assert "T-LATE" not in entity_ids
        finally:
            _audit_store.clear()
            _audit_store.extend(original)

    def test_date_range_both_bounds(self):
        """Combined date_from and date_to creates a window."""
        from governance.stores.audit import query_audit_trail, _audit_store

        original = _audit_store.copy()
        _audit_store.clear()

        try:
            for day, eid in [(10, "T-BEFORE"), (12, "T-INSIDE"), (16, "T-AFTER")]:
                _audit_store.append({
                    "audit_id": f"A-{eid}", "entity_id": eid, "entity_type": "task",
                    "action_type": "CREATE", "actor_id": "agent",
                    "timestamp": f"2026-02-{day:02d}T10:00:00", "correlation_id": f"C-{eid}",
                    "applied_rules": [], "metadata": {},
                })

            results = query_audit_trail(date_from="2026-02-11", date_to="2026-02-14")
            entity_ids = [e["entity_id"] for e in results]
            assert entity_ids == ["T-INSIDE"]
        finally:
            _audit_store.clear()
            _audit_store.extend(original)


class TestAuditAPISupportsDateRange:
    """API endpoint passes date params to store."""

    @pytest.mark.asyncio
    async def test_list_audit_entries_accepts_date_params(self):
        """GET /api/audit accepts date_from and date_to query params."""
        import inspect
        from governance.routes.audit import list_audit_entries
        sig = inspect.signature(list_audit_entries)
        assert "date_from" in sig.parameters
        assert "date_to" in sig.parameters


class TestAuditStateHasDateFilters:
    """Initial state includes date filter variables."""

    def test_state_has_audit_filter_date_from(self):
        """Initial state declares audit_filter_date_from."""
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "audit_filter_date_from" in state

    def test_state_has_audit_filter_date_to(self):
        """Initial state declares audit_filter_date_to."""
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        assert "audit_filter_date_to" in state


class TestAuditViewHasDatePickers:
    """Audit filter UI includes date picker inputs."""

    def test_audit_filters_include_date_from(self):
        """build_audit_filters includes date_from input."""
        import inspect
        from agent.governance_ui.views.audit_view import build_audit_filters
        source = inspect.getsource(build_audit_filters)
        assert "audit_filter_date_from" in source

    def test_audit_filters_include_date_to(self):
        """build_audit_filters includes date_to input."""
        import inspect
        from agent.governance_ui.views.audit_view import build_audit_filters
        source = inspect.getsource(build_audit_filters)
        assert "audit_filter_date_to" in source
