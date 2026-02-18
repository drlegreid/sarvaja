"""Batch 234 — Compat + orchestrator + chat defense tests.

Validates fixes for:
- BUG-234-LOGIC-002: state["cycles_completed"] KeyError on partial state
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-234-LOGIC-002: cycles_completed safe access ─────────────────

class TestOrchestratorCyclesCompleted:
    """cycles_completed must use .get() with default."""

    def test_uses_get_with_default(self):
        src = (SRC / "governance/workflows/orchestrator/nodes.py").read_text()
        assert 'state.get("cycles_completed", 0)' in src

    def test_no_direct_subscript(self):
        """Should not use state['cycles_completed'] — raises KeyError on partial state."""
        src = (SRC / "governance/workflows/orchestrator/nodes.py").read_text()
        assert 'state["cycles_completed"]' not in src

    def test_bug_marker_present(self):
        src = (SRC / "governance/workflows/orchestrator/nodes.py").read_text()
        assert "BUG-234-LOGIC-002" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch234Imports:
    def test_orchestrator_graph_importable(self):
        import governance.workflows.orchestrator.graph
        assert governance.workflows.orchestrator.graph is not None

    def test_orchestrator_nodes_importable(self):
        import governance.workflows.orchestrator.nodes
        assert governance.workflows.orchestrator.nodes is not None

    def test_orchestrator_state_importable(self):
        import governance.workflows.orchestrator.state
        assert governance.workflows.orchestrator.state is not None

    def test_orchestrator_spec_tiers_importable(self):
        import governance.workflows.orchestrator.spec_tiers
        assert governance.workflows.orchestrator.spec_tiers is not None

    def test_chat_commands_importable(self):
        import governance.routes.chat.commands
        assert governance.routes.chat.commands is not None

    def test_chat_endpoints_importable(self):
        import governance.routes.chat.endpoints
        assert governance.routes.chat.endpoints is not None

    def test_chat_session_bridge_importable(self):
        import governance.routes.chat.session_bridge
        assert governance.routes.chat.session_bridge is not None

    def test_api_startup_importable(self):
        import governance.api_startup
        assert governance.api_startup is not None
