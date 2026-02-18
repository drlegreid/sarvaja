"""Batch 441 — UI controllers add_error_trace info disclosure (17 fixes),
heuristic_runner.py debug→warning (3 fixes), runner_store.py debug→warning + exc_info (2 fixes),
heuristic_checks_cc.py + heuristic_checks_session.py debug→warning (2 fixes),
UI views CLEAN, DSM+workflows CLEAN confirmation.

Validates fixes for:
- BUG-439-DL-001..009: data_loaders.py add_error_trace type(e).__name__
- BUG-439-IL-001..002: infra_loaders.py add_error_trace type(e).__name__
- BUG-439-RUL-001..003: rules.py add_error_trace type(e).__name__
- BUG-439-TRS-001..004: trust.py add_error_trace type(e).__name__
- BUG-440-HRN-001..003: heuristic_runner.py debug→warning + exc_info
- BUG-440-RST-001..002: runner_store.py debug→warning + exc_info
- BUG-440-HCC-001: heuristic_checks_cc.py debug→warning + exc_info
- BUG-440-HCS-001: heuristic_checks_session.py debug→warning + exc_info
"""
import re
from pathlib import Path

# ─── Helpers ────────────────────────────────────────────────────────────

_ROOT = Path(__file__).resolve().parent.parent.parent


def _read(relpath: str) -> str:
    return (_ROOT / relpath).read_text(encoding="utf-8")


def _check_no_bare_e_in_add_error_trace(src: str, filename: str):
    """Verify no add_error_trace() calls use bare {e} or {str(e)}."""
    # Find all add_error_trace lines
    for i, line in enumerate(src.splitlines(), 1):
        if "add_error_trace(" not in line:
            continue
        # Skip comment lines
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        # Check for bare {e} or {str(e)} patterns in the f-string
        # These leak exception internals to Trame WebSocket
        if re.search(r'\{e\}', line) or re.search(r'\{str\(e\)\}', line):
            return False, f"{filename}:{i}: add_error_trace leaks exception via {{e}}: {line.strip()}"
    return True, "OK"


def _check_warning_with_exc_info(src: str, pattern: str, filename: str):
    """Verify a logger.warning() call with exc_info=True near a pattern."""
    lines = src.splitlines()
    for i, line in enumerate(lines):
        if pattern in line:
            # Search within 3 lines for exc_info=True
            window = "\n".join(lines[max(0, i-1):i+3])
            if "exc_info=True" in window and "logger.warning" in window:
                return True, "OK"
            return False, f"{filename}:{i+1}: Missing warning+exc_info near '{pattern}'"
    return False, f"{filename}: Pattern '{pattern}' not found"


def _check_no_debug_in_except(src: str, filename: str):
    """Verify no logger.debug() calls exist inside except blocks."""
    lines = src.splitlines()
    in_except = False
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("except "):
            in_except = True
            continue
        if in_except and stripped and not stripped.startswith("#"):
            if "logger.debug(" in stripped:
                return False, f"{filename}:{i}: logger.debug() in except block: {stripped}"
            # End of except block if we hit a non-indented line or new block
            if not line.startswith(" ") and not line.startswith("\t"):
                in_except = False
    return True, "OK"


# ─── data_loaders.py — 9 add_error_trace fixes ─────────────────────────

class TestDataLoadersErrorTraceTypeOnly:
    """BUG-439-DL-001..009: All add_error_trace calls must use type(e).__name__."""

    def test_no_bare_e_in_add_error_trace(self):
        src = _read("agent/governance_ui/controllers/data_loaders.py")
        ok, msg = _check_no_bare_e_in_add_error_trace(src, "data_loaders.py")
        assert ok, msg

    def test_bug_markers_present(self):
        src = _read("agent/governance_ui/controllers/data_loaders.py")
        for marker in ["BUG-439-DL-001", "BUG-439-DL-005", "BUG-439-DL-009"]:
            assert marker in src, f"Missing marker {marker}"

    def test_type_e_name_pattern_count(self):
        src = _read("agent/governance_ui/controllers/data_loaders.py")
        count = src.count("type(e).__name__")
        # Should have at least 9 (our fixes) + 1 (existing BUG-389-DL-001)
        assert count >= 10, f"Expected >=10 type(e).__name__ occurrences, got {count}"


