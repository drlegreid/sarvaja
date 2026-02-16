"""TDD Tests for Session Evidence Auto-Generation (P0 — HIGHEST PRIORITY).

Architectural gap: end_session() does NOT auto-generate evidence documents
when evidence_files is not provided. Sessions completed via REST API or MCP
have no evidence attached, leaving an audit trail gap.

Solution: A session evidence generation service that:
1. Compiles tool calls, decisions, tasks from _sessions_store
2. Generates comprehensive markdown evidence document
3. Writes to evidence/{SESSION-ID}.md
4. Links evidence to session via evidence_files array

These tests are TDD — they WILL FAIL until the service is implemented.
"""
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Test Group 1: Evidence Generator Service Exists
# ---------------------------------------------------------------------------

class TestEvidenceGeneratorServiceExists:
    """Verify the auto-evidence generation service can be imported."""

    def test_service_module_importable(self):
        """Session evidence generator module exists and is importable."""
        from governance.services.session_evidence import generate_session_evidence
        assert callable(generate_session_evidence)

    def test_compile_evidence_data_importable(self):
        """compile_evidence_data helper exists for gathering session data."""
        from governance.services.session_evidence import compile_evidence_data
        assert callable(compile_evidence_data)

    def test_render_evidence_markdown_importable(self):
        """render_evidence_markdown converts evidence data to markdown."""
        from governance.services.session_evidence import render_evidence_markdown
        assert callable(render_evidence_markdown)


# ---------------------------------------------------------------------------
# Test Group 2: compile_evidence_data
# ---------------------------------------------------------------------------

class TestCompileEvidenceData:
    """compile_evidence_data gathers session artifacts from stores."""

    def test_returns_dict_with_required_keys(self):
        """Evidence data dict has session_id, tool_calls, decisions, tasks, etc."""
        from governance.services.session_evidence import compile_evidence_data

        session_data = {
            "session_id": "SESSION-2026-02-15-TEST",
            "status": "COMPLETED",
            "start_time": "2026-02-15T10:00:00",
            "end_time": "2026-02-15T11:00:00",
            "description": "Test session",
            "agent_id": "code-agent",
        }

        result = compile_evidence_data(session_data)

        assert isinstance(result, dict)
        assert "session_id" in result
        assert "start_time" in result
        assert "end_time" in result
        assert "tool_calls" in result
        assert "decisions" in result
        assert "tasks" in result
        assert "description" in result

    def test_includes_tool_calls_from_session(self):
        """Tool calls are extracted from session data if present."""
        from governance.services.session_evidence import compile_evidence_data

        session_data = {
            "session_id": "SESSION-2026-02-15-TOOLS",
            "status": "COMPLETED",
            "start_time": "2026-02-15T10:00:00",
            "end_time": "2026-02-15T11:00:00",
            "tool_calls": [
                {"tool_name": "Read", "timestamp": "2026-02-15T10:05:00"},
                {"tool_name": "Edit", "timestamp": "2026-02-15T10:10:00"},
            ],
        }

        result = compile_evidence_data(session_data)
        assert len(result["tool_calls"]) == 2
        assert result["tool_calls"][0]["tool_name"] == "Read"

    def test_includes_decisions_from_session(self):
        """Decisions linked to session are included."""
        from governance.services.session_evidence import compile_evidence_data

        session_data = {
            "session_id": "SESSION-2026-02-15-DECISIONS",
            "status": "COMPLETED",
            "start_time": "2026-02-15T10:00:00",
            "end_time": "2026-02-15T11:00:00",
            "decisions": [
                {"decision_id": "DEC-001", "title": "Use TypeDB"},
            ],
        }

        result = compile_evidence_data(session_data)
        assert len(result["decisions"]) >= 1

    def test_computes_duration(self):
        """Duration is computed from start/end times."""
        from governance.services.session_evidence import compile_evidence_data

        session_data = {
            "session_id": "SESSION-2026-02-15-DURATION",
            "status": "COMPLETED",
            "start_time": "2026-02-15T10:00:00",
            "end_time": "2026-02-15T11:30:00",
        }

        result = compile_evidence_data(session_data)
        assert "duration" in result
        assert result["duration"] == "1h 30m"

    def test_handles_missing_fields_gracefully(self):
        """Missing optional fields default to empty lists/None."""
        from governance.services.session_evidence import compile_evidence_data

        session_data = {
            "session_id": "SESSION-2026-02-15-MINIMAL",
            "status": "COMPLETED",
        }

        result = compile_evidence_data(session_data)
        assert result["tool_calls"] == []
        assert result["decisions"] == []
        assert result["tasks"] == []


# ---------------------------------------------------------------------------
# Test Group 3: render_evidence_markdown
# ---------------------------------------------------------------------------

