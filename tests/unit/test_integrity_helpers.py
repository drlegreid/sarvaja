"""
Tests for data integrity helpers and models.

Per RULE-012: DSP Semantic Code Structure.
Covers entity ID extraction, field lookup, naming conventions, and validation models.

Created: 2026-01-30
"""

import pytest

from governance.integrity.helpers import get_entity_id, get_field_value, camel_case
from governance.integrity.models import ValidationLevel, ValidationResult


class TestGetEntityId:
    """Test entity ID extraction from various naming conventions."""

    def test_kebab_case(self):
        """Extract from kebab-case key (e.g., rule-id)."""
        assert get_entity_id("rule", {"rule-id": "RULE-001"}) == "RULE-001"

    def test_snake_case(self):
        """Extract from snake_case key (e.g., rule_id)."""
        assert get_entity_id("rule", {"rule_id": "RULE-002"}) == "RULE-002"

    def test_camel_case(self):
        """Extract from camelCase key (e.g., ruleId)."""
        assert get_entity_id("rule", {"ruleId": "RULE-003"}) == "RULE-003"

    def test_generic_id(self):
        """Extract from generic 'id' key."""
        assert get_entity_id("task", {"id": "T-001"}) == "T-001"

    def test_priority_kebab_first(self):
        """Kebab-case has priority over generic id."""
        data = {"task-id": "T-001", "id": "generic"}
        assert get_entity_id("task", {"task-id": "T-001", "id": "generic"}) == "T-001"

    def test_unknown_returns_unknown(self):
        """Missing ID returns 'unknown'."""
        assert get_entity_id("rule", {"name": "test"}) == "unknown"

    def test_empty_dict(self):
        """Empty dict returns 'unknown'."""
        assert get_entity_id("task", {}) == "unknown"

    def test_numeric_id_converted(self):
        """Numeric ID is converted to string."""
        assert get_entity_id("task", {"task-id": 42}) == "42"

    def test_session_entity(self):
        """Session entity ID extraction."""
        assert get_entity_id("session", {"session-id": "S-2026"}) == "S-2026"


class TestGetFieldValue:
    """Test field value lookup with naming convention handling."""

    def test_exact_match(self):
        """Exact field name match."""
        assert get_field_value({"task-status": "OPEN"}, "task-status") == "OPEN"

    def test_snake_case_fallback(self):
        """Falls back to snake_case."""
        assert get_field_value({"task_status": "OPEN"}, "task-status") == "OPEN"

    def test_no_separator_fallback(self):
        """Falls back to no separator."""
        assert get_field_value({"taskstatus": "OPEN"}, "task-status") == "OPEN"

    def test_camel_case_fallback(self):
        """Falls back to camelCase."""
        assert get_field_value({"taskStatus": "OPEN"}, "task-status") == "OPEN"

    def test_not_found(self):
        """Returns None when field not found."""
        assert get_field_value({"other": "value"}, "missing-field") is None

    def test_empty_dict(self):
        """Returns None for empty dict."""
        assert get_field_value({}, "any-field") is None

    def test_value_types(self):
        """Handles various value types."""
        assert get_field_value({"count": 42}, "count") == 42
        assert get_field_value({"active": True}, "active") is True
        assert get_field_value({"items": [1, 2]}, "items") == [1, 2]


class TestCamelCase:
    """Test kebab-case to camelCase conversion."""

    def test_simple(self):
        """Convert simple kebab-case."""
        assert camel_case("task-id") == "taskId"

    def test_multiple_parts(self):
        """Convert multiple parts."""
        assert camel_case("task-created-at") == "taskCreatedAt"

    def test_single_word(self):
        """Single word unchanged."""
        assert camel_case("status") == "status"

    def test_already_camel(self):
        """No dashes, returned as-is."""
        assert camel_case("taskId") == "taskId"


class TestValidationLevel:
    """Test ValidationLevel enum."""

    def test_all_levels(self):
        """All four validation levels exist."""
        assert ValidationLevel.SCHEMA.value == "schema"
        assert ValidationLevel.CLIENT.value == "client"
        assert ValidationLevel.API.value == "api"
        assert ValidationLevel.UI.value == "ui"


class TestValidationResult:
    """Test ValidationResult model."""

    def test_initial_state(self):
        """New result has no passes, fails, or warnings."""
        r = ValidationResult("rule", "RULE-001", ValidationLevel.API)
        assert r.entity_type == "rule"
        assert r.entity_id == "RULE-001"
        assert r.level == ValidationLevel.API
        assert r.is_valid is True
        assert r.passed == []
        assert r.failed == []
        assert r.warnings == []

    def test_add_pass(self):
        """Add passing check."""
        r = ValidationResult("rule", "R1", ValidationLevel.SCHEMA)
        r.add_pass("has_name")
        assert "has_name" in r.passed
        assert r.is_valid is True

    def test_add_fail(self):
        """Add failing check makes result invalid."""
        r = ValidationResult("rule", "R1", ValidationLevel.SCHEMA)
        r.add_fail("has_directive", "directive is empty")
        assert r.is_valid is False
        assert r.failed[0] == ("has_directive", "directive is empty")

    def test_add_warning(self):
        """Warnings don't affect validity."""
        r = ValidationResult("rule", "R1", ValidationLevel.CLIENT)
        r.add_warning("deprecated_field", "field is deprecated")
        assert r.is_valid is True
        assert len(r.warnings) == 1

    def test_to_dict(self):
        """Serialize to dict."""
        r = ValidationResult("task", "T-001", ValidationLevel.UI)
        r.add_pass("has_id")
        r.add_fail("has_phase", "phase missing")
        r.add_warning("old_format", "legacy format")
        d = r.to_dict()
        assert d["entity_type"] == "task"
        assert d["entity_id"] == "T-001"
        assert d["level"] == "ui"
        assert d["is_valid"] is False
        assert len(d["passed"]) == 1
        assert len(d["failed"]) == 1
        assert d["failed"][0]["check"] == "has_phase"
        assert len(d["warnings"]) == 1
        assert "timestamp" in d

    def test_multiple_failures(self):
        """Multiple failures tracked."""
        r = ValidationResult("rule", "R1", ValidationLevel.SCHEMA)
        r.add_fail("check1", "reason1")
        r.add_fail("check2", "reason2")
        assert len(r.failed) == 2
        assert r.is_valid is False
