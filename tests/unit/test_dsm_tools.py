"""
Unit tests for DSM Tracker MCP Tools.

Per RULE-012: Tests for dsm_start, dsm_advance, dsm_checkpoint,
dsm_finding, dsm_status, dsm_complete, dsm_metrics tool functions.
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from governance.mcp_tools.dsm import register_dsm_tools


def _json_format(data, **kw):
    """Force JSON output instead of TOON."""
    return json.dumps(data, default=str)


class _CaptureMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


@pytest.fixture(autouse=True)
def _force_json():
    with patch("governance.mcp_tools.dsm.format_mcp_result", side_effect=_json_format):
        yield


@pytest.fixture
def mcp_tools():
    mcp = _CaptureMCP()
    register_dsm_tools(mcp)
    return mcp.tools


# ---------------------------------------------------------------------------
# Unavailable tracker
# ---------------------------------------------------------------------------
class TestDSMUnavailable:
    """Tests when DSMTracker is not available."""

    def test_dsm_start_unavailable(self, mcp_tools, monkeypatch):
        import governance.mcp_tools.dsm as dsm_mod
        monkeypatch.setattr(dsm_mod, "DSM_TRACKER_AVAILABLE", False)
        result = json.loads(mcp_tools["dsm_start"]())
        assert "error" in result
        assert "not available" in result["error"]

    def test_dsm_advance_unavailable(self, mcp_tools, monkeypatch):
        import governance.mcp_tools.dsm as dsm_mod
        monkeypatch.setattr(dsm_mod, "DSM_TRACKER_AVAILABLE", False)
        result = json.loads(mcp_tools["dsm_advance"]())
        assert "error" in result

    def test_dsm_status_unavailable(self, mcp_tools, monkeypatch):
        import governance.mcp_tools.dsm as dsm_mod
        monkeypatch.setattr(dsm_mod, "DSM_TRACKER_AVAILABLE", False)
        result = json.loads(mcp_tools["dsm_status"]())
        assert "error" in result

    def test_dsm_complete_unavailable(self, mcp_tools, monkeypatch):
        import governance.mcp_tools.dsm as dsm_mod
        monkeypatch.setattr(dsm_mod, "DSM_TRACKER_AVAILABLE", False)
        result = json.loads(mcp_tools["dsm_complete"]())
        assert "error" in result

    def test_dsm_checkpoint_unavailable(self, mcp_tools, monkeypatch):
        import governance.mcp_tools.dsm as dsm_mod
        monkeypatch.setattr(dsm_mod, "DSM_TRACKER_AVAILABLE", False)
        result = json.loads(mcp_tools["dsm_checkpoint"](description="test"))
        assert "error" in result

    def test_dsm_finding_unavailable(self, mcp_tools, monkeypatch):
        import governance.mcp_tools.dsm as dsm_mod
        monkeypatch.setattr(dsm_mod, "DSM_TRACKER_AVAILABLE", False)
        result = json.loads(mcp_tools["dsm_finding"](finding_type="gap", description="test"))
        assert "error" in result

    def test_dsm_metrics_unavailable(self, mcp_tools, monkeypatch):
        import governance.mcp_tools.dsm as dsm_mod
        monkeypatch.setattr(dsm_mod, "DSM_TRACKER_AVAILABLE", False)
        result = json.loads(mcp_tools["dsm_metrics"](metrics_json='{"a": 1}'))
        assert "error" in result


# ---------------------------------------------------------------------------
# dsm_start
# ---------------------------------------------------------------------------
class TestDSMStart:
    """Tests for dsm_start() tool."""

    def test_start_success(self, mcp_tools, monkeypatch):
        import governance.mcp_tools.dsm as dsm_mod
        monkeypatch.setattr(dsm_mod, "DSM_TRACKER_AVAILABLE", True)
        mock_cycle = MagicMock()
        mock_cycle.cycle_id = "DSM-2026-02-11-120000"
        mock_cycle.batch_id = "BATCH-1"
        mock_cycle.current_phase = "audit"
        mock_cycle.start_time = "2026-02-11T12:00:00"
        mock_tracker = MagicMock()
        mock_tracker.start_cycle.return_value = mock_cycle
        monkeypatch.setattr(dsm_mod, "get_tracker", lambda: mock_tracker)
        result = json.loads(mcp_tools["dsm_start"](batch_id="BATCH-1"))
        assert result["cycle_id"] == "DSM-2026-02-11-120000"
        assert result["batch_id"] == "BATCH-1"
        assert "DSM cycle started" in result["message"]

    def test_start_error(self, mcp_tools, monkeypatch):
        import governance.mcp_tools.dsm as dsm_mod
        monkeypatch.setattr(dsm_mod, "DSM_TRACKER_AVAILABLE", True)
        mock_tracker = MagicMock()
        mock_tracker.start_cycle.side_effect = ValueError("Cycle already active")
        monkeypatch.setattr(dsm_mod, "get_tracker", lambda: mock_tracker)
        result = json.loads(mcp_tools["dsm_start"]())
        assert "error" in result
        assert "Cycle already active" in result["error"]


# ---------------------------------------------------------------------------
# dsm_advance
# ---------------------------------------------------------------------------
class TestDSMAdvance:
    """Tests for dsm_advance() tool."""

    def test_advance_success(self, mcp_tools, monkeypatch):
        import governance.mcp_tools.dsm as dsm_mod
        monkeypatch.setattr(dsm_mod, "DSM_TRACKER_AVAILABLE", True)
        mock_phase = MagicMock()
        mock_phase.value = "hypothesize"
        mock_phase.required_mcps = ["claude-mem"]
        mock_tracker = MagicMock()
        mock_tracker.advance_phase.return_value = mock_phase
        monkeypatch.setattr(dsm_mod, "get_tracker", lambda: mock_tracker)
        result = json.loads(mcp_tools["dsm_advance"]())
        assert result["new_phase"] == "hypothesize"
        assert "Advanced to phase" in result["message"]

    def test_advance_error(self, mcp_tools, monkeypatch):
        import governance.mcp_tools.dsm as dsm_mod
        monkeypatch.setattr(dsm_mod, "DSM_TRACKER_AVAILABLE", True)
        mock_tracker = MagicMock()
        mock_tracker.advance_phase.side_effect = ValueError("No active cycle")
        monkeypatch.setattr(dsm_mod, "get_tracker", lambda: mock_tracker)
        result = json.loads(mcp_tools["dsm_advance"]())
        assert "error" in result


# ---------------------------------------------------------------------------
# dsm_checkpoint
# ---------------------------------------------------------------------------
class TestDSMCheckpoint:
    """Tests for dsm_checkpoint() tool."""

    def test_checkpoint_success(self, mcp_tools, monkeypatch):
        import governance.mcp_tools.dsm as dsm_mod
        monkeypatch.setattr(dsm_mod, "DSM_TRACKER_AVAILABLE", True)
        mock_cp = MagicMock()
        mock_cp.phase = "audit"
        mock_cp.description = "Checked rules"
        mock_cp.timestamp = "2026-02-11T12:00:00"
        mock_cp.metrics = {"rules": 50}
        mock_cp.evidence = ["ev.md"]
        mock_tracker = MagicMock()
        mock_tracker.checkpoint.return_value = mock_cp
        monkeypatch.setattr(dsm_mod, "get_tracker", lambda: mock_tracker)
        result = json.loads(mcp_tools["dsm_checkpoint"](
            description="Checked rules", metrics={"rules": 50}, evidence="ev.md",
        ))
        assert result["phase"] == "audit"
        assert result["message"] == "Checkpoint recorded"

    def test_checkpoint_json_string_metrics(self, mcp_tools, monkeypatch):
        import governance.mcp_tools.dsm as dsm_mod
        monkeypatch.setattr(dsm_mod, "DSM_TRACKER_AVAILABLE", True)
        mock_cp = MagicMock()
        mock_cp.phase = "measure"
        mock_cp.description = "test"
        mock_cp.timestamp = "now"
        mock_cp.metrics = {"tests": 78}
        mock_cp.evidence = None
        mock_tracker = MagicMock()
        mock_tracker.checkpoint.return_value = mock_cp
        monkeypatch.setattr(dsm_mod, "get_tracker", lambda: mock_tracker)
        result = json.loads(mcp_tools["dsm_checkpoint"](
            description="test", metrics='{"tests": 78}',
        ))
        assert result["phase"] == "measure"

    def test_checkpoint_invalid_json_metrics(self, mcp_tools, monkeypatch):
        import governance.mcp_tools.dsm as dsm_mod
        monkeypatch.setattr(dsm_mod, "DSM_TRACKER_AVAILABLE", True)
        monkeypatch.setattr(dsm_mod, "get_tracker", lambda: MagicMock())
        result = json.loads(mcp_tools["dsm_checkpoint"](
            description="test", metrics="not json",
        ))
        assert "error" in result
        assert "Invalid metrics JSON" in result["error"]


# ---------------------------------------------------------------------------
# dsm_finding
# ---------------------------------------------------------------------------
class TestDSMFinding:
    """Tests for dsm_finding() tool."""

    def test_finding_success(self, mcp_tools, monkeypatch):
        import governance.mcp_tools.dsm as dsm_mod
        monkeypatch.setattr(dsm_mod, "DSM_TRACKER_AVAILABLE", True)
        mock_tracker = MagicMock()
        mock_tracker.add_finding.return_value = {"id": "FIND-001"}
        monkeypatch.setattr(dsm_mod, "get_tracker", lambda: mock_tracker)
        result = json.loads(mcp_tools["dsm_finding"](
            finding_type="gap", description="Missing tests", severity="HIGH",
            related_rules="R-1,R-2",
        ))
        assert result["finding_id"] == "FIND-001"
        assert result["finding_type"] == "gap"
        assert result["severity"] == "HIGH"
        assert result["related_rules"] == ["R-1", "R-2"]

    def test_finding_no_rules(self, mcp_tools, monkeypatch):
        import governance.mcp_tools.dsm as dsm_mod
        monkeypatch.setattr(dsm_mod, "DSM_TRACKER_AVAILABLE", True)
        mock_tracker = MagicMock()
        mock_tracker.add_finding.return_value = {"id": "FIND-002"}
        monkeypatch.setattr(dsm_mod, "get_tracker", lambda: mock_tracker)
        result = json.loads(mcp_tools["dsm_finding"](
            finding_type="observation", description="Note",
        ))
        assert result["related_rules"] == []


# ---------------------------------------------------------------------------
# dsm_status
# ---------------------------------------------------------------------------
class TestDSMStatus:
    """Tests for dsm_status() tool."""

    def test_status_returns_tracker_data(self, mcp_tools, monkeypatch):
        import governance.mcp_tools.dsm as dsm_mod
        monkeypatch.setattr(dsm_mod, "DSM_TRACKER_AVAILABLE", True)
        mock_tracker = MagicMock()
        mock_tracker.get_status.return_value = {"phase": "audit", "findings": 3}
        monkeypatch.setattr(dsm_mod, "get_tracker", lambda: mock_tracker)
        result = json.loads(mcp_tools["dsm_status"]())
        assert result["phase"] == "audit"
        assert result["findings"] == 3


# ---------------------------------------------------------------------------
# dsm_complete
# ---------------------------------------------------------------------------
class TestDSMComplete:
    """Tests for dsm_complete() tool."""

    def test_complete_success(self, mcp_tools, monkeypatch):
        import governance.mcp_tools.dsm as dsm_mod
        monkeypatch.setattr(dsm_mod, "DSM_TRACKER_AVAILABLE", True)
        mock_tracker = MagicMock()
        mock_tracker.complete_cycle.return_value = "evidence/DSM-2026-02-11.md"
        mock_tracker.completed_cycles = [MagicMock(), MagicMock()]
        monkeypatch.setattr(dsm_mod, "get_tracker", lambda: mock_tracker)
        result = json.loads(mcp_tools["dsm_complete"]())
        assert result["status"] == "completed"
        assert result["evidence_path"] == "evidence/DSM-2026-02-11.md"
        assert result["completed_cycles"] == 2

    def test_complete_error(self, mcp_tools, monkeypatch):
        import governance.mcp_tools.dsm as dsm_mod
        monkeypatch.setattr(dsm_mod, "DSM_TRACKER_AVAILABLE", True)
        mock_tracker = MagicMock()
        mock_tracker.complete_cycle.side_effect = ValueError("No active cycle")
        monkeypatch.setattr(dsm_mod, "get_tracker", lambda: mock_tracker)
        result = json.loads(mcp_tools["dsm_complete"]())
        assert "error" in result


# ---------------------------------------------------------------------------
# dsm_metrics
# ---------------------------------------------------------------------------
class TestDSMMetrics:
    """Tests for dsm_metrics() tool."""

    def test_metrics_dict_input(self, mcp_tools, monkeypatch):
        import governance.mcp_tools.dsm as dsm_mod
        monkeypatch.setattr(dsm_mod, "DSM_TRACKER_AVAILABLE", True)
        mock_tracker = MagicMock()
        mock_tracker.current_cycle.metrics = {"tests": 78, "coverage": 85}
        monkeypatch.setattr(dsm_mod, "get_tracker", lambda: mock_tracker)
        result = json.loads(mcp_tools["dsm_metrics"](
            metrics_json={"tests": 78, "coverage": 85},
        ))
        assert result["metrics"]["tests"] == 78
        assert result["message"] == "Metrics updated"

    def test_metrics_json_string(self, mcp_tools, monkeypatch):
        import governance.mcp_tools.dsm as dsm_mod
        monkeypatch.setattr(dsm_mod, "DSM_TRACKER_AVAILABLE", True)
        mock_tracker = MagicMock()
        mock_tracker.current_cycle.metrics = {"a": 1}
        monkeypatch.setattr(dsm_mod, "get_tracker", lambda: mock_tracker)
        result = json.loads(mcp_tools["dsm_metrics"](
            metrics_json='{"a": 1}',
        ))
        assert result["message"] == "Metrics updated"

    def test_metrics_invalid_json(self, mcp_tools, monkeypatch):
        import governance.mcp_tools.dsm as dsm_mod
        monkeypatch.setattr(dsm_mod, "DSM_TRACKER_AVAILABLE", True)
        result = json.loads(mcp_tools["dsm_metrics"](metrics_json="not json"))
        assert "error" in result
        assert "Invalid metrics JSON" in result["error"]
