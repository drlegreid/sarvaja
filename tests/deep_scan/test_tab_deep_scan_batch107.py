"""Deep scan batch 107: TypeDB access + session services.

Batch 107 findings: 14 total, 0 confirmed fixes, 14 rejected.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


# ── TypeDB task conversion defense ──────────────


class TestTypeDBTaskConversion:
    """Verify _task_to_dict includes all active fields."""

    def test_task_to_dict_returns_all_core_fields(self):
        """_task_to_dict includes all core task fields."""
        from governance.stores.typedb_access import _task_to_dict

        task = MagicMock()
        task.id = "TASK-001"
        task.name = "Test Task"
        task.description = "Description"
        task.body = "Full body"
        task.phase = "implementation"
        task.status = "TODO"
        task.priority = "HIGH"
        task.task_type = "gap"
        task.agent_id = "code-agent"
        task.created_at = datetime(2026, 2, 15)
        task.claimed_at = None
        task.completed_at = None
        task.resolution = None
        task.linked_rules = ["RULE-001"]
        task.linked_sessions = ["SESSION-001"]
        task.linked_commits = []
        task.linked_documents = []
        task.gap_id = "GAP-001"
        task.evidence = None
        task.document_path = None

        result = _task_to_dict(task)
        assert result["task_id"] == "TASK-001"
        assert result["description"] == "Full body"  # body takes priority
        assert result["linked_rules"] == ["RULE-001"]
        assert result["linked_sessions"] == ["SESSION-001"]

    def test_task_to_dict_null_safe_lists(self):
        """_task_to_dict converts None lists to empty lists."""
        from governance.stores.typedb_access import _task_to_dict

        task = MagicMock()
        task.id = "TASK-002"
        task.name = ""
        task.description = ""
        task.body = None
        task.phase = "planning"
        task.status = "OPEN"
        task.priority = "LOW"
        task.task_type = None
        task.agent_id = None
        task.created_at = None
        task.claimed_at = None
        task.completed_at = None
        task.resolution = None
        task.linked_rules = None
        task.linked_sessions = None
        task.linked_commits = None
        task.linked_documents = None
        task.gap_id = None
        task.evidence = None
        task.document_path = None

        result = _task_to_dict(task)
        assert result["linked_rules"] == []
        assert result["linked_sessions"] == []
        assert result["linked_commits"] == []
        assert result["linked_documents"] == []

    def test_task_body_priority_over_description(self):
        """_task_to_dict uses body > description > name for display."""
        from governance.stores.typedb_access import _task_to_dict

        task = MagicMock()
        task.id = "TASK-003"
        task.name = "Short"
        task.description = "Medium desc"
        task.body = "Full body text"
        task.phase = "planning"
        task.status = "TODO"
        task.priority = "MEDIUM"
        task.task_type = None
        task.agent_id = None
        task.created_at = None
        task.claimed_at = None
        task.completed_at = None
        task.resolution = None
        task.linked_rules = []
        task.linked_sessions = []
        task.linked_commits = []
        task.linked_documents = []
        task.gap_id = None
        task.evidence = None
        task.document_path = None

        result = _task_to_dict(task)
        # body takes priority per GAP-DATA-001
        assert result["description"] == "Full body text"


# ── TypeDB session conversion defense ──────────────


class TestTypeDBSessionConversion:
    """Verify _session_to_dict handles all edge cases."""

    def test_session_to_dict_null_start_time(self):
        """_session_to_dict uses now() for null start_time."""
        from governance.stores.typedb_access import _session_to_dict

        session = MagicMock()
        session.id = "SESSION-TEST"
        session.started_at = None
        session.completed_at = None
        session.name = "Test"
        session.description = "Test session"
        session.status = "ACTIVE"
        session.agent_id = "code-agent"
        session.tasks_completed = 0
        session.tool_calls = []
        session.thinking_blocks = []
        session.linked_rules = []
        session.linked_decisions = []
        session.evidence_files = []
        session.cc_session_uuid = None
        session.cc_project_slug = None
        session.cc_git_branch = None
        session.cc_tool_count = None
        session.cc_thinking_chars = None
        session.cc_compaction_count = None
        session.project_id = None

        result = _session_to_dict(session)
        assert result["start_time"] is not None
        assert result["session_id"] == "SESSION-TEST"


# ── Transcript generator defense ──────────────


class TestTranscriptGeneratorDefense:
    """Verify transcript handles file and generator edge cases."""

    def test_stream_transcript_missing_file_returns_empty(self):
        """stream_transcript yields nothing for missing file."""
        from governance.services.cc_transcript import stream_transcript

        entries = list(stream_transcript("/nonexistent/path.jsonl"))
        assert entries == []

    def test_stream_transcript_empty_file(self):
        """stream_transcript yields nothing for empty file."""
        import tempfile
        import os
        from governance.services.cc_transcript import stream_transcript

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write("")
            tmp = f.name
        try:
            entries = list(stream_transcript(tmp))
            assert entries == []
        finally:
            os.unlink(tmp)

    def test_stream_transcript_malformed_json(self):
        """stream_transcript skips malformed JSON lines."""
        import tempfile
        import os
        from governance.services.cc_transcript import stream_transcript

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write("not valid json\n")
            f.write("{also broken\n")
            tmp = f.name
        try:
            entries = list(stream_transcript(tmp))
            assert entries == []
        finally:
            os.unlink(tmp)


# ── Session service defense ──────────────


class TestSessionServiceDefense:
    """Verify session service handles edge cases."""

    def test_get_session_returns_dict_type(self):
        """get_session returns dict, not SessionResponse."""
        from governance.services.sessions import get_session
        import inspect

        sig = inspect.signature(get_session)
        ret_str = str(sig.return_annotation)
        assert "Dict" in ret_str or "dict" in ret_str

    def test_get_session_none_for_missing(self):
        """get_session returns None for non-existent session."""
        from governance.services.sessions import get_session

        with patch("governance.services.sessions_crud.get_session_from_typedb", return_value=None):
            result = get_session("NON-EXISTENT")
            assert result is None


# ── Evidence markdown defense ──────────────


class TestEvidenceMarkdownDefense:
    """Verify evidence rendering handles edge cases."""

    def test_render_with_default_values(self):
        """render_evidence_markdown uses defaults for missing fields."""
        from governance.services.session_evidence import render_evidence_markdown

        minimal = {
            "session_id": "SESSION-TEST",
            "tasks": [],
            "decisions": [],
            "tool_calls": [],
            "duration": "1h",
            "status": "COMPLETED",
        }
        md = render_evidence_markdown(minimal)
        assert "SESSION-TEST" in md
        assert "COMPLETED" in md

    def test_render_with_pipe_in_decision_title(self):
        """Decision titles with pipes are escaped in markdown table."""
        from governance.services.session_evidence import render_evidence_markdown

        data = {
            "session_id": "SESSION-TEST",
            "tasks": [],
            "decisions": [
                {
                    "decision_id": "DEC-001",
                    "title": "Input | Output | Both",
                    "rationale": "Need to handle pipe chars",
                    "status": "APPROVED",
                }
            ],
            "tool_calls": [],
            "duration": "1h",
            "status": "COMPLETED",
        }
        md = render_evidence_markdown(data)
        assert "Input \\| Output \\| Both" in md


# ── CC session scanner defense ──────────────


class TestCCSessionScannerDefense:
    """Verify CC session scanner handles edge cases."""

    def test_discover_cc_projects_no_dir(self):
        """discover_cc_projects handles missing .claude directory."""
        from governance.services.cc_session_scanner import discover_cc_projects

        with patch("governance.services.cc_session_scanner.DEFAULT_CC_DIR") as mock_dir:
            mock_dir.is_dir.return_value = False
            result = discover_cc_projects()
            assert isinstance(result, list)
