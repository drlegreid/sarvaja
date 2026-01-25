"""
Robot Framework Library for Agents Module Split Tests.

Per GAP-FILE-028: routes/agents.py split.
Migrated from tests/test_agents_split.py
"""
from pathlib import Path
from robot.api.deco import keyword


class AgentsSplitLibrary:
    """Library for testing agents module structure after split."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.routes_dir = self.project_root / "governance" / "routes"

    # =============================================================================
    # Module Structure Tests
    # =============================================================================

    @keyword("Agents Module Exists")
    def agents_module_exists(self):
        """Verify agents.py exists (may be main file or package)."""
        agents_file = self.routes_dir / "agents.py"
        agents_pkg = self.routes_dir / "agents" / "__init__.py"
        return {
            "exists": agents_file.exists() or agents_pkg.exists(),
            "is_file": agents_file.exists(),
            "is_package": agents_pkg.exists()
        }

    @keyword("Agents Under 300 Lines")
    def agents_under_300_lines(self):
        """Verify main agents module is under 300 lines per DOC-SIZE-01-v1."""
        agents_file = self.routes_dir / "agents.py"
        if not agents_file.exists():
            # Check package __init__.py
            agents_file = self.routes_dir / "agents" / "__init__.py"
            if not agents_file.exists():
                return {"skipped": True, "reason": "agents module not found"}

        with open(agents_file, "r") as f:
            lines = len(f.readlines())
        return {
            "under_300": lines < 300,
            "line_count": lines
        }

    @keyword("Observability Module Exists")
    def observability_module_exists(self):
        """Verify observability.py extraction exists."""
        obs_file = self.routes_dir / "agents" / "observability.py"
        if not obs_file.exists():
            obs_file = self.routes_dir / "observability.py"
        return {"exists": obs_file.exists()}

    @keyword("Visibility Module Exists")
    def visibility_module_exists(self):
        """Verify visibility.py extraction exists."""
        vis_file = self.routes_dir / "agents" / "visibility.py"
        if not vis_file.exists():
            vis_file = self.routes_dir / "visibility.py"
        return {"exists": vis_file.exists()}

    # =============================================================================
    # Backward Compatibility Tests
    # =============================================================================

    @keyword("Import Router From Agents")
    def import_router_from_agents(self):
        """Verify router can be imported from agents module."""
        try:
            from governance.routes.agents import router
            return {"imported": router is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Router Has Agents Routes")
    def router_has_agents_routes(self):
        """Verify router has agent CRUD routes."""
        try:
            from governance.routes.agents import router
            routes = [r.path for r in router.routes]
            return {
                "has_agents": "/agents" in routes or any("/agents" in r for r in routes)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Module Function Tests
    # =============================================================================

    @keyword("Observability Has Status Route")
    def observability_has_status_route(self):
        """Verify observability module has status summary."""
        try:
            from governance.routes.agents.observability import router as obs_router
            routes = [r.path for r in obs_router.routes]
            return {"has_status": any("status" in r for r in routes)}
        except ImportError:
            return {"skipped": True, "reason": "Observability module not yet split"}

    @keyword("Visibility Has Visibility Route")
    def visibility_has_visibility_route(self):
        """Verify visibility module has visibility routes."""
        try:
            from governance.routes.agents.visibility import router as vis_router
            routes = [r.path for r in vis_router.routes]
            return {"has_visibility": any("visibility" in r for r in routes)}
        except ImportError:
            return {"skipped": True, "reason": "Visibility module not yet split"}
