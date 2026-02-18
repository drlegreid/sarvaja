"""Tests for governance/mcp_tools/dsm.py — DSM Tracker MCP tools.

Covers: register_dsm_tools (dsm_start, dsm_advance, dsm_checkpoint,
dsm_finding, dsm_status, dsm_complete, dsm_metrics).
"""

import json
import unittest
from unittest.mock import patch, MagicMock


# Patch format_mcp_result at module level so tools return plain JSON
_fmt_patch = patch(
    "governance.mcp_tools.dsm.format_mcp_result",
    side_effect=lambda data, **kw: json.dumps(data),
)


def _register_tools():
    """Register DSM tools via the MCP tool decorator capture pattern."""
    tools = {}

    class MockMCP:
        def tool(self):
            def decorator(func):
                tools[func.__name__] = func
                return func
            return decorator

    mcp = MockMCP()
    from governance.mcp_tools.dsm import register_dsm_tools
    register_dsm_tools(mcp)
    return tools


# Register once at module level
_TOOLS = _register_tools()


class TestDsmStart(unittest.TestCase):
    """Tests for dsm_start tool."""

    def setUp(self):
        self.dsm_start = _TOOLS["dsm_start"]
        self._patcher = _fmt_patch
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()

    @patch("governance.mcp_tools.dsm.MONITORING_AVAILABLE", False)
    @patch("governance.mcp_tools.dsm.DSM_TRACKER_AVAILABLE", True)
    @patch("governance.mcp_tools.dsm.get_tracker")
    def test_start_success(self, mock_get_tracker):
        cycle = MagicMock()
        cycle.cycle_id = "DSM-001"
        cycle.batch_id = "P4.3"
        cycle.current_phase = "AUDIT"
        cycle.start_time = "2026-02-13T10:00:00"
        mock_get_tracker.return_value.start_cycle.return_value = cycle

        result = json.loads(self.dsm_start(batch_id="P4.3"))
        self.assertEqual(result["cycle_id"], "DSM-001")
        self.assertEqual(result["batch_id"], "P4.3")

    @patch("governance.mcp_tools.dsm.DSM_TRACKER_AVAILABLE", False)
    def test_start_unavailable(self):
        result = json.loads(self.dsm_start())
        self.assertIn("error", result)
        self.assertIn("not available", result["error"])

    @patch("governance.mcp_tools.dsm.MONITORING_AVAILABLE", False)
    @patch("governance.mcp_tools.dsm.DSM_TRACKER_AVAILABLE", True)
    @patch("governance.mcp_tools.dsm.get_tracker")
    def test_start_exception(self, mock_get_tracker):
        mock_get_tracker.return_value.start_cycle.side_effect = Exception("boom")
        result = json.loads(self.dsm_start())
        self.assertIn("error", result)
        self.assertIn("dsm_start failed: Exception", result["error"])


class TestDsmAdvance(unittest.TestCase):
    """Tests for dsm_advance tool."""

    def setUp(self):
        self.dsm_advance = _TOOLS["dsm_advance"]
        self._patcher = _fmt_patch
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()

    @patch("governance.mcp_tools.dsm.MONITORING_AVAILABLE", False)
    @patch("governance.mcp_tools.dsm.DSM_TRACKER_AVAILABLE", True)
    @patch("governance.mcp_tools.dsm.get_tracker")
    def test_advance_success(self, mock_get_tracker):
        phase = MagicMock()
        phase.value = "HYPOTHESIZE"
        phase.required_mcps = ["chroma"]
        mock_get_tracker.return_value.advance_phase.return_value = phase

        result = json.loads(self.dsm_advance())
        self.assertEqual(result["new_phase"], "HYPOTHESIZE")
        self.assertEqual(result["required_mcps"], ["chroma"])

    @patch("governance.mcp_tools.dsm.DSM_TRACKER_AVAILABLE", False)
    def test_advance_unavailable(self):
        result = json.loads(self.dsm_advance())
        self.assertIn("error", result)


