"""
Unit tests for Composite Traceability MCP Tools.

Batch 129: Tests for governance/mcp_tools/traceability.py
- _trace_task: single task trace node
- _trace_session: single session trace node
- _trace_rule: single rule trace node
- register_traceability_tools: trace_task_chain, trace_session_chain,
  trace_rule_chain, trace_gap_chain, trace_evidence_chain
"""

import json
from unittest.mock import patch, MagicMock

import pytest

from governance.mcp_tools.traceability import (
    _trace_task,
    _trace_session,
    _trace_rule,
    register_traceability_tools,
)


_MOD = "governance.mcp_tools.traceability"


def _json_fmt(data):
    """Simulate format_mcp_result returning JSON."""
    return json.dumps(data, indent=2, default=str)


# ── _trace_task ──────────────────────────────────────────


class TestTraceTask:

    def test_not_found(self):
        client = MagicMock()
        client.get_task.return_value = None
        result = _trace_task(client, "T-MISSING")
        assert result["task_id"] == "T-MISSING"
        assert result["error"] == "not found"

    def test_found_with_all_fields(self):
        task = MagicMock()
        task.description = "Fix bug"
        task.status = "DONE"
        task.phase = "P3"
        task.gap_id = "GAP-001"
        task.linked_rules = ["RULE-A"]
        task.linked_sessions = ["SESSION-2026-01-01-TEST"]

        client = MagicMock()
        client.get_task.return_value = task
        client.get_task_evidence.return_value = ["evidence/file.md"]
        client.get_task_commits.return_value = ["abc123"]

        result = _trace_task(client, "T-1")
        assert result["task_id"] == "T-1"
        assert result["description"] == "Fix bug"
        assert result["status"] == "DONE"
        assert result["linked_rules"] == ["RULE-A"]
        assert result["evidence_files"] == ["evidence/file.md"]
        assert result["commits"] == ["abc123"]

    def test_none_linked_fields_default_to_empty_list(self):
        task = MagicMock()
        task.linked_rules = None
        task.linked_sessions = None

        client = MagicMock()
        client.get_task.return_value = task
        client.get_task_evidence.return_value = None
        client.get_task_commits.return_value = None

        result = _trace_task(client, "T-1")
        assert result["linked_rules"] == []
        assert result["linked_sessions"] == []
        assert result["evidence_files"] == []
        assert result["commits"] == []


# ── _trace_session ───────────────────────────────────────


class TestTraceSession:

    def test_not_found(self):
        client = MagicMock()
        client.get_session.return_value = None
        result = _trace_session(client, "S-MISSING")
        assert result["error"] == "not found"

    def test_found_with_task_dicts(self):
        session = MagicMock()
        session.status = "COMPLETED"

        client = MagicMock()
        client.get_session.return_value = session
        client.get_session_evidence.return_value = ["ev1"]
        client.get_session_rules.return_value = ["RULE-A"]
        client.get_session_decisions.return_value = [{"decision_id": "D-1"}]
        client.get_tasks_for_session.return_value = [
            {"task_id": "T-1"}, {"task_id": "T-2"}
        ]

        result = _trace_session(client, "S-1")
        assert result["session_id"] == "S-1"
        assert result["task_ids"] == ["T-1", "T-2"]
        assert result["rules_applied"] == ["RULE-A"]

    def test_found_with_task_objects(self):
        session = MagicMock()
        session.status = "ACTIVE"

        task_obj = MagicMock()
        task_obj.task_id = "T-3"

        client = MagicMock()
        client.get_session.return_value = session
        client.get_session_evidence.return_value = []
        client.get_session_rules.return_value = []
        client.get_session_decisions.return_value = []
        client.get_tasks_for_session.return_value = [task_obj]

        result = _trace_session(client, "S-1")
        assert result["task_ids"] == ["T-3"]

    def test_none_tasks_data(self):
        session = MagicMock()
        session.status = "COMPLETED"

        client = MagicMock()
        client.get_session.return_value = session
        client.get_session_evidence.return_value = None
        client.get_session_rules.return_value = None
        client.get_session_decisions.return_value = None
        client.get_tasks_for_session.return_value = None

        result = _trace_session(client, "S-1")
        assert result["task_ids"] == []
        assert result["evidence_files"] == []
        assert result["rules_applied"] == []


# ── _trace_rule ──────────────────────────────────────────


class TestTraceRule:

    def test_not_found(self):
        client = MagicMock()
        client.get_rule_by_id.return_value = None
        result = _trace_rule(client, "RULE-MISSING")
        assert result["error"] == "not found"

    def test_found(self):
        rule = MagicMock()
        rule.name = "Test Rule"
        rule.category = "governance"
        rule.priority = "HIGH"
        rule.status = "ACTIVE"

        client = MagicMock()
        client.get_rule_by_id.return_value = rule
        client.get_rule_dependencies.return_value = ["RULE-B"]
        client.get_rules_depending_on.return_value = ["RULE-C"]

        result = _trace_rule(client, "RULE-A")
        assert result["name"] == "Test Rule"
        assert result["dependencies"] == ["RULE-B"]
        assert result["depended_by"] == ["RULE-C"]


