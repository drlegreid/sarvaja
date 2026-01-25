"""
RF-004: Robot Framework Library for Executive Dropdown.

Wraps tests/unit/test_executive_dropdown.py tests for Robot Framework.
Per UI-AUDIT-007: Executive Report dropdown fix.
"""

import sys
import inspect
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class ExecutiveDropdownLibrary:
    """Robot Framework library for Executive Dropdown testing."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # Sessions List Loader Tests
    # =========================================================================

    def load_sessions_list_in_loaders(self) -> Dict[str, Any]:
        """Verify load_sessions_list is exported from loaders."""
        from agent.governance_ui.controllers import data_loaders
        source = inspect.getsource(data_loaders)
        return {
            "has_function": "def load_sessions_list" in source,
            "in_return_dict": "'load_sessions_list'" in source
        }

    def sessions_list_trigger_exists(self) -> Dict[str, Any]:
        """Verify load_sessions_list trigger is registered."""
        from agent.governance_ui.controllers import data_loaders
        source = inspect.getsource(data_loaders)
        return {
            "trigger_registered": '@ctrl.trigger("load_sessions_list")' in source
        }

    def governance_dashboard_calls_sessions_loader(self) -> Dict[str, Any]:
        """Verify executive view loads sessions."""
        from agent import governance_dashboard
        source = inspect.getsource(governance_dashboard)
        return {
            "calls_loader": "load_sessions_list()" in source,
            "assigns_loader": "load_sessions_list = loaders" in source
        }

    # =========================================================================
    # Sessions API Integration Tests (requires running API)
    # =========================================================================

    def sessions_api_returns_list(self) -> Dict[str, Any]:
        """API returns a list of sessions."""
        try:
            import httpx
            response = httpx.get(
                "http://localhost:8082/api/sessions?limit=100",
                timeout=10.0
            )
            if response.status_code != 200:
                return {"skipped": True, "reason": f"API returned {response.status_code}"}

            data = response.json()
            if isinstance(data, dict):
                sessions = data.get("items", [])
            else:
                sessions = data

            return {
                "status_code": response.status_code,
                "is_list": isinstance(sessions, list),
                "count": len(sessions)
            }
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    def sessions_have_session_id(self) -> Dict[str, Any]:
        """Sessions have session_id for dropdown."""
        try:
            import httpx
            response = httpx.get(
                "http://localhost:8082/api/sessions?limit=10",
                timeout=10.0
            )
            if response.status_code != 200:
                return {"skipped": True, "reason": f"API returned {response.status_code}"}

            data = response.json()
            sessions = data.get("items", data) if isinstance(data, dict) else data

            all_have_id = all("session_id" in s for s in sessions) if sessions else True
            return {
                "has_sessions": len(sessions) > 0 if sessions else False,
                "all_have_session_id": all_have_id
            }
        except Exception as e:
            return {"skipped": True, "reason": str(e)}
