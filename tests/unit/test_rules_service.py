"""
Unit tests for Rules Service Layer.

Per DOC-SIZE-01-v1: Tests for services/rules.py module.
Tests: _monitor, _get_client_or_raise, get_semantic_id, resolve_rule,
       rule_to_response_dict, list_rules, get_rule, create_rule,
       update_rule, delete_rule.
"""

from unittest.mock import patch, MagicMock
from datetime import datetime

import pytest

from governance.services.rules import (
    _monitor,
    _get_client_or_raise,
    get_semantic_id,
    resolve_rule,
    rule_to_response_dict,
    list_rules,
    get_rule,
    create_rule,
    update_rule,
    delete_rule,
)


def _make_rule(rule_id="RULE-001", name="Test", category="GOV",
               priority="HIGH", status="ACTIVE", directive="Do X",
               created_date=None, applicability=None):
    r = MagicMock()
    r.id = rule_id
    r.name = name
    r.category = category
    r.priority = priority
    r.status = status
    r.directive = directive
    r.created_date = created_date
    r.applicability = applicability
    return r


_P_CLIENT = "governance.services.rules.get_client"
_P_AUDIT = "governance.services.rules.record_audit"
_P_EVENT = "governance.services.rules.log_event"
_P_DOC_PATHS = "governance.services.rules.get_rule_document_paths"
_P_LINKAGE = "governance.services.rules.get_rule_linkage_counts"


class TestMonitor:
    def test_no_error_on_import_failure(self):
        # Should silently pass even if monitoring unavailable
        with patch("governance.services.rules.log_monitor_event",
                   side_effect=ImportError("no module"), create=True):
            _monitor("test", "RULE-001")


class TestGetClientOrRaise:
    @patch(_P_CLIENT, return_value=MagicMock())
    def test_success(self, _):
        client = _get_client_or_raise()
        assert client is not None

    @patch(_P_CLIENT, return_value=None)
    def test_raises(self, _):
        with pytest.raises(ConnectionError, match="TypeDB not connected"):
            _get_client_or_raise()


class TestGetSemanticId:
    def test_found(self):
        with patch.dict("governance.services.rules.LEGACY_TO_SEMANTIC",
                        {"RULE-001": "GOV-SESSION-01-v1"}):
            assert get_semantic_id("RULE-001") == "GOV-SESSION-01-v1"

    def test_not_found(self):
        assert get_semantic_id("NONEXISTENT-999") is None


class TestResolveRule:
    def test_direct_match(self):
        client = MagicMock()
        rule = _make_rule()
        client.get_rule_by_id.return_value = rule
        actual_id, result = resolve_rule(client, "RULE-001")
        assert actual_id == "RULE-001"
        assert result is rule

    def test_legacy_fallback(self):
        client = MagicMock()
        rule = _make_rule(rule_id="RULE-001-LEGACY")
        client.get_rule_by_id.side_effect = [None, rule]
        with patch("governance.services.rules.normalize_rule_id",
                   return_value="RULE-001-LEGACY"):
            actual_id, result = resolve_rule(client, "RULE-001")
        assert actual_id == "RULE-001-LEGACY"

    def test_not_found(self):
        client = MagicMock()
        client.get_rule_by_id.return_value = None
        with patch("governance.services.rules.normalize_rule_id",
                   return_value="RULE-001"):
            with pytest.raises(KeyError, match="not found"):
                resolve_rule(client, "RULE-001")


class TestRuleToResponseDict:
    def test_basic(self):
        rule = _make_rule()
        result = rule_to_response_dict(rule)
        assert result["id"] == "RULE-001"
        assert result["name"] == "Test"
        assert result["linked_tasks_count"] == 0

    def test_with_doc_path(self):
        rule = _make_rule()
        result = rule_to_response_dict(rule, doc_path="/docs/rules/leaf/GOV.md")
        assert result["document_path"] == "/docs/rules/leaf/GOV.md"

    def test_with_linkage(self):
        rule = _make_rule()
        result = rule_to_response_dict(
            rule, linkage_counts={"tasks": 3, "sessions": 2}
        )
        assert result["linked_tasks_count"] == 3
        assert result["linked_sessions_count"] == 2

    def test_with_created_date(self):
        dt = datetime(2026, 1, 15, 10, 0, 0)
        rule = _make_rule(created_date=dt)
        result = rule_to_response_dict(rule)
        assert result["created_date"] == dt.isoformat()


