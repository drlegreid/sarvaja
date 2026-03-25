"""DSP-04: Resolution Collator Edge Case Tests.

Covers gaps in resolution_collator.py:
1. _render_session_list — metadata with topic fallback, empty lists
2. _render_template_section — all key types (linked_commits, evidence, etc.)
3. build_resolution_summary — with/without session_metadata
4. fetch_session_metadata — from empty store, partial data, missing sessions
5. _build_generic_summary — all empty, partial data combinations
6. Type dispatch — every canonical type produces unique header
"""
import pytest
from unittest.mock import patch

from governance.services.resolution_collator import (
    TYPE_RESOLUTION_TEMPLATES,
    build_resolution_summary,
    fetch_session_metadata,
    _render_session_list,
    _render_template_section,
    _build_typed_summary,
    _build_generic_summary,
)


# =============================================================================
# 1. _render_session_list Edge Cases
# =============================================================================


class TestRenderSessionList:
    """_render_session_list with varied inputs."""

    def test_empty_list_returns_empty(self):
        assert _render_session_list([]) == []

    def test_single_session_no_metadata(self):
        result = _render_session_list(["S-001"])
        assert result == ["- S-001"]

    def test_single_session_with_metadata(self):
        meta = [{"session_id": "S-001", "description": "Bug fix", "duration": "15m"}]
        result = _render_session_list(["S-001"], session_metadata=meta)
        assert len(result) == 1
        assert "S-001" in result[0]
        assert "Bug fix" in result[0]
        assert "15m" in result[0]

    def test_metadata_uses_topic_fallback(self):
        """When description is None, falls back to topic field."""
        meta = [{"session_id": "S-002", "topic": "Research spike", "duration": None}]
        result = _render_session_list(["S-002"], session_metadata=meta)
        assert "Research spike" in result[0]

    def test_metadata_both_none_shows_na(self):
        meta = [{"session_id": "S-003", "description": None, "topic": None}]
        result = _render_session_list(["S-003"], session_metadata=meta)
        assert "N/A" in result[0]

    def test_metadata_no_duration_no_suffix(self):
        meta = [{"session_id": "S-004", "description": "Test"}]
        result = _render_session_list(["S-004"], session_metadata=meta)
        assert result[0] == "- S-004: Test"

    def test_multiple_sessions_mixed_metadata(self):
        """Some sessions have metadata, some don't."""
        meta = [{"session_id": "S-005", "description": "Found it"}]
        result = _render_session_list(["S-005", "S-006"], session_metadata=meta)
        assert len(result) == 2
        assert "Found it" in result[0]
        assert result[1] == "- S-006"


# =============================================================================
# 2. _render_template_section — All Key Types
# =============================================================================


class TestRenderTemplateSection:
    """_render_template_section covers all data key paths."""

    def test_linked_sessions_populated(self):
        section = {"title": "Sessions", "key": "linked_sessions", "fallback": "None"}
        data = {"linked_sessions": ["S-1", "S-2"]}
        result = _render_template_section(section, data)
        assert "### Sessions" in result[0]
        assert any("S-1" in line for line in result)
        assert any("S-2" in line for line in result)

    def test_linked_sessions_empty_shows_fallback(self):
        section = {"title": "Sessions", "key": "linked_sessions", "fallback": "No sessions"}
        data = {"linked_sessions": []}
        result = _render_template_section(section, data)
        assert "No sessions" in result

    def test_linked_commits_populated(self):
        section = {"title": "Commits", "key": "linked_commits", "fallback": "None"}
        data = {"linked_commits": ["abc123", "def456"]}
        result = _render_template_section(section, data)
        assert any("abc123" in line for line in result)

    def test_linked_commits_empty_shows_fallback(self):
        section = {"title": "Commits", "key": "linked_commits", "fallback": "No commits"}
        data = {}
        result = _render_template_section(section, data)
        assert "No commits" in result

    def test_linked_documents_populated(self):
        section = {"title": "Docs", "key": "linked_documents", "fallback": "None"}
        data = {"linked_documents": ["docs/spec.md"]}
        result = _render_template_section(section, data)
        assert any("docs/spec.md" in line for line in result)

    def test_evidence_populated(self):
        section = {"title": "Root Cause", "key": "evidence", "fallback": "Not documented"}
        data = {"evidence": "Null ref in handler"}
        result = _render_template_section(section, data)
        assert "Null ref in handler" in result

    def test_evidence_none_shows_fallback(self):
        section = {"title": "Root Cause", "key": "evidence", "fallback": "Not documented"}
        data = {}
        result = _render_template_section(section, data)
        assert "Not documented" in result

    def test_underscore_key_always_fallback(self):
        """Keys starting with _ are computed — always show fallback."""
        section = {"title": "Coverage", "key": "_coverage", "fallback": "N/A"}
        data = {}
        result = _render_template_section(section, data)
        assert "N/A" in result

    def test_generic_string_field(self):
        section = {"title": "Custom", "key": "custom_field", "fallback": "Empty"}
        data = {"custom_field": "Some value"}
        result = _render_template_section(section, data)
        assert "Some value" in result

    def test_generic_field_missing(self):
        section = {"title": "Custom", "key": "custom_field", "fallback": "Empty"}
        data = {}
        result = _render_template_section(section, data)
        assert "Empty" in result


# =============================================================================
# 3. build_resolution_summary — Type Dispatch Completeness
# =============================================================================


