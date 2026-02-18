"""Batch 243 — Routes layer defense tests.

Validates fixes for:
- BUG-243-RUN-001: Test pattern validation in runner.py
- BUG-243-RUN-002: Markers validation in runner.py
- BUG-243-HRUN-001: KeyError guard in heuristic_runner.py
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-243-RUN-001: Test pattern validation ────────────────────────

class TestRunnerPatternValidation:
    """Pattern param must be validated before subprocess."""

    def test_pattern_regex_present(self):
        src = (SRC / "governance/routes/tests/runner.py").read_text()
        idx = src.index("if pattern:")
        block = src[idx:idx + 400]
        assert "re.match(" in block or "_re.match(" in block

    def test_pattern_must_start_with_tests(self):
        src = (SRC / "governance/routes/tests/runner.py").read_text()
        idx = src.index("if pattern:")
        block = src[idx:idx + 400]
        assert "tests/" in block

    def test_pattern_raises_400(self):
        src = (SRC / "governance/routes/tests/runner.py").read_text()
        idx = src.index("if pattern:")
        block = src[idx:idx + 400]
        assert "400" in block or "HTTPException" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/routes/tests/runner.py").read_text()
        assert "BUG-243-RUN-001" in src


# ── BUG-243-RUN-002: Markers validation ─────────────────────────────

class TestRunnerMarkersValidation:
    """Markers param must be validated before subprocess."""

    def test_markers_regex_present(self):
        src = (SRC / "governance/routes/tests/runner.py").read_text()
        idx = src.index("if markers:")
        block = src[idx:idx + 400]
        assert "re.match(" in block or "_re.match(" in block

    def test_markers_raises_400(self):
        src = (SRC / "governance/routes/tests/runner.py").read_text()
        # Find the markers validation block (not the first `if markers:`)
        assert "BUG-243-RUN-002" in src

    def test_bug_marker_present(self):
        src = (SRC / "governance/routes/tests/runner.py").read_text()
        assert "BUG-243-RUN-002" in src


# ── BUG-243-HRUN-001: KeyError guard ────────────────────────────────

class TestHeuristicRunnerKeyGuard:
    """result['status'] must use .get() to prevent KeyError."""

    def test_uses_get_for_status(self):
        src = (SRC / "governance/routes/tests/heuristic_runner.py").read_text()
        # Find the actual call site, not the import
        idx = src.index("record_chat_tool_call(")
        block = src[idx:idx + 500]
        assert "result.get(" in block

    def test_no_direct_subscript_in_record_call(self):
        """result['status'] must not be used in record_chat_tool_call args."""
        src = (SRC / "governance/routes/tests/heuristic_runner.py").read_text()
        idx = src.index("record_chat_tool_call")
        block = src[idx:idx + 300]
        assert "result['status']" not in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/routes/tests/heuristic_runner.py").read_text()
        assert "BUG-243-HRUN-001" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch243Imports:
    def test_runner_importable(self):
        import governance.routes.tests.runner
        assert governance.routes.tests.runner is not None

    def test_heuristic_runner_importable(self):
        import governance.routes.tests.heuristic_runner
        assert governance.routes.tests.heuristic_runner is not None

    def test_runner_store_importable(self):
        import governance.routes.tests.runner_store
        assert governance.routes.tests.runner_store is not None

    def test_heuristic_checks_importable(self):
        import governance.routes.tests.heuristic_checks
        assert governance.routes.tests.heuristic_checks is not None

    def test_sessions_detail_importable(self):
        import governance.routes.sessions.detail
        assert governance.routes.sessions.detail is not None

    def test_sessions_relations_importable(self):
        import governance.routes.sessions.relations
        assert governance.routes.sessions.relations is not None
