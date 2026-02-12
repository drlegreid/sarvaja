"""
Unit tests for TypeDB Rule CRUD Operations.

Batch 128: Tests for governance/typedb/queries/rules/crud.py
- create_rule: validation, escaping, TypeDB insert, existence check
- update_rule: attribute updates, new attrs, no-change optimization
- deprecate_rule: delegation to update_rule
- delete_rule: archive + delete
"""

import sys
from unittest.mock import patch, MagicMock

import pytest


_MOD = "governance.typedb.queries.rules.crud"


def _make_typedb_mocks():
    mock_typedb = MagicMock()
    mock_typedb.TransactionType = MagicMock()
    mock_typedb.TransactionType.WRITE = "WRITE"
    return mock_typedb


def _make_tx():
    mock_tx = MagicMock()
    mock_tx.query.return_value.resolve.return_value = None
    mock_tx.__enter__ = MagicMock(return_value=mock_tx)
    mock_tx.__exit__ = MagicMock(return_value=False)
    return mock_tx


def _make_rule(rule_id="RULE-001", name="Test Rule", category="governance",
               priority="HIGH", status="ACTIVE", directive="Do the thing",
               rule_type=None, semantic_id=None, applicability=None):
    rule = MagicMock()
    rule.id = rule_id
    rule.name = name
    rule.category = category
    rule.priority = priority
    rule.status = status
    rule.directive = directive
    rule.rule_type = rule_type
    rule.semantic_id = semantic_id
    rule.applicability = applicability
    return rule


def _make_client(existing_rule=None):
    from governance.typedb.queries.rules.crud import RuleCRUDOperations

    class MockClient(RuleCRUDOperations):
        pass

    client = MockClient()
    client.database = "test-db"
    client._driver = MagicMock()
    client._execute_query = MagicMock(return_value=[])
    client._execute_write = MagicMock()
    client.get_rule_by_id = MagicMock(return_value=existing_rule)
    client.archive_rule = MagicMock()
    return client


# ── create_rule ──────────────────────────────────────────


class TestCreateRule:

    def test_successful_create(self):
        client = _make_client()
        created = _make_rule()
        client.get_rule_by_id = MagicMock(side_effect=[None, created])

        result = client.create_rule("RULE-001", "Test", "governance", "HIGH", "Do X")
        assert result is created
        client._execute_write.assert_called_once()

    def test_invalid_category_raises(self):
        client = _make_client()
        with pytest.raises(ValueError, match="Invalid category"):
            client.create_rule("R-1", "Test", "INVALID_CAT", "HIGH", "text")

    def test_invalid_priority_raises(self):
        client = _make_client()
        with pytest.raises(ValueError, match="Invalid priority"):
            client.create_rule("R-1", "Test", "governance", "ULTRA", "text")

    def test_invalid_status_raises(self):
        client = _make_client()
        with pytest.raises(ValueError, match="Invalid status"):
            client.create_rule("R-1", "Test", "governance", "HIGH", "text", status="BANANA")

    def test_invalid_rule_type_raises(self):
        client = _make_client()
        with pytest.raises(ValueError, match="Invalid rule_type"):
            client.create_rule("R-1", "Test", "governance", "HIGH", "text", rule_type="INVALID")

    def test_existing_rule_raises(self):
        client = _make_client(existing_rule=_make_rule())
        with pytest.raises(ValueError, match="already exists"):
            client.create_rule("RULE-001", "Test", "governance", "HIGH", "text")

    def test_escapes_directive(self):
        client = _make_client()
        client.get_rule_by_id = MagicMock(side_effect=[None, _make_rule()])

        client.create_rule("R-1", "Test", "governance", "HIGH", 'Quote "this"')
        query = client._execute_write.call_args[0][0]
        assert '\\"this\\"' in query

    def test_includes_rule_type(self):
        client = _make_client()
        client.get_rule_by_id = MagicMock(side_effect=[None, _make_rule()])

        client.create_rule("R-1", "Test", "governance", "HIGH", "text", rule_type="FOUNDATIONAL")
        query = client._execute_write.call_args[0][0]
        assert 'rule-type "FOUNDATIONAL"' in query

    def test_no_rule_type(self):
        client = _make_client()
        client.get_rule_by_id = MagicMock(side_effect=[None, _make_rule()])

        client.create_rule("R-1", "Test", "governance", "HIGH", "text")
        query = client._execute_write.call_args[0][0]
        assert "rule-type" not in query


# ── update_rule ──────────────────────────────────────────


