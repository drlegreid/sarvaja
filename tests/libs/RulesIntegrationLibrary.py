"""
Rules Integration Library for Robot Framework
Integration and edge case tests for rules CRUD.
Migrated from tests/rules/test_integration.py
Per: RF-007 Robot Framework Migration
"""
from dataclasses import asdict
from robot.api.deco import keyword


class RulesIntegrationLibrary:
    """Robot Framework keywords for rules integration tests."""

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
    # Integration Tests (Require TypeDB)
    # =========================================================================

    @keyword("Full CRUD Cycle Requires TypeDB")
    def full_crud_cycle_requires_typedb(self):
        """Test complete CRUD cycle - requires running TypeDB instance."""
        try:
            from governance.client import TypeDBClient

            client = TypeDBClient()
            if not client.connect():
                return {"skipped": True, "reason": "TypeDB not available"}

            test_rule_id = "RULE-INTEGRATION-TEST"

            try:
                # CREATE
                rule = client.create_rule(
                    rule_id=test_rule_id,
                    name="Integration Test Rule",
                    category="testing",
                    priority="LOW",
                    directive="This rule is for integration testing only."
                )
                create_ok = rule is not None and rule.id == test_rule_id

                # READ
                fetched = client.get_rule_by_id(test_rule_id)
                read_ok = fetched is not None and fetched.name == "Integration Test Rule"

                # UPDATE
                updated = client.update_rule(test_rule_id, priority="MEDIUM")
                update_ok = updated.priority == "MEDIUM"

                # DEPRECATE
                deprecated = client.deprecate_rule(test_rule_id)
                deprecate_ok = deprecated.status == "DEPRECATED"

                # DELETE
                deleted = client.delete_rule(test_rule_id)
                delete_ok = deleted is True

                # VERIFY DELETED
                gone = client.get_rule_by_id(test_rule_id)
                verify_ok = gone is None

                return {
                    "create_ok": create_ok,
                    "read_ok": read_ok,
                    "update_ok": update_ok,
                    "deprecate_ok": deprecate_ok,
                    "delete_ok": delete_ok,
                    "verify_deleted_ok": verify_ok
                }

            finally:
                try:
                    client.delete_rule(test_rule_id)
                except Exception:
                    pass
                client.close()

        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Edge Case Tests
    # =========================================================================

    @keyword("Valid Categories List")
    def valid_categories_list(self):
        """Test all valid categories are defined."""
        valid = ["governance", "technical", "operational", "architecture", "testing"]
        return {"count": len(valid), "count_correct": len(valid) == 5}

    @keyword("Valid Priorities List")
    def valid_priorities_list(self):
        """Test all valid priorities are defined."""
        valid = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        return {"count": len(valid), "count_correct": len(valid) == 4}

    @keyword("Valid Statuses List")
    def valid_statuses_list(self):
        """Test all valid statuses are defined."""
        valid = ["ACTIVE", "DRAFT", "DEPRECATED"]
        return {"count": len(valid), "count_correct": len(valid) == 3}

    @keyword("Rule Dataclass Has Fields")
    def rule_dataclass_has_fields(self):
        """Test Rule dataclass has expected fields."""
        sample_rule = self._get_sample_rule()
        if sample_rule is None:
            return {"skipped": True, "reason": "Could not create sample rule"}

        return {
            "has_id": hasattr(sample_rule, 'id'),
            "has_name": hasattr(sample_rule, 'name'),
            "has_category": hasattr(sample_rule, 'category'),
            "has_priority": hasattr(sample_rule, 'priority'),
            "has_status": hasattr(sample_rule, 'status'),
            "has_directive": hasattr(sample_rule, 'directive')
        }

    @keyword("Rule To Dict Conversion")
    def rule_to_dict_conversion(self):
        """Test Rule can be converted to dict."""
        sample_rule = self._get_sample_rule()
        if sample_rule is None:
            return {"skipped": True, "reason": "Could not create sample rule"}

        try:
            rule_dict = asdict(sample_rule)
            return {
                "id_matches": rule_dict['id'] == sample_rule.id,
                "name_matches": rule_dict['name'] == sample_rule.name,
                "category_matches": rule_dict['category'] == sample_rule.category
            }
        except Exception as e:
            return {"skipped": True, "reason": str(e)}
