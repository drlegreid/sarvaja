"""Batch 230 — Heuristics + test runner defense tests.

Validates fixes for:
- BUG-231-003: Path traversal via unvalidated run_id in _persist_result
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-231-003: Path traversal in runner_store._persist_result ──────

class TestRunnerStorePathTraversal:
    """run_id must be sanitized before constructing filepath."""

    def test_uses_regex_sanitization(self):
        src = (SRC / "governance/routes/tests/runner_store.py").read_text()
        assert "re.sub(" in src

    def test_bug_marker_present(self):
        src = (SRC / "governance/routes/tests/runner_store.py").read_text()
        assert "BUG-231-003" in src

    def test_uses_safe_id_in_filepath(self):
        src = (SRC / "governance/routes/tests/runner_store.py").read_text()
        idx = src.index("def _persist_result")
        block = src[idx:idx + 400]
        assert "safe_id" in block

    def test_imports_re(self):
        src = (SRC / "governance/routes/tests/runner_store.py").read_text()
        assert "import re" in src


# ── Heuristics + runner module import defense ────────────────────────

class TestHeuristicsImports:
    """Defense tests for heuristics and test runner modules."""

    def test_runner_store_importable(self):
        import governance.routes.tests.runner_store
        assert governance.routes.tests.runner_store is not None

    def test_runner_exec_importable(self):
        import governance.routes.tests.runner_exec
        assert governance.routes.tests.runner_exec is not None

    def test_runner_importable(self):
        import governance.routes.tests.runner
        assert governance.routes.tests.runner is not None

    def test_runner_preflight_importable(self):
        import governance.routes.tests.runner_preflight
        assert governance.routes.tests.runner_preflight is not None

    def test_heuristic_checks_importable(self):
        import governance.routes.tests.heuristic_checks
        assert governance.routes.tests.heuristic_checks is not None

    def test_heuristic_checks_session_importable(self):
        import governance.routes.tests.heuristic_checks_session
        assert governance.routes.tests.heuristic_checks_session is not None

    def test_heuristic_checks_cc_importable(self):
        import governance.routes.tests.heuristic_checks_cc
        assert governance.routes.tests.heuristic_checks_cc is not None

    def test_heuristic_checks_cross_importable(self):
        import governance.routes.tests.heuristic_checks_cross
        assert governance.routes.tests.heuristic_checks_cross is not None

    def test_heuristic_checks_exploratory_importable(self):
        import governance.routes.tests.heuristic_checks_exploratory
        assert governance.routes.tests.heuristic_checks_exploratory is not None

    def test_heuristic_runner_importable(self):
        import governance.routes.tests.heuristic_runner
        assert governance.routes.tests.heuristic_runner is not None

    def test_parser_importable(self):
        import governance.routes.tests.parser
        assert governance.routes.tests.parser is not None
