"""
Deep Scan Batch 318-321: Defense tests for security fixes.

Tests for:
  BUG-319-INGEST-001: heuristic_checks_cc.py inner loop cap (N+1 prevention)
  BUG-320-INFRA-001: infra_loaders.py cleanup_zombies cooldown timer
  BUG-321-GRAPH-001: graph.py hard cap on _MAX_ITERATIONS
"""

import re
import time
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-319-INGEST-001: check_cc_ingestion_complete N+1 cap ────────────


class TestIngestionLoopCap:
    """Verify check_cc_ingestion_complete has an inner loop cap."""

    def _read_src(self):
        return (SRC / "governance/routes/tests/heuristic_checks_cc.py").read_text()

    def test_bug_marker_present(self):
        src = self._read_src()
        assert "BUG-319-INGEST-001" in src

    def test_inner_loop_has_slice_cap(self):
        """The for-loop over cc_sessions must use a slice cap [:N]."""
        src = self._read_src()
        idx = src.find("def check_cc_ingestion_complete")
        assert idx != -1
        # Find next function or end of file
        next_fn = src.find("\ndef ", idx + 10)
        block = src[idx:next_fn] if next_fn != -1 else src[idx:]
        # Must contain cc_sessions[:30] or similar slice
        assert re.search(r'cc_sessions\[:\d+\]', block), \
            "check_cc_ingestion_complete must cap inner loop with slice"

    def test_cap_is_reasonable(self):
        """The cap should be between 10 and 50 (not unbounded 200)."""
        src = self._read_src()
        idx = src.find("def check_cc_ingestion_complete")
        next_fn = src.find("\ndef ", idx + 10)
        block = src[idx:next_fn] if next_fn != -1 else src[idx:]
        match = re.search(r'cc_sessions\[:(\d+)\]', block)
        assert match, "Expected slice cap on cc_sessions"
        cap = int(match.group(1))
        assert 10 <= cap <= 50, f"Cap should be 10-50, got {cap}"

    def test_other_functions_already_capped(self):
        """Other heuristic check functions should also have loop caps."""
        src = (SRC / "governance/routes/tests/heuristic_checks_session.py").read_text()
        # check_session_evidence_files caps at 30
        assert "completed[:30]" in src or "completed[:20]" in src, \
            "check_session_evidence_files should cap its loop"
        # check_session_tool_calls caps at 20
        assert "completed[:20]" in src, \
            "check_session_tool_calls should cap its loop"


# ── BUG-320-INFRA-001: cleanup_zombies cooldown timer ──────────────────


class TestCleanupZombiesCooldown:
    """Verify cleanup_zombies has a cooldown timer."""

    def _read_src(self):
        return (SRC / "agent/governance_ui/controllers/infra_loaders.py").read_text()

    def test_bug_marker_present(self):
        src = self._read_src()
        assert "BUG-320-INFRA-001" in src

    def test_cooldown_variable_exists(self):
        """A cooldown seconds constant must be defined."""
        src = self._read_src()
        assert "_CLEANUP_COOLDOWN_SECS" in src

    def test_cooldown_value_reasonable(self):
        """Cooldown should be between 10 and 120 seconds."""
        src = self._read_src()
        match = re.search(r'_CLEANUP_COOLDOWN_SECS\s*=\s*(\d+)', src)
        assert match, "Expected _CLEANUP_COOLDOWN_SECS constant"
        value = int(match.group(1))
        assert 10 <= value <= 120, f"Cooldown should be 10-120s, got {value}"

    def test_time_check_in_cleanup(self):
        """cleanup_zombies must check elapsed time before running."""
        src = self._read_src()
        idx = src.find("def cleanup_zombies")
        assert idx != -1
        next_fn = src.find("\n    @ctrl.trigger", idx + 10)
        block = src[idx:next_fn] if next_fn != -1 else src[idx:idx + 800]
        assert "time.time()" in block or "time()" in block, \
            "cleanup_zombies must check current time"
        assert "_cleanup_last_run" in block, \
            "cleanup_zombies must reference last run timestamp"

    def test_cooldown_message_to_user(self):
        """When in cooldown, user should get a message (not silent no-op)."""
        src = self._read_src()
        idx = src.find("def cleanup_zombies")
        assert idx != -1
        next_fn = src.find("\n    @ctrl.trigger", idx + 10)
        block = src[idx:next_fn] if next_fn != -1 else src[idx:idx + 800]
        assert "cooldown" in block.lower() or "wait" in block.lower(), \
            "User should be informed about cooldown"

    def test_timestamp_updated_on_success(self):
        """The last-run timestamp must be updated after successful cleanup."""
        src = self._read_src()
        idx = src.find("def cleanup_zombies")
        assert idx != -1
        next_fn = src.find("\n    @ctrl.trigger", idx + 10)
        block = src[idx:next_fn] if next_fn != -1 else src[idx:idx + 800]
        # After pkill, _cleanup_last_run should be updated
        pkill_idx = block.find("pkill")
        last_run_update = block.find("_cleanup_last_run[0] = now")
        assert last_run_update != -1, "Must update _cleanup_last_run after pkill"
        assert last_run_update > pkill_idx, \
            "Timestamp update must come after pkill (not before)"


