"""
Unit tests for CRUD operations on semantic-only rule IDs.

Per EPIC-GOV-RULES-V3 P7: Legacy ID Debt + Semantic-Only Rule CRUD.
Tests that rules.py service layer handles semantic-only IDs correctly.
"""

from unittest.mock import MagicMock, patch
from governance.services.rules import (
    get_rule,
    create_rule,
    update_rule,
    delete_rule,
    list_rules,
    resolve_rule,
)


def _make_mock_rule(rule_id="CONTAINER-TYPEDB-01-v1", name="TypeDB Container",
                    category="infrastructure", priority="MEDIUM",
                    status="ACTIVE", directive="Use TypeDB containers",
                    applicability="MANDATORY"):
    """Create a mock rule object."""
    rule = MagicMock()
    rule.id = rule_id
    rule.name = name
    rule.category = category
    rule.priority = priority
    rule.status = status
    rule.directive = directive
    rule.created_date = None
    rule.applicability = applicability
    return rule


class TestResolveRuleSemanticOnly:
    @patch("governance.services.rules.get_client")
    def test_resolve_semantic_only_id_finds_directly(self, mock_get_client):
        """Semantic-only IDs should resolve on first lookup, no legacy fallback."""
        mock_client = MagicMock()
        mock_rule = _make_mock_rule()
        mock_client.get_rule_by_id.return_value = mock_rule
        mock_get_client.return_value = mock_client

        actual_id, rule = resolve_rule(mock_client, "CONTAINER-TYPEDB-01-v1")

        assert actual_id == "CONTAINER-TYPEDB-01-v1"
        assert rule == mock_rule
        # Should only be called once — no legacy fallback
        mock_client.get_rule_by_id.assert_called_once_with("CONTAINER-TYPEDB-01-v1")

    @patch("governance.services.rules.get_client")
    def test_resolve_semantic_only_not_found_raises(self, mock_get_client):
        """Semantic-only IDs that don't exist should raise KeyError."""
        mock_client = MagicMock()
        mock_client.get_rule_by_id.return_value = None
        mock_get_client.return_value = mock_client

        import pytest
        with pytest.raises(KeyError, match="CONTAINER-TYPEDB-01-v1"):
            resolve_rule(mock_client, "CONTAINER-TYPEDB-01-v1")


class TestCreateRuleSemanticOnly:
    @patch("governance.services.rules.log_event")
    @patch("governance.services.rules._monitor")
    @patch("governance.services.rules.record_audit")
    @patch("governance.services.rules.get_client")
    def test_create_rule_with_semantic_only_id(self, mock_get_client,
                                                mock_audit, mock_monitor,
                                                mock_log_event):
        mock_client = MagicMock()
        mock_client.get_rule_by_id.return_value = None  # Doesn't exist yet
        mock_rule = _make_mock_rule()
        mock_client.create_rule.return_value = mock_rule
        mock_get_client.return_value = mock_client

        result = create_rule(
            rule_id="CONTAINER-TYPEDB-01-v1",
            name="TypeDB Container",
            category="infrastructure",
        )

        assert result["id"] == "CONTAINER-TYPEDB-01-v1"
        mock_client.create_rule.assert_called_once()


class TestGetRuleSemanticOnly:
    @patch("governance.services.rules.get_rule_linkage_counts")
    @patch("governance.services.rules.get_rule_document_paths")
    @patch("governance.services.rules.get_client")
    def test_get_rule_by_semantic_only_id(self, mock_get_client,
                                          mock_doc_paths, mock_linkage):
        mock_client = MagicMock()
        mock_rule = _make_mock_rule()
        mock_client.get_rule_by_id.return_value = mock_rule
        mock_get_client.return_value = mock_client
        mock_doc_paths.return_value = {}
        mock_linkage.return_value = {}

        result = get_rule("CONTAINER-TYPEDB-01-v1")

        assert result["id"] == "CONTAINER-TYPEDB-01-v1"
        mock_client.get_rule_by_id.assert_called_once_with("CONTAINER-TYPEDB-01-v1")


class TestUpdateRuleSemanticOnly:
    @patch("governance.services.rules.get_rule_document_paths")
    @patch("governance.services.rules.log_event")
    @patch("governance.services.rules._monitor")
    @patch("governance.services.rules.record_audit")
    @patch("governance.services.rules.get_client")
    def test_update_rule_semantic_only_id(self, mock_get_client,
                                          mock_audit, mock_monitor,
                                          mock_log_event, mock_doc_paths):
        mock_client = MagicMock()
        mock_rule = _make_mock_rule()
        mock_client.get_rule_by_id.return_value = mock_rule
        mock_client.update_rule.return_value = mock_rule
        mock_get_client.return_value = mock_client
        mock_doc_paths.return_value = {}

        result = update_rule("CONTAINER-TYPEDB-01-v1", name="Updated Name")

        assert result["id"] == "CONTAINER-TYPEDB-01-v1"


class TestDeleteRuleSemanticOnly:
    @patch("governance.services.rules.log_event")
    @patch("governance.services.rules._monitor")
    @patch("governance.services.rules.record_audit")
    @patch("governance.services.rules.get_client")
    def test_delete_rule_semantic_only_id(self, mock_get_client,
                                          mock_audit, mock_monitor,
                                          mock_log_event):
        mock_client = MagicMock()
        mock_rule = _make_mock_rule()
        mock_client.get_rule_by_id.return_value = mock_rule
        mock_client.delete_rule.return_value = True
        mock_get_client.return_value = mock_client

        result = delete_rule("CONTAINER-TYPEDB-01-v1")

        assert result is True


class TestListRulesIncludesSemanticOnly:
    @patch("governance.services.rules.get_rule_linkage_counts")
    @patch("governance.services.rules.get_rule_document_paths")
    @patch("governance.services.rules.get_client")
    def test_list_rules_includes_semantic_only(self, mock_get_client,
                                               mock_doc_paths, mock_linkage):
        mock_client = MagicMock()
        mock_rules = [
            _make_mock_rule("RULE-001", "Evidence Rule"),
            _make_mock_rule("CONTAINER-TYPEDB-01-v1", "TypeDB Container"),
        ]
        mock_client.get_all_rules.return_value = mock_rules
        mock_get_client.return_value = mock_client
        mock_doc_paths.return_value = {}
        mock_linkage.return_value = {}

        result = list_rules()

        ids = [item["id"] for item in result["items"]]
        assert "CONTAINER-TYPEDB-01-v1" in ids