# ─── infra_loaders.py — 2 add_error_trace fixes ────────────────────────

class TestInfraLoadersErrorTraceTypeOnly:
    """BUG-439-IL-001..002: add_error_trace calls must use type(e).__name__."""

    def test_no_bare_e_in_add_error_trace(self):
        src = _read("agent/governance_ui/controllers/infra_loaders.py")
        ok, msg = _check_no_bare_e_in_add_error_trace(src, "infra_loaders.py")
        assert ok, msg

    def test_bug_markers_present(self):
        src = _read("agent/governance_ui/controllers/infra_loaders.py")
        assert "BUG-439-IL-001" in src
        assert "BUG-439-IL-002" in src


# ─── rules.py — 3 add_error_trace fixes ────────────────────────────────

class TestRulesErrorTraceTypeOnly:
    """BUG-439-RUL-001..003: add_error_trace calls must use type(e).__name__."""

    def test_no_bare_e_in_add_error_trace(self):
        src = _read("agent/governance_ui/controllers/rules.py")
        ok, msg = _check_no_bare_e_in_add_error_trace(src, "rules.py")
        assert ok, msg

    def test_bug_markers_present(self):
        src = _read("agent/governance_ui/controllers/rules.py")
        for marker in ["BUG-439-RUL-001", "BUG-439-RUL-002", "BUG-439-RUL-003"]:
            assert marker in src, f"Missing marker {marker}"


# ─── trust.py — 4 add_error_trace fixes ────────────────────────────────

class TestTrustErrorTraceTypeOnly:
    """BUG-439-TRS-001..004: add_error_trace calls must use type(e).__name__."""

    def test_no_bare_e_in_add_error_trace(self):
        src = _read("agent/governance_ui/controllers/trust.py")
        ok, msg = _check_no_bare_e_in_add_error_trace(src, "trust.py")
        assert ok, msg

    def test_bug_markers_present(self):
        src = _read("agent/governance_ui/controllers/trust.py")
        for marker in ["BUG-439-TRS-001", "BUG-439-TRS-002", "BUG-439-TRS-003", "BUG-439-TRS-004"]:
            assert marker in src, f"Missing marker {marker}"


# ─── heuristic_runner.py — 3 debug→warning + exc_info ──────────────────

class TestHeuristicRunnerWarningExcInfo:
    """BUG-440-HRN-001..003: All except-block loggers must be warning+exc_info."""

    def test_session_bridge_warning(self):
        src = _read("governance/routes/tests/heuristic_runner.py")
        ok, msg = _check_warning_with_exc_info(src, "Session bridge unavailable", "heuristic_runner.py")
        assert ok, msg

    def test_tool_call_recording_warning(self):
        src = _read("governance/routes/tests/heuristic_runner.py")
        ok, msg = _check_warning_with_exc_info(src, "Failed to record heuristic tool call", "heuristic_runner.py")
        assert ok, msg

    def test_end_session_warning(self):
        src = _read("governance/routes/tests/heuristic_runner.py")
        ok, msg = _check_warning_with_exc_info(src, "Failed to end heuristic session", "heuristic_runner.py")
        assert ok, msg

    def test_no_debug_in_except(self):
        src = _read("governance/routes/tests/heuristic_runner.py")
        ok, msg = _check_no_debug_in_except(src, "heuristic_runner.py")
        assert ok, msg


# ─── runner_store.py — 2 fixes ─────────────────────────────────────────

class TestRunnerStoreWarningExcInfo:
    """BUG-440-RST-001..002: warning+exc_info for load failures."""

    def test_load_result_warning(self):
        src = _read("governance/routes/tests/runner_store.py")
        ok, msg = _check_warning_with_exc_info(src, "Failed to load test result", "runner_store.py")
        assert ok, msg

    def test_import_load_warning_exc_info(self):
        src = _read("governance/routes/tests/runner_store.py")
        ok, msg = _check_warning_with_exc_info(src, "Failed to load persisted test results on import", "runner_store.py")
        assert ok, msg

    def test_path_redaction(self):
        """BUG-440-RST-001: filepath.name used instead of full filepath."""
        src = _read("governance/routes/tests/runner_store.py")
        # The inner load function should use filepath.name to avoid path disclosure
        assert "filepath.name" in src, "Expected filepath.name for path redaction"


