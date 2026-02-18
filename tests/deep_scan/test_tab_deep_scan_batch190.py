"""Deep scan batch 190: Route handlers layer.

Batch 190 findings: 13 total, 5 confirmed fixes, 8 rejected/deferred.
- BUG-190-004: DELETE session missing try-except.
- BUG-190-005: GET agent missing try-except.
- BUG-190-006: DELETE agent missing try-except.
- BUG-190-007: CREATE agent missing try-except.
- BUG-190-001/002: Route shadowing — FALSE POSITIVE (segment count).
"""
import pytest
from pathlib import Path


# ── Agent CRUD exception safety defense ──────────────


class TestAgentCrudExceptionSafety:
    """Verify agent CRUD endpoints have try-except blocks."""

    def test_create_agent_has_try_except(self):
        """create_agent endpoint has try-except."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/routes/agents/crud.py").read_text()
        start = src.index("async def create_agent")
        # Find the next function definition
        rest = src[start:]
        end = rest.index("\nasync def ", 10)
        func = rest[:end]
        assert "try:" in func
        assert "except HTTPException:" in func
        assert "except Exception" in func

    def test_list_agents_has_try_except(self):
        """list_agents endpoint has try-except (existing)."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/routes/agents/crud.py").read_text()
        start = src.index("async def list_agents")
        rest = src[start:]
        end = rest.index("\nasync def ", 10) if "\nasync def " in rest[10:] else len(rest)
        func = rest[:end]
        assert "try:" in func
        assert "except Exception" in func

    def test_get_agent_has_try_except(self):
        """get_agent endpoint has try-except."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/routes/agents/crud.py").read_text()
        start = src.index("async def get_agent")
        rest = src[start:]
        end = rest.index("\nasync def ", 10) if "\nasync def " in rest[10:] else len(rest)
        func = rest[:end]
        assert "try:" in func
        assert "except HTTPException:" in func
        assert "except Exception" in func

    def test_delete_agent_has_try_except(self):
        """delete_agent endpoint has try-except."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/routes/agents/crud.py").read_text()
        start = src.index("async def delete_agent")
        rest = src[start:]
        end = rest.index("\nasync def ", 10) if "\nasync def " in rest[10:] else len(rest)
        func = rest[:end]
        assert "try:" in func
        assert "except HTTPException:" in func
        assert "except Exception" in func


# ── Session CRUD exception safety defense ──────────────


class TestSessionCrudExceptionSafety:
    """Verify session CRUD endpoints have try-except blocks."""

    def test_delete_session_has_try_except(self):
        """delete_session endpoint has try-except."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/routes/sessions/crud.py").read_text()
        start = src.index("async def delete_session")
        rest = src[start:]
        end = rest.index("\nasync def ", 10) if "\nasync def " in rest[10:] else len(rest)
        func = rest[:end]
        assert "try:" in func
        assert "except HTTPException:" in func
        assert "except Exception" in func

    def test_list_sessions_has_try_except(self):
        """list_sessions endpoint has try-except (existing)."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/routes/sessions/crud.py").read_text()
        start = src.index("async def list_sessions")
        rest = src[start:]
        end = rest.index("\nasync def ", 10) if "\nasync def " in rest[10:] else len(rest)
        func = rest[:end]
        assert "try:" in func
        assert "except" in func


# ── Route structure defense ──────────────


class TestRouteStructureDefense:
    """Verify route packages are properly structured."""

    def test_agents_package_has_crud(self):
        """Agents route package includes CRUD router."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/routes/agents/__init__.py").read_text()
        assert "crud_router" in src
        assert "include_router(crud_router)" in src

    def test_sessions_package_has_crud(self):
        """Sessions route package includes CRUD router."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/routes/sessions/__init__.py").read_text()
        assert "crud_router" in src
        assert "include_router(crud_router)" in src

    def test_agent_crud_importable(self):
        """Agent CRUD module is importable."""
        from governance.routes.agents import crud
        assert crud is not None

    def test_session_crud_importable(self):
        """Session CRUD module is importable."""
        from governance.routes.sessions import crud
        assert crud is not None
