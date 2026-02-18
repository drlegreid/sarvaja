"""Batch 246 — Orchestrator layer defense tests.

Validates fixes for:
- BUG-246-NOD-001: Path traversal sanitization in spec_node
- BUG-246-EDG-001: None validation_passed routes to park (not retry)
- BUG-246-GRP-001: Type coercion on max_cycles safety cap
- BUG-246-NOD-005: Operator precedence in certify_node filter
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-246-NOD-001: Path traversal sanitization ─────────────────────

class TestSpecNodePathTraversal:
    """spec_node must sanitize task_id before using in file paths."""

    def test_re_import_present(self):
        src = (SRC / "governance/workflows/orchestrator/nodes.py").read_text()
        assert "import re" in src

    def test_re_sub_sanitization(self):
        src = (SRC / "governance/workflows/orchestrator/nodes.py").read_text()
        idx = src.index("def spec_node")
        block = src[idx:idx + 600]
        assert "re.sub(" in block

    def test_safe_id_used_in_path(self):
        src = (SRC / "governance/workflows/orchestrator/nodes.py").read_text()
        idx = src.index("def spec_node")
        block = src[idx:idx + 600]
        assert "safe_id" in block

    def test_no_raw_task_id_in_path(self):
        """task['task_id'] must NOT appear directly in f-string file path."""
        src = (SRC / "governance/workflows/orchestrator/nodes.py").read_text()
        idx = src.index("def spec_node")
        block = src[idx:idx + 600]
        assert "task['task_id'].lower()}.py" not in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/workflows/orchestrator/nodes.py").read_text()
        assert "BUG-246-NOD-001" in src

    def test_traversal_stripped(self):
        """Dots and slashes must be sanitized to underscores."""
        from governance.workflows.orchestrator.nodes import spec_node
        state = {"current_task": {"task_id": "../../etc/passwd", "description": "test"}}
        result = spec_node(state)
        files = result["specification"]["files_to_modify"]
        assert ".." not in files[0]
        assert "/" not in files[0].split("orchestrator/")[1].split(".py")[0]


# ── BUG-246-EDG-001: None validation_passed distinction ──────────────

class TestEdgeNoneValidation:
    """check_validation_result must distinguish None from False."""

    def test_vp_is_true_check(self):
        src = (SRC / "governance/workflows/orchestrator/edges.py").read_text()
        idx = src.index("def check_validation_result")
        block = src[idx:idx + 600]
        assert "vp is True" in block

    def test_vp_is_none_check(self):
        src = (SRC / "governance/workflows/orchestrator/edges.py").read_text()
        idx = src.index("def check_validation_result")
        block = src[idx:idx + 600]
        assert "vp is None" in block

    def test_none_routes_to_park(self):
        from governance.workflows.orchestrator.edges import check_validation_result
        state = {"validation_passed": None, "retry_count": 0}
        assert check_validation_result(state) == "park_task"

    def test_false_routes_to_retry(self):
        from governance.workflows.orchestrator.edges import check_validation_result
        state = {"validation_passed": False, "retry_count": 0}
        assert check_validation_result(state) == "loop_to_spec"

    def test_true_routes_to_complete(self):
        from governance.workflows.orchestrator.edges import check_validation_result
        state = {"validation_passed": True, "gaps_discovered": []}
        assert check_validation_result(state) == "complete_cycle"

    def test_true_with_gaps_routes_to_inject(self):
        from governance.workflows.orchestrator.edges import check_validation_result
        state = {"validation_passed": True, "gaps_discovered": [{"gap_id": "G1"}]}
        assert check_validation_result(state) == "inject"

    def test_bug_marker_present(self):
        src = (SRC / "governance/workflows/orchestrator/edges.py").read_text()
        assert "BUG-246-EDG-001" in src


# ── BUG-246-GRP-001: max_cycles type coercion ────────────────────────

class TestGraphMaxCyclesCoercion:
    """_run_fallback_workflow must coerce max_cycles to int."""

    def test_int_coercion_present(self):
        src = (SRC / "governance/workflows/orchestrator/graph.py").read_text()
        idx = src.index("def _run_fallback_workflow")
        block = src[idx:idx + 400]
        assert "int(state.get(\"max_cycles\"" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/workflows/orchestrator/graph.py").read_text()
        assert "BUG-246-GRP-001" in src


# ── BUG-246-NOD-005: Operator precedence in certify_node ─────────────

class TestCertifyNodePrecedence:
    """certify_node must use != instead of 'not x == y'."""

    def test_uses_not_equal(self):
        src = (SRC / "governance/workflows/orchestrator/nodes.py").read_text()
        idx = src.index("def certify_node")
        block = src[idx:idx + 600]
        assert '!= "parked"' in block

    def test_no_not_equals_pattern(self):
        """'not h.get(...) ==' pattern must be gone."""
        src = (SRC / "governance/workflows/orchestrator/nodes.py").read_text()
        idx = src.index("def certify_node")
        block = src[idx:idx + 600]
        assert 'not h.get("status") ==' not in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/workflows/orchestrator/nodes.py").read_text()
        assert "BUG-246-NOD-005" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch246Imports:
    def test_nodes_importable(self):
        import governance.workflows.orchestrator.nodes
        assert governance.workflows.orchestrator.nodes is not None

    def test_edges_importable(self):
        import governance.workflows.orchestrator.edges
        assert governance.workflows.orchestrator.edges is not None

    def test_graph_importable(self):
        import governance.workflows.orchestrator.graph
        assert governance.workflows.orchestrator.graph is not None

    def test_state_importable(self):
        import governance.workflows.orchestrator.state
        assert governance.workflows.orchestrator.state is not None

    def test_spec_tiers_importable(self):
        import governance.workflows.orchestrator.spec_tiers
        assert governance.workflows.orchestrator.spec_tiers is not None

    def test_budget_importable(self):
        import governance.workflows.orchestrator.budget
        assert governance.workflows.orchestrator.budget is not None
