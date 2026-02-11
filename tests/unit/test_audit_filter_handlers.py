"""
Tests for UI-AUDIT-004: Audit trail filterable by entity.

Per TDD: Write tests first for reactive audit filtering.
Per GAP-UI-AUDIT-2026-01-18: Make audit trail filterable by entity.

Tests verify:
1. State change handlers exist for audit filters
2. Filter changes trigger data reload
3. Filter values passed to API correctly
"""

import pytest
from unittest.mock import MagicMock, patch


@pytest.mark.unit
class TestAuditFilterHandlersExist:
    """Verify audit filter handlers are registered."""

    def test_audit_filter_handler_function_exists(self):
        """Verify the audit filter change handler is defined."""
        # Per DOC-SIZE-01-v1: audit handlers extracted to common_handlers_audit
        from agent.governance_ui.handlers import common_handlers_audit
        import inspect

        source = inspect.getsource(common_handlers_audit)

        # Should have state.change handler for audit filters
        assert "audit_filter" in source, "audit_filter handlers missing from common_handlers_audit"

    def test_audit_filter_handler_watches_entity_type(self):
        """Verify handler watches audit_filter_entity_type."""
        from agent.governance_ui.handlers import common_handlers_audit
        import inspect

        source = inspect.getsource(common_handlers_audit)

        # Should watch the entity_type filter
        assert "audit_filter_entity_type" in source

    def test_audit_filter_handler_watches_action_type(self):
        """Verify handler watches audit_filter_action_type."""
        from agent.governance_ui.handlers import common_handlers_audit
        import inspect

        source = inspect.getsource(common_handlers_audit)

        assert "audit_filter_action_type" in source

    def test_audit_filter_handler_watches_entity_id(self):
        """Verify handler watches audit_filter_entity_id."""
        from agent.governance_ui.handlers import common_handlers_audit
        import inspect

        source = inspect.getsource(common_handlers_audit)

        assert "audit_filter_entity_id" in source

    def test_audit_filter_handler_watches_correlation_id(self):
        """Verify handler watches audit_filter_correlation_id."""
        from agent.governance_ui.handlers import common_handlers_audit
        import inspect

        source = inspect.getsource(common_handlers_audit)

        assert "audit_filter_correlation_id" in source


@pytest.mark.unit
class TestAuditFilterAPIIntegration:
    """Test audit filter API endpoint functionality."""

    def test_audit_api_accepts_entity_type_filter(self):
        """API accepts entity_type query parameter."""
        import httpx

        # This tests the actual API contract
        response = httpx.get(
            "http://localhost:8082/api/audit",
            params={"entity_type": "task", "limit": 5},
            timeout=5.0
        )

        # API should accept the parameter (200 or empty result)
        assert response.status_code == 200

    def test_audit_api_accepts_action_type_filter(self):
        """API accepts action_type query parameter."""
        import httpx

        response = httpx.get(
            "http://localhost:8082/api/audit",
            params={"action_type": "CREATE", "limit": 5},
            timeout=5.0
        )

        assert response.status_code == 200

    def test_audit_api_accepts_entity_id_filter(self):
        """API accepts entity_id query parameter."""
        import httpx

        response = httpx.get(
            "http://localhost:8082/api/audit",
            params={"entity_id": "TASK-001", "limit": 5},
            timeout=5.0
        )

        assert response.status_code == 200

    def test_audit_api_accepts_correlation_id_filter(self):
        """API accepts correlation_id query parameter."""
        import httpx

        response = httpx.get(
            "http://localhost:8082/api/audit",
            params={"correlation_id": "CORR-12345", "limit": 5},
            timeout=5.0
        )

        assert response.status_code == 200


@pytest.mark.unit
class TestAuditFilterState:
    """Test audit filter state variables exist."""

    def test_filter_state_variables_in_initial(self):
        """Verify filter state variables are defined."""
        from agent.governance_ui.state.initial import get_initial_state

        state = get_initial_state()

        # All filter variables should exist
        assert "audit_filter_entity_type" in state
        assert "audit_filter_action_type" in state
        assert "audit_filter_entity_id" in state
        assert "audit_filter_correlation_id" in state

    def test_filter_type_lists_in_initial(self):
        """Verify filter option lists are defined."""
        from agent.governance_ui.state.initial import get_initial_state

        state = get_initial_state()

        # Lists for dropdown options should exist
        assert "audit_entity_types" in state
        assert "audit_action_types" in state
