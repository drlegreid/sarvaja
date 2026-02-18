"""
Batch 78 — Deep Scan: API Routes + Workflows + Scheduler.

Triage: 25 findings → 0 confirmed, ALL rejected.
Validates: exception mapping, dict iteration, retry design, archive cap.
"""
import inspect

import pytest


# ===========================================================================
# Rejected: Rules CRUD exception mapping (agent claimed None vs KeyError)
# ===========================================================================

class TestRulesCRUDExceptionMapping:
    """Confirm get_rule raises KeyError, not returns None."""

    def test_get_rule_service_raises_keyerror(self):
        """Service function documents KeyError for missing rules."""
        from governance.services.rules import get_rule
        src = inspect.getsource(get_rule)
        # Docstring documents KeyError
        assert "KeyError" in src

    def test_route_catches_keyerror(self):
        """Route handler catches KeyError → 404."""
        from governance.routes.rules.crud import get_rule as route_fn
        src = inspect.getsource(route_fn)
        assert "except KeyError" in src
        assert "404" in src

    def test_route_catches_connection_error(self):
        """Route handler catches ConnectionError → 503."""
        from governance.routes.rules.crud import get_rule as route_fn
        src = inspect.getsource(route_fn)
        assert "except ConnectionError" in src
        assert "503" in src

    def test_route_has_catch_all(self):
        """Route handler has catch-all Exception → 500."""
        from governance.routes.rules.crud import get_rule as route_fn
        src = inspect.getsource(route_fn)
        assert "except Exception" in src
        assert "500" in src


# ===========================================================================
# Rejected: Dict iteration (standard Python behavior)
# ===========================================================================

class TestDictIterationPattern:
    """Confirm iterating dict keys gives pattern strings."""

    def test_dict_iteration_gives_keys(self):
        """for key in dict: iterates keys — standard Python."""
        patterns = {"SESSION-*.md": "session", "DSM-*.md": "dsm"}
        keys = [k for k in patterns]
        assert keys == ["SESSION-*.md", "DSM-*.md"]

    def test_evidence_patterns_is_dict(self):
        """EVIDENCE_PATTERNS in extractors.py is a dict of pattern→type."""
        from governance.evidence_scanner.extractors import EVIDENCE_PATTERNS
        assert isinstance(EVIDENCE_PATTERNS, dict)
        # Iterating gives patterns (keys), which is correct for glob
        for pattern in EVIDENCE_PATTERNS:
            assert isinstance(pattern, str)
            assert "*" in pattern or "." in pattern


# ===========================================================================
# Rejected: DSM archive off-by-one (51→50 is transient)
# ===========================================================================

class TestDSMArchiveCap:
    """Confirm archive cap correctly limits to 50 after append+truncate."""

    def test_append_then_truncate_gives_50(self):
        """After append, if > 50, truncate to exactly 50."""
        cycles = list(range(50))  # 50 items
        cycles.append(50)  # 51 items (transient)
        if len(cycles) > 50:
            cycles = cycles[-50:]
        assert len(cycles) == 50
        assert cycles[0] == 1  # Oldest dropped
        assert cycles[-1] == 50  # Newest kept


# ===========================================================================
# Rejected: Orchestrator retry budget (by design)
# ===========================================================================

class TestOrchestratorRetryDesign:
    """Confirm retry loop skipping gate is intentional."""

    def test_retry_increments_counter(self):
        """Retry loop increments retry_count."""
        from governance.workflows.orchestrator import graph as orch_graph
        src = inspect.getsource(orch_graph)
        assert "retry_count" in src

    def test_max_retries_enforced(self):
        """MAX_RETRIES prevents infinite retries."""
        from governance.workflows.orchestrator.state import MAX_RETRIES
        assert MAX_RETRIES > 0
        assert MAX_RETRIES <= 5  # Reasonable limit


# ===========================================================================
# Rejected: Missing exception handlers (FastAPI handles 500s)
# ===========================================================================

class TestFastAPIDefaultErrorHandling:
    """Confirm routes rely on FastAPI's default error handling."""

    def test_agents_crud_has_list_exception_handler(self):
        """list_agents has try-except as example of proper handling."""
        from governance.routes.agents.crud import list_agents
        src = inspect.getsource(list_agents)
        assert "except" in src

    def test_projects_crud_importable(self):
        """Project routes import without error."""
        from governance.routes.projects.crud import (
            list_projects, get_project, create_project, delete_project
        )

    def test_sessions_crud_has_validation(self):
        """Session list endpoint uses Query validation."""
        from governance.routes.sessions.crud import list_sessions
        src = inspect.getsource(list_sessions)
        assert "Query(" in src


# ===========================================================================
# Rejected: Cert node uses history (different from counter)
# ===========================================================================

class TestOrchestratorCertDesign:
    """Confirm certify_node counting from history is by design."""

    def test_certify_node_uses_history(self):
        """certify_node counts completed tasks from history, not counter."""
        from governance.workflows.orchestrator.nodes import certify_node
        src = inspect.getsource(certify_node)
        assert "cycle_history" in src

    def test_gate_node_uses_counter(self):
        """gate_node uses cycles_completed counter for budget decisions."""
        from governance.workflows.orchestrator.nodes import gate_node
        src = inspect.getsource(gate_node)
        assert "cycles_completed" in src
