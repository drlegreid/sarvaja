"""
Rules Validation Tests
======================
Tests for TypeDBClient input validation on rules.
Per DOC-SIZE-01-v1: Split from test_rules_crud.py (838 lines)
Per TEST-TAXON-01-v1: Taxonomy markers applied.
"""

import pytest
from unittest.mock import patch

from governance.client import TypeDBClient, Rule


@pytest.mark.unit
@pytest.mark.rules
@pytest.mark.validate
class TestTypeDBClientValidation:
    """Tests for TypeDBClient input validation."""

    @pytest.mark.create
    def test_create_rule_validates_category(self, mock_client, sample_rule):
        """Test that create_rule validates category."""
        with patch.object(TypeDBClient, 'connect', return_value=True):
            with patch.object(TypeDBClient, 'get_rule_by_id', return_value=None):
                client = TypeDBClient()
                client._connected = True

                with patch.object(client, '_execute_write'):
                    valid = ["governance", "technical", "operational", "architecture", "testing"]
                    for cat in valid:
                        pass

                    with pytest.raises(ValueError, match="Invalid category"):
                        client.create_rule(
                            rule_id="RULE-TEST",
                            name="Test",
                            category="invalid_category",
                            priority="HIGH",
                            directive="Test"
                        )

    def test_create_rule_validates_priority(self, mock_client):
        """Test that create_rule validates priority."""
        with patch.object(TypeDBClient, 'connect', return_value=True):
            with patch.object(TypeDBClient, 'get_rule_by_id', return_value=None):
                client = TypeDBClient()
                client._connected = True

                with pytest.raises(ValueError, match="Invalid priority"):
                    client.create_rule(
                        rule_id="RULE-TEST",
                        name="Test",
                        category="governance",
                        priority="INVALID",
                        directive="Test"
                    )

    def test_create_rule_validates_status(self, mock_client):
        """Test that create_rule validates status."""
        with patch.object(TypeDBClient, 'connect', return_value=True):
            with patch.object(TypeDBClient, 'get_rule_by_id', return_value=None):
                client = TypeDBClient()
                client._connected = True

                with pytest.raises(ValueError, match="Invalid status"):
                    client.create_rule(
                        rule_id="RULE-TEST",
                        name="Test",
                        category="governance",
                        priority="HIGH",
                        directive="Test",
                        status="INVALID"
                    )

    def test_create_rule_checks_duplicate(self, sample_rule):
        """Test that create_rule rejects duplicate IDs."""
        with patch.object(TypeDBClient, 'connect', return_value=True):
            client = TypeDBClient()
            client._connected = True

            with patch.object(client, 'get_rule_by_id', return_value=sample_rule):
                with pytest.raises(ValueError, match="already exists"):
                    client.create_rule(
                        rule_id=sample_rule.id,
                        name="New Name",
                        category="governance",
                        priority="HIGH",
                        directive="New directive"
                    )

    def test_update_rule_raises_for_missing(self):
        """Test that update_rule raises for non-existent rule."""
        with patch.object(TypeDBClient, 'connect', return_value=True):
            client = TypeDBClient()
            client._connected = True

            with patch.object(client, 'get_rule_by_id', return_value=None):
                with pytest.raises(ValueError, match="not found"):
                    client.update_rule("RULE-NONEXISTENT", name="New Name")

    def test_update_rule_returns_unchanged_if_no_updates(self, sample_rule):
        """Test that update_rule returns existing rule if nothing changes."""
        with patch.object(TypeDBClient, 'connect', return_value=True):
            client = TypeDBClient()
            client._connected = True

            with patch.object(client, 'get_rule_by_id', return_value=sample_rule):
                result = client.update_rule(sample_rule.id)
                assert result == sample_rule

    def test_deprecate_rule_calls_update_with_deprecated(self, sample_rule):
        """Test that deprecate_rule calls update_rule with DEPRECATED status."""
        with patch.object(TypeDBClient, 'connect', return_value=True):
            client = TypeDBClient()
            client._connected = True

            deprecated_rule = Rule(
                id=sample_rule.id,
                name=sample_rule.name,
                category=sample_rule.category,
                priority=sample_rule.priority,
                status="DEPRECATED",
                directive=sample_rule.directive
            )

            with patch.object(client, 'update_rule', return_value=deprecated_rule) as mock_update:
                result = client.deprecate_rule(sample_rule.id)
                mock_update.assert_called_once_with(sample_rule.id, status="DEPRECATED")
                assert result.status == "DEPRECATED"

    def test_delete_rule_returns_false_for_missing(self):
        """Test that delete_rule returns False for non-existent rule."""
        with patch.object(TypeDBClient, 'connect', return_value=True):
            client = TypeDBClient()
            client._connected = True

            with patch.object(client, 'get_rule_by_id', return_value=None):
                result = client.delete_rule("RULE-NONEXISTENT")
                assert result is False
