"""
Unit tests for DSM Tracker MCP Tools.

Per DOC-SIZE-01-v1: Tests for mcp_tools/dsm.py module.
Tests: register_dsm_tools — dsm_start, dsm_advance, dsm_checkpoint,
       dsm_finding, dsm_status, dsm_complete, dsm_metrics.
"""

import json
from unittest.mock import patch, MagicMock

import pytest


class _CaptureMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


_P = "governance.mcp_tools.dsm"


@pytest.fixture(autouse=True)
def _format_mcp():
    with patch(f"{_P}.format_mcp_result",
               side_effect=lambda x: json.dumps(x)):
        yield


@pytest.fixture(autouse=True)
def _no_monitoring():
    with patch(f"{_P}.MONITORING_AVAILABLE", False):
        yield


def _register():
    from governance.mcp_tools.dsm import register_dsm_tools
    mcp = _CaptureMCP()
    register_dsm_tools(mcp)
    return mcp.tools


def _make_cycle(cycle_id="DSM-001", batch_id=None, phase="AUDIT"):
    c = MagicMock()
    c.cycle_id = cycle_id
    c.batch_id = batch_id
    c.current_phase = phase
    c.start_time = "2026-01-01T10:00:00"
    c.metrics = {}
    return c


def _make_phase(value="HYPOTHESIZE", required_mcps=None):
    p = MagicMock()
    p.value = value
    p.required_mcps = required_mcps or []
    return p


class TestDsmStart:
    def test_tracker_unavailable(self):
        tools = _register()
        with patch(f"{_P}.DSM_TRACKER_AVAILABLE", False):
            result = json.loads(tools["dsm_start"]())
        assert "error" in result

    def test_success(self):
        tools = _register()
        tracker = MagicMock()
        tracker.start_cycle.return_value = _make_cycle()
        with patch(f"{_P}.get_tracker", return_value=tracker):
            result = json.loads(tools["dsm_start"]())
        assert result["cycle_id"] == "DSM-001"
        assert "message" in result

    def test_with_batch_id(self):
        tools = _register()
        tracker = MagicMock()
        tracker.start_cycle.return_value = _make_cycle(batch_id="P4.3")
        with patch(f"{_P}.get_tracker", return_value=tracker):
            result = json.loads(tools["dsm_start"](batch_id="P4.3"))
        assert result["batch_id"] == "P4.3"

    def test_value_error(self):
        tools = _register()
        tracker = MagicMock()
        tracker.start_cycle.side_effect = ValueError("already active")
        with patch(f"{_P}.get_tracker", return_value=tracker):
            result = json.loads(tools["dsm_start"]())
        assert "error" in result


class TestDsmAdvance:
    def test_tracker_unavailable(self):
        tools = _register()
        with patch(f"{_P}.DSM_TRACKER_AVAILABLE", False):
            result = json.loads(tools["dsm_advance"]())
        assert "error" in result

    def test_success(self):
        tools = _register()
        tracker = MagicMock()
        tracker.advance_phase.return_value = _make_phase()
        with patch(f"{_P}.get_tracker", return_value=tracker):
            result = json.loads(tools["dsm_advance"]())
        assert result["new_phase"] == "HYPOTHESIZE"

    def test_value_error(self):
        tools = _register()
        tracker = MagicMock()
        tracker.advance_phase.side_effect = ValueError("no active cycle")
        with patch(f"{_P}.get_tracker", return_value=tracker):
            result = json.loads(tools["dsm_advance"]())
        assert "error" in result


