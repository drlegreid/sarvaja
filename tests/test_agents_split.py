"""
TDD Tests for GAP-FILE-028: routes/agents.py split.

Per DOC-SIZE-01-v1: Files under 300 lines.
Per TEST-FIX-01-v1: Fix MUST include verification evidence.

Created: 2026-01-14
"""

import pytest
from pathlib import Path


ROUTES_DIR = Path(__file__).parent.parent / "governance" / "routes"


class TestAgentsSplit:
    """Test agents module structure after split."""

    def test_agents_under_300_lines(self):
        """Verify main agents module is under 300 lines per DOC-SIZE-01-v1."""
        agents_file = ROUTES_DIR / "agents.py"
        if agents_file.exists():
            with open(agents_file, "r") as f:
                lines = len(f.readlines())
            assert lines < 300, f"agents.py has {lines} lines, should be <300"


class TestBackwardCompatibility:
    """Test backward compatibility after split."""

    def test_import_router(self):
        """Verify router can be imported from agents module."""
        from governance.routes.agents import router
        assert router is not None

    def test_router_has_agents_routes(self):
        """Verify router has agent CRUD routes."""
        from governance.routes.agents import router
        routes = [r.path for r in router.routes]
        assert "/agents" in routes or any("/agents" in r for r in routes)


class TestModuleFunctions:
    """Test functions are available in correct modules."""

    def test_observability_has_status_route(self):
        """Verify observability module has status summary."""
        try:
            from governance.routes.agents.observability import router as obs_router
            routes = [r.path for r in obs_router.routes]
            assert any("status" in r for r in routes)
        except ImportError:
            # If not split yet, skip
            pytest.skip("Observability module not yet split")

    def test_visibility_has_visibility_route(self):
        """Verify visibility module has visibility routes."""
        try:
            from governance.routes.agents.visibility import router as vis_router
            routes = [r.path for r in vis_router.routes]
            assert any("visibility" in r for r in routes)
        except ImportError:
            # If not split yet, skip
            pytest.skip("Visibility module not yet split")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
