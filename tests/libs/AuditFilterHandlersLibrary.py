"""
RF-004: Robot Framework Library for Audit Filter Handlers.

Wraps tests/unit/test_audit_filter_handlers.py tests for Robot Framework.
Per UI-AUDIT-004: Audit trail filterable by entity.
"""

import sys
import inspect
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class AuditFilterHandlersLibrary:
    """Robot Framework library for Audit Filter Handlers testing."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # Handler Existence Tests
    # =========================================================================

    def audit_filter_handler_function_exists(self) -> Dict[str, Any]:
        """Verify the audit filter change handler is defined."""
        from agent.governance_ui.handlers import common_handlers
        source = inspect.getsource(common_handlers)
        return {
            "has_audit_filter": "audit_filter" in source
        }

    def audit_filter_handler_watches_entity_type(self) -> Dict[str, Any]:
        """Verify handler watches audit_filter_entity_type."""
        from agent.governance_ui.handlers import common_handlers
        source = inspect.getsource(common_handlers)
        return {
            "watches_entity_type": "audit_filter_entity_type" in source
        }

    def audit_filter_handler_watches_action_type(self) -> Dict[str, Any]:
        """Verify handler watches audit_filter_action_type."""
        from agent.governance_ui.handlers import common_handlers
        source = inspect.getsource(common_handlers)
        return {
            "watches_action_type": "audit_filter_action_type" in source
        }

    def audit_filter_handler_watches_entity_id(self) -> Dict[str, Any]:
        """Verify handler watches audit_filter_entity_id."""
        from agent.governance_ui.handlers import common_handlers
        source = inspect.getsource(common_handlers)
        return {
            "watches_entity_id": "audit_filter_entity_id" in source
        }

    def audit_filter_handler_watches_correlation_id(self) -> Dict[str, Any]:
        """Verify handler watches audit_filter_correlation_id."""
        from agent.governance_ui.handlers import common_handlers
        source = inspect.getsource(common_handlers)
        return {
            "watches_correlation_id": "audit_filter_correlation_id" in source
        }

    # =========================================================================
    # Audit Filter State Tests
    # =========================================================================

    def filter_state_variables_in_initial(self) -> Dict[str, Any]:
        """Verify filter state variables are defined."""
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        return {
            "has_entity_type": "audit_filter_entity_type" in state,
            "has_action_type": "audit_filter_action_type" in state,
            "has_entity_id": "audit_filter_entity_id" in state,
            "has_correlation_id": "audit_filter_correlation_id" in state
        }

    def filter_type_lists_in_initial(self) -> Dict[str, Any]:
        """Verify filter option lists are defined."""
        from agent.governance_ui.state.initial import get_initial_state
        state = get_initial_state()
        return {
            "has_entity_types": "audit_entity_types" in state,
            "has_action_types": "audit_action_types" in state
        }

    # =========================================================================
    # Audit Filter API Integration Tests (requires running API)
    # =========================================================================

    def audit_api_accepts_entity_type_filter(self) -> Dict[str, Any]:
        """API accepts entity_type query parameter."""
        try:
            import httpx
            response = httpx.get(
                "http://localhost:8082/api/audit",
                params={"entity_type": "task", "limit": 5},
                timeout=5.0
            )
            return {
                "status_code": response.status_code,
                "accepted": response.status_code == 200
            }
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    def audit_api_accepts_action_type_filter(self) -> Dict[str, Any]:
        """API accepts action_type query parameter."""
        try:
            import httpx
            response = httpx.get(
                "http://localhost:8082/api/audit",
                params={"action_type": "CREATE", "limit": 5},
                timeout=5.0
            )
            return {
                "status_code": response.status_code,
                "accepted": response.status_code == 200
            }
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    def audit_api_accepts_entity_id_filter(self) -> Dict[str, Any]:
        """API accepts entity_id query parameter."""
        try:
            import httpx
            response = httpx.get(
                "http://localhost:8082/api/audit",
                params={"entity_id": "TASK-001", "limit": 5},
                timeout=5.0
            )
            return {
                "status_code": response.status_code,
                "accepted": response.status_code == 200
            }
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    def audit_api_accepts_correlation_id_filter(self) -> Dict[str, Any]:
        """API accepts correlation_id query parameter."""
        try:
            import httpx
            response = httpx.get(
                "http://localhost:8082/api/audit",
                params={"correlation_id": "CORR-12345", "limit": 5},
                timeout=5.0
            )
            return {
                "status_code": response.status_code,
                "accepted": response.status_code == 200
            }
        except Exception as e:
            return {"skipped": True, "reason": str(e)}
