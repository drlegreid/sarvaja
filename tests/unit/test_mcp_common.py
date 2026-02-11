"""
Unit tests for MCP Common Utilities.

Per RULE-012: Tests for calculate_vote_weight, TrustScore, format_mcp_result,
warn_deprecated, log_monitor_event, and typedb_client context manager.
"""

import pytest
from unittest.mock import patch, MagicMock

from governance.mcp_tools.common import (
    calculate_vote_weight,
    TrustScore,
    warn_deprecated,
    log_monitor_event,
    TYPEDB_HOST,
    TYPEDB_PORT,
    DATABASE_NAME,
)


# ---------------------------------------------------------------------------
# calculate_vote_weight
# ---------------------------------------------------------------------------
class TestCalculateVoteWeight:
    """Tests for calculate_vote_weight() — RULE-011."""

    def test_high_trust_returns_one(self):
        assert calculate_vote_weight(0.9) == 1.0

    def test_exactly_half_returns_one(self):
        assert calculate_vote_weight(0.5) == 1.0

    def test_low_trust_returns_score(self):
        assert calculate_vote_weight(0.3) == 0.3

    def test_zero_trust(self):
        assert calculate_vote_weight(0.0) == 0.0

    def test_max_trust(self):
        assert calculate_vote_weight(1.0) == 1.0

    def test_just_below_threshold(self):
        assert calculate_vote_weight(0.49) == 0.49

    def test_negative_trust(self):
        assert calculate_vote_weight(-0.1) == -0.1


# ---------------------------------------------------------------------------
# TrustScore dataclass
# ---------------------------------------------------------------------------
class TestTrustScore:
    """Tests for TrustScore dataclass."""

    def test_creation(self):
        ts = TrustScore(
            agent_id="agent-1", agent_name="Code Agent",
            trust_score=0.85, compliance_rate=0.9,
            accuracy_rate=0.95, tenure_days=30, vote_weight=1.0,
        )
        assert ts.agent_id == "agent-1"
        assert ts.trust_score == 0.85
        assert ts.vote_weight == 1.0

    def test_all_fields(self):
        ts = TrustScore(
            agent_id="a", agent_name="n",
            trust_score=0.1, compliance_rate=0.2,
            accuracy_rate=0.3, tenure_days=5, vote_weight=0.1,
        )
        assert ts.compliance_rate == 0.2
        assert ts.accuracy_rate == 0.3
        assert ts.tenure_days == 5


# ---------------------------------------------------------------------------
# warn_deprecated
# ---------------------------------------------------------------------------
class TestWarnDeprecated:
    """Tests for warn_deprecated()."""

    @patch("governance.mcp_tools.common.logger")
    def test_logs_warning(self, mock_logger):
        warn_deprecated("old_tool", "new_tool")
        mock_logger.warning.assert_called_once()
        msg = mock_logger.warning.call_args[0][0]
        assert "old_tool" in msg
        assert "new_tool" in msg
        assert "deprecated" in msg.lower()


# ---------------------------------------------------------------------------
# log_monitor_event
# ---------------------------------------------------------------------------
class TestLogMonitorEvent:
    """Tests for log_monitor_event() lazy import wrapper."""

    def test_no_error_when_import_fails(self):
        """Should silently pass when monitoring is unavailable."""
        import sys
        with patch.dict(sys.modules, {"agent.governance_ui.data_access.monitoring": None}):
            # Should not raise
            log_monitor_event("test_event", "test_source")

    def test_passes_params(self):
        mock_log = MagicMock()
        with patch.dict("sys.modules", {
            "agent": MagicMock(),
            "agent.governance_ui": MagicMock(),
            "agent.governance_ui.data_access": MagicMock(),
            "agent.governance_ui.data_access.monitoring": MagicMock(log_monitor_event=mock_log),
        }):
            log_monitor_event("evt", "src", {"key": "val"}, severity="WARN")
            mock_log.assert_called_once_with(
                event_type="evt", source="src",
                details={"key": "val"}, severity="WARN",
            )

    def test_default_details_empty(self):
        mock_log = MagicMock()
        with patch.dict("sys.modules", {
            "agent": MagicMock(),
            "agent.governance_ui": MagicMock(),
            "agent.governance_ui.data_access": MagicMock(),
            "agent.governance_ui.data_access.monitoring": MagicMock(log_monitor_event=mock_log),
        }):
            log_monitor_event("evt", "src")
            call_kwargs = mock_log.call_args[1]
            assert call_kwargs["details"] == {}


# ---------------------------------------------------------------------------
# format_mcp_result
# ---------------------------------------------------------------------------
class TestFormatMcpResult:
    """Tests for format_mcp_result()."""

    def test_returns_string(self):
        """format_mcp_result should return a string."""
        from governance.mcp_tools.common import format_mcp_result
        with patch("governance.mcp_output.format_output", return_value='{"key": "val"}'):
            result = format_mcp_result({"key": "val"})
            assert isinstance(result, str)

    def test_passes_indent(self):
        """format_mcp_result should pass indent to format_output."""
        from governance.mcp_tools.common import format_mcp_result
        with patch("governance.mcp_output.format_output", return_value="{}") as mock_fmt:
            format_mcp_result({"k": "v"}, indent=4)
            _, kwargs = mock_fmt.call_args
            assert kwargs.get("indent") == 4


# ---------------------------------------------------------------------------
# typedb_client context manager
# ---------------------------------------------------------------------------
class TestTypeDBClient:
    """Tests for typedb_client() context manager."""

    @patch("governance.mcp_tools.common.get_typedb_client")
    def test_successful_connection(self, mock_get):
        from governance.mcp_tools.common import typedb_client
        client = MagicMock()
        client.connect.return_value = True
        mock_get.return_value = client

        with typedb_client() as c:
            assert c is client
        client.close.assert_called_once()

    @patch("governance.mcp_tools.common.get_typedb_client")
    def test_connection_failure(self, mock_get):
        from governance.mcp_tools.common import typedb_client
        client = MagicMock()
        client.connect.return_value = False
        mock_get.return_value = client

        with pytest.raises(ConnectionError):
            with typedb_client():
                pass
        client.close.assert_called_once()

    @patch("governance.mcp_tools.common.get_typedb_client")
    def test_close_called_on_exception(self, mock_get):
        from governance.mcp_tools.common import typedb_client
        client = MagicMock()
        client.connect.return_value = True
        mock_get.return_value = client

        with pytest.raises(ValueError):
            with typedb_client() as c:
                raise ValueError("test error")
        client.close.assert_called_once()


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
class TestConstants:
    """Tests for module-level constants."""

    def test_default_host(self):
        assert isinstance(TYPEDB_HOST, str)

    def test_default_port(self):
        assert TYPEDB_PORT == 1729

    def test_database_name(self):
        assert DATABASE_NAME == "sim-ai-governance"
