"""DSP-04c: Task Rules Engine Edge Case Tests.

Covers gaps in task_rules.py:
1. validate_on_create — all rule paths (RequiredField, FormatRule, ProjectAcronym, TypePrefix)
2. validate_on_create — laconic format variations
3. validate_on_complete — all types with empty lists vs None
4. validate_agent_id — valid/invalid/None
5. format_validation_result — structure verification
6. ValidationError — serialization
"""
import pytest
from unittest.mock import patch

from governance.services.task_rules import (
    validate_on_create,
    validate_on_complete,
    validate_agent_id,
    format_validation_result,
    ValidationError,
    TYPE_DOD_REQUIREMENTS,
    LACONIC_PATTERN,
    LACONIC_MIN_PATTERN,
)


# =============================================================================
# 1. validate_on_create — RequiredField
# =============================================================================


class TestValidateOnCreateRequired:
    """RequiredField rule: summary or description must exist."""

    def test_both_none_triggers_error(self):
        errors = validate_on_create(summary=None, description=None)
        assert any(e.rule == "RequiredField" for e in errors)

    def test_summary_only_no_error(self):
        errors = validate_on_create(summary="task > test > create > summary")
        required = [e for e in errors if e.rule == "RequiredField"]
        assert len(required) == 0

    def test_description_only_no_error(self):
        errors = validate_on_create(description="A detailed description")
        required = [e for e in errors if e.rule == "RequiredField"]
        assert len(required) == 0

    def test_both_provided_no_error(self):
        errors = validate_on_create(
            summary="task > test > both", description="detail"
        )
        required = [e for e in errors if e.rule == "RequiredField"]
        assert len(required) == 0

    def test_empty_strings_trigger_error(self):
        errors = validate_on_create(summary="", description="")
        assert any(e.rule == "RequiredField" for e in errors)


# =============================================================================
# 2. validate_on_create — FormatRule (Laconic)
# =============================================================================


class TestValidateOnCreateFormat:
    """FormatRule: summary should follow laconic format."""

    def test_four_segment_laconic_passes(self):
        errors = validate_on_create(summary="task > lifecycle > validate > dod")
        format_errors = [e for e in errors if e.rule == "FormatRule"]
        assert len(format_errors) == 0

    def test_three_segment_laconic_passes(self):
        errors = validate_on_create(summary="task > lifecycle > validate")
        format_errors = [e for e in errors if e.rule == "FormatRule"]
        assert len(format_errors) == 0

    def test_two_segment_fails_format(self):
        errors = validate_on_create(summary="task > lifecycle")
        format_errors = [e for e in errors if e.rule == "FormatRule"]
        assert len(format_errors) == 1

    def test_plain_text_fails_format(self):
        errors = validate_on_create(summary="Fix the bug")
        format_errors = [e for e in errors if e.rule == "FormatRule"]
        assert len(format_errors) == 1

    def test_none_summary_skips_format_check(self):
        """When summary is None (auto-generated from description), skip format check."""
        errors = validate_on_create(summary=None, description="Auto gen")
        format_errors = [e for e in errors if e.rule == "FormatRule"]
        assert len(format_errors) == 0


# =============================================================================
# 3. validate_on_create — Task ID Rules
# =============================================================================


class TestValidateOnCreateTaskId:
    """ProjectAcronymRule and TypePrefixRule for task IDs."""

    def test_valid_new_format_id(self):
        errors = validate_on_create(
            task_id="SRVJ-BUG-001",
            summary="task > test > id > valid",
            task_type="bug",
        )
        # Should only have format/acronym errors if constants don't include SRVJ
        acronym_errors = [e for e in errors if e.rule == "ProjectAcronymRule"]
        prefix_errors = [e for e in errors if e.rule == "TypePrefixRule"]
        # SRVJ is a known acronym
        assert len(acronym_errors) == 0
        assert len(prefix_errors) == 0

    def test_unknown_acronym_triggers_error(self):
        errors = validate_on_create(
            task_id="ZZZZZ-BUG-001",
            summary="task > test > id > unknown",
        )
        assert any(e.rule == "ProjectAcronymRule" for e in errors)

    def test_invalid_type_prefix_triggers_error(self):
        # "ZZZZZ" is 5 chars (fits {2,6}), not a valid type prefix
        errors = validate_on_create(
            task_id="SRVJ-ZZZZZ-001",
            summary="task > test > id > prefix",
        )
        assert any(e.rule == "TypePrefixRule" for e in errors)

    def test_type_prefix_mismatch_triggers_error(self):
        """task_id says BUG but task_type says feature."""
        errors = validate_on_create(
            task_id="SRVJ-BUG-001",
            summary="task > test > id > mismatch",
            task_type="feature",
        )
        assert any(e.rule == "TypePrefixMismatch" for e in errors)

    def test_legacy_format_id_skips_new_rules(self):
        """Legacy IDs like BUG-001 don't trigger new-format rules."""
        errors = validate_on_create(
            task_id="BUG-001",
            summary="task > test > id > legacy",
        )
        # No ProjectAcronymRule or TypePrefixRule for legacy format
        assert not any(e.rule in ("ProjectAcronymRule", "TypePrefixRule") for e in errors)

    def test_no_task_id_skips_id_validation(self):
        errors = validate_on_create(
            summary="task > test > no id",
        )
        assert not any(e.rule in ("ProjectAcronymRule", "TypePrefixRule", "TypePrefixMismatch") for e in errors)