class TestDsmCheckpoint(unittest.TestCase):
    """Tests for dsm_checkpoint tool."""

    def setUp(self):
        self.dsm_checkpoint = _TOOLS["dsm_checkpoint"]
        self._patcher = _fmt_patch
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()

    @patch("governance.mcp_tools.dsm.MONITORING_AVAILABLE", False)
    @patch("governance.mcp_tools.dsm.DSM_TRACKER_AVAILABLE", True)
    @patch("governance.mcp_tools.dsm.get_tracker")
    def test_checkpoint_str_metrics(self, mock_get_tracker):
        cp = MagicMock()
        cp.phase = "MEASURE"
        cp.description = "Tests passed"
        cp.timestamp = "2026-02-13T10:00:00"
        cp.metrics = {"tests": 78}
        cp.evidence = ["proof.md"]
        mock_get_tracker.return_value.checkpoint.return_value = cp

        result = json.loads(self.dsm_checkpoint(
            description="Tests passed",
            metrics='{"tests": 78}',
            evidence="proof.md",
        ))
        self.assertEqual(result["phase"], "MEASURE")
        self.assertEqual(result["description"], "Tests passed")

    @patch("governance.mcp_tools.dsm.MONITORING_AVAILABLE", False)
    @patch("governance.mcp_tools.dsm.DSM_TRACKER_AVAILABLE", True)
    @patch("governance.mcp_tools.dsm.get_tracker")
    def test_checkpoint_dict_metrics(self, mock_get_tracker):
        """Per GAP-DSM-002: accepts both str and dict."""
        cp = MagicMock()
        cp.phase = "AUDIT"
        cp.description = "Done"
        cp.timestamp = "now"
        cp.metrics = {"x": 1}
        cp.evidence = None
        mock_get_tracker.return_value.checkpoint.return_value = cp

        result = json.loads(self.dsm_checkpoint(
            description="Done",
            metrics={"x": 1},
        ))
        self.assertNotIn("error", result)

    @patch("governance.mcp_tools.dsm.MONITORING_AVAILABLE", False)
    @patch("governance.mcp_tools.dsm.DSM_TRACKER_AVAILABLE", True)
    @patch("governance.mcp_tools.dsm.get_tracker")
    def test_checkpoint_invalid_json(self, mock_get_tracker):
        result = json.loads(self.dsm_checkpoint(
            description="Bad",
            metrics="NOT JSON",
        ))
        self.assertIn("error", result)
        self.assertIn("Invalid metrics JSON", result["error"])

    @patch("governance.mcp_tools.dsm.DSM_TRACKER_AVAILABLE", False)
    def test_checkpoint_unavailable(self):
        result = json.loads(self.dsm_checkpoint(description="x"))
        self.assertIn("error", result)


class TestDsmFinding(unittest.TestCase):
    """Tests for dsm_finding tool."""

    def setUp(self):
        self.dsm_finding = _TOOLS["dsm_finding"]
        self._patcher = _fmt_patch
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()

    @patch("governance.mcp_tools.dsm.MONITORING_AVAILABLE", False)
    @patch("governance.mcp_tools.dsm.DSM_TRACKER_AVAILABLE", True)
    @patch("governance.mcp_tools.dsm.get_tracker")
    def test_finding_success(self, mock_get_tracker):
        mock_get_tracker.return_value.add_finding.return_value = {"id": "F-001"}

        result = json.loads(self.dsm_finding(
            finding_type="gap",
            description="Missing tests",
            severity="HIGH",
            related_rules="RULE-001,RULE-002",
        ))
        self.assertEqual(result["finding_id"], "F-001")
        self.assertEqual(result["finding_type"], "gap")
        self.assertEqual(result["severity"], "HIGH")
        self.assertEqual(result["related_rules"], ["RULE-001", "RULE-002"])

    @patch("governance.mcp_tools.dsm.MONITORING_AVAILABLE", False)
    @patch("governance.mcp_tools.dsm.DSM_TRACKER_AVAILABLE", True)
    @patch("governance.mcp_tools.dsm.get_tracker")
    def test_finding_no_rules(self, mock_get_tracker):
        mock_get_tracker.return_value.add_finding.return_value = {"id": "F-002"}
        result = json.loads(self.dsm_finding(
            finding_type="observation",
            description="Looks good",
        ))
        self.assertEqual(result["related_rules"], [])

    @patch("governance.mcp_tools.dsm.DSM_TRACKER_AVAILABLE", False)
    def test_finding_unavailable(self):
        result = json.loads(self.dsm_finding(
            finding_type="issue", description="oops",
        ))
        self.assertIn("error", result)


