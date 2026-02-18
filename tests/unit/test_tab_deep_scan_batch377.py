"""
Deep Scan Batch 377 — Defense Tests
====================================
Verifies BUG-377-TDB-001 through BUG-377-HRN-001 and BUG-375-STS-001.

Batch 374-377 findings:
- BUG-377-TDB-001: TypeDBUnavailable sanitized in typedb_access.py (4 fixes)
- BUG-377-DEC-001: HTTPException detail sanitized in decisions.py (8 fixes)
- BUG-377-NOD-001: error_message sanitized in nodes_execution.py (8 fixes)
- BUG-377-RNR-001: Error dicts sanitized in runner_exec.py (5 fixes)
- BUG-377-HRN-001: Error message sanitized in heuristic_runner.py (1 fix)
- BUG-375-STS-001: Pinned auto-reset resolution delete in status.py (1 fix)

Total: 27 production fixes, verified by source introspection tests.
"""

import importlib
import inspect
import re
import textwrap

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_source(module_path: str) -> str:
    """Get source code of a module by dotted path."""
    mod = importlib.import_module(module_path)
    return inspect.getsource(mod)


def _count_raw_str_e(source: str) -> int:
    """Count instances where raw str(e) leaks into return values (not logger)."""
    count = 0
    for line in source.splitlines():
        stripped = line.strip()
        # Skip logger lines — those are server-side only
        if "logger." in stripped:
            continue
        if stripped.startswith("#"):
            continue
        # Check error return patterns
        if any(kw in stripped for kw in [
            "format_mcp_result", "HTTPException", '"error"',
            "error_message", "_create_phase_result",
        ]):
            if "str(e)" in stripped or re.search(r'\{e\}', stripped):
                if "type(e).__name__" not in stripped:
                    count += 1
    return count


# ===========================================================================
# BUG-377-TDB-001: typedb_access.py — TypeDBUnavailable sanitized
# ===========================================================================

class TestTypedbAccessSanitization:
    """Verify TypeDBUnavailable no longer forwards raw str(e)."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        self.source = _get_source("governance.stores.typedb_access")

    def test_bug_marker_present(self):
        assert "BUG-377-TDB-001" in self.source

    def test_no_raw_str_e_in_typedb_unavailable(self):
        """TypeDBUnavailable raise sites should use type(e).__name__."""
        for line in self.source.splitlines():
            stripped = line.strip()
            if "raise TypeDBUnavailable" in stripped:
                if "str(e)" in stripped or re.search(r'\{e\}', stripped):
                    if "type(e).__name__" not in stripped:
                        pytest.fail(f"Raw str(e) in TypeDBUnavailable: {stripped}")

    def test_type_name_pattern_count(self):
        """All 4 TypeDBUnavailable raises should use type(e).__name__."""
        count = self.source.count("TypeDBUnavailable(f\"TypeDB unavailable: {type(e).__name__}\")")
        assert count == 4, f"Expected 4 sanitized raises, found {count}"


# ===========================================================================
# BUG-377-DEC-001: decisions.py — HTTPException sanitized
# ===========================================================================

class TestDecisionsSanitization:
    """Verify decisions.py HTTPException details no longer leak str(e)."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        self.source = _get_source("governance.routes.rules.decisions")

    def test_bug_marker_present(self):
        assert "BUG-377-DEC-001" in self.source

    def test_no_raw_str_e_in_http_exception(self):
        """HTTPException detail should not use str(e)."""
        for line in self.source.splitlines():
            stripped = line.strip()
            if "HTTPException" in stripped and "detail=" in stripped:
                if "str(e)" in stripped:
                    pytest.fail(f"Raw str(e) in HTTPException: {stripped}")

    def test_500_handlers_use_type_name(self):
        """All 500 status handlers should use type(e).__name__."""
        count_500_sanitized = 0
        for line in self.source.splitlines():
            stripped = line.strip()
            if "status_code=500" in stripped and "type(e).__name__" in stripped:
                count_500_sanitized += 1
        assert count_500_sanitized >= 5, f"Expected >=5 sanitized 500 handlers, found {count_500_sanitized}"

    def test_exc_info_logging(self):
        """Error paths should log with exc_info=True."""
        count = self.source.count("exc_info=True")
        assert count >= 5, f"Expected >=5 exc_info=True, found {count}"


# ===========================================================================
# BUG-377-NOD-001: nodes_execution.py — error_message sanitized
# ===========================================================================

