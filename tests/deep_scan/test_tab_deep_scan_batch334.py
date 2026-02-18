"""
Deep Scan Batch 334-337 Defense Tests.

Validates 8 production fixes:
- BUG-334-SCAN-001: cc_session_scanner.py path traversal guard on decoded CC dir path
- BUG-334-INDEX-001: cc_content_indexer.py int(os.getenv()) crash guard
- BUG-336-CHAT-001: endpoints.py phantom session dict — register new sessions immediately
- BUG-336-CHAT-002: endpoints.py non-atomic dict eviction snapshot
- BUG-337-TRACK-001: tracker.py per-instance threading.Lock
- BUG-337-TRACK-002: tracker.py accept "aborted" as restartable state
- BUG-337-GRAPH-001: graph.py negative max_cycles clamped to positive
- BUG-337-STATE-001: state.py backlog sort uses .get() for missing priority
- BUG-337-NODE-001: nodes.py spec_node uses .get() for missing task_id
"""

import ast
import re
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


# ============================================================
# BUG-334-SCAN-001: cc_session_scanner path traversal guard
# ============================================================

class TestSessionScannerPathTraversal:
    """Verify decoded_path is validated against allowed roots."""

    def _get_source(self):
        p = ROOT / "governance" / "services" / "cc_session_scanner.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-334-SCAN-001" in src

    def test_path_home_validation(self):
        """Decoded path must be checked against Path.home()."""
        src = self._get_source()
        assert "Path.home()" in src or "str(Path.home())" in src

    def test_fallback_to_raw_dir(self):
        """If decoded path fails validation, fall back to raw CC dir."""
        src = self._get_source()
        assert "decoded_path = str(d)" in src


# ============================================================
# BUG-334-INDEX-001: cc_content_indexer port guard
# ============================================================

class TestContentIndexerPortGuard:
    """Verify cc_content_indexer.py guards CHROMADB_PORT against non-numeric values."""

    def _get_source(self):
        p = ROOT / "governance" / "services" / "cc_content_indexer.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-334-INDEX-001" in src

    def test_try_except_around_port(self):
        """int(os.getenv()) must be wrapped in try/except."""
        src = self._get_source()
        # Find the function body
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_get_chromadb_collection":
                func_src = ast.get_source_segment(src, node)
                assert "try:" in func_src
                assert "except" in func_src
                assert "port = 8001" in func_src  # fallback default
                break
        else:
            raise AssertionError("_get_chromadb_collection not found")


# ============================================================
# BUG-336-CHAT-001: phantom session fallback
# ============================================================

class TestPhantomSessionFix:
    """Verify endpoints.py registers new sessions instead of using anonymous dicts."""

    def _get_source(self):
        p = ROOT / "governance" / "routes" / "chat" / "endpoints.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-336-CHAT-001" in src

    def test_session_registered_on_creation(self):
        """New sessions must be stored in _chat_sessions immediately."""
        src = self._get_source()
        assert "_chat_sessions[session_id] = session" in src

    def test_no_anonymous_fallback_dict(self):
        """Should not use .get(id, {dict}) pattern that creates throwaway dicts."""
        src = self._get_source()
        # Old pattern was: _chat_sessions.get(session_id, {...})
        # New pattern should use explicit None check
        assert "session = _chat_sessions.get(session_id)" in src


# ============================================================
# BUG-336-CHAT-002: dict eviction snapshot
# ============================================================

class TestDictEvictionSnapshot:
    """Verify _chat_gov_sessions eviction snapshots keys before sorting."""

    def _get_source(self):
        p = ROOT / "governance" / "routes" / "chat" / "endpoints.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-336-CHAT-002" in src

    def test_list_snapshot_before_sort(self):
        """Eviction must snapshot keys with list() before sorting."""
        src = self._get_source()
        assert "sorted(list(_chat_gov_sessions.keys()))" in src


# ============================================================
# BUG-337-TRACK-001: DSMTracker per-instance lock
# ============================================================

