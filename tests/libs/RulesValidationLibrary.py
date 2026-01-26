"""
Rules Validation Library for Robot Framework
Tests for TypeDBClient input validation on rules.
Migrated from tests/rules/test_validation.py
Per: RF-007 Robot Framework Migration
"""
from unittest.mock import patch, Mock
from robot.api.deco import keyword


class RulesValidationLibrary:
    """Robot Framework keywords for rules validation tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def _get_sample_rule(self):
        """Create a sample rule for testing."""
        try:
            from governance.client import Rule
            return Rule(
                id="RULE-TEST-001",
                name="Test Rule",
                category="testing",
                priority="MEDIUM",
                status="DRAFT",
                directive="This is a test rule directive."
            )
        except ImportError:
            return None

    # =========================================================================
    # Category Validation Tests
    # =========================================================================

    @keyword("Create Rule Validates Category")
    def create_rule_validates_category(self):
        """Test that create_rule validates category."""
        try:
            from governance.client import TypeDBClient

            with patch.object(TypeDBClient, 'connect', return_value=True):
                with patch.object(TypeDBClient, 'get_rule_by_id', return_value=None):
                    client = TypeDBClient()
                    client._connected = True

                    try:
                        with patch.object(client, '_execute_write'):
                            client.create_rule(
                                rule_id="RULE-TEST",
                                name="Test",
                                category="invalid_category",
                                priority="HIGH",
                                directive="Test"
                            )
                        return {"raises_error": False, "error_type": None}
                    except ValueError as e:
                        return {
                            "raises_error": True,
                            "error_type": "ValueError",
                            "message_correct": "Invalid category" in str(e)
                        }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Priority Validation Tests
    # =========================================================================

    @keyword("Create Rule Validates Priority")
    def create_rule_validates_priority(self):
        """Test that create_rule validates priority."""
        try:
            from governance.client import TypeDBClient

            with patch.object(TypeDBClient, 'connect', return_value=True):
                with patch.object(TypeDBClient, 'get_rule_by_id', return_value=None):
                    client = TypeDBClient()
                    client._connected = True

                    try:
                        client.create_rule(
                            rule_id="RULE-TEST",
                            name="Test",
                            category="governance",
                            priority="INVALID",
                            directive="Test"
                        )
                        return {"raises_error": False, "error_type": None}
                    except ValueError as e:
                        return {
                            "raises_error": True,
                            "error_type": "ValueError",
                            "message_correct": "Invalid priority" in str(e)
                        }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Status Validation Tests
    # =========================================================================

    @keyword("Create Rule Validates Status")
    def create_rule_validates_status(self):
        """Test that create_rule validates status."""
        try:
            from governance.client import TypeDBClient

            with patch.object(TypeDBClient, 'connect', return_value=True):
                with patch.object(TypeDBClient, 'get_rule_by_id', return_value=None):
                    client = TypeDBClient()
                    client._connected = True

                    try:
                        client.create_rule(
                            rule_id="RULE-TEST",
                            name="Test",
                            category="governance",
                            priority="HIGH",
                            directive="Test",
                            status="INVALID"
                        )
                        return {"raises_error": False, "error_type": None}
                    except ValueError as e:
                        return {
                            "raises_error": True,
                            "error_type": "ValueError",
                            "message_correct": "Invalid status" in str(e)
                        }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Duplicate Checking Tests
    # =========================================================================

    @keyword("Create Rule Checks Duplicate")
    def create_rule_checks_duplicate(self):
        """Test that create_rule rejects duplicate IDs."""
        try:
            from governance.client import TypeDBClient
            sample_rule = self._get_sample_rule()
            if sample_rule is None:
                return {"skipped": True, "reason": "Could not create sample rule"}

            with patch.object(TypeDBClient, 'connect', return_value=True):
                client = TypeDBClient()
                client._connected = True

                with patch.object(client, 'get_rule_by_id', return_value=sample_rule):
                    try:
                        client.create_rule(
                            rule_id=sample_rule.id,
                            name="New Name",
                            category="governance",
                            priority="HIGH",
                            directive="New directive"
                        )
                        return {"raises_error": False, "error_type": None}
                    except ValueError as e:
                        return {
                            "raises_error": True,
                            "error_type": "ValueError",
                            "message_correct": "already exists" in str(e)
                        }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Update Rule Validation Tests
    # =========================================================================

    @keyword("Update Rule Raises For Missing")
    def update_rule_raises_for_missing(self):
        """Test that update_rule raises for non-existent rule."""
        try:
            from governance.client import TypeDBClient

            with patch.object(TypeDBClient, 'connect', return_value=True):
                client = TypeDBClient()
                client._connected = True

                with patch.object(client, 'get_rule_by_id', return_value=None):
                    try:
                        client.update_rule("RULE-NONEXISTENT", name="New Name")
                        return {"raises_error": False, "error_type": None}
                    except ValueError as e:
                        return {
                            "raises_error": True,
                            "error_type": "ValueError",
                            "message_correct": "not found" in str(e)
                        }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Update Rule Returns Unchanged If No Updates")
    def update_rule_returns_unchanged_if_no_updates(self):
        """Test that update_rule returns existing rule if nothing changes."""
        try:
            from governance.client import TypeDBClient
            sample_rule = self._get_sample_rule()
            if sample_rule is None:
                return {"skipped": True, "reason": "Could not create sample rule"}

            with patch.object(TypeDBClient, 'connect', return_value=True):
                client = TypeDBClient()
                client._connected = True

                with patch.object(client, 'get_rule_by_id', return_value=sample_rule):
                    result = client.update_rule(sample_rule.id)
                    return {"returns_same_rule": result == sample_rule}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Deprecate Rule Tests
    # =========================================================================

    @keyword("Deprecate Rule Calls Update With Deprecated")
    def deprecate_rule_calls_update_with_deprecated(self):
        """Test that deprecate_rule calls update_rule with DEPRECATED status."""
        try:
            from governance.client import TypeDBClient, Rule
            sample_rule = self._get_sample_rule()
            if sample_rule is None:
                return {"skipped": True, "reason": "Could not create sample rule"}

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
                    return {
                        "calls_update": True,
                        "result_status_deprecated": result.status == "DEPRECATED"
                    }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except AssertionError:
            return {"calls_update": False, "result_status_deprecated": False}

    # =========================================================================
    # Delete Rule Tests
    # =========================================================================

    @keyword("Delete Rule Returns False For Missing")
    def delete_rule_returns_false_for_missing(self):
        """Test that delete_rule returns False for non-existent rule."""
        try:
            from governance.client import TypeDBClient

            with patch.object(TypeDBClient, 'connect', return_value=True):
                client = TypeDBClient()
                client._connected = True

                with patch.object(client, 'get_rule_by_id', return_value=None):
                    result = client.delete_rule("RULE-NONEXISTENT")
                    return {"returns_false": result is False}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