class TestDsmStatus(unittest.TestCase):
    """Tests for dsm_status tool."""

    def setUp(self):
        self.dsm_status = _TOOLS["dsm_status"]
        self._patcher = _fmt_patch
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()

    @patch("governance.mcp_tools.dsm.DSM_TRACKER_AVAILABLE", True)
    @patch("governance.mcp_tools.dsm.get_tracker")
    def test_status_success(self, mock_get_tracker):
        mock_get_tracker.return_value.get_status.return_value = {
            "current_phase": "AUDIT", "checkpoints": 2,
        }
        result = json.loads(self.dsm_status())
        self.assertEqual(result["current_phase"], "AUDIT")

    @patch("governance.mcp_tools.dsm.DSM_TRACKER_AVAILABLE", False)
    def test_status_unavailable(self):
        result = json.loads(self.dsm_status())
        self.assertIn("error", result)


class TestDsmComplete(unittest.TestCase):
    """Tests for dsm_complete tool."""

    def setUp(self):
        self.dsm_complete = _TOOLS["dsm_complete"]
        self._patcher = _fmt_patch
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()

    @patch("governance.mcp_tools.dsm.MONITORING_AVAILABLE", False)
    @patch("governance.mcp_tools.dsm.DSM_TRACKER_AVAILABLE", True)
    @patch("governance.mcp_tools.dsm.get_tracker")
    def test_complete_success(self, mock_get_tracker):
        tracker = mock_get_tracker.return_value
        tracker.complete_cycle.return_value = "evidence/DSM-2026-02-13.md"
        tracker.completed_cycles = ["c1", "c2"]

        result = json.loads(self.dsm_complete())
        self.assertEqual(result["status"], "completed")
        self.assertIn("evidence", result["evidence_path"])
        self.assertEqual(result["completed_cycles"], 2)

    @patch("governance.mcp_tools.dsm.MONITORING_AVAILABLE", False)
    @patch("governance.mcp_tools.dsm.DSM_TRACKER_AVAILABLE", True)
    @patch("governance.mcp_tools.dsm.get_tracker")
    def test_complete_exception(self, mock_get_tracker):
        mock_get_tracker.return_value.complete_cycle.side_effect = Exception("no active cycle")
        result = json.loads(self.dsm_complete())
        self.assertIn("error", result)

    @patch("governance.mcp_tools.dsm.DSM_TRACKER_AVAILABLE", False)
    def test_complete_unavailable(self):
        result = json.loads(self.dsm_complete())
        self.assertIn("error", result)


class TestDsmMetrics(unittest.TestCase):
    """Tests for dsm_metrics tool."""

    def setUp(self):
        self.dsm_metrics = _TOOLS["dsm_metrics"]
        self._patcher = _fmt_patch
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()

    @patch("governance.mcp_tools.dsm.MONITORING_AVAILABLE", False)
    @patch("governance.mcp_tools.dsm.DSM_TRACKER_AVAILABLE", True)
    @patch("governance.mcp_tools.dsm.get_tracker")
    def test_metrics_dict(self, mock_get_tracker):
        """Per GAP-DSM-002: accepts dict."""
        tracker = mock_get_tracker.return_value
        tracker.current_cycle.metrics = {"tests": 100}

        result = json.loads(self.dsm_metrics(metrics_json={"tests": 100}))
        self.assertEqual(result["metrics"]["tests"], 100)

    @patch("governance.mcp_tools.dsm.MONITORING_AVAILABLE", False)
    @patch("governance.mcp_tools.dsm.DSM_TRACKER_AVAILABLE", True)
    @patch("governance.mcp_tools.dsm.get_tracker")
    def test_metrics_str(self, mock_get_tracker):
        tracker = mock_get_tracker.return_value
        tracker.current_cycle.metrics = {"coverage": 85}

        result = json.loads(self.dsm_metrics(metrics_json='{"coverage": 85}'))
        self.assertEqual(result["metrics"]["coverage"], 85)

    @patch("governance.mcp_tools.dsm.MONITORING_AVAILABLE", False)
    @patch("governance.mcp_tools.dsm.DSM_TRACKER_AVAILABLE", True)
    @patch("governance.mcp_tools.dsm.get_tracker")
    def test_metrics_invalid_json(self, mock_get_tracker):
        result = json.loads(self.dsm_metrics(metrics_json="NOT JSON"))
        self.assertIn("error", result)

    @patch("governance.mcp_tools.dsm.DSM_TRACKER_AVAILABLE", False)
    def test_metrics_unavailable(self):
        result = json.loads(self.dsm_metrics(metrics_json="{}"))
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