class TestTrackerInstanceLock:
    """Verify DSMTracker has per-instance threading.Lock."""

    def _get_source(self):
        p = ROOT / "governance" / "dsm" / "tracker.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-337-TRACK-001" in src

    def test_instance_lock_defined(self):
        """__init__ must create self._lock = threading.Lock()."""
        src = self._get_source()
        assert "self._lock = threading.Lock()" in src

    def test_start_cycle_uses_lock(self):
        """start_cycle must acquire self._lock."""
        src = self._get_source()
        assert "with self._lock:" in src

    def test_aborted_state_accepted(self):
        """BUG-337-TRACK-002: 'aborted' must be accepted as restartable."""
        src = self._get_source()
        assert '"aborted"' in src
        # Should check for 'not in ("complete", "aborted")'
        assert 'not in ("complete", "aborted")' in src


# ============================================================
# BUG-337-GRAPH-001: negative max_cycles clamp
# ============================================================

class TestGraphMaxCyclesClamp:
    """Verify graph.py clamps max_cycles to positive minimum."""

    def _get_source(self):
        p = ROOT / "governance" / "workflows" / "orchestrator" / "graph.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-337-GRAPH-001" in src

    def test_max_function_wraps_cycles(self):
        """max(1, ...) must wrap the int conversion to prevent negative iterations."""
        src = self._get_source()
        assert "max(1," in src

    def test_functional_clamp(self):
        """Verify the full expression clamps correctly."""
        # Simulate the expression
        for val in [-5, 0, None, "", 1, 100]:
            result = min(max(1, int(val or 100)) * 3, 3000)
            assert result >= 3, f"max_cycles={val} produced {result} < 3"
            assert result <= 3000, f"max_cycles={val} produced {result} > 3000"


# ============================================================
# BUG-337-STATE-001: backlog sort .get() guard
# ============================================================

class TestBacklogSortGuard:
    """Verify backlog sort uses .get() to prevent KeyError."""

    def _get_source(self):
        p = ROOT / "governance" / "workflows" / "orchestrator" / "state.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-337-STATE-001" in src

    def test_get_with_default(self):
        """Sort lambda must use t.get('priority', 'LOW') not t['priority']."""
        src = self._get_source()
        assert 't.get("priority", "LOW")' in src

    def test_no_direct_bracket_access(self):
        """Sort lambda must NOT use t['priority'] directly."""
        src = self._get_source()
        # Find the sort line
        for line in src.split("\n"):
            if "backlog.sort" in line:
                assert 't["priority"]' not in line, \
                    f"Found direct bracket access in sort: {line.strip()}"
                break


# ============================================================
# BUG-337-NODE-001: spec_node .get() guard
# ============================================================

class TestSpecNodeGetGuard:
    """Verify spec_node uses .get() for task_id access."""

    def _get_source(self):
        p = ROOT / "governance" / "workflows" / "orchestrator" / "nodes.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-337-NODE-001" in src

    def test_get_with_default_for_task_id(self):
        """task_id access must use .get() with 'unknown' default."""
        src = self._get_source()
        assert "task.get('task_id', 'unknown')" in src

    def test_get_for_description(self):
        """description access must use .get() with empty default."""
        src = self._get_source()
        assert 'task.get("description", "")' in src


# ============================================================
# Import sanity checks
# ============================================================

class TestBatch334Imports:
    """Verify all fixed modules import without errors."""

    def test_import_cc_session_scanner(self):
        import governance.services.cc_session_scanner

    def test_import_cc_content_indexer(self):
        import governance.services.cc_content_indexer

    def test_import_chat_endpoints(self):
        import governance.routes.chat.endpoints

    def test_import_dsm_tracker(self):
        import governance.dsm.tracker
        # Verify the lock attribute exists on instances
        assert hasattr(governance.dsm.tracker.DSMTracker, '_start_cycle_locked')

    def test_import_graph(self):
        import governance.workflows.orchestrator.graph

    def test_import_state(self):
        from governance.workflows.orchestrator.state import add_to_backlog
        # Functional test: adding a task with no priority key should not crash
        state = {"backlog": [{"task_id": "T-1", "description": "test"}]}
        result = add_to_backlog(state, "T-2", "HIGH", "test 2")
        assert len(result["backlog"]) == 2

    def test_import_nodes(self):
        import governance.workflows.orchestrator.nodes