class TestUpdateRule:

    def test_not_found_raises(self):
        client = _make_client(existing_rule=None)
        with pytest.raises(ValueError, match="not found"):
            client.update_rule("MISSING", name="New Name")

    def test_no_changes_returns_existing(self):
        existing = _make_rule()
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client(existing_rule=existing)
            result = client.update_rule("RULE-001")
            assert result is existing

    def test_update_name(self):
        existing = _make_rule()
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client(existing_rule=existing)
            mock_tx = _make_tx()
            client._driver.transaction.return_value = mock_tx
            # After update, return updated rule
            updated = _make_rule(name="New Name")
            client.get_rule_by_id = MagicMock(side_effect=[existing, updated])

            result = client.update_rule("RULE-001", name="New Name")
            assert result is updated
            mock_tx.commit.assert_called_once()

    def test_update_status(self):
        existing = _make_rule()
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client(existing_rule=existing)
            mock_tx = _make_tx()
            client._driver.transaction.return_value = mock_tx
            client.get_rule_by_id = MagicMock(side_effect=[existing, existing])

            client.update_rule("RULE-001", status="DEPRECATED")
            queries = [c.args[0] for c in mock_tx.query.call_args_list]
            assert any("DEPRECATED" in q for q in queries)

    def test_new_rule_type_inserts(self):
        """When rule_type is None on existing rule, should insert (not delete+insert)."""
        existing = _make_rule(rule_type=None)
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client(existing_rule=existing)
            mock_tx = _make_tx()
            client._driver.transaction.return_value = mock_tx
            client.get_rule_by_id = MagicMock(side_effect=[existing, existing])

            client.update_rule("RULE-001", rule_type="OPERATIONAL")
            queries = [c.args[0] for c in mock_tx.query.call_args_list]
            # Should have insert but no delete for rule-type
            insert_qs = [q for q in queries if "rule-type" in q and "insert" in q.lower()]
            delete_qs = [q for q in queries if "rule-type" in q and "delete" in q.lower()]
            assert len(insert_qs) == 1
            assert len(delete_qs) == 0

    def test_new_semantic_id_inserts(self):
        existing = _make_rule(semantic_id=None)
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client(existing_rule=existing)
            mock_tx = _make_tx()
            client._driver.transaction.return_value = mock_tx
            client.get_rule_by_id = MagicMock(side_effect=[existing, existing])

            client.update_rule("RULE-001", semantic_id="SESSION-EVID-01-v1")
            queries = [c.args[0] for c in mock_tx.query.call_args_list]
            assert any("semantic-id" in q for q in queries)

    def test_invalid_applicability_raises(self):
        existing = _make_rule()
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client(existing_rule=existing)
            with pytest.raises(ValueError, match="Invalid applicability"):
                client.update_rule("RULE-001", applicability="MAYBE")

    def test_same_values_skipped(self):
        """Passing same values as existing should result in no updates."""
        existing = _make_rule(name="Test Rule", priority="HIGH")
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client(existing_rule=existing)

            result = client.update_rule("RULE-001", name="Test Rule", priority="HIGH")
            assert result is existing  # No changes


# ── deprecate_rule ───────────────────────────────────────


class TestDeprecateRule:

    def test_delegates_to_update(self):
        from governance.typedb.queries.rules.crud import RuleCRUDOperations

        class MockClient(RuleCRUDOperations):
            pass

        client = MockClient()
        client.update_rule = MagicMock(return_value=_make_rule(status="DEPRECATED"))
        result = client.deprecate_rule("RULE-001", reason="obsolete")
        client.update_rule.assert_called_once_with("RULE-001", status="DEPRECATED")


# ── delete_rule ──────────────────────────────────────────


class TestDeleteRule:

    def test_not_found_returns_false(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client(existing_rule=None)
            assert client.delete_rule("MISSING") is False

    def test_successful_delete_with_archive(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client(existing_rule=_make_rule())
            mock_tx = _make_tx()
            client._driver.transaction.return_value = mock_tx

            result = client.delete_rule("RULE-001")
            assert result is True
            client.archive_rule.assert_called_once_with("RULE-001", reason="deleted")
            mock_tx.commit.assert_called_once()

    def test_delete_without_archive(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client(existing_rule=_make_rule())
            mock_tx = _make_tx()
            client._driver.transaction.return_value = mock_tx

            result = client.delete_rule("RULE-001", archive=False)
            assert result is True
            client.archive_rule.assert_not_called()

    def test_archive_failure_doesnt_block_delete(self):
        mock_typedb = _make_typedb_mocks()
        with patch.dict(sys.modules, {"typedb": MagicMock(), "typedb.driver": mock_typedb}):
            client = _make_client(existing_rule=_make_rule())
            client.archive_rule.side_effect = Exception("Archive failed")
            mock_tx = _make_tx()
            client._driver.transaction.return_value = mock_tx

            result = client.delete_rule("RULE-001")
            assert result is True  # Delete still succeeds
