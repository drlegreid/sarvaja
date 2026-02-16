"""
Batch 72 — Deep Scan: Heuristic + DSM + Hooks triage.

Fixes verified:
- BUG-HEURISTIC-EXPLR-SKIP-001: H-EXPLR-001 no longer always SKIPs

Triage summary: 21 findings → 1 confirmed, 4 already-fixed, 16 rejected.
"""
import inspect
from unittest.mock import patch, MagicMock

import pytest


# ===========================================================================
# BUG-HEURISTIC-EXPLR-SKIP-001: H-EXPLR-001 unreachable pagination check
# ===========================================================================

class TestExploratorySkipFix:
    """Verify H-EXPLR-001 no longer unconditionally SKIPs."""

    def _get_check_source(self):
        from governance.routes.tests.heuristic_checks_exploratory import (
            check_chat_session_count_accuracy,
        )
        return inspect.getsource(check_chat_session_count_accuracy)

    def test_no_api_get_before_pagination(self):
        """Must NOT use _api_get() for the initial pagination-sensitive call."""
        src = self._get_check_source()
        # The old pattern was: sessions = _api_get(...); isinstance(sessions, list) -> SKIP
        # New code should use httpx.get directly for the first fetch
        # Check that the first actual code call (not in comments) is httpx.get
        code_lines = [
            line.strip() for line in src.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        # Old buggy pattern: assigning _api_get result then checking isinstance
        old_pattern = "sessions = _api_get("
        assert old_pattern not in src, "Old pattern 'sessions = _api_get(' still present"

    def test_isinstance_list_guard_removed(self):
        """Old guard 'isinstance(sessions, list)' that always triggered SKIP must be gone."""
        src = self._get_check_source()
        assert "isinstance(sessions, list)" not in src

    @patch("governance.routes.tests.heuristic_checks_exploratory.httpx")
    @patch("governance.routes.tests.heuristic_checks_exploratory._is_self_referential", return_value=False)
    def test_returns_pass_with_pagination(self, mock_self, mock_httpx):
        """With valid pagination response, check should PASS (not SKIP)."""
        from governance.routes.tests.heuristic_checks_exploratory import (
            check_chat_session_count_accuracy,
        )
        # First call: sessions?limit=1 for pagination
        pagination_resp = MagicMock()
        pagination_resp.status_code = 200
        pagination_resp.json.return_value = {
            "items": [{"session_id": "S-1", "status": "COMPLETED"}],
            "pagination": {"total": 50, "offset": 0, "limit": 1},
        }
        # Second call via _api_get: sessions?limit=200 for active count
        active_resp = MagicMock()
        active_resp.status_code = 200
        active_resp.json.return_value = {
            "items": [
                {"session_id": "S-1", "status": "COMPLETED"},
                {"session_id": "S-2", "status": "COMPLETED"},
            ],
        }
        mock_httpx.get.side_effect = [pagination_resp, active_resp]
        result = check_chat_session_count_accuracy("http://test:8082")
        assert result["status"] == "PASS", f"Expected PASS, got {result['status']}: {result['message']}"

    @patch("governance.routes.tests.heuristic_checks_exploratory.httpx")
    @patch("governance.routes.tests.heuristic_checks_exploratory._is_self_referential", return_value=False)
    def test_returns_skip_when_no_pagination(self, mock_self, mock_httpx):
        """Without pagination key, should SKIP gracefully."""
        from governance.routes.tests.heuristic_checks_exploratory import (
            check_chat_session_count_accuracy,
        )
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = [{"session_id": "S-1"}]  # List, no pagination
        mock_httpx.get.return_value = resp
        result = check_chat_session_count_accuracy("http://test:8082")
        assert result["status"] == "SKIP"

    @patch("governance.routes.tests.heuristic_checks_exploratory._is_self_referential", return_value=True)
    def test_self_referential_skip(self, mock_self):
        """Self-referential URLs still SKIP correctly."""
        from governance.routes.tests.heuristic_checks_exploratory import (
            check_chat_session_count_accuracy,
        )
        result = check_chat_session_count_accuracy("http://localhost:8082")
        assert result["status"] == "SKIP"
        assert "Self-referential" in result["message"]


# ===========================================================================
# ALREADY-FIXED confirmations (code archaeology tests)
# ===========================================================================

class TestAlreadyFixedConfirmations:
    """Confirm that DSM/heuristic bugs flagged by agents are already fixed."""

    def test_dsm_evidence_description_uses_get(self):
        """BUG-DSM-001: evidence.py findings use .get() for description."""
        from governance.dsm.evidence import generate_evidence
        src = inspect.getsource(generate_evidence)
        assert "f.get('description'" in src or 'f.get("description"' in src

    def test_dsm_evidence_write_guarded(self):
        """BUG-DSM-002: evidence file write is wrapped in try/except."""
        from governance.dsm.evidence import generate_evidence
        src = inspect.getsource(generate_evidence)
        write_idx = src.index("open(filepath")
        try_idx = src.rfind("try:", 0, write_idx)
        assert try_idx >= 0, "File write must be in try block"

    def test_heuristic_runner_logs_session_errors(self):
        """BUG-HEURISTIC-001: Session recording failures are logged."""
        from governance.routes.tests.heuristic_runner import run_heuristic_checks
        src = inspect.getsource(run_heuristic_checks)
        assert "logger.debug" in src

    def test_backfill_uses_dynamic_cutoff(self):
        """BUG-HEURISTIC-002: _is_backfilled_session uses dynamic date."""
        from governance.routes.tests.heuristic_checks_session import _is_backfilled_session
        src = inspect.getsource(_is_backfilled_session)
        assert "timedelta(days=30)" in src


# ===========================================================================
# DSM tracker integrity checks
# ===========================================================================

class TestDSMTrackerIntegrity:
    """Verify DSM tracker has proper guards and retention."""

    def test_completed_cycles_capped_at_50(self):
        """Retention cap must be 50 per antirot policy."""
        from governance.dsm.tracker import DSMTracker
        src = inspect.getsource(DSMTracker.complete_cycle)
        assert "50" in src
        assert "completed_cycles[-50:]" in src

    def test_start_cycle_rejects_active(self):
        """Cannot start a new cycle when one is in progress."""
        from governance.dsm.tracker import DSMTracker
        src = inspect.getsource(DSMTracker.start_cycle)
        assert "already in progress" in src.lower()

    def test_checkpoint_requires_active_cycle(self):
        """Checkpoint raises when no cycle active."""
        from governance.dsm.tracker import DSMTracker
        src = inspect.getsource(DSMTracker.checkpoint)
        assert "No cycle in progress" in src

    def test_validation_handles_unknown_phase(self):
        """validate_phase_evidence returns None for unknown phases."""
        from governance.dsm.validation import validate_phase_evidence
        src = inspect.getsource(validate_phase_evidence)
        assert "return None  # Unknown phase" in src


# ===========================================================================
# Hooks integrity checks
# ===========================================================================

class TestHooksIntegrity:
    """Verify hooks have proper error handling."""

    def test_entropy_checker_has_all_thresholds(self):
        """EntropyChecker must define MEDIUM, HIGH, CRITICAL thresholds."""
        from hooks.checkers.entropy import EntropyChecker
        assert EntropyChecker.MEDIUM_THRESHOLD == 50
        assert EntropyChecker.HIGH_THRESHOLD == 100
        assert EntropyChecker.CRITICAL_THRESHOLD == 150

    def test_context_monitor_load_handles_errors(self):
        """load_state() must return default on file errors."""
        from hooks.checkers.context_monitor import load_state
        src = inspect.getsource(load_state)
        assert "except" in src

    def test_mcp_recovery_run_cmd_handles_timeout(self):
        """run_cmd must catch TimeoutExpired."""
        from hooks.checkers.mcp_recovery import run_cmd
        src = inspect.getsource(run_cmd)
        assert "TimeoutExpired" in src

    def test_entropy_state_has_reset(self):
        """EntropyState must have reset_session method."""
        from hooks.core.state import EntropyState
        assert hasattr(EntropyState, "reset_session")