class TestDsmCheckpoint:
    def test_tracker_unavailable(self):
        tools = _register()
        with patch(f"{_P}.DSM_TRACKER_AVAILABLE", False):
            result = json.loads(tools["dsm_checkpoint"](description="test"))
        assert "error" in result

    def test_success(self):
        tools = _register()
        tracker = MagicMock()
        checkpoint = MagicMock()
        checkpoint.phase = "AUDIT"
        checkpoint.description = "Audited rules"
        checkpoint.timestamp = "2026-01-01T10:00:00"
        checkpoint.metrics = {}
        checkpoint.evidence = None
        tracker.checkpoint.return_value = checkpoint
        with patch(f"{_P}.get_tracker", return_value=tracker):
            result = json.loads(tools["dsm_checkpoint"](description="Audited rules"))
        assert result["phase"] == "AUDIT"
        assert result["message"] == "Checkpoint recorded"

    def test_with_metrics_dict(self):
        tools = _register()
        tracker = MagicMock()
        checkpoint = MagicMock()
        checkpoint.phase = "MEASURE"
        checkpoint.description = "test"
        checkpoint.timestamp = "2026-01-01"
        checkpoint.metrics = {"tests": 100}
        checkpoint.evidence = None
        tracker.checkpoint.return_value = checkpoint
        with patch(f"{_P}.get_tracker", return_value=tracker):
            tools["dsm_checkpoint"](description="test", metrics={"tests": 100})
        call_kwargs = tracker.checkpoint.call_args[1]
        assert call_kwargs["metrics"] == {"tests": 100}

    def test_with_metrics_string(self):
        tools = _register()
        tracker = MagicMock()
        checkpoint = MagicMock()
        checkpoint.phase = "MEASURE"
        checkpoint.description = "test"
        checkpoint.timestamp = "2026-01-01"
        checkpoint.metrics = {"tests": 100}
        checkpoint.evidence = None
        tracker.checkpoint.return_value = checkpoint
        with patch(f"{_P}.get_tracker", return_value=tracker):
            tools["dsm_checkpoint"](description="test", metrics='{"tests": 100}')
        call_kwargs = tracker.checkpoint.call_args[1]
        assert call_kwargs["metrics"] == {"tests": 100}

    def test_invalid_metrics_json(self):
        tools = _register()
        tracker = MagicMock()
        with patch(f"{_P}.get_tracker", return_value=tracker):
            result = json.loads(tools["dsm_checkpoint"](
                description="test", metrics="not json"))
        assert "Invalid metrics JSON" in result["error"]

    def test_with_evidence(self):
        tools = _register()
        tracker = MagicMock()
        checkpoint = MagicMock()
        checkpoint.phase = "AUDIT"
        checkpoint.description = "test"
        checkpoint.timestamp = "2026-01-01"
        checkpoint.metrics = None
        checkpoint.evidence = ["evidence/file.md"]
        tracker.checkpoint.return_value = checkpoint
        with patch(f"{_P}.get_tracker", return_value=tracker):
            tools["dsm_checkpoint"](description="test", evidence="evidence/file.md")
        call_kwargs = tracker.checkpoint.call_args[1]
        assert call_kwargs["evidence"] == ["evidence/file.md"]

    def test_value_error(self):
        tools = _register()
        tracker = MagicMock()
        tracker.checkpoint.side_effect = ValueError("no cycle")
        with patch(f"{_P}.get_tracker", return_value=tracker):
            result = json.loads(tools["dsm_checkpoint"](description="test"))
        assert "error" in result


class TestDsmFinding:
    def test_tracker_unavailable(self):
        tools = _register()
        with patch(f"{_P}.DSM_TRACKER_AVAILABLE", False):
            result = json.loads(tools["dsm_finding"](
                finding_type="gap", description="test"))
        assert "error" in result

    def test_success(self):
        tools = _register()
        tracker = MagicMock()
        tracker.add_finding.return_value = {"id": "F-001"}
        with patch(f"{_P}.get_tracker", return_value=tracker):
            result = json.loads(tools["dsm_finding"](
                finding_type="gap", description="Missing tests"))
        assert result["finding_id"] == "F-001"
        assert result["finding_type"] == "gap"

    def test_with_related_rules(self):
        tools = _register()
        tracker = MagicMock()
        tracker.add_finding.return_value = {"id": "F-002"}
        with patch(f"{_P}.get_tracker", return_value=tracker):
            result = json.loads(tools["dsm_finding"](
                finding_type="issue", description="test",
                related_rules="RULE-001,RULE-002"))
        assert result["related_rules"] == ["RULE-001", "RULE-002"]

    def test_no_related_rules(self):
        tools = _register()
        tracker = MagicMock()
        tracker.add_finding.return_value = {"id": "F-003"}
        with patch(f"{_P}.get_tracker", return_value=tracker):
            result = json.loads(tools["dsm_finding"](
                finding_type="observation", description="test"))
        assert result["related_rules"] == []

    def test_value_error(self):
        tools = _register()
        tracker = MagicMock()
        tracker.add_finding.side_effect = ValueError("no cycle")
        with patch(f"{_P}.get_tracker", return_value=tracker):
            result = json.loads(tools["dsm_finding"](
                finding_type="gap", description="test"))
        assert "error" in result