class TestRenderEvidenceMarkdown:
    """render_evidence_markdown produces valid markdown evidence."""

    def test_produces_markdown_string(self):
        """Output is a non-empty string."""
        from governance.services.session_evidence import render_evidence_markdown

        evidence_data = {
            "session_id": "SESSION-2026-02-15-TEST",
            "start_time": "2026-02-15T10:00:00",
            "end_time": "2026-02-15T11:00:00",
            "duration": "1h 0m",
            "description": "Test session",
            "agent_id": "code-agent",
            "tool_calls": [],
            "decisions": [],
            "tasks": [],
        }

        md = render_evidence_markdown(evidence_data)
        assert isinstance(md, str)
        assert len(md) > 50

    def test_contains_session_header(self):
        """Markdown has session ID in title."""
        from governance.services.session_evidence import render_evidence_markdown

        evidence_data = {
            "session_id": "SESSION-2026-02-15-HEADER",
            "start_time": "2026-02-15T10:00:00",
            "end_time": "2026-02-15T11:00:00",
            "duration": "1h 0m",
            "tool_calls": [],
            "decisions": [],
            "tasks": [],
        }

        md = render_evidence_markdown(evidence_data)
        assert "SESSION-2026-02-15-HEADER" in md
        assert "# " in md  # Has a markdown heading

    def test_contains_tool_calls_section(self):
        """Markdown has tool calls section when tools exist."""
        from governance.services.session_evidence import render_evidence_markdown

        evidence_data = {
            "session_id": "SESSION-2026-02-15-TOOLS",
            "start_time": "2026-02-15T10:00:00",
            "end_time": "2026-02-15T11:00:00",
            "duration": "1h 0m",
            "tool_calls": [
                {"tool_name": "Read", "timestamp": "2026-02-15T10:05:00"},
                {"tool_name": "Edit", "timestamp": "2026-02-15T10:10:00"},
                {"tool_name": "Read", "timestamp": "2026-02-15T10:15:00"},
            ],
            "decisions": [],
            "tasks": [],
        }

        md = render_evidence_markdown(evidence_data)
        assert "Tool Calls" in md or "tool_calls" in md.lower()
        assert "Read" in md

    def test_contains_tool_summary_counts(self):
        """Markdown summarizes tool call counts (e.g., Read: 2, Edit: 1)."""
        from governance.services.session_evidence import render_evidence_markdown

        evidence_data = {
            "session_id": "SESSION-2026-02-15-COUNTS",
            "start_time": "2026-02-15T10:00:00",
            "end_time": "2026-02-15T11:00:00",
            "duration": "1h 0m",
            "tool_calls": [
                {"tool_name": "Read", "timestamp": "10:05"},
                {"tool_name": "Read", "timestamp": "10:10"},
                {"tool_name": "Edit", "timestamp": "10:15"},
            ],
            "decisions": [],
            "tasks": [],
        }

        md = render_evidence_markdown(evidence_data)
        # Should show summary like "Read | 2" or "Read: 2"
        assert "2" in md  # Count of Read calls
        assert "1" in md  # Count of Edit calls

    def test_contains_decisions_section(self):
        """Markdown has decisions section when decisions exist."""
        from governance.services.session_evidence import render_evidence_markdown

        evidence_data = {
            "session_id": "SESSION-2026-02-15-DEC",
            "start_time": "2026-02-15T10:00:00",
            "end_time": "2026-02-15T11:00:00",
            "duration": "1h 0m",
            "tool_calls": [],
            "decisions": [
                {"decision_id": "DEC-001", "title": "Use TypeDB", "rationale": "Best fit"},
            ],
            "tasks": [],
        }

        md = render_evidence_markdown(evidence_data)
        assert "Decision" in md
        assert "DEC-001" in md

    def test_contains_tasks_section(self):
        """Markdown has tasks section when tasks exist."""
        from governance.services.session_evidence import render_evidence_markdown

        evidence_data = {
            "session_id": "SESSION-2026-02-15-TASKS",
            "start_time": "2026-02-15T10:00:00",
            "end_time": "2026-02-15T11:00:00",
            "duration": "1h 0m",
            "tool_calls": [],
            "decisions": [],
            "tasks": [
                {"task_id": "TASK-001", "description": "Fix bug", "status": "DONE"},
            ],
        }

        md = render_evidence_markdown(evidence_data)
        assert "Task" in md
        assert "TASK-001" in md


# ---------------------------------------------------------------------------
# Test Group 4: generate_session_evidence (end-to-end)
# ---------------------------------------------------------------------------

