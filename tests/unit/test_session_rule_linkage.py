"""Tests for Session-Rule Auto-Linkage (EPIC-RULES-V3 P5).

TDD RED: Tests for create_session_rule_link(), link_session_to_rule(),
session_bridge auto-linking, and rule ID extraction.

Created: 2026-03-25
"""
import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.unit
class TestCreateSessionRuleLink:
    """Tests for create_session_rule_link() in inference.py — idempotent insert."""

    def test_creates_relation_successfully(self):
        """Successfully creates session-applied-rule relation."""
        from governance.typedb.queries.rules.inference import RuleInferenceQueries

        obj = RuleInferenceQueries.__new__(RuleInferenceQueries)
        mock_tx = MagicMock()
        mock_tx.query.return_value.resolve.return_value = None
        mock_driver = MagicMock()
        mock_driver.transaction.return_value.__enter__ = MagicMock(return_value=mock_tx)
        mock_driver.transaction.return_value.__exit__ = MagicMock(return_value=False)
        obj._driver = mock_driver
        obj.database = "test-db"

        result = obj.create_session_rule_link("SESSION-2026-01-01-TEST", "RULE-001")
        assert result is True
        mock_tx.query.assert_called_once()
        mock_tx.commit.assert_called_once()

    def test_returns_false_on_failure(self):
        """Returns False if TypeDB insert fails."""
        from governance.typedb.queries.rules.inference import RuleInferenceQueries

        obj = RuleInferenceQueries.__new__(RuleInferenceQueries)
        mock_driver = MagicMock()
        mock_driver.transaction.side_effect = Exception("DB down")
        obj._driver = mock_driver
        obj.database = "test-db"

        result = obj.create_session_rule_link("SESSION-2026-01-01-TEST", "RULE-001")
        assert result is False

    def test_query_contains_not_exists_for_idempotency(self):
        """Insert query uses NOT EXISTS to prevent duplicate relations."""
        from governance.typedb.queries.rules.inference import RuleInferenceQueries

        obj = RuleInferenceQueries.__new__(RuleInferenceQueries)
        mock_tx = MagicMock()
        mock_tx.query.return_value.resolve.return_value = None
        mock_driver = MagicMock()
        mock_driver.transaction.return_value.__enter__ = MagicMock(return_value=mock_tx)
        mock_driver.transaction.return_value.__exit__ = MagicMock(return_value=False)
        obj._driver = mock_driver
        obj.database = "test-db"

        obj.create_session_rule_link("SESSION-2026-01-01-TEST", "RULE-001")

        query_arg = mock_tx.query.call_args[0][0]
        assert "not" in query_arg.lower()
        assert "session-applied-rule" in query_arg

    def test_escapes_special_characters(self):
        """Input with quotes/backslashes is safely escaped."""
        from governance.typedb.queries.rules.inference import RuleInferenceQueries

        obj = RuleInferenceQueries.__new__(RuleInferenceQueries)
        mock_tx = MagicMock()
        mock_tx.query.return_value.resolve.return_value = None
        mock_driver = MagicMock()
        mock_driver.transaction.return_value.__enter__ = MagicMock(return_value=mock_tx)
        mock_driver.transaction.return_value.__exit__ = MagicMock(return_value=False)
        obj._driver = mock_driver
        obj.database = "test-db"

        # Should not raise despite special chars
        result = obj.create_session_rule_link('SESSION-"test"', 'RULE-\\001')
        assert result is True


@pytest.mark.unit
class TestLinkSessionToRule:
    """Tests for link_session_to_rule() service function in rules_relations.py."""

    @patch("governance.services.rules_relations.get_client")
    def test_calls_client_create_session_rule_link(self, mock_get_client):
        """Service function calls client.create_session_rule_link()."""
        from governance.services.rules_relations import link_session_to_rule

        mock_client = MagicMock()
        mock_client.create_session_rule_link.return_value = True
        mock_get_client.return_value = mock_client

        result = link_session_to_rule("SESSION-2026-01-01-TEST", "RULE-001")
        assert result is True
        mock_client.create_session_rule_link.assert_called_once_with(
            "SESSION-2026-01-01-TEST", "RULE-001"
        )

    @patch("governance.services.rules_relations.get_client")
    def test_returns_false_no_client(self, mock_get_client):
        """Returns False when TypeDB not connected."""
        from governance.services.rules_relations import link_session_to_rule

        mock_get_client.return_value = None
        result = link_session_to_rule("SESSION-2026-01-01-TEST", "RULE-001")
        assert result is False

    @patch("governance.services.rules_relations.get_client")
    def test_returns_false_on_exception(self, mock_get_client):
        """Returns False on client exception."""
        from governance.services.rules_relations import link_session_to_rule

        mock_client = MagicMock()
        mock_client.create_session_rule_link.side_effect = Exception("DB error")
        mock_get_client.return_value = mock_client

        result = link_session_to_rule("SESSION-2026-01-01-TEST", "RULE-001")
        assert result is False


