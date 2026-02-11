"""
Unit tests for Handoff Models and Data Types.

Per DOC-SIZE-01-v1: Tests for extracted handoff_pkg/models.py module.
Tests: HandoffStatus, AgentRole, TaskHandoff, markdown parsing utilities.
"""

import pytest
from datetime import datetime

from governance.orchestrator.handoff_pkg.models import (
    HandoffStatus,
    AgentRole,
    TaskHandoff,
    _extract_section,
    _extract_list,
    _extract_numbered_list,
)


class TestEnums:
    """Tests for HandoffStatus and AgentRole enums."""

    def test_handoff_statuses(self):
        assert HandoffStatus.READY_FOR_RESEARCH == "READY_FOR_RESEARCH"
        assert HandoffStatus.COMPLETED == "COMPLETED"
        assert HandoffStatus.BLOCKED == "BLOCKED"
        assert len(HandoffStatus) == 7

    def test_agent_roles(self):
        assert AgentRole.RESEARCH == "RESEARCH"
        assert AgentRole.CODING == "CODING"
        assert len(AgentRole) == 4


class TestExtractSection:
    """Tests for _extract_section()."""

    def test_extracts_content(self):
        content = "## Context Gathered\nSome context\nMore context\n## Next Section"
        result = _extract_section(content, "## Context Gathered")
        assert "Some context" in result
        assert "More context" in result
        assert "Next Section" not in result

    def test_stops_at_h2(self):
        content = "## A\nline1\n## B\nline2"
        result = _extract_section(content, "## A")
        assert "line1" in result
        assert "line2" not in result

    def test_stops_at_h3(self):
        content = "## A\nline1\n### Sub\nline2"
        result = _extract_section(content, "## A")
        assert "line1" in result
        assert "line2" not in result

    def test_empty_when_not_found(self):
        assert _extract_section("no match", "## Missing") == ""


class TestExtractList:
    """Tests for _extract_list()."""

    def test_extracts_items(self):
        content = "### Files Examined\n- file1.py\n- file2.py\n### Next"
        result = _extract_list(content, "### Files Examined")
        assert result == ["file1.py", "file2.py"]

    def test_strips_backticks(self):
        content = "### Files\n- `src/main.py`\n"
        result = _extract_list(content, "### Files")
        assert result == ["src/main.py"]

    def test_empty_when_no_items(self):
        content = "### Files\nno bullets\n"
        assert _extract_list(content, "### Files") == []


class TestExtractNumberedList:
    """Tests for _extract_numbered_list()."""

    def test_extracts_items(self):
        content = "### Steps\n1. Do A\n2. Do B\n3. Do C\n"
        result = _extract_numbered_list(content, "### Steps")
        assert result == ["Do A", "Do B", "Do C"]

    def test_empty_when_not_found(self):
        assert _extract_numbered_list("no match", "### Steps") == []


class TestTaskHandoff:
    """Tests for TaskHandoff dataclass."""

    @pytest.fixture
    def sample_handoff(self):
        return TaskHandoff(
            task_id="GAP-UI-005",
            title="Implement dark mode",
            from_agent="RESEARCH",
            to_agent="CODING",
            status="READY_FOR_CODING",
            context_summary="Research complete",
            files_examined=["src/theme.py"],
            evidence_gathered=["User survey results"],
            recommended_action="Add theme toggle",
            action_steps=["Add CSS vars", "Create toggle component"],
            linked_rules=["UI-THEME-01"],
            constraints=["Must support high contrast"],
            priority="HIGH",
        )

    def test_to_dict(self, sample_handoff):
        d = sample_handoff.to_dict()
        assert d["task_id"] == "GAP-UI-005"
        assert d["from_agent"] == "RESEARCH"
        assert d["priority"] == "HIGH"
        assert isinstance(d["files_examined"], list)

    def test_to_markdown(self, sample_handoff):
        md = sample_handoff.to_markdown()
        assert "# Task Handoff: Implement dark mode" in md
        assert "**From:** RESEARCH Agent" in md
        assert "**To:** CODING Agent" in md
        assert "**Task ID:** GAP-UI-005" in md
        assert "Research complete" in md
        assert "`src/theme.py`" in md
        assert "1. Add CSS vars" in md
        assert "UI-THEME-01" in md

    def test_to_markdown_minimal(self):
        h = TaskHandoff(
            task_id="T-1", title="Test", from_agent="R", to_agent="C", status="READY"
        )
        md = h.to_markdown()
        assert "# Task Handoff: Test" in md
        assert "**Task ID:** T-1" in md

    def test_roundtrip_markdown(self, sample_handoff):
        md = sample_handoff.to_markdown()
        parsed = TaskHandoff.from_markdown(md)
        assert parsed is not None
        assert parsed.task_id == "GAP-UI-005"
        assert parsed.title == "Implement dark mode"
        assert parsed.from_agent == "RESEARCH"
        assert parsed.to_agent == "CODING"
        assert parsed.status == "READY_FOR_CODING"
        assert parsed.priority == "HIGH"
        assert "src/theme.py" in parsed.files_examined
        assert len(parsed.action_steps) == 2

    def test_from_markdown_no_task_id(self):
        assert TaskHandoff.from_markdown("no task id here") is None

    def test_from_markdown_with_session(self, sample_handoff):
        sample_handoff.source_session_id = "SESSION-2026-02-11-TEST"
        md = sample_handoff.to_markdown()
        parsed = TaskHandoff.from_markdown(md)
        assert parsed.source_session_id == "SESSION-2026-02-11-TEST"

    def test_default_created_at(self):
        h = TaskHandoff(task_id="T-1", title="T", from_agent="R", to_agent="C", status="S")
        assert h.created_at is not None
        # Should be parseable as ISO format
        datetime.fromisoformat(h.created_at)

    def test_default_lists_empty(self):
        h = TaskHandoff(task_id="T-1", title="T", from_agent="R", to_agent="C", status="S")
        assert h.files_examined == []
        assert h.evidence_gathered == []
        assert h.action_steps == []
        assert h.linked_rules == []
        assert h.constraints == []
