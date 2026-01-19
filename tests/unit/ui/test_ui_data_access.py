"""
UI Data Access Function Tests.

Per DOC-SIZE-01-v1: Split from test_governance_ui.py.
Tests for data access pure functions.
"""
import pytest
from unittest.mock import patch, MagicMock

TYPEDB_CLIENT_MOCK_PATH = 'governance.mcp_tools.common.get_typedb_client'


class TestDataAccessFunctions:
    """Tests for data access pure functions."""

    @pytest.mark.unit
    def test_get_rules_importable(self):
        """get_rules function must be importable."""
        from agent.governance_ui import get_rules
        assert callable(get_rules)

    @pytest.mark.unit
    def test_get_rules_by_category_importable(self):
        """get_rules_by_category function must be importable."""
        from agent.governance_ui import get_rules_by_category
        assert callable(get_rules_by_category)

    @pytest.mark.unit
    def test_get_decisions_importable(self):
        """get_decisions function must be importable."""
        from agent.governance_ui import get_decisions
        assert callable(get_decisions)

    @pytest.mark.unit
    def test_get_sessions_importable(self):
        """get_sessions function must be importable."""
        from agent.governance_ui import get_sessions
        assert callable(get_sessions)

    @pytest.mark.unit
    def test_get_tasks_importable(self):
        """get_tasks function must be importable."""
        from agent.governance_ui import get_tasks
        assert callable(get_tasks)

    @pytest.mark.unit
    def test_search_evidence_importable(self):
        """search_evidence function must be importable."""
        from agent.governance_ui import search_evidence
        assert callable(search_evidence)

    @pytest.mark.unit
    @patch(TYPEDB_CLIENT_MOCK_PATH)
    def test_get_rules_returns_list(self, mock_client):
        """get_rules should return a list."""
        from agent.governance_ui import get_rules

        mock_tx = MagicMock()
        mock_tx.query.fetch.return_value = iter([])
        mock_client.return_value.__enter__.return_value.transaction.return_value.__enter__.return_value = mock_tx

        result = get_rules()
        assert isinstance(result, list)

    @pytest.mark.unit
    @patch(TYPEDB_CLIENT_MOCK_PATH)
    def test_get_decisions_returns_list(self, mock_client):
        """get_decisions should return a list."""
        from agent.governance_ui import get_decisions

        mock_tx = MagicMock()
        mock_tx.query.fetch.return_value = iter([])
        mock_client.return_value.__enter__.return_value.transaction.return_value.__enter__.return_value = mock_tx

        result = get_decisions()
        assert isinstance(result, list)