class TestListRules:
    @patch(_P_LINKAGE, return_value={})
    @patch(_P_DOC_PATHS, return_value={})
    @patch(_P_CLIENT)
    def test_all_rules(self, mock_client, _, __):
        client = MagicMock()
        client.get_all_rules.return_value = [_make_rule()]
        mock_client.return_value = client
        result = list_rules()
        assert result["total"] == 1
        assert len(result["items"]) == 1

    @patch(_P_LINKAGE, return_value={})
    @patch(_P_DOC_PATHS, return_value={})
    @patch(_P_CLIENT)
    def test_active_filter(self, mock_client, _, __):
        client = MagicMock()
        client.get_active_rules.return_value = [_make_rule()]
        mock_client.return_value = client
        result = list_rules(status="ACTIVE")
        client.get_active_rules.assert_called_once()

    @patch(_P_LINKAGE, return_value={})
    @patch(_P_DOC_PATHS, return_value={})
    @patch(_P_CLIENT)
    def test_category_filter(self, mock_client, _, __):
        client = MagicMock()
        client.get_rules_by_category.return_value = [_make_rule()]
        mock_client.return_value = client
        result = list_rules(category="GOV")
        client.get_rules_by_category.assert_called_with("GOV")

    @patch(_P_LINKAGE, return_value={})
    @patch(_P_DOC_PATHS, return_value={})
    @patch(_P_CLIENT)
    def test_pagination(self, mock_client, _, __):
        client = MagicMock()
        client.get_all_rules.return_value = [_make_rule(rule_id=f"R-{i}") for i in range(5)]
        mock_client.return_value = client
        result = list_rules(offset=2, limit=2)
        assert result["total"] == 5
        assert len(result["items"]) == 2
        assert result["has_more"] is True

    @patch(_P_CLIENT, return_value=None)
    def test_no_client(self, _):
        with pytest.raises(ConnectionError):
            list_rules()


class TestGetRule:
    @patch(_P_DOC_PATHS, return_value={})
    @patch(_P_CLIENT)
    def test_found(self, mock_client, _):
        client = MagicMock()
        rule = _make_rule()
        client.get_rule_by_id.return_value = rule
        mock_client.return_value = client
        result = get_rule("RULE-001")
        assert result["id"] == "RULE-001"

    @patch(_P_CLIENT)
    def test_not_found(self, mock_client):
        client = MagicMock()
        client.get_rule_by_id.return_value = None
        mock_client.return_value = client
        with patch("governance.services.rules.normalize_rule_id",
                   return_value="RULE-001"):
            with pytest.raises(KeyError):
                get_rule("RULE-001")


class TestCreateRule:
    @patch(_P_EVENT)
    @patch(_P_AUDIT)
    @patch(_P_CLIENT)
    def test_success(self, mock_client, _, __):
        client = MagicMock()
        client.get_rule_by_id.return_value = None
        created = _make_rule()
        client.create_rule.return_value = created
        mock_client.return_value = client
        result = create_rule("RULE-NEW", name="New Rule")
        assert result["id"] == "RULE-001"

    @patch(_P_CLIENT)
    def test_duplicate(self, mock_client):
        client = MagicMock()
        client.get_rule_by_id.return_value = _make_rule()
        mock_client.return_value = client
        with pytest.raises(ValueError, match="already exists"):
            create_rule("RULE-001")

    @patch(_P_CLIENT)
    def test_create_failure(self, mock_client):
        client = MagicMock()
        client.get_rule_by_id.return_value = None
        client.create_rule.return_value = None
        mock_client.return_value = client
        with pytest.raises(RuntimeError, match="Failed to create"):
            create_rule("RULE-NEW")


class TestUpdateRule:
    @patch(_P_DOC_PATHS, return_value={})
    @patch(_P_EVENT)
    @patch(_P_AUDIT)
    @patch(_P_CLIENT)
    def test_success(self, mock_client, _, __, ___):
        client = MagicMock()
        rule = _make_rule()
        client.get_rule_by_id.return_value = rule
        client.update_rule.return_value = rule
        mock_client.return_value = client
        result = update_rule("RULE-001", name="Updated")
        assert result["id"] == "RULE-001"

    @patch(_P_CLIENT)
    def test_not_found(self, mock_client):
        client = MagicMock()
        client.get_rule_by_id.return_value = None
        mock_client.return_value = client
        with patch("governance.services.rules.normalize_rule_id",
                   return_value="RULE-001"):
            with pytest.raises(KeyError):
                update_rule("RULE-001", name="X")

    @patch(_P_CLIENT)
    def test_update_failure(self, mock_client):
        client = MagicMock()
        client.get_rule_by_id.return_value = _make_rule()
        client.update_rule.return_value = None
        mock_client.return_value = client
        with pytest.raises(RuntimeError, match="Failed to update"):
            update_rule("RULE-001", name="X")


class TestDeleteRule:
    @patch(_P_EVENT)
    @patch(_P_AUDIT)
    @patch(_P_CLIENT)
    def test_success(self, mock_client, _, __):
        client = MagicMock()
        client.get_rule_by_id.return_value = _make_rule()
        client.delete_rule.return_value = True
        mock_client.return_value = client
        assert delete_rule("RULE-001") is True

    @patch(_P_EVENT)
    @patch(_P_AUDIT)
    @patch(_P_CLIENT)
    def test_delete_failure(self, mock_client, _, __):
        client = MagicMock()
        client.get_rule_by_id.return_value = _make_rule()
        client.delete_rule.return_value = False
        mock_client.return_value = client
        assert delete_rule("RULE-001") is False
