"""
Unit tests for Handoff Models and Data Types.

Per DOC-SIZE-01-v1: Tests for orchestrator/handoff_pkg/models.py module.
Tests: HandoffStatus, AgentRole, _extract_section, _extract_list,
       _extract_numbered_list, TaskHandoff (to_dict, to_markdown, from_markdown).
"""

from governance.orchestrator.handoff_pkg.models import (
    HandoffStatus,
    AgentRole,
    _extract_section,
    _extract_list,
    _extract_numbered_list,
    TaskHandoff,
)


class TestEnums:
    def test_handoff_status_values(self):
        assert HandoffStatus.READY_FOR_RESEARCH == "READY_FOR_RESEARCH"
        assert HandoffStatus.COMPLETED == "COMPLETED"
        assert HandoffStatus.BLOCKED == "BLOCKED"
        assert len(HandoffStatus) == 7

    def test_agent_role_values(self):
        assert AgentRole.RESEARCH == "RESEARCH"
        assert AgentRole.CODING == "CODING"
        assert len(AgentRole) == 4


class TestExtractSection:
    def test_basic(self):
        content = "## Context\nSome context here\nMore lines\n## Next"
        result = _extract_section(content, "## Context")
        assert "Some context here" in result
        assert "More lines" in result

    def test_stops_at_header(self):
        content = "## A\nContent A\n## B\nContent B"
        result = _extract_section(content, "## A")
        assert "Content A" in result
        assert "Content B" not in result

    def test_stops_at_separator(self):
        content = "## A\nContent A\n---\nAfter"
        result = _extract_section(content, "## A")
        assert "Content A" in result
        assert "After" not in result

    def test_no_match(self):
        result = _extract_section("nothing", "## Missing")
        assert result == ""


class TestExtractList:
    def test_basic(self):
        content = "### Files\n- file1.py\n- file2.py\n## Next"
        result = _extract_list(content, "### Files")
        assert len(result) == 2
        assert "file1.py" in result

    def test_strips_backticks(self):
        content = "### Files\n- `path/to/file.py`"
        result = _extract_list(content, "### Files")
        assert result[0] == "path/to/file.py"

    def test_empty(self):
        result = _extract_list("### Files\n## Next", "### Files")
        assert result == []


class TestExtractNumberedList:
    def test_basic(self):
        content = "### Steps\n1. Do A\n2. Do B\n## Next"
        result = _extract_numbered_list(content, "### Steps")
        assert len(result) == 2
        assert result[0] == "Do A"
        assert result[1] == "Do B"

    def test_empty(self):
        result = _extract_numbered_list("### Steps\n## Next", "### Steps")
        assert result == []


class TestTaskHandoff:
    def _make_handoff(self, **kw):
        defaults = dict(
            task_id="GAP-UI-005", title="Fix UI bug",
            from_agent="RESEARCH", to_agent="CODING",
            status="READY_FOR_CODING",
        )
        defaults.update(kw)
        return TaskHandoff(**defaults)

    def test_defaults(self):
        h = self._make_handoff()
        assert h.context_summary == ""
        assert h.files_examined == []
        assert h.priority == "MEDIUM"

    def test_to_dict(self):
        h = self._make_handoff(context_summary="Found bug")
        d = h.to_dict()
        assert d["task_id"] == "GAP-UI-005"
        assert d["context_summary"] == "Found bug"

    def test_to_markdown(self):
        h = self._make_handoff(
            context_summary="Bug in sidebar",
            files_examined=["sidebar.py"],
            evidence_gathered=["Evidence 1"],
            recommended_action="Fix the CSS",
            action_steps=["Step 1", "Step 2"],
            constraints=["No breaking changes"],
            linked_rules=["UI-TRAME-01-v1"],
            source_session_id="SESSION-2026-02-11",
        )
        md = h.to_markdown()
        assert "# Task Handoff: Fix UI bug" in md
        assert "**From:** RESEARCH Agent" in md
        assert "**To:** CODING Agent" in md
        assert "Bug in sidebar" in md
        assert "`sidebar.py`" in md
        assert "Evidence 1" in md
        assert "Fix the CSS" in md
        assert "1. Step 1" in md
        assert "No breaking changes" in md
        assert "UI-TRAME-01-v1" in md
        assert "SESSION-2026-02-11" in md

    def test_roundtrip_markdown(self):
        h = self._make_handoff(
            context_summary="Found bug in sidebar",
            files_examined=["sidebar.py", "nav.py"],
            evidence_gathered=["Logs show error"],
            recommended_action="Fix the CSS layout",
            action_steps=["Step 1", "Step 2"],
            constraints=["No breaking changes"],
            linked_rules=["UI-TRAME-01-v1"],
            priority="HIGH",
        )
        md = h.to_markdown()
        parsed = TaskHandoff.from_markdown(md)
        assert parsed is not None
        assert parsed.task_id == "GAP-UI-005"
        assert parsed.title == "Fix UI bug"
        assert parsed.from_agent == "RESEARCH"
        assert parsed.to_agent == "CODING"
        assert parsed.priority == "HIGH"
        assert len(parsed.files_examined) == 2
        assert len(parsed.action_steps) == 2

    def test_from_markdown_no_task_id(self):
        result = TaskHandoff.from_markdown("# No task info here\nJust text")
        assert result is None

    def test_to_markdown_minimal(self):
        h = self._make_handoff()
        md = h.to_markdown()
        assert "# Task Handoff:" in md
        assert "GAP-UI-005" in md