# =============================================================================
# 4. validate_on_complete — Empty List vs None
# =============================================================================


class TestValidateOnCompleteEmptyVsNone:
    """Empty list [] should be treated same as None for required list fields."""

    @patch("governance.stores.agents.VALID_AGENT_IDS", {"code-agent"})
    def test_bug_empty_sessions_fails(self):
        errors = validate_on_complete(
            task_id="BUG-001", task_type="bug",
            summary="test > empty > sessions",
            agent_id="code-agent",
            completed_at="2026-01-01T00:00:00",
            linked_sessions=[],  # Empty list, not None
            evidence="Tests pass",
        )
        fields = [e.field for e in errors]
        assert "linked_sessions" in fields

    @patch("governance.stores.agents.VALID_AGENT_IDS", {"code-agent"})
    def test_feature_empty_documents_fails(self):
        errors = validate_on_complete(
            task_id="FEAT-001", task_type="feature",
            summary="test > empty > docs",
            agent_id="code-agent",
            completed_at="2026-01-01T00:00:00",
            linked_sessions=["S-1"],
            linked_documents=[],  # Empty list
        )
        fields = [e.field for e in errors]
        assert "linked_documents" in fields

    @patch("governance.stores.agents.VALID_AGENT_IDS", {"code-agent"})
    def test_empty_string_evidence_fails(self):
        """Empty string evidence should be treated as missing."""
        errors = validate_on_complete(
            task_id="TEST-001", task_type="test",
            summary="test > empty > evidence",
            agent_id="code-agent",
            completed_at="2026-01-01T00:00:00",
            evidence="",  # Empty string
        )
        fields = [e.field for e in errors]
        assert "evidence" in fields


# =============================================================================
# 5. validate_agent_id
# =============================================================================


class TestValidateAgentId:
    """Agent ID validation against registered agents."""

    @patch("governance.stores.agents.VALID_AGENT_IDS", {"code-agent", "research-agent"})
    def test_valid_agent_passes(self):
        errors = validate_agent_id("code-agent")
        assert len(errors) == 0

    @patch("governance.stores.agents.VALID_AGENT_IDS", {"code-agent"})
    def test_invalid_agent_fails(self):
        errors = validate_agent_id("unknown-agent")
        assert len(errors) == 1
        assert errors[0].rule == "InvalidAgent"

    def test_none_agent_passes(self):
        """None is valid — agent_id is optional."""
        errors = validate_agent_id(None)
        assert len(errors) == 0


# =============================================================================
# 6. ValidationError + format_validation_result
# =============================================================================


class TestValidationErrorSerialization:
    """ValidationError to_dict and format_validation_result."""

    def test_to_dict_has_all_keys(self):
        err = ValidationError("RequiredField", "summary", "Summary is required")
        d = err.to_dict()
        assert d["rule"] == "RequiredField"
        assert d["field"] == "summary"
        assert d["message"] == "Summary is required"

    def test_format_empty_errors_is_valid(self):
        result = format_validation_result([])
        assert result["valid"] is True
        assert result["validation_errors"] == []

    def test_format_with_errors_is_invalid(self):
        errors = [
            ValidationError("RequiredField", "summary", "Missing"),
            ValidationError("FormatRule", "summary", "Bad format"),
        ]
        result = format_validation_result(errors)
        assert result["valid"] is False
        assert len(result["validation_errors"]) == 2


# =============================================================================
# 7. Laconic Pattern Matching
# =============================================================================


class TestLaconicPatterns:
    """Regex patterns for laconic summary validation."""

    def test_full_laconic_matches(self):
        assert LACONIC_PATTERN.match("task > lifecycle > validate > dod")

    def test_min_laconic_matches(self):
        assert LACONIC_MIN_PATTERN.match("task > lifecycle > validate")

    def test_min_pattern_rejects_two_segments(self):
        assert not LACONIC_MIN_PATTERN.match("task > lifecycle")

    def test_pattern_allows_spaces(self):
        assert LACONIC_MIN_PATTERN.match("task  >  lifecycle  >  validate")

    def test_pattern_allows_mixed_content(self):
        assert LACONIC_MIN_PATTERN.match("API > /tasks/create > 500 error > missing validation")