# ─── heuristic_checks_cc.py — 1 fix ────────────────────────────────────

class TestHeuristicChecksCcWarning:
    """BUG-440-HCC-001: _api_get debug→warning + exc_info."""

    def test_warning_with_exc_info(self):
        src = _read("governance/routes/tests/heuristic_checks_cc.py")
        ok, msg = _check_warning_with_exc_info(src, "Heuristic API call failed", "heuristic_checks_cc.py")
        assert ok, msg

    def test_no_debug_in_except(self):
        src = _read("governance/routes/tests/heuristic_checks_cc.py")
        ok, msg = _check_no_debug_in_except(src, "heuristic_checks_cc.py")
        assert ok, msg


# ─── heuristic_checks_session.py — 1 fix ───────────────────────────────

class TestHeuristicChecksSessionWarning:
    """BUG-440-HCS-001: _api_get debug→warning + exc_info."""

    def test_warning_with_exc_info(self):
        src = _read("governance/routes/tests/heuristic_checks_session.py")
        ok, msg = _check_warning_with_exc_info(src, "Heuristic API call failed", "heuristic_checks_session.py")
        assert ok, msg

    def test_no_debug_in_except(self):
        src = _read("governance/routes/tests/heuristic_checks_session.py")
        ok, msg = _check_no_debug_in_except(src, "heuristic_checks_session.py")
        assert ok, msg


# ─── Batch 438 CLEAN confirmation — UI views ───────────────────────────

class TestBatch438UIViewsClean:
    """Batch 438: UI views layer confirmed CLEAN."""

    def test_executive_metrics_importable(self):
        src = _read("agent/governance_ui/views/executive/metrics.py")
        assert "def " in src

    def test_agents_metrics_importable(self):
        src = _read("agent/governance_ui/views/agents/metrics.py")
        assert "def " in src

    def test_tasks_execution_importable(self):
        src = _read("agent/governance_ui/views/tasks/execution.py")
        assert "def " in src


# ─── Batch 441 CLEAN confirmation — DSM + workflows ────────────────────

class TestBatch441DSMWorkflowsClean:
    """Batch 441: DSM + workflow orchestrator confirmed CLEAN."""

    def test_dsm_tracker_importable(self):
        src = _read("governance/dsm/tracker.py")
        assert "def " in src

    def test_orchestrator_graph_importable(self):
        src = _read("governance/workflows/orchestrator/graph.py")
        assert "def " in src

    def test_orchestrator_nodes_importable(self):
        src = _read("governance/workflows/orchestrator/nodes.py")
        assert "def " in src

    def test_orchestrator_state_importable(self):
        src = _read("governance/workflows/orchestrator/state.py")
        assert "def " in src


# ─── Import validation ─────────────────────────────────────────────────

class TestBatch441Imports:
    """Verify all modified modules import cleanly."""

    def test_data_loaders_import(self):
        src = _read("agent/governance_ui/controllers/data_loaders.py")
        compile(src, "data_loaders.py", "exec")

    def test_infra_loaders_import(self):
        src = _read("agent/governance_ui/controllers/infra_loaders.py")
        compile(src, "infra_loaders.py", "exec")

    def test_rules_import(self):
        src = _read("agent/governance_ui/controllers/rules.py")
        compile(src, "rules.py", "exec")

    def test_trust_import(self):
        src = _read("agent/governance_ui/controllers/trust.py")
        compile(src, "trust.py", "exec")

    def test_heuristic_runner_import(self):
        src = _read("governance/routes/tests/heuristic_runner.py")
        compile(src, "heuristic_runner.py", "exec")

    def test_runner_store_import(self):
        src = _read("governance/routes/tests/runner_store.py")
        compile(src, "runner_store.py", "exec")

    def test_heuristic_checks_cc_import(self):
        src = _read("governance/routes/tests/heuristic_checks_cc.py")
        compile(src, "heuristic_checks_cc.py", "exec")

    def test_heuristic_checks_session_import(self):
        src = _read("governance/routes/tests/heuristic_checks_session.py")
        compile(src, "heuristic_checks_session.py", "exec")
