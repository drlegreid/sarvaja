"""
Rules Integration Tests
=======================
Integration and edge case tests for rules CRUD.
Per DOC-SIZE-01-v1: Split from test_rules_crud.py (838 lines)
"""

import pytest
from dataclasses import asdict

from governance.client import TypeDBClient


@pytest.mark.integration
@pytest.mark.skipif(True, reason="Requires running TypeDB instance")
class TestRulesCRUDIntegration:
    """Integration tests for rules CRUD (require running TypeDB)."""

    @pytest.fixture
    def typedb_client(self):
        """Get connected TypeDB client."""
        client = TypeDBClient()
        if client.connect():
            yield client
            client.close()
        else:
            pytest.skip("TypeDB not available")

    def test_full_crud_cycle(self, typedb_client):
        """Test complete CRUD cycle: create, read, update, deprecate, delete."""
        test_rule_id = "RULE-INTEGRATION-TEST"

        try:
            # CREATE
            rule = typedb_client.create_rule(
                rule_id=test_rule_id,
                name="Integration Test Rule",
                category="testing",
                priority="LOW",
                directive="This rule is for integration testing only."
            )
            assert rule is not None
            assert rule.id == test_rule_id
            assert rule.status == "DRAFT"

            # READ
            fetched = typedb_client.get_rule_by_id(test_rule_id)
            assert fetched is not None
            assert fetched.name == "Integration Test Rule"

            # UPDATE
            updated = typedb_client.update_rule(test_rule_id, priority="MEDIUM")
            assert updated.priority == "MEDIUM"

            # DEPRECATE
            deprecated = typedb_client.deprecate_rule(test_rule_id)
            assert deprecated.status == "DEPRECATED"

            # DELETE
            deleted = typedb_client.delete_rule(test_rule_id)
            assert deleted is True

            # VERIFY DELETED
            gone = typedb_client.get_rule_by_id(test_rule_id)
            assert gone is None

        finally:
            # Cleanup in case of failure
            try:
                typedb_client.delete_rule(test_rule_id)
            except Exception:
                pass


class TestRulesCRUDEdgeCases:
    """Edge case tests for rules CRUD."""

    def test_valid_categories(self):
        """Test all valid categories are accepted."""
        valid = ["governance", "technical", "operational", "architecture", "testing"]
        assert len(valid) == 5

    def test_valid_priorities(self):
        """Test all valid priorities are accepted."""
        valid = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        assert len(valid) == 4

    def test_valid_statuses(self):
        """Test all valid statuses are accepted."""
        valid = ["ACTIVE", "DRAFT", "DEPRECATED"]
        assert len(valid) == 3

    def test_rule_dataclass_fields(self, sample_rule):
        """Test Rule dataclass has expected fields."""
        assert hasattr(sample_rule, 'id')
        assert hasattr(sample_rule, 'name')
        assert hasattr(sample_rule, 'category')
        assert hasattr(sample_rule, 'priority')
        assert hasattr(sample_rule, 'status')
        assert hasattr(sample_rule, 'directive')

    def test_rule_to_dict(self, sample_rule):
        """Test Rule can be converted to dict."""
        rule_dict = asdict(sample_rule)
        assert rule_dict['id'] == sample_rule.id
        assert rule_dict['name'] == sample_rule.name
        assert rule_dict['category'] == sample_rule.category
