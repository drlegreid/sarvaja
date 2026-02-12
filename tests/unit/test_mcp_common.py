"""
Unit tests for MCP Tools Common Utilities.

Per DOC-SIZE-01-v1: Tests for mcp_tools/common.py module.
Tests: TrustScore, calculate_vote_weight, log_monitor_event,
       format_mcp_result, warn_deprecated, typedb_client context manager.
"""

import logging
import pytest
from unittest.mock import patch, MagicMock

from governance.mcp_tools.common import (
    TrustScore,
    calculate_vote_weight,
    log_monitor_event,
    warn_deprecated,
    TYPEDB_HOST,
    TYPEDB_PORT,
    DATABASE_NAME,
)


class TestTrustScore:
    def test_basic(self):
        ts = TrustScore(
            agent_id="A-1", agent_name="Test",
            trust_score=0.85, compliance_rate=0.9,
            accuracy_rate=0.95, tenure_days=30, vote_weight=1.0,
        )
        assert ts.agent_id == "A-1"
        assert ts.vote_weight == 1.0


class TestCalculateVoteWeight:
    def test_high_trust(self):
        assert calculate_vote_weight(0.9) == 1.0
        assert calculate_vote_weight(0.5) == 1.0

    def test_low_trust(self):
        assert calculate_vote_weight(0.3) == 0.3
        assert calculate_vote_weight(0.0) == 0.0

    def test_boundary(self):
        assert calculate_vote_weight(0.5) == 1.0
        assert calculate_vote_weight(0.49) == 0.49


class TestLogMonitorEvent:
    @patch("governance.mcp_tools.common.logger")
    def test_import_failure_silent(self, mock_logger):
        # Should not raise even if monitoring is unavailable
        with patch.dict("sys.modules", {"agent.governance_ui.data_access.monitoring": None}):
            log_monitor_event("test", "source")


class TestWarnDeprecated:
    def test_logs_warning(self, caplog):
        with caplog.at_level(logging.WARNING, logger="governance.mcp_tools.common"):
            warn_deprecated("old_tool", "new_tool")
        assert "old_tool" in caplog.text
        assert "new_tool" in caplog.text
        assert "deprecated" in caplog.text.lower()


class TestConstants:
    def test_defaults(self):
        assert isinstance(TYPEDB_HOST, str)
        assert isinstance(TYPEDB_PORT, int)
        assert DATABASE_NAME == "sim-ai-governance"


class TestTypedbClientContextManager:
    @patch("governance.mcp_tools.common.get_typedb_client")
    def test_success(self, mock_get):
        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_get.return_value = mock_client

        from governance.mcp_tools.common import typedb_client
        with typedb_client() as client:
            assert client is mock_client
        mock_client.close.assert_called_once()

    @patch("governance.mcp_tools.common.get_typedb_client")
    def test_connect_failure(self, mock_get):
        mock_client = MagicMock()
        mock_client.connect.return_value = False
        mock_get.return_value = mock_client

        from governance.mcp_tools.common import typedb_client
        with pytest.raises(ConnectionError):
            with typedb_client():
                pass
        mock_client.close.assert_called_once()