class TestGenerateSessionEvidence:
    """generate_session_evidence writes file and returns path."""

    def test_writes_evidence_file_to_disk(self):
        """Evidence file is created at expected path."""
        from governance.services.session_evidence import generate_session_evidence

        session_data = {
            "session_id": "SESSION-2026-02-15-E2E",
            "status": "COMPLETED",
            "start_time": "2026-02-15T10:00:00",
            "end_time": "2026-02-15T11:00:00",
            "description": "E2E test",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = generate_session_evidence(session_data, output_dir=Path(tmpdir))
            assert path is not None
            assert Path(path).exists()
            content = Path(path).read_text()
            assert "SESSION-2026-02-15-E2E" in content

    def test_filename_matches_session_id(self):
        """Evidence filename is {session_id}.md."""
        from governance.services.session_evidence import generate_session_evidence

        session_data = {
            "session_id": "SESSION-2026-02-15-FNAME",
            "status": "COMPLETED",
            "start_time": "2026-02-15T10:00:00",
            "end_time": "2026-02-15T11:00:00",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = generate_session_evidence(session_data, output_dir=Path(tmpdir))
            assert Path(path).name == "SESSION-2026-02-15-FNAME.md"

    def test_returns_none_for_active_session(self):
        """Active sessions should not generate evidence."""
        from governance.services.session_evidence import generate_session_evidence

        session_data = {
            "session_id": "SESSION-2026-02-15-ACTIVE",
            "status": "ACTIVE",
            "start_time": "2026-02-15T10:00:00",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = generate_session_evidence(session_data, output_dir=Path(tmpdir))
            assert path is None

    def test_idempotent_no_overwrite_existing(self):
        """If evidence file already exists, returns existing path without overwrite."""
        from governance.services.session_evidence import generate_session_evidence

        session_data = {
            "session_id": "SESSION-2026-02-15-IDEMPOTENT",
            "status": "COMPLETED",
            "start_time": "2026-02-15T10:00:00",
            "end_time": "2026-02-15T11:00:00",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            # First call creates
            path1 = generate_session_evidence(session_data, output_dir=Path(tmpdir))
            mtime1 = Path(path1).stat().st_mtime

            # Second call returns existing
            path2 = generate_session_evidence(session_data, output_dir=Path(tmpdir))
            mtime2 = Path(path2).stat().st_mtime
            assert mtime1 == mtime2  # File not overwritten

    def test_includes_tool_call_data_no_llm(self):
        """Evidence contains tool call data collated via API, no LLM generation."""
        from governance.services.session_evidence import generate_session_evidence

        session_data = {
            "session_id": "SESSION-2026-02-15-NOLLM",
            "status": "COMPLETED",
            "start_time": "2026-02-15T10:00:00",
            "end_time": "2026-02-15T11:00:00",
            "tool_calls": [
                {"tool_name": "Read", "timestamp": "10:05", "args": {"path": "/a.py"}},
                {"tool_name": "Bash", "timestamp": "10:10", "args": {"cmd": "ls"}},
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = generate_session_evidence(session_data, output_dir=Path(tmpdir))
            content = Path(path).read_text()
            assert "Read" in content
            assert "Bash" in content
            # Tool summary without LLM-generated text
            assert "Tool" in content


# ---------------------------------------------------------------------------
# Test Group 5: Integration with end_session
# ---------------------------------------------------------------------------

class TestEndSessionAutoEvidence:
    """end_session should auto-generate evidence when none provided."""

    @patch("governance.services.sessions_lifecycle.get_typedb_client")
    @patch("governance.services.sessions_lifecycle._sessions_store", new_callable=dict)
    def test_end_session_generates_evidence_when_none_provided(
        self, mock_store, mock_client_fn
    ):
        """When evidence_files=None, end_session auto-generates evidence."""
        mock_client_fn.return_value = None  # Force fallback to in-memory

        mock_store["SESSION-2026-02-15-AUTOEVID"] = {
            "session_id": "SESSION-2026-02-15-AUTOEVID",
            "status": "ACTIVE",
            "start_time": "2026-02-15T10:00:00",
            "description": "Auto-evidence test",
            "tool_calls": [
                {"tool_name": "Read", "timestamp": "10:05"},
            ],
        }

        with patch(
            "governance.services.sessions_lifecycle.generate_session_evidence"
        ) as mock_gen:
            mock_gen.return_value = "/tmp/evidence/SESSION-2026-02-15-AUTOEVID.md"

            from governance.services.sessions_lifecycle import end_session
            result = end_session("SESSION-2026-02-15-AUTOEVID", source="test")

            # Should have called generate_session_evidence
            mock_gen.assert_called_once()
            # evidence_files should contain the auto-generated path
            assert result is not None
            evidence = result.get("evidence_files", [])
            assert len(evidence) >= 1

    @patch("governance.services.sessions_lifecycle.get_typedb_client")
    @patch("governance.services.sessions_lifecycle._sessions_store", new_callable=dict)
    def test_end_session_skips_auto_evidence_when_provided(
        self, mock_store, mock_client_fn
    ):
        """When evidence_files are explicitly provided, skip auto-generation."""
        mock_client_fn.return_value = None

        mock_store["SESSION-2026-02-15-SKIPEVID"] = {
            "session_id": "SESSION-2026-02-15-SKIPEVID",
            "status": "ACTIVE",
            "start_time": "2026-02-15T10:00:00",
        }

        with patch(
            "governance.services.sessions_lifecycle.generate_session_evidence"
        ) as mock_gen:
            from governance.services.sessions_lifecycle import end_session
            result = end_session(
                "SESSION-2026-02-15-SKIPEVID",
                evidence_files=["evidence/manual.md"],
                source="test",
            )

            # Should NOT call auto-generation
            mock_gen.assert_not_called()
            assert result is not None
            assert result.get("evidence_files") == ["evidence/manual.md"]