@pytest.mark.unit
class TestExtractRuleIdsFromText:
    """Tests for extract_rule_ids_from_text() — rule ID detection in tool args."""

    def test_extracts_legacy_rule_id(self):
        """Finds RULE-NNN pattern."""
        from governance.routes.chat.session_bridge import extract_rule_ids_from_text

        ids = extract_rule_ids_from_text("Checking RULE-001 and RULE-042 status")
        assert "RULE-001" in ids
        assert "RULE-042" in ids

    def test_extracts_semantic_rule_id(self):
        """Finds DOMAIN-SUB-NN-vN pattern."""
        from governance.routes.chat.session_bridge import extract_rule_ids_from_text

        ids = extract_rule_ids_from_text("Per SESSION-EVID-01-v1: evidence required")
        assert "SESSION-EVID-01-v1" in ids

    def test_empty_text_returns_empty(self):
        """Empty/None text returns empty list."""
        from governance.routes.chat.session_bridge import extract_rule_ids_from_text

        assert extract_rule_ids_from_text("") == []
        assert extract_rule_ids_from_text(None) == []

    def test_no_rule_ids_in_text(self):
        """Text without rule IDs returns empty."""
        from governance.routes.chat.session_bridge import extract_rule_ids_from_text

        assert extract_rule_ids_from_text("just some random text") == []

    def test_deduplicates_results(self):
        """Repeated rule IDs are deduplicated."""
        from governance.routes.chat.session_bridge import extract_rule_ids_from_text

        ids = extract_rule_ids_from_text("RULE-001 then RULE-001 again")
        assert ids.count("RULE-001") == 1


@pytest.mark.unit
class TestSessionBridgeAutoLink:
    """Tests for auto-linking rule references in record_chat_tool_call()."""

    @patch("governance.routes.chat.session_bridge._auto_link_rules")
    def test_record_tool_call_triggers_auto_link(self, mock_auto_link):
        """record_chat_tool_call calls _auto_link_rules with session_id, args, result."""
        from governance.routes.chat.session_bridge import record_chat_tool_call

        collector = MagicMock()
        collector.session_id = "SESSION-2026-01-01-TEST"
        collector.events = []

        record_chat_tool_call(
            collector=collector,
            tool_name="mcp__gov-core__rule_get",
            arguments={"rule_id": "RULE-001"},
            result="Rule found",
        )
        mock_auto_link.assert_called_once_with(
            "SESSION-2026-01-01-TEST",
            {"rule_id": "RULE-001"},
            "Rule found",
        )

    @patch("governance.services.rules_relations.link_session_to_rule")
    def test_auto_link_detects_and_links_rules(self, mock_link):
        """_auto_link_rules extracts rule IDs and calls link for each."""
        from governance.routes.chat.session_bridge import _auto_link_rules

        mock_link.return_value = True
        _auto_link_rules(
            "SESSION-2026-01-01-TEST",
            {"rule_id": "RULE-001"},
            "Per GOV-BICAM-01-v1: rule loaded",
        )
        # Should link both detected rule IDs
        assert mock_link.call_count >= 1

    @patch("governance.services.rules_relations.link_session_to_rule")
    def test_auto_link_no_rules_no_calls(self, mock_link):
        """No rule IDs in text = no link calls."""
        from governance.routes.chat.session_bridge import _auto_link_rules

        _auto_link_rules("SESSION-2026-01-01-TEST", {"key": "value"}, "no rules here")
        mock_link.assert_not_called()

    @patch("governance.services.rules_relations.link_session_to_rule")
    def test_auto_link_handles_exception_gracefully(self, mock_link):
        """Exceptions in auto-link don't propagate (non-blocking)."""
        from governance.routes.chat.session_bridge import _auto_link_rules

        mock_link.side_effect = Exception("DB down")
        # Should NOT raise
        _auto_link_rules("SESSION-2026-01-01-TEST", {"rule_id": "RULE-001"}, None)
