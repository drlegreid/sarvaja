"""
Unit tests for Session Evidence MCP Tools.

Per DOC-SIZE-01-v1: Tests for mcp_tools/sessions_evidence.py module.
Tests: session_test_summary, test_evidence_push,
       test_evidence_query, test_evidence_get.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

_P = "governance.mcp_tools.sessions_evidence"


class _CaptureMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


def _register(**overrides):
    mcp = _CaptureMCP()
    with patch(f"{_P}.SUMMARY_COMPRESSOR_AVAILABLE", overrides.get("compressor", True)), \
         patch(f"{_P}.HOLOGRAPHIC_AVAILABLE", overrides.get("holographic", True)):
        from governance.mcp_tools.sessions_evidence import register_session_evidence_tools
        register_session_evidence_tools(mcp)
    return mcp.tools


@pytest.fixture(autouse=True)
def _mock_format():
    with patch(f"{_P}.format_mcp_result", side_effect=lambda x: json.dumps(x)):
        yield


# ── session_test_summary ────────────────────────────────────────


class TestSessionTestSummary:
    def test_success_compact(self):
        tools = _register()
        summary_mock = MagicMock()
        summary_mock.format_compact.return_value = "5P 0F 0S"
        summary_mock.compression_ratio = 0.8
        summary_mock.total = 5
        summary_mock.passed = 5
        summary_mock.failed = 0
        summary_mock.skipped = 0
        compressor = MagicMock()
        compressor.compress_test_list.return_value = summary_mock
        with patch(f"{_P}.SummaryCompressor", create=True, return_value=compressor):
            result = json.loads(tools["session_test_summary"](
                tests_json='[{"test_id":"T-1","status":"passed"}]',
            ))
        assert result["summary"] == "5P 0F 0S"
        assert result["stats"]["total"] == 5

    def test_oneline_format(self):
        tools = _register()
        summary_mock = MagicMock()
        summary_mock.format_oneline.return_value = "ALL PASS"
        summary_mock.compression_ratio = 0.9
        summary_mock.total = 3
        summary_mock.passed = 3
        summary_mock.failed = 0
        summary_mock.skipped = 0
        compressor = MagicMock()
        compressor.compress_test_list.return_value = summary_mock
        with patch(f"{_P}.SummaryCompressor", create=True, return_value=compressor):
            result = json.loads(tools["session_test_summary"](
                tests_json="[]", format="oneline",
            ))
        assert result["summary"] == "ALL PASS"

    def test_dict_format(self):
        tools = _register()
        summary_mock = MagicMock()
        summary_mock.to_dict.return_value = {"total": 2, "passed": 2}
        compressor = MagicMock()
        compressor.compress_test_list.return_value = summary_mock
        with patch(f"{_P}.SummaryCompressor", create=True, return_value=compressor):
            result = json.loads(tools["session_test_summary"](
                tests_json="[]", format="dict",
            ))
        assert result["total"] == 2

    def test_invalid_json(self):
        tools = _register()
        result = json.loads(tools["session_test_summary"](tests_json="not json"))
        assert "error" in result

    def test_compressor_unavailable(self):
        tools = _register(compressor=False)
        with patch(f"{_P}.SUMMARY_COMPRESSOR_AVAILABLE", False):
            result = json.loads(tools["session_test_summary"](tests_json="[]"))
        assert "error" in result


# ── test_evidence_push ──────────────────────────────────────────


class TestTestEvidencePush:
    def test_success(self):
        tools = _register()
        store = MagicMock()
        store.push_event.return_value = "abc123def456abcd"
        store.count = 1
        with patch(f"{_P}.get_global_store", create=True, return_value=store):
            result = json.loads(tools["test_evidence_push"](
                test_id="T-1", name="Test", status="passed",
            ))
        assert result["evidence_hash"] == "abc123def456abcd"
        assert result["store_count"] == 1

    def test_with_fixtures(self):
        tools = _register()
        store = MagicMock()
        store.push_event.return_value = "hash123"
        store.count = 2
        with patch(f"{_P}.get_global_store", create=True, return_value=store):
            result = json.loads(tools["test_evidence_push"](
                test_id="T-1", name="Test", status="passed",
                fixtures_json='{"request": "/api/test"}',
            ))
        assert result["evidence_hash"] == "hash123"
        # Verify fixtures were parsed
        call_kwargs = store.push_event.call_args[1]
        assert call_kwargs["fixtures"] == {"request": "/api/test"}

    def test_invalid_fixtures_json(self):
        tools = _register()
        store = MagicMock()
        store.push_event.return_value = "hash123"
        store.count = 1
        with patch(f"{_P}.get_global_store", create=True, return_value=store):
            result = json.loads(tools["test_evidence_push"](
                test_id="T-1", name="Test", status="failed",
                fixtures_json="not json",
            ))
        assert result["evidence_hash"] == "hash123"
        call_kwargs = store.push_event.call_args[1]
        assert call_kwargs["fixtures"] == {"raw": "not json"}

    def test_with_linked_rules(self):
        tools = _register()
        store = MagicMock()
        store.push_event.return_value = "hash123"
        store.count = 1
        with patch(f"{_P}.get_global_store", create=True, return_value=store):
            tools["test_evidence_push"](
                test_id="T-1", name="Test", status="passed",
                linked_rules="RULE-A, RULE-B",
            )
        call_kwargs = store.push_event.call_args[1]
        assert call_kwargs["linked_rules"] == ["RULE-A", "RULE-B"]

    def test_holographic_unavailable(self):
        tools = _register(holographic=False)
        with patch(f"{_P}.HOLOGRAPHIC_AVAILABLE", False):
            result = json.loads(tools["test_evidence_push"](
                test_id="T-1", name="Test", status="passed",
            ))
        assert "error" in result


# ── test_evidence_query ─────────────────────────────────────────


class TestTestEvidenceQuery:
    def test_success(self):
        tools = _register()
        store = MagicMock()
        store.count = 5
        store.query.return_value = {"zoom": 1, "tests": []}
        with patch(f"{_P}.get_global_store", create=True, return_value=store):
            result = json.loads(tools["test_evidence_query"](zoom=1))
        assert result["zoom"] == 1

    def test_empty_store(self):
        tools = _register()
        store = MagicMock()
        store.count = 0
        with patch(f"{_P}.get_global_store", create=True, return_value=store):
            result = json.loads(tools["test_evidence_query"]())
        assert result["count"] == 0
        assert "No evidence" in result["message"]

    def test_with_filters(self):
        tools = _register()
        store = MagicMock()
        store.count = 10
        store.query.return_value = {"filtered": True}
        with patch(f"{_P}.get_global_store", create=True, return_value=store):
            tools["test_evidence_query"](
                zoom=2, test_id="T-1", category="unit", status="passed",
            )
        store.query.assert_called_once_with(
            zoom=2, test_id="T-1", category="unit", status="passed",
        )

    def test_holographic_unavailable(self):
        tools = _register(holographic=False)
        with patch(f"{_P}.HOLOGRAPHIC_AVAILABLE", False):
            result = json.loads(tools["test_evidence_query"]())
        assert "error" in result


# ── test_evidence_get ───────────────────────────────────────────


class TestTestEvidenceGet:
    def test_found(self):
        tools = _register()
        store = MagicMock()
        evidence = MagicMock()
        evidence.to_full_dict.return_value = {"test_id": "T-1", "status": "passed"}
        store.get_by_hash.return_value = evidence
        with patch(f"{_P}.get_global_store", create=True, return_value=store):
            result = json.loads(tools["test_evidence_get"](evidence_hash="abc123"))
        assert result["test_id"] == "T-1"

    def test_not_found(self):
        tools = _register()
        store = MagicMock()
        store.get_by_hash.return_value = None
        with patch(f"{_P}.get_global_store", create=True, return_value=store):
            result = json.loads(tools["test_evidence_get"](evidence_hash="missing"))
        assert "error" in result

    def test_holographic_unavailable(self):
        tools = _register(holographic=False)
        with patch(f"{_P}.HOLOGRAPHIC_AVAILABLE", False):
            result = json.loads(tools["test_evidence_get"](evidence_hash="abc"))
        assert "error" in result
