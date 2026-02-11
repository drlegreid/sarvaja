"""
Unit tests for Rule-Document TypeDB Operations.

Per P10.8: Tests for _get_document, _insert_document,
_check_document_rule_relation, _create_document_rule_relation.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from governance.rule_linker_db import (
    _get_document,
    _insert_document,
    _check_document_rule_relation,
    _create_document_rule_relation,
)
from governance.rule_linker_scan import RuleDocument


# ---------------------------------------------------------------------------
# _get_document
# ---------------------------------------------------------------------------
class TestGetDocument:
    """Tests for _get_document()."""

    def test_found(self):
        client = MagicMock()
        client.execute_query.return_value = [{"id": "DOC-1"}]
        result = _get_document(client, "DOC-1")
        assert result == {"id": "DOC-1"}

    def test_not_found(self):
        client = MagicMock()
        client.execute_query.return_value = []
        result = _get_document(client, "DOC-999")
        assert result is None

    def test_query_exception(self):
        client = MagicMock()
        client.execute_query.side_effect = Exception("DB error")
        result = _get_document(client, "DOC-1")
        assert result is None

    def test_query_contains_document_id(self):
        client = MagicMock()
        client.execute_query.return_value = []
        _get_document(client, "DOC-TEST-001")
        query = client.execute_query.call_args[0][0]
        assert "DOC-TEST-001" in query


# ---------------------------------------------------------------------------
# _insert_document
# ---------------------------------------------------------------------------
class TestInsertDocument:
    """Tests for _insert_document()."""

    def _make_doc(self, **kw):
        defaults = {
            "document_id": "DOC-001",
            "title": "Test Document",
            "path": "docs/rules/leaf/TEST.md",
            "document_type": "leaf",
            "storage": "filesystem",
            "rule_ids": ["RULE-001"],
            "last_modified": datetime(2026, 2, 11, 10, 0, 0),
        }
        defaults.update(kw)
        return RuleDocument(**defaults)

    def test_success(self):
        client = MagicMock()
        doc = self._make_doc()
        success, error = _insert_document(client, doc)
        assert success is True
        assert error == ""
        client._execute_write.assert_called_once()

    def test_failure(self):
        client = MagicMock()
        client._execute_write.side_effect = Exception("Insert failed")
        doc = self._make_doc()
        success, error = _insert_document(client, doc)
        assert success is False
        assert "Insert failed" in error

    def test_escapes_quotes_in_title(self):
        client = MagicMock()
        doc = self._make_doc(title='Rule "test" doc')
        _insert_document(client, doc)
        query = client._execute_write.call_args[0][0]
        assert '\\"test\\"' in query

    def test_escapes_backslashes_in_path(self):
        client = MagicMock()
        doc = self._make_doc(path="docs\\rules\\test.md")
        _insert_document(client, doc)
        query = client._execute_write.call_args[0][0]
        assert "\\\\" in query

    def test_no_last_modified_uses_now(self):
        client = MagicMock()
        doc = self._make_doc(last_modified=None)
        _insert_document(client, doc)
        query = client._execute_write.call_args[0][0]
        # Should still have a date in the query
        assert "has last-modified" in query

    def test_query_contains_all_fields(self):
        client = MagicMock()
        doc = self._make_doc()
        _insert_document(client, doc)
        query = client._execute_write.call_args[0][0]
        assert "document-id" in query
        assert "document-title" in query
        assert "document-path" in query
        assert "document-type" in query
        assert "document-storage" in query
        assert "last-modified" in query


# ---------------------------------------------------------------------------
# _check_document_rule_relation
# ---------------------------------------------------------------------------
class TestCheckDocumentRuleRelation:
    """Tests for _check_document_rule_relation()."""

    def test_exists(self):
        client = MagicMock()
        client.execute_query.return_value = [{"d": "doc", "r": "rule"}]
        assert _check_document_rule_relation(client, "DOC-1", "RULE-001") is True

    def test_not_exists(self):
        client = MagicMock()
        client.execute_query.return_value = []
        assert _check_document_rule_relation(client, "DOC-1", "RULE-001") is False

    def test_exception_returns_false(self):
        client = MagicMock()
        client.execute_query.side_effect = Exception("DB error")
        assert _check_document_rule_relation(client, "DOC-1", "RULE-001") is False

    def test_query_contains_both_ids(self):
        client = MagicMock()
        client.execute_query.return_value = []
        _check_document_rule_relation(client, "DOC-X", "RULE-Y")
        query = client.execute_query.call_args[0][0]
        assert "DOC-X" in query
        assert "RULE-Y" in query


# ---------------------------------------------------------------------------
# _create_document_rule_relation
# ---------------------------------------------------------------------------
class TestCreateDocumentRuleRelation:
    """Tests for _create_document_rule_relation()."""

    def test_success(self):
        client = MagicMock()
        success, error = _create_document_rule_relation(client, "DOC-1", "RULE-001")
        assert success is True
        assert error == ""

    def test_failure(self):
        client = MagicMock()
        client._execute_write.side_effect = Exception("Relation error")
        success, error = _create_document_rule_relation(client, "DOC-1", "RULE-001")
        assert success is False
        assert "Relation error" in error

    def test_query_structure(self):
        client = MagicMock()
        _create_document_rule_relation(client, "DOC-1", "RULE-001")
        query = client._execute_write.call_args[0][0]
        assert "match" in query
        assert "insert" in query
        assert "document-references-rule" in query
        assert "referencing-document" in query
        assert "referenced-rule" in query