# ── registered MCP tools ─────────────────────────────────


def _register_tools():
    """Register tools and return them as a dict."""
    mcp = MagicMock()
    tools = {}

    def tool_decorator():
        def wrapper(func):
            tools[func.__name__] = func
            return func
        return wrapper

    mcp.tool = tool_decorator
    register_traceability_tools(mcp)
    return tools


class TestTraceTaskChain:

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.typedb_client")
    def test_depth_0_task_only(self, mock_ctx, mock_fmt, mock_log):
        tools = _register_tools()
        client = MagicMock()
        client.get_task.return_value = MagicMock(
            description="Fix", status="DONE", phase="P1", gap_id=None,
            linked_rules=[], linked_sessions=[])
        client.get_task_evidence.return_value = []
        client.get_task_commits.return_value = []
        mock_ctx.return_value.__enter__ = MagicMock(return_value=client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["trace_task_chain"]("T-1", depth=0))
        assert result["task_id"] == "T-1"
        assert "sessions_detail" not in result

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.typedb_client")
    def test_depth_1_expands_sessions_and_rules(self, mock_ctx, mock_fmt, mock_log):
        tools = _register_tools()
        task = MagicMock(
            description="Fix", status="DONE", phase="P1", gap_id=None,
            linked_rules=["RULE-A"], linked_sessions=["S-1"])
        session = MagicMock(status="COMPLETED")
        rule = MagicMock(name="R", category="governance", priority="HIGH", status="ACTIVE")

        client = MagicMock()
        client.get_task.return_value = task
        client.get_task_evidence.return_value = []
        client.get_task_commits.return_value = []
        client.get_session.return_value = session
        client.get_session_evidence.return_value = []
        client.get_session_rules.return_value = []
        client.get_session_decisions.return_value = []
        client.get_tasks_for_session.return_value = []
        client.get_rule_by_id.return_value = rule
        client.get_rule_dependencies.return_value = []
        client.get_rules_depending_on.return_value = []
        mock_ctx.return_value.__enter__ = MagicMock(return_value=client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["trace_task_chain"]("T-1", depth=1))
        assert len(result["sessions_detail"]) == 1
        assert len(result["rules_detail"]) == 1

    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.typedb_client")
    def test_not_found_returns_error(self, mock_ctx, mock_fmt):
        tools = _register_tools()
        client = MagicMock()
        client.get_task.return_value = None
        mock_ctx.return_value.__enter__ = MagicMock(return_value=client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["trace_task_chain"]("T-X"))
        assert result["error"] == "not found"

    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.typedb_client")
    def test_connection_error(self, mock_ctx, mock_fmt):
        tools = _register_tools()
        mock_ctx.return_value.__enter__ = MagicMock(side_effect=ConnectionError("fail"))
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["trace_task_chain"]("T-1"))
        assert "error" in result


class TestTraceSessionChain:

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.typedb_client")
    def test_depth_1_expands(self, mock_ctx, mock_fmt, mock_log):
        tools = _register_tools()
        session = MagicMock(status="COMPLETED")
        task = MagicMock(
            description="X", status="DONE", phase="P1", gap_id=None,
            linked_rules=[], linked_sessions=[])
        rule = MagicMock(name="R", category="governance", priority="HIGH", status="ACTIVE")

        client = MagicMock()
        client.get_session.return_value = session
        client.get_session_evidence.return_value = []
        client.get_session_rules.return_value = ["RULE-A"]
        client.get_session_decisions.return_value = []
        client.get_tasks_for_session.return_value = [{"task_id": "T-1"}]
        client.get_task.return_value = task
        client.get_task_evidence.return_value = []
        client.get_task_commits.return_value = []
        client.get_rule_by_id.return_value = rule
        client.get_rule_dependencies.return_value = []
        client.get_rules_depending_on.return_value = []
        mock_ctx.return_value.__enter__ = MagicMock(return_value=client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["trace_session_chain"]("S-1", depth=1))
        assert len(result["tasks_detail"]) == 1
        assert len(result["rules_detail"]) == 1

    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.typedb_client")
    def test_not_found_returns_error(self, mock_ctx, mock_fmt):
        tools = _register_tools()
        client = MagicMock()
        client.get_session.return_value = None
        mock_ctx.return_value.__enter__ = MagicMock(return_value=client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["trace_session_chain"]("S-MISSING"))
        assert result["error"] == "not found"

    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.typedb_client")
    def test_exception_returns_error(self, mock_ctx, mock_fmt):
        tools = _register_tools()
        mock_ctx.return_value.__enter__ = MagicMock(
            side_effect=RuntimeError("TypeDB timeout"))
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["trace_session_chain"]("S-1"))
        assert "error" in result
        assert "trace_session_chain failed" in result["error"]


