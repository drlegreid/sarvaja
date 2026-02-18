"""Batch 266-269 — Graph None guard, node KeyError, correlation timezone,
vector store search guard, sync UnboundLocalError, rules_query logging,
UI null guard tests.

Validates fixes for:
- BUG-266-GRAPH-001: max_cycles None guard in graph.py
- BUG-266-NODE-001: state["backlog"] → state.get("backlog", []) in nodes.py
- BUG-267-CORR-001: Mixed timezone TypeError guard in correlation.py
- BUG-267-VSTORE-001: search() connected guard in vector_store/store.py
- BUG-267-SYNC-001: client=None before try in sync.py _index_decision_to_typedb
- BUG-268-RQUERY-001: Logging in silent except blocks in rules_query.py
- BUG-269-PANEL-001: proposals null guard in trust/panels.py
- BUG-269-TRANSCRIPT-001: session_transcript null guard in session_transcript.py
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-266-GRAPH-001: graph.py max_cycles None guard ────────────────

class TestGraphMaxCyclesGuard:
    """graph.py must use `or 100` to guard against explicit None max_cycles."""

    def test_or_guard_present(self):
        src = (SRC / "governance/workflows/orchestrator/graph.py").read_text()
        idx = src.index("def _run_fallback_workflow")
        block = src[idx:idx + 600]
        assert 'state.get("max_cycles") or 100' in block

    def test_no_bare_default_100(self):
        """Must NOT have state.get("max_cycles", 100) — that passes None through."""
        src = (SRC / "governance/workflows/orchestrator/graph.py").read_text()
        idx = src.index("def _run_fallback_workflow")
        block = src[idx:idx + 600]
        assert 'state.get("max_cycles", 100)' not in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/workflows/orchestrator/graph.py").read_text()
        assert "BUG-266-GRAPH-001" in src


# ── BUG-266-NODE-001: nodes.py backlog .get() guard ──────────────────

class TestNodesBacklogGuard:
    """nodes.py must use .get("backlog", []) instead of state["backlog"]."""

    def test_backlog_node_uses_get(self):
        src = (SRC / "governance/workflows/orchestrator/nodes.py").read_text()
        idx = src.index("def backlog_node")
        block = src[idx:idx + 400]
        assert 'state.get("backlog"' in block

    def test_inject_node_uses_get(self):
        src = (SRC / "governance/workflows/orchestrator/nodes.py").read_text()
        idx = src.index("def inject_node")
        block = src[idx:idx + 400]
        assert 'state.get("backlog"' in block

    def test_no_bare_state_backlog(self):
        """No bare state["backlog"] should exist (only state.get("backlog"...))."""
        src = (SRC / "governance/workflows/orchestrator/nodes.py").read_text()
        assert 'state["backlog"]' not in src

    def test_bug_marker_present(self):
        src = (SRC / "governance/workflows/orchestrator/nodes.py").read_text()
        assert "BUG-266-NODE-001" in src


# ── BUG-267-CORR-001: correlation.py timezone guard ──────────────────

class TestCorrelationTimezoneGuard:
    """correlation.py must guard against mixed timezone TypeError."""

    def test_try_except_present(self):
        src = (SRC / "governance/session_metrics/correlation.py").read_text()
        idx = src.index("def correlate_tool_calls")
        block = src[idx:idx + 1500]
        assert "except TypeError" in block

    def test_delta_none_fallback(self):
        src = (SRC / "governance/session_metrics/correlation.py").read_text()
        idx = src.index("def correlate_tool_calls")
        block = src[idx:idx + 1800]
        assert "delta is None" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/session_metrics/correlation.py").read_text()
        assert "BUG-267-CORR-001" in src


# ── BUG-267-VSTORE-001: vector_store search guard ────────────────────

class TestVectorStoreSearchGuard:
    """VectorStore.search() must check _connected before loading cache."""

    def test_connected_guard_in_search(self):
        src = (SRC / "governance/vector_store/store.py").read_text()
        idx = src.index("def search(")
        block = src[idx:idx + 1200]
        assert "_connected" in block

    def test_returns_empty_when_disconnected(self):
        src = (SRC / "governance/vector_store/store.py").read_text()
        idx = src.index("def search(")
        block = src[idx:idx + 1200]
        assert "return []" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/vector_store/store.py").read_text()
        assert "BUG-267-VSTORE-001" in src


# ── BUG-267-SYNC-001: sync.py client=None guard ──────────────────────

class TestSyncClientNoneGuard:
    """_index_decision_to_typedb must initialize client=None before try."""

    def test_decision_indexer_has_client_none(self):
        src = (SRC / "governance/session_collector/sync.py").read_text()
        idx = src.index("def _index_decision_to_typedb")
        block = src[idx:idx + 800]
        assert "client = None" in block

    def test_decision_finally_checks_none(self):
        src = (SRC / "governance/session_collector/sync.py").read_text()
        idx = src.index("def _index_decision_to_typedb")
        block = src[idx:idx + 2000]
        assert "client is not None" in block

    def test_task_indexer_also_guarded(self):
        """_index_task_to_typedb should also have client=None (BUG-248-SYN-002)."""
        src = (SRC / "governance/session_collector/sync.py").read_text()
        idx = src.index("def _index_task_to_typedb")
        block = src[idx:idx + 600]
        assert "client = None" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/session_collector/sync.py").read_text()
        assert "BUG-267-SYNC-001" in src


# ── BUG-268-RQUERY-001: rules_query.py logging ───────────────────────

class TestRulesQueryLogging:
    """Silent except blocks in rules_query.py must log."""

    def test_rules_query_except_logs(self):
        src = (SRC / "governance/mcp_tools/rules_query.py").read_text()
        idx = src.index("def rules_query(")
        block = src[idx:idx + 2500]
        assert "logger" in block or "logging" in block or "_logging" in block

    def test_rule_get_except_logs(self):
        src = (SRC / "governance/mcp_tools/rules_query.py").read_text()
        idx = src.index("def rule_get(")
        block = src[idx:idx + 1500]
        assert "logger" in block or "logging" in block or "_logging" in block

    def test_no_bare_except_pass(self):
        """No bare 'except Exception:\\n            use_fallback' without logging."""
        src = (SRC / "governance/mcp_tools/rules_query.py").read_text()
        lines = src.split("\n")
        for i, line in enumerate(lines):
            if "except Exception:" in line.strip() and "except Exception as" not in line:
                # Bare except without 'as e' — should not exist
                assert False, f"Bare except without 'as e' at line {i+1}: {line.strip()}"

    def test_bug_marker_present(self):
        src = (SRC / "governance/mcp_tools/rules_query.py").read_text()
        assert "BUG-268-RQUERY-001" in src


# ── BUG-269-PANEL-001: trust/panels.py null guard ────────────────────

class TestPanelsNullGuard:
    """proposals.slice must have null guard."""

    def test_proposals_null_guard(self):
        src = (SRC / "agent/governance_ui/views/trust/panels.py").read_text()
        assert "(proposals || []).slice" in src

    def test_no_bare_proposals_slice(self):
        src = (SRC / "agent/governance_ui/views/trust/panels.py").read_text()
        assert "proposals.slice" not in src.replace("(proposals || []).slice", "")

    def test_bug_marker_present(self):
        src = (SRC / "agent/governance_ui/views/trust/panels.py").read_text()
        assert "BUG-269-PANEL-001" in src


# ── BUG-269-TRANSCRIPT-001: session_transcript null guard ─────────────

class TestTranscriptNullGuard:
    """session_transcript.length must have null guard."""

    def test_length_has_null_guard(self):
        src = (SRC / "agent/governance_ui/views/sessions/session_transcript.py").read_text()
        assert "(session_transcript || []).length" in src

    def test_v_if_has_null_guard(self):
        src = (SRC / "agent/governance_ui/views/sessions/session_transcript.py").read_text()
        assert "session_transcript && session_transcript.length > 0" in src

    def test_empty_state_has_null_guard(self):
        src = (SRC / "agent/governance_ui/views/sessions/session_transcript.py").read_text()
        assert "!session_transcript || session_transcript.length === 0" in src

    def test_bug_marker_present(self):
        src = (SRC / "agent/governance_ui/views/sessions/session_transcript.py").read_text()
        assert "BUG-269-TRANSCRIPT-001" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch266Imports:
    def test_graph_importable(self):
        import governance.workflows.orchestrator.graph
        assert governance.workflows.orchestrator.graph is not None

    def test_nodes_importable(self):
        import governance.workflows.orchestrator.nodes
        assert governance.workflows.orchestrator.nodes is not None

    def test_correlation_importable(self):
        import governance.session_metrics.correlation
        assert governance.session_metrics.correlation is not None

    def test_vector_store_importable(self):
        import governance.vector_store.store
        assert governance.vector_store.store is not None

    def test_sync_importable(self):
        import governance.session_collector.sync
        assert governance.session_collector.sync is not None

    def test_rules_query_importable(self):
        import governance.mcp_tools.rules_query
        assert governance.mcp_tools.rules_query is not None

    def test_panels_importable(self):
        import agent.governance_ui.views.trust.panels
        assert agent.governance_ui.views.trust.panels is not None

    def test_session_transcript_importable(self):
        import agent.governance_ui.views.sessions.session_transcript
        assert agent.governance_ui.views.sessions.session_transcript is not None
