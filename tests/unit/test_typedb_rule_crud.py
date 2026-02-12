"""
Unit tests for TypeDB Rule CRUD Operations.

Per DOC-SIZE-01-v1: Tests for typedb/queries/rules/crud.py module.
Tests: create_rule, update_rule, deprecate_rule, delete_rule.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

from governance.typedb.queries.rules.crud import RuleCRUDOperations

_mock_typedb_driver = MagicMock()
_mock_typedb_driver.TransactionType.WRITE = "write"
_mock_typedb_driver.TransactionType.READ = "read"


@pytest.fixture(autouse=True)
def _mock_typedb():
    with patch.dict(sys.modules, {
        "typedb": MagicMock(),
        "typedb.driver": _mock_typedb_driver,
    }):
        yield


def _make_rule(rule_id="RULE-001", name="Test", category="governance",
               priority="HIGH", directive="Do X", status="ACTIVE",
               rule_type=None, semantic_id=None, applicability=None):
    r = MagicMock()
    r.id = rule_id
    r.name = name
    r.category = category
    r.priority = priority
    r.directive = directive
    r.status = status
    r.rule_type = rule_type
    r.semantic_id = semantic_id
    r.applicability = applicability
    r.description = name
    return r


class _ConcreteRuleCRUD(RuleCRUDOperations):
    def __init__(self):
        self._execute_query = MagicMock(return_value=[])
        self._execute_write = MagicMock()
        self._driver = MagicMock()
        self.database = "test-db"
        self._mock_rules = {}

    def get_rule_by_id(self, rule_id):
        return self._mock_rules.get(rule_id)

    def archive_rule(self, rule_id, reason=None):
        pass

    def _setup_tx(self):
        tx = MagicMock()
        tx.query.return_value = MagicMock(resolve=MagicMock())
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=tx)
        ctx.__exit__ = MagicMock(return_value=False)
        self._driver.transaction.return_value = ctx
        return tx


@pytest.fixture()
def crud():
    return _ConcreteRuleCRUD()


class TestCreateRule:
    def test_success(self, crud):
        created = _make_rule()
        # First call: get_rule_by_id returns None (not exists)
        # After insert: get_rule_by_id returns the rule
        crud._mock_rules["RULE-001"] = None  # doesn't exist yet
        crud.get_rule_by_id = MagicMock(side_effect=[None, created])
        result = crud.create_rule("RULE-001", "Test", "governance", "HIGH", "Do X")
        assert result is not None
        assert result.id == "RULE-001"
        crud._execute_write.assert_called_once()

    def test_invalid_category(self, crud):
        with pytest.raises(ValueError, match="Invalid category"):
            crud.create_rule("R-1", "Test", "INVALID", "HIGH", "Do X")

    def test_invalid_priority(self, crud):
        with pytest.raises(ValueError, match="Invalid priority"):
            crud.create_rule("R-1", "Test", "governance", "INVALID", "Do X")

    def test_invalid_status(self, crud):
        with pytest.raises(ValueError, match="Invalid status"):
            crud.create_rule("R-1", "Test", "governance", "HIGH", "Do X", status="INVALID")

    def test_invalid_rule_type(self, crud):
        with pytest.raises(ValueError, match="Invalid rule_type"):
            crud.create_rule("R-1", "Test", "governance", "HIGH", "Do X", rule_type="INVALID")

    def test_already_exists(self, crud):
        crud._mock_rules["RULE-001"] = _make_rule()
        with pytest.raises(ValueError, match="already exists"):
            crud.create_rule("RULE-001", "Test", "governance", "HIGH", "Do X")

    def test_with_rule_type(self, crud):
        crud.get_rule_by_id = MagicMock(side_effect=[None, _make_rule()])
        result = crud.create_rule("R-1", "Test", "governance", "HIGH", "Do X",
                                  rule_type="FOUNDATIONAL")
        query = crud._execute_write.call_args[0][0]
        assert "FOUNDATIONAL" in query


class TestUpdateRule:
    def test_not_found(self, crud):
        with pytest.raises(ValueError, match="not found"):
            crud.update_rule("NONEXISTENT", name="X")

    def test_no_changes(self, crud):
        crud._mock_rules["RULE-001"] = _make_rule()
        result = crud.update_rule("RULE-001")
        assert result is not None

    def test_update_name(self, crud):
        crud._mock_rules["RULE-001"] = _make_rule()
        crud._setup_tx()
        result = crud.update_rule("RULE-001", name="New Name")
        assert result is not None

    def test_update_status(self, crud):
        crud._mock_rules["RULE-001"] = _make_rule(status="DRAFT")
        crud._setup_tx()
        result = crud.update_rule("RULE-001", status="ACTIVE")
        assert result is not None

    def test_add_new_rule_type(self, crud):
        crud._mock_rules["RULE-001"] = _make_rule(rule_type=None)
        crud._setup_tx()
        result = crud.update_rule("RULE-001", rule_type="OPERATIONAL")
        assert result is not None

    def test_invalid_applicability(self, crud):
        crud._mock_rules["RULE-001"] = _make_rule()
        with pytest.raises(ValueError, match="Invalid applicability"):
            crud.update_rule("RULE-001", applicability="INVALID")

    def test_valid_applicability(self, crud):
        crud._mock_rules["RULE-001"] = _make_rule(applicability=None)
        crud._setup_tx()
        result = crud.update_rule("RULE-001", applicability="MANDATORY")
        assert result is not None


class TestDeprecateRule:
    def test_deprecate(self, crud):
        crud._mock_rules["RULE-001"] = _make_rule(status="ACTIVE")
        crud._setup_tx()
        result = crud.deprecate_rule("RULE-001")
        assert result is not None


class TestDeleteRule:
    def test_success(self, crud):
        crud._mock_rules["RULE-001"] = _make_rule()
        crud._setup_tx()
        result = crud.delete_rule("RULE-001")
        assert result is True

    def test_not_found(self, crud):
        result = crud.delete_rule("NONEXISTENT")
        assert result is False

    def test_archive_failure_still_deletes(self, crud):
        crud._mock_rules["RULE-001"] = _make_rule()
        crud.archive_rule = MagicMock(side_effect=Exception("archive failed"))
        crud._setup_tx()
        result = crud.delete_rule("RULE-001")
        assert result is True

    def test_no_archive(self, crud):
        crud._mock_rules["RULE-001"] = _make_rule()
        crud._setup_tx()
        crud.archive_rule = MagicMock()
        result = crud.delete_rule("RULE-001", archive=False)
        assert result is True
        crud.archive_rule.assert_not_called()
