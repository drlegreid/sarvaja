"""
Tests for session-status schema attribute (EPIC-PERF-TELEM-V1 Phase 1).

BDD Scenarios:
  - schema.tql defines session-status attribute with value type string
  - work-session entity owns session-status
"""

import os
import re

import pytest

SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "governance", "schema.tql"
)


@pytest.fixture
def schema_text():
    """Load schema.tql content."""
    with open(SCHEMA_PATH, "r") as f:
        return f.read()


class TestSessionStatusAttributeDefined:
    """Scenario: schema.tql defines session-status attribute."""

    def test_session_status_attribute_exists(self, schema_text):
        """session-status attribute is declared in schema."""
        assert re.search(
            r"attribute\s+session-status\s*,\s*value\s+string\s*;",
            schema_text,
        ), "schema.tql must define 'attribute session-status, value string;'"

    def test_session_status_value_type_is_string(self, schema_text):
        """session-status value type is string, not integer or datetime."""
        match = re.search(
            r"attribute\s+session-status\s*,\s*value\s+(\w+)\s*;",
            schema_text,
        )
        assert match is not None, "session-status attribute not found"
        assert match.group(1) == "string", (
            f"session-status value type should be 'string', got '{match.group(1)}'"
        )


class TestWorkSessionOwnsSessionStatus:
    """Scenario: work-session entity owns session-status."""

    def test_work_session_owns_session_status(self, schema_text):
        """work-session entity block includes 'owns session-status'."""
        # Extract the work-session entity block (from 'entity work-session,' to its closing ';')
        ws_match = re.search(
            r"entity\s+work-session\s*,(.*?);",
            schema_text,
            re.DOTALL,
        )
        assert ws_match is not None, "work-session entity not found in schema"
        ws_block = ws_match.group(1)
        assert re.search(
            r"owns\s+session-status",
            ws_block,
        ), "work-session must 'owns session-status'"


class TestSessionStatusNotDuplicated:
    """Guard: session-status attribute defined exactly once."""

    def test_attribute_defined_once(self, schema_text):
        """session-status attribute should not be duplicated."""
        matches = re.findall(
            r"attribute\s+session-status\s*,",
            schema_text,
        )
        assert len(matches) == 1, (
            f"session-status attribute defined {len(matches)} times, expected 1"
        )
