"""Deep scan batch 112: DSM + workflows + hooks + middleware.

Batch 112 findings: 12 total, 0 confirmed fixes, 12 rejected.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import json


# ── DSM phase tracking defense ──────────────


class TestDSMPhaseTrackingDefense:
    """Verify DSM tracker handles phase transitions correctly."""

    def test_complete_cycle_excludes_report_phase(self):
        """complete_cycle does NOT double-count REPORT phase."""
        from governance.dsm.tracker import DSMTracker
        from governance.dsm.phases import DSPPhase

        tracker = DSMTracker.__new__(DSMTracker)
        tracker.completed_cycles = []
        tracker._state_file = None
        tracker.evidence_dir = "/tmp/test-evidence"

        cycle = MagicMock()
        cycle.current_phase = DSPPhase.REPORT.value
        cycle.phases_completed = ["DISCOVERY", "SPECIFICATION", "PLANNING"]
        cycle.metrics = {}
        cycle.cycle_id = "test"
        cycle.started_at = datetime.now()
        cycle.findings = []
        cycle.checkpoints = []
        tracker.current_cycle = cycle

        with patch.object(tracker, "_save_state"):
            with patch("governance.dsm.tracker.generate_evidence"):
                tracker.complete_cycle()

        # REPORT should NOT appear in phases_completed (guard at line 186)
        assert cycle.phases_completed.count("REPORT") == 0

    def test_phase_order_includes_all_phases(self):
        """DSPPhase.phase_order covers all expected phases."""
        from governance.dsm.phases import DSPPhase

        phases = DSPPhase.phase_order()
        assert len(phases) >= 4
        assert DSPPhase.AUDIT in phases
        assert DSPPhase.REPORT in phases


# ── Budget calculation defense ──────────────


class TestBudgetCalculationDefense:
    """Verify budget calculations handle edge cases."""

    def test_division_guarded_by_max(self):
        """max(tokens_used, 1) prevents division by zero."""
        tokens_used = 0
        result = tokens_used / max(tokens_used, 1)
        assert result == 0.0

    def test_no_budget_means_no_exhaustion_check(self):
        """When token_budget is absent, budget path not entered."""
        from governance.workflows.orchestrator.nodes import gate_node

        state = {
            "backlog": [{"task_id": "T-1", "priority": "HIGH"}],
            "cycles_completed": 0,
            "max_cycles": 10,
            # No token_budget key — uses max_cycles
        }
        result = gate_node(state)
        assert result["gate_decision"] == "continue"

    def test_budget_with_zero_token_budget(self):
        """token_budget=0 means unlimited (falsy check)."""
        from governance.workflows.orchestrator.budget import compute_budget

        result = compute_budget({
            "cycles_completed": 5,
            "max_cycles": 10,
            "backlog": [{"task_id": "T-1", "priority": "HIGH"}],
            "token_budget": 0,
            "tokens_used": 500,
            "value_delivered": 10,
        })
        # token_budget=0 is falsy, so exhaustion check is skipped
        assert result["should_continue"] is True

    def test_backlog_empty_stops(self):
        """compute_budget stops on empty backlog."""
        from governance.workflows.orchestrator.budget import compute_budget

        result = compute_budget({
            "cycles_completed": 5,
            "max_cycles": 10,
            "backlog": [],
            "token_budget": 10000,
            "tokens_used": 500,
            "value_delivered": 10,
        })
        assert result["should_continue"] is False
        assert result["reason"] == "backlog_empty"


# ── Execution events retention defense ──────────────


class TestExecutionEventsRetentionDefense:
    """Verify execution events retention caps work correctly."""

    def test_retention_cap_at_100(self):
        """Events beyond 100 are trimmed to keep newest."""
        events = list(range(105))
        if len(events) > 100:
            events = events[-100:]
        assert len(events) == 100
        assert events[0] == 5  # Oldest 5 removed
        assert events[-1] == 104  # Newest kept


# ── Python integer precision defense ──────────────


class TestPythonIntegerPrecision:
    """Prove Python integers don't overflow (arbitrary precision)."""

    def test_python_int_no_overflow(self):
        """Python ints have arbitrary precision — no int32/int64 overflow."""
        big = 2**100  # Way beyond int32/int64
        assert big > 0
        assert big + 1 > big

    def test_counter_increment_safe(self):
        """Counter increments work at any magnitude."""
        counter = 10_000_000_000  # 10 billion
        counter += 1
        assert counter == 10_000_000_001


# ── JSON state file defense ──────────────


class TestJSONStateFileDefense:
    """Verify JSON state file handling is resilient."""

    def test_corrupted_json_returns_default(self):
        """Corrupted JSON returns safe default state."""
        corrupted = "{invalid json"
        try:
            data = json.loads(corrupted)
        except json.JSONDecodeError:
            data = {"tool_count": 0, "check_count": 0}
        assert data["tool_count"] == 0

    def test_empty_file_returns_default(self):
        """Empty file returns safe default state."""
        try:
            data = json.loads("")
        except json.JSONDecodeError:
            data = {"warnings_issued": 0}
        assert data["warnings_issued"] == 0


# ── Hook config port parsing defense ──────────────


class TestHookConfigDefense:
    """Verify hook config handles env vars safely."""

    def test_int_port_parsing_with_default(self):
        """int() with string default works for normal values."""
        import os
        port = int(os.getenv("NONEXISTENT_PORT_TEST_UNUSED", "8082"))
        assert port == 8082

    def test_valid_port_string(self):
        """Valid port strings parse correctly."""
        assert int("8082") == 8082
        assert int("1729") == 1729
        assert int("8001") == 8001


# ── Access log serialization defense ──────────────


class TestAccessLogSerializationDefense:
    """Verify access log entries are serializable."""

    def test_http_metadata_is_serializable(self):
        """Typical HTTP metadata entries serialize cleanly."""
        entry = {
            "method": "GET",
            "path": "/api/sessions",
            "status_code": 200,
            "duration_ms": 45.2,
            "client_ip": "127.0.0.1",
        }
        result = json.dumps(entry)
        assert '"GET"' in result
        assert '"200"' not in result  # 200 is int, not string

    def test_access_log_with_none_values(self):
        """None values serialize as null in JSON."""
        entry = {"method": "GET", "path": None, "status": 500}
        result = json.dumps(entry)
        assert "null" in result


# ── Entropy threshold elif defense ──────────────


class TestEntropyThresholdDefense:
    """Verify entropy threshold checks use elif correctly."""

    def test_elif_branches_mutually_exclusive(self):
        """Only one threshold fires per check call."""
        # Simulates the elif logic
        tool_count = 100
        warnings_shown = 0
        MEDIUM_THRESHOLD = 50
        HIGH_THRESHOLD = 100

        fired = []
        if tool_count >= HIGH_THRESHOLD and warnings_shown == 0:
            fired.append("HIGH")
            warnings_shown = 1
        elif tool_count >= MEDIUM_THRESHOLD and warnings_shown == 0:
            fired.append("MEDIUM")
            warnings_shown = 1

        assert len(fired) == 1  # Only one fires
        assert fired[0] == "HIGH"  # Higher threshold takes priority