class TestBuildResolutionSummaryAllTypes:
    """Every canonical type produces distinct header."""

    @pytest.mark.parametrize("task_type", ["bug", "feature", "chore", "research", "spec", "test"])
    def test_typed_header(self, task_type):
        result = build_resolution_summary({"task_type": task_type})
        assert f"## Resolution Summary ({task_type})" in result

    @pytest.mark.parametrize("task_type", [None, "unknown", "gap"])
    def test_untyped_uses_generic(self, task_type):
        result = build_resolution_summary({"task_type": task_type})
        # Should NOT have typed header
        assert "## Resolution Summary\n" in result or result == "Task completed."


class TestBuildResolutionSummaryWithData:
    """build_resolution_summary with various data combinations."""

    def test_bug_all_sections_populated(self):
        data = {
            "task_type": "bug",
            "evidence": "Stack trace analysis",
            "linked_commits": ["abc123"],
            "linked_sessions": ["S-100"],
        }
        result = build_resolution_summary(data)
        assert "Root Cause" in result
        assert "Stack trace analysis" in result
        assert "Fix Applied" in result
        assert "abc123" in result
        assert "Regression Test" in result
        assert "Sessions" in result

    def test_feature_with_documents_and_commits(self):
        data = {
            "task_type": "feature",
            "linked_documents": ["docs/spec.md", "docs/design.md"],
            "linked_commits": ["abc123"],
            "linked_sessions": ["S-200"],
        }
        result = build_resolution_summary(data)
        assert "Requirements Met" in result
        assert "docs/spec.md" in result
        assert "Files Changed" in result

    def test_chore_with_evidence(self):
        data = {
            "task_type": "chore",
            "evidence": "Cleaned up temp files",
            "linked_commits": ["def456"],
            "linked_sessions": [],
        }
        result = build_resolution_summary(data)
        assert "What Changed" in result
        assert "Why" in result
        assert "Cleaned up temp files" in result


# =============================================================================
# 4. fetch_session_metadata Edge Cases
# =============================================================================


class TestFetchSessionMetadata:
    """fetch_session_metadata from store with various states."""

    @patch("governance.stores._sessions_store", {})
    def test_empty_store_returns_basic(self):
        result = fetch_session_metadata(["S-MISSING"])
        assert len(result) == 1
        assert result[0]["session_id"] == "S-MISSING"
        assert "description" not in result[0]

    @patch("governance.stores._sessions_store", {
        "S-100": {"description": "Bug hunt", "duration": "30m", "agent_id": "code-agent"},
    })
    def test_found_session_includes_metadata(self):
        result = fetch_session_metadata(["S-100"])
        assert result[0]["description"] == "Bug hunt"
        assert result[0]["duration"] == "30m"
        assert result[0]["agent_id"] == "code-agent"

    @patch("governance.stores._sessions_store", {
        "S-101": {"topic": "Research session"},
    })
    def test_topic_fallback_when_no_description(self):
        result = fetch_session_metadata(["S-101"])
        desc = result[0].get("description")
        # description or topic — either way, topic is returned
        assert desc == "Research session" or result[0].get("topic") is not None

    @patch("governance.stores._sessions_store", {})
    def test_empty_list_returns_empty(self):
        result = fetch_session_metadata([])
        assert result == []

    @patch("governance.stores._sessions_store", {
        "S-200": {"description": "Found"},
    })
    def test_mixed_found_and_missing(self):
        result = fetch_session_metadata(["S-200", "S-MISSING"])
        assert len(result) == 2
        assert result[0]["description"] == "Found"
        assert "description" not in result[1]


# =============================================================================
# 5. _build_generic_summary — Combination Tests
# =============================================================================


class TestBuildGenericSummary:
    """Generic summary with partial data combinations."""

    def test_only_sessions(self):
        result = _build_generic_summary({"linked_sessions": ["S-1"]})
        assert "### Sessions" in result
        assert "S-1" in result

    def test_only_documents(self):
        result = _build_generic_summary({"linked_documents": ["doc.md"]})
        assert "### Linked Documents" in result
        assert "doc.md" in result

    def test_only_commits(self):
        result = _build_generic_summary({"linked_commits": ["abc"]})
        assert "### Commits" in result
        assert "abc" in result

    def test_only_evidence(self):
        result = _build_generic_summary({"evidence": "Tests pass"})
        assert "### Evidence" in result
        assert "Tests pass" in result

    def test_all_empty_returns_minimal(self):
        result = _build_generic_summary({})
        assert result == "Task completed."

    def test_all_populated(self):
        data = {
            "linked_sessions": ["S-1"],
            "linked_documents": ["doc.md"],
            "linked_commits": ["abc"],
            "evidence": "Tests pass",
        }
        result = _build_generic_summary(data)
        assert "### Sessions" in result
        assert "### Linked Documents" in result
        assert "### Commits" in result
        assert "### Evidence" in result


# =============================================================================
# 6. Template Structure Validation
# =============================================================================


class TestTemplateStructure:
    """Every template section has all required keys."""

    def test_all_types_have_sessions_section(self):
        """Every type template should end with a Sessions section."""
        for task_type, sections in TYPE_RESOLUTION_TEMPLATES.items():
            last = sections[-1]
            assert last["key"] == "linked_sessions", (
                f"{task_type} template doesn't end with Sessions section"
            )

    def test_no_duplicate_titles_within_type(self):
        for task_type, sections in TYPE_RESOLUTION_TEMPLATES.items():
            titles = [s["title"] for s in sections]
            assert len(titles) == len(set(titles)), (
                f"{task_type} has duplicate section titles: {titles}"
            )