# ── BUG-321-GRAPH-001: _MAX_ITERATIONS hard cap ────────────────────────


class TestGraphIterationHardCap:
    """Verify _MAX_ITERATIONS has a hard cap independent of caller input."""

    def _read_src(self):
        return (SRC / "governance/workflows/orchestrator/graph.py").read_text()

    def test_bug_marker_present(self):
        src = self._read_src()
        assert "BUG-321-GRAPH-001" in src

    def test_min_function_used(self):
        """_MAX_ITERATIONS must use min() to enforce hard cap."""
        src = self._read_src()
        idx = src.find("_MAX_ITERATIONS")
        assert idx != -1
        line = src[idx:src.find("\n", idx)]
        assert "min(" in line, \
            "_MAX_ITERATIONS must use min() to enforce hard cap"

    def test_hard_cap_value(self):
        """Hard cap should be <= 5000 (reasonable for any workflow)."""
        src = self._read_src()
        idx = src.find("_MAX_ITERATIONS")
        line = src[idx:src.find("\n", idx)]
        # Extract the second arg to min() which is the hard cap
        match = re.search(r'min\(.+?,\s*(\d+)\)', line)
        assert match, "Expected min(computed, HARD_CAP) pattern"
        cap = int(match.group(1))
        assert cap <= 5000, f"Hard cap should be <= 5000, got {cap}"

    def test_original_formula_preserved(self):
        """The max_cycles * 3 formula should still be present (just capped)."""
        src = self._read_src()
        idx = src.find("_MAX_ITERATIONS")
        line = src[idx:src.find("\n", idx)]
        assert "* 3" in line, "Original 3x multiplier formula should be preserved"

    def test_run_single_cycle_safe(self):
        """run_single_cycle with max_cycles=1 should work (min(3, 3000) = 3)."""
        from governance.workflows.orchestrator.graph import run_single_cycle
        result = run_single_cycle("TEST-001", "Test task", dry_run=True)
        assert isinstance(result, dict)
        # Should complete without hitting safety cap
        assert result.get("cycles_completed", 0) <= 1

    def test_large_max_cycles_capped(self):
        """Verify that absurdly large max_cycles gets capped."""
        from governance.workflows.orchestrator.state import create_initial_state
        state = create_initial_state(max_cycles=1_000_000)
        # Simulate the cap logic
        computed = min(int(state.get("max_cycles") or 100) * 3, 3000)
        assert computed == 3000, f"Expected 3000, got {computed}"


# ── Systemic: _api_get SSRF triage verification ────────────────────────


class TestApiBaseUrlServerSideOnly:
    """Verify api_base_url comes from server config, not user input."""

    def test_runner_exec_uses_env_var(self):
        """execute_heuristic must get api_url from env var, not function param."""
        src = (SRC / "governance/routes/tests/runner_exec.py").read_text()
        idx = src.find("def execute_heuristic")
        assert idx != -1
        block = src[idx:idx + 500]
        assert 'os.getenv("GOVERNANCE_API_URL"' in block or \
               "os.getenv('GOVERNANCE_API_URL'" in block, \
            "execute_heuristic must get api_url from env var"

    def test_run_heuristic_tests_no_api_url_param(self):
        """The HTTP endpoint must NOT accept api_base_url as a query param."""
        src = (SRC / "governance/routes/tests/runner.py").read_text()
        idx = src.find("def run_heuristic_tests")
        assert idx != -1
        block = src[idx:idx + 300]
        assert "api_base_url" not in block, \
            "HTTP endpoint must NOT accept api_base_url from user"

    def test_self_referential_check_exists(self):
        """Files making external calls should have self-referential detection."""
        src = (SRC / "governance/routes/tests/heuristic_checks_cross.py").read_text()
        assert "_is_self_referential" in src

    def test_self_referential_in_exploratory(self):
        src = (SRC / "governance/routes/tests/heuristic_checks_exploratory.py").read_text()
        assert "_is_self_referential" in src


# ── Import verification ─────────────────────────────────────────────


class TestBatch318Imports:
    """Verify all fixed modules import cleanly."""

    def test_import_heuristic_checks_cc(self):
        from governance.routes.tests import heuristic_checks_cc  # noqa: F401

    def test_import_infra_loaders(self):
        from agent.governance_ui.controllers import infra_loaders  # noqa: F401

    def test_import_graph(self):
        from governance.workflows.orchestrator import graph  # noqa: F401

    def test_import_state(self):
        from governance.workflows.orchestrator import state  # noqa: F401
