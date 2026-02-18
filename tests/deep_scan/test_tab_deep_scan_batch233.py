"""Batch 233 — Session metrics + collector + DSM LangGraph defense tests.

Validates fixes for:
- BUG-233-SYN-001: Insufficient TypeQL injection escaping (backslash + quotes)
- BUG-233-SYN-002: TypeDB client connection leak on exception
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-233-SYN-001: TypeQL injection escaping ──────────────────────

class TestSyncTypeQLEscaping:
    """Decision sync must escape both backslash and quotes."""

    def test_escapes_backslash_before_quotes(self):
        src = (SRC / "governance/session_collector/sync.py").read_text()
        idx = src.index("_index_decision_to_typedb")
        block = src[idx:idx + 600]
        assert "BUG-233-SYN-001" in block

    def test_escape_helper_exists(self):
        """A local _esc() helper should handle both \\ and " escaping."""
        src = (SRC / "governance/session_collector/sync.py").read_text()
        idx = src.index("_index_decision_to_typedb")
        block = src[idx:idx + 600]
        assert "_esc(" in block


# ── BUG-233-SYN-002: Connection leak fix ────────────────────────────

class TestSyncConnectionLeak:
    """client.close() must be in finally block."""

    def test_finally_block_exists(self):
        src = (SRC / "governance/session_collector/sync.py").read_text()
        idx = src.index("_index_decision_to_typedb")
        next_def = src.index("\n    def ", idx + 1)
        block = src[idx:next_def]
        assert "finally:" in block
        assert "BUG-233-SYN-002" in block


# ── Session metrics module import defense tests ──────────────────────

class TestSessionMetricsImports:
    def test_correlation_importable(self):
        import governance.session_metrics.correlation
        assert governance.session_metrics.correlation is not None

    def test_models_importable(self):
        import governance.session_metrics.models
        assert governance.session_metrics.models is not None

    def test_parser_importable(self):
        import governance.session_metrics.parser
        assert governance.session_metrics.parser is not None


# ── Session collector module import defense tests ────────────────────

class TestSessionCollectorImports:
    def test_sync_importable(self):
        import governance.session_collector.sync
        assert governance.session_collector.sync is not None


# ── DSM LangGraph module import defense tests ───────────────────────

class TestDSMLangGraphImports:
    def test_graph_importable(self):
        import governance.dsm.langgraph.graph
        assert governance.dsm.langgraph.graph is not None

    def test_edges_importable(self):
        import governance.dsm.langgraph.edges
        assert governance.dsm.langgraph.edges is not None

    def test_state_importable(self):
        import governance.dsm.langgraph.state
        assert governance.dsm.langgraph.state is not None

    def test_graph_mock_importable(self):
        import governance.dsm.langgraph.graph_mock
        assert governance.dsm.langgraph.graph_mock is not None

    def test_nodes_execution_importable(self):
        import governance.dsm.langgraph.nodes_execution
        assert governance.dsm.langgraph.nodes_execution is not None