class TestTraceRuleChain:

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.typedb_client")
    def test_depth_1_finds_implementing_tasks(self, mock_ctx, mock_fmt, mock_log):
        tools = _register_tools()
        rule = MagicMock(name="R", category="governance", priority="HIGH", status="ACTIVE")
        task = MagicMock(
            description="Impl", status="DONE", phase="P1", gap_id=None,
            linked_rules=[], linked_sessions=[])

        client = MagicMock()
        client.get_rule_by_id.return_value = rule
        client.get_rule_dependencies.return_value = []
        client.get_rules_depending_on.return_value = []
        client.execute_query.return_value = [{"tid": "T-1"}]
        client.get_task.return_value = task
        client.get_task_evidence.return_value = []
        client.get_task_commits.return_value = []
        mock_ctx.return_value.__enter__ = MagicMock(return_value=client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["trace_rule_chain"]("RULE-A", depth=1))
        assert result["implementing_count"] == 1

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.typedb_client")
    def test_query_failure_yields_empty_tasks(self, mock_ctx, mock_fmt, mock_log):
        tools = _register_tools()
        rule = MagicMock(name="R", category="governance", priority="HIGH", status="ACTIVE")

        client = MagicMock()
        client.get_rule_by_id.return_value = rule
        client.get_rule_dependencies.return_value = []
        client.get_rules_depending_on.return_value = []
        client.execute_query.side_effect = Exception("TypeDB error")
        mock_ctx.return_value.__enter__ = MagicMock(return_value=client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["trace_rule_chain"]("RULE-A", depth=1))
        assert result["implementing_count"] == 0


class TestTraceGapChain:

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.typedb_client")
    def test_no_tasks_for_gap(self, mock_ctx, mock_fmt, mock_log):
        tools = _register_tools()
        client = MagicMock()
        client.execute_query.return_value = []
        mock_ctx.return_value.__enter__ = MagicMock(return_value=client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["trace_gap_chain"]("GAP-MISSING"))
        assert "No tasks found" in result["error"]

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.typedb_client")
    def test_aggregates_linked_entities(self, mock_ctx, mock_fmt, mock_log):
        tools = _register_tools()
        task = MagicMock(
            description="Fix", status="DONE", phase="P1", gap_id="GAP-1",
            linked_rules=["RULE-A"], linked_sessions=["S-1"])

        client = MagicMock()
        client.execute_query.return_value = [{"tid": "T-1"}]
        client.get_task.return_value = task
        client.get_task_evidence.return_value = ["evidence/file.md"]
        client.get_task_commits.return_value = ["abc"]
        mock_ctx.return_value.__enter__ = MagicMock(return_value=client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["trace_gap_chain"]("GAP-1"))
        assert result["task_count"] == 1
        assert result["session_count"] == 1
        assert result["rule_count"] == 1
        assert result["evidence_count"] == 1

    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.typedb_client")
    def test_connection_error(self, mock_ctx, mock_fmt):
        tools = _register_tools()
        mock_ctx.return_value.__enter__ = MagicMock(side_effect=ConnectionError("fail"))
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["trace_gap_chain"]("GAP-1"))
        assert "error" in result


class TestTraceEvidenceChain:

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.typedb_client")
    def test_finds_tasks_and_sessions(self, mock_ctx, mock_fmt, mock_log):
        tools = _register_tools()
        task = MagicMock(
            description="X", status="DONE", phase="P1", gap_id=None,
            linked_rules=["RULE-A"], linked_sessions=[])

        client = MagicMock()
        # First call: task query, second: session query
        client.execute_query.side_effect = [
            [{"tid": "T-1"}],
            [{"sid": "S-1"}],
        ]
        client.get_task.return_value = task
        client.get_task_evidence.return_value = []
        client.get_task_commits.return_value = []
        mock_ctx.return_value.__enter__ = MagicMock(return_value=client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["trace_evidence_chain"]("evidence/test.md"))
        assert result["task_count"] == 1
        assert result["session_count"] == 1
        assert result["rule_count"] == 1

    @patch(f"{_MOD}.log_monitor_event")
    @patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt)
    @patch(f"{_MOD}.typedb_client")
    def test_query_failures_yield_empty(self, mock_ctx, mock_fmt, mock_log):
        tools = _register_tools()
        client = MagicMock()
        client.execute_query.side_effect = Exception("TypeDB error")
        mock_ctx.return_value.__enter__ = MagicMock(return_value=client)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

        result = json.loads(tools["trace_evidence_chain"]("evidence/x.md"))
        assert result["task_count"] == 0
        assert result["session_count"] == 0