class TestNodesExecutionSanitization:
    """Verify DSP nodes no longer expose raw str(e) in state."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        self.source = _get_source("governance.dsm.langgraph.nodes_execution")

    def test_bug_marker_present(self):
        assert "BUG-377-NOD-001" in self.source

    def test_no_raw_str_e_in_error_message(self):
        """error_message fields should use type(e).__name__."""
        for line in self.source.splitlines():
            stripped = line.strip()
            if "error_message" in stripped:
                if "str(e)" in stripped:
                    pytest.fail(f"Raw str(e) in error_message: {stripped}")

    def test_no_raw_str_e_in_phase_result(self):
        """_create_phase_result error arg should use type(e).__name__."""
        for line in self.source.splitlines():
            stripped = line.strip()
            if "_create_phase_result" in stripped and "failed" in stripped:
                if "str(e)" in stripped:
                    pytest.fail(f"Raw str(e) in _create_phase_result: {stripped}")

    def test_exc_info_added_to_all_error_paths(self):
        """All 4 error logger.error calls should have exc_info=True."""
        error_lines = [
            l for l in self.source.splitlines()
            if "logger.error" in l and "phase failed" in l
        ]
        for line in error_lines:
            assert "exc_info=True" in line, f"Missing exc_info=True: {line.strip()}"

    def test_four_nodes_sanitized(self):
        """All 4 node error handlers should use type(e).__name__."""
        count = self.source.count("type(e).__name__")
        # 4 error_message + 4 _create_phase_result = 8
        assert count >= 8, f"Expected >=8 type(e).__name__, found {count}"


# ===========================================================================
# BUG-377-RNR-001: runner_exec.py — error dicts sanitized
# ===========================================================================

class TestRunnerExecSanitization:
    """Verify runner_exec.py error results no longer leak str(e)."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        self.source = _get_source("governance.routes.tests.runner_exec")

    def test_bug_marker_present(self):
        assert "BUG-377-RNR-001" in self.source

    def test_no_raw_str_e_in_error_dicts(self):
        """Error result dicts should not contain str(e)."""
        raw_count = _count_raw_str_e(self.source)
        assert raw_count == 0, f"Found {raw_count} raw str(e) leaks in runner_exec.py"

    def test_parse_robot_xml_sanitized(self):
        """parse_robot_xml error should use type(e).__name__."""
        for line in self.source.splitlines():
            if "Error parsing output.xml" in line:
                assert "type(e).__name__" in line, f"Unsanitized parse_robot_xml error: {line.strip()}"
                break
        else:
            pytest.fail("parse_robot_xml error handler not found")

    def test_remediate_violations_sanitized(self):
        """Remediation error details should use type(e).__name__."""
        for line in self.source.splitlines():
            if '"action": "failed"' in line or "'action': 'failed'" in line:
                if "str(e)" in line:
                    pytest.fail(f"Raw str(e) in remediation error: {line.strip()}")


# ===========================================================================
# BUG-377-HRN-001: heuristic_runner.py — error message sanitized
# ===========================================================================

class TestHeuristicRunnerSanitization:
    """Verify heuristic_runner.py no longer leaks raw errors."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        self.source = _get_source("governance.routes.tests.heuristic_runner")

    def test_bug_marker_present(self):
        assert "BUG-377-HRN-001" in self.source

    def test_no_raw_str_e_in_results(self):
        """Check result dicts don't leak raw str(e)."""
        raw_count = _count_raw_str_e(self.source)
        assert raw_count == 0, f"Found {raw_count} raw str(e) leaks in heuristic_runner.py"

    def test_error_message_uses_type_name(self):
        """Error message in check results should use type(e).__name__."""
        for line in self.source.splitlines():
            if '"message"' in line and "Check failed" in line:
                assert "type(e).__name__" in line
                break
        else:
            pytest.fail("Sanitized error message pattern not found")


# ===========================================================================
# BUG-375-STS-001: tasks/status.py — pinned auto-reset resolution delete
# ===========================================================================

class TestStatusPinnedDelete:
    """Verify auto-reset resolution delete now pins the value."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        self.source = _get_source("governance.typedb.queries.tasks.status")

    def test_bug_marker_present(self):
        assert "BUG-375-STS-001" in self.source

    def test_auto_reset_delete_is_pinned(self):
        """The auto-reset resolution delete should pin value with $r == ..."""
        # Find the auto-reset block
        in_auto_reset = False
        found_pinned = False
        for line in self.source.splitlines():
            if "Auto-reset resolution to NONE" in line:
                in_auto_reset = True
            if in_auto_reset and 'current_res_reset_escaped' in line:
                found_pinned = True
                break
        assert found_pinned, "Auto-reset resolution delete should use pinned value"

    def test_no_unpinned_resolution_delete(self):
        """No resolution delete should lack a value pin ($r == ...)."""
        lines = self.source.splitlines()
        for i, line in enumerate(lines):
            stripped = line.strip()
            if "has task-resolution $r;" in stripped and "delete" in "".join(
                l.strip() for l in lines[max(0, i-3):i+5]
            ):
                # Check that a pin ($r ==) appears in the nearby lines
                context = "\n".join(lines[max(0, i-2):i+5])
                if '$r ==' not in context:
                    pytest.fail(f"Unpinned resolution delete near line {i+1}")


# ===========================================================================
# Import Verification
# ===========================================================================

class TestBatch377Imports:
    """Verify all modified modules import cleanly."""

    @pytest.mark.parametrize("module_path", [
        "governance.stores.typedb_access",
        "governance.stores.data_stores",
        "governance.routes.rules.decisions",
        "governance.dsm.langgraph.nodes_execution",
        "governance.routes.tests.runner_exec",
        "governance.routes.tests.heuristic_runner",
        "governance.routes.tests.runner_store",
        "governance.typedb.queries.tasks.status",
    ])
    def test_module_imports(self, module_path):
        mod = importlib.import_module(module_path)
        assert mod is not None
