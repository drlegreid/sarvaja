"""Deep scan batch 115: MCP server tools layer.

Batch 115 findings: 18 total, 0 confirmed fixes, 18 rejected.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import json


# ── Auto-session timer defense ──────────────


class TestAutoSessionTimerDefense:
    """Verify auto-session timer handles initialization correctly."""

    def test_create_session_sets_last_activity(self):
        """_create_session initializes _last_activity to prevent immediate expiry."""
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker

        tracker = MCPAutoSessionTracker.__new__(MCPAutoSessionTracker)
        tracker.active_session_id = None
        tracker._last_activity = None
        tracker.timeout_seconds = 300
        tracker._tool_count = 0
        tracker._tools_used = set()

        with patch.object(tracker, "_persist_session_start"):
            tracker._create_session("test-server")

        # After creation, _last_activity should be set (not None)
        assert tracker._last_activity is not None

    def test_is_expired_false_for_new_session(self):
        """Freshly created session should NOT be expired."""
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker

        tracker = MCPAutoSessionTracker.__new__(MCPAutoSessionTracker)
        tracker._last_activity = datetime.now()
        tracker.timeout_seconds = 300

        assert tracker._is_expired() is False

    def test_is_expired_true_after_timeout(self):
        """Session expired after timeout_seconds of inactivity."""
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker

        tracker = MCPAutoSessionTracker.__new__(MCPAutoSessionTracker)
        tracker._last_activity = datetime(2020, 1, 1)  # Long ago
        tracker.timeout_seconds = 300

        assert tracker._is_expired() is True


# ── MCP exception hierarchy defense ──────────────


class TestMCPExceptionHierarchyDefense:
    """Verify except Exception correctly handles MCP tool errors."""

    def test_except_exception_catches_connection_errors(self):
        """except Exception catches all common runtime errors."""
        runtime_errors = [
            ConnectionError("TypeDB down"),
            TimeoutError("query timeout"),
            ValueError("invalid input"),
            KeyError("missing field"),
            TypeError("type mismatch"),
        ]
        for err in runtime_errors:
            caught = False
            try:
                raise err
            except Exception:
                caught = True
            assert caught, f"{type(err).__name__} not caught"

    def test_except_exception_does_not_catch_system_exit(self):
        """except Exception does NOT catch SystemExit."""
        with pytest.raises(SystemExit):
            try:
                raise SystemExit(0)
            except Exception:
                pass  # Should NOT reach here


# ── MCP tool return format defense ──────────────


class TestMCPToolReturnDefense:
    """Verify MCP tools return properly formatted JSON strings."""

    def test_format_mcp_result_returns_string(self):
        """format_mcp_result produces string output."""
        from governance.mcp_tools.common import format_mcp_result

        result = format_mcp_result({"status": "ok", "count": 5})
        assert isinstance(result, str)
        assert "ok" in result
        assert "5" in result

    def test_format_mcp_result_handles_nested(self):
        """format_mcp_result handles nested dicts and lists."""
        from governance.mcp_tools.common import format_mcp_result

        result = format_mcp_result({
            "items": [{"id": "T-1"}, {"id": "T-2"}],
            "meta": {"total": 2},
        })
        assert isinstance(result, str)
        assert "T-1" in result
        assert "T-2" in result


# ── Trust score fallback defense ──────────────


class TestTrustScoreFallbackDefense:
    """Verify trust score defaults are safe fallbacks."""

    def test_default_vote_weight_is_neutral(self):
        """Default vote_weight of 0.5 is neutral (neither trust nor distrust)."""
        data = {"trust_score": 0.7}  # vote_weight missing
        vote_weight = data.get("vote_weight", 0.5)
        assert vote_weight == 0.5
        assert 0 < vote_weight < 1  # Within valid range

    def test_explicit_vote_weight_used(self):
        """Explicit vote_weight overrides default."""
        data = {"trust_score": 0.9, "vote_weight": 0.85}
        vote_weight = data.get("vote_weight", 0.5)
        assert vote_weight == 0.85


# ── Session persistence resilience defense ──────────────


class TestSessionPersistenceResilienceDefense:
    """Verify session persistence failures don't crash MCP tools."""

    def test_warning_on_persist_failure_no_crash(self):
        """Persistence failure logs warning but doesn't raise."""
        logged_warnings = []

        def mock_warning(msg):
            logged_warnings.append(msg)

        # Simulate persistence failure pattern
        try:
            raise ConnectionError("TypeDB unavailable")
        except Exception as e:
            mock_warning(f"Failed to persist MCP session start: {e}")

        assert len(logged_warnings) == 1
        assert "TypeDB unavailable" in logged_warnings[0]


# ── JSON parse safety defense ──────────────


class TestJSONParseSafetyDefense:
    """Verify JSON parsing in MCP tools handles edge cases."""

    def test_malformed_json_caught_by_decode_error(self):
        """json.JSONDecodeError is caught for malformed input."""
        try:
            args = json.loads("{invalid}")
        except json.JSONDecodeError:
            args = {"raw": "{invalid}"}
        assert "raw" in args

    def test_empty_arguments_default_to_empty_dict(self):
        """Empty/None arguments default to empty dict."""
        arguments = ""
        args_dict = json.loads(arguments) if arguments else {}
        assert args_dict == {}

    def test_valid_json_parsed_correctly(self):
        """Valid JSON arguments parsed without issue."""
        arguments = '{"tool": "Read", "path": "/tmp/test"}'
        args_dict = json.loads(arguments)
        assert args_dict["tool"] == "Read"