class TestDsmStatus:
    def test_tracker_unavailable(self):
        tools = _register()
        with patch(f"{_P}.DSM_TRACKER_AVAILABLE", False):
            result = json.loads(tools["dsm_status"]())
        assert "error" in result

    def test_success(self):
        tools = _register()
        tracker = MagicMock()
        tracker.get_status.return_value = {"phase": "AUDIT", "active": True}
        with patch(f"{_P}.get_tracker", return_value=tracker):
            result = json.loads(tools["dsm_status"]())
        assert result["phase"] == "AUDIT"


class TestDsmComplete:
    def test_tracker_unavailable(self):
        tools = _register()
        with patch(f"{_P}.DSM_TRACKER_AVAILABLE", False):
            result = json.loads(tools["dsm_complete"]())
        assert "error" in result

    def test_success(self):
        tools = _register()
        tracker = MagicMock()
        tracker.complete_cycle.return_value = "evidence/dsm-001.md"
        tracker.completed_cycles = ["c1"]
        with patch(f"{_P}.get_tracker", return_value=tracker):
            result = json.loads(tools["dsm_complete"]())
        assert result["status"] == "completed"
        assert result["evidence_path"] == "evidence/dsm-001.md"
        assert result["completed_cycles"] == 1

    def test_value_error(self):
        tools = _register()
        tracker = MagicMock()
        tracker.complete_cycle.side_effect = ValueError("no cycle")
        with patch(f"{_P}.get_tracker", return_value=tracker):
            result = json.loads(tools["dsm_complete"]())
        assert "error" in result


class TestDsmMetrics:
    def test_tracker_unavailable(self):
        tools = _register()
        with patch(f"{_P}.DSM_TRACKER_AVAILABLE", False):
            result = json.loads(tools["dsm_metrics"](metrics_json='{"k": 1}'))
        assert "error" in result

    def test_with_dict(self):
        tools = _register()
        tracker = MagicMock()
        tracker.current_cycle = _make_cycle()
        tracker.current_cycle.metrics = {"tests": 100}
        with patch(f"{_P}.get_tracker", return_value=tracker):
            result = json.loads(tools["dsm_metrics"](
                metrics_json={"tests": 100}))
        assert result["message"] == "Metrics updated"
        tracker.update_metrics.assert_called_once_with({"tests": 100})

    def test_with_string(self):
        tools = _register()
        tracker = MagicMock()
        tracker.current_cycle = _make_cycle()
        tracker.current_cycle.metrics = {"tests": 100}
        with patch(f"{_P}.get_tracker", return_value=tracker):
            result = json.loads(tools["dsm_metrics"](
                metrics_json='{"tests": 100}'))
        assert result["message"] == "Metrics updated"

    def test_invalid_json(self):
        tools = _register()
        tracker = MagicMock()
        with patch(f"{_P}.get_tracker", return_value=tracker):
            result = json.loads(tools["dsm_metrics"](metrics_json="bad json"))
        assert "Invalid metrics JSON" in result["error"]

    def test_value_error(self):
        tools = _register()
        tracker = MagicMock()
        tracker.update_metrics.side_effect = ValueError("no cycle")
        with patch(f"{_P}.get_tracker", return_value=tracker):
            result = json.loads(tools["dsm_metrics"](
                metrics_json={"k": 1}))
        assert "error" in result
