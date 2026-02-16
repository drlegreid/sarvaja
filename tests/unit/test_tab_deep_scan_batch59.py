"""
Batch 59 — Deep Scan: Route exception handling consistency.

Fixes verified:
- BUG-ROUTE-MISSING-EXCEPT-001: list_agents wrapped in try-except
- BUG-ROUTE-MISSING-EXCEPT-002: update_session wrapped in try-except
"""
import inspect

import pytest


# ===========================================================================
# BUG-ROUTE-MISSING-EXCEPT-001: Agent list route error handling
# ===========================================================================

class TestAgentListRouteErrorHandling:
    """Verify list_agents has try-except block."""

    def _get_agents_crud_source(self):
        from governance.routes.agents import crud
        return inspect.getsource(crud)

    def test_list_agents_has_try_except(self):
        """list_agents must have try-except block."""
        src = self._get_agents_crud_source()
        list_idx = src.index("async def list_agents")
        next_func = src.find("@router", list_idx + 50)
        body = src[list_idx:next_func] if next_func > 0 else src[list_idx:]
        assert "try:" in body, "list_agents must have try block"
        assert "except" in body, "list_agents must have except block"

    def test_list_agents_has_http_exception_reraise(self):
        """list_agents must re-raise HTTPException."""
        src = self._get_agents_crud_source()
        list_idx = src.index("async def list_agents")
        next_func = src.find("@router", list_idx + 50)
        body = src[list_idx:next_func] if next_func > 0 else src[list_idx:]
        assert "except HTTPException:" in body or "except HTTPException" in body

    def test_create_agent_also_has_error_handling(self):
        """create_agent should already have error handling (reference)."""
        src = self._get_agents_crud_source()
        create_idx = src.index("async def create_agent")
        next_func = src.find("@router", create_idx + 50)
        body = src[create_idx:next_func] if next_func > 0 else src[create_idx:]
        assert "except" in body or "raise HTTPException" in body


# ===========================================================================
# BUG-ROUTE-MISSING-EXCEPT-002: Session update route error handling
# ===========================================================================

class TestSessionUpdateRouteErrorHandling:
    """Verify update_session has try-except block."""

    def _get_sessions_crud_source(self):
        from governance.routes.sessions import crud
        return inspect.getsource(crud)

    def test_update_session_has_try_except(self):
        """update_session must have try-except block."""
        src = self._get_sessions_crud_source()
        update_idx = src.index("async def update_session")
        next_func = src.find("@router", update_idx + 50)
        body = src[update_idx:next_func] if next_func > 0 else src[update_idx:]
        assert "try:" in body, "update_session must have try block"
        assert "except" in body, "update_session must have except block"

    def test_update_session_has_http_exception_reraise(self):
        """update_session must re-raise HTTPException."""
        src = self._get_sessions_crud_source()
        update_idx = src.index("async def update_session")
        next_func = src.find("@router", update_idx + 50)
        body = src[update_idx:next_func] if next_func > 0 else src[update_idx:]
        assert "except HTTPException:" in body or "except HTTPException" in body

    def test_get_session_also_has_error_handling(self):
        """get_session should already have error handling (reference)."""
        src = self._get_sessions_crud_source()
        get_idx = src.index("async def get_session")
        next_func = src.find("@router", get_idx + 50)
        body = src[get_idx:next_func] if next_func > 0 else src[get_idx:]
        assert "try:" in body


# ===========================================================================
# Route exception handling audit
# ===========================================================================

class TestRouteExceptionHandlingAudit:
    """Cross-route audit: all CRUD routes must have error handling."""

    def test_task_routes_all_have_error_handling(self):
        """All task CRUD routes must have try-except."""
        from governance.routes.tasks import crud
        src = inspect.getsource(crud)
        for func_name in ["create_task", "get_task", "update_task", "delete_task"]:
            func_idx = src.index(f"async def {func_name}")
            next_func = src.find("@router", func_idx + 50)
            body = src[func_idx:next_func] if next_func > 0 else src[func_idx:]
            assert "except" in body, f"{func_name} must have except block"

    def test_session_routes_have_error_handling(self):
        """Session CRUD routes must have error handling."""
        from governance.routes.sessions import crud
        src = inspect.getsource(crud)
        for func_name in ["create_session", "get_session", "update_session"]:
            func_idx = src.index(f"async def {func_name}")
            next_func = src.find("@router", func_idx + 50)
            body = src[func_idx:next_func] if next_func > 0 else src[func_idx:]
            assert "except" in body or "raise HTTPException" in body, f"{func_name} must handle errors"
