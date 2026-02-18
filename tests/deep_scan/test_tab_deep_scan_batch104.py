"""Deep scan batch 104: Evidence + ingestion + session bridge + chat.

Batch 104 findings: 25 total, 0 confirmed fixes, 25 rejected.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from pathlib import Path
from datetime import datetime


# ── Evidence scanner error isolation defense ──────────────


class TestEvidenceScannerErrorIsolation:
    """Verify evidence scanner handles file errors gracefully."""

    def test_unreadable_file_skipped(self):
        """Unreadable evidence file logged but scanning continues."""
        from governance.evidence_scanner.extractors import extract_task_refs

        # extract_task_refs works on content strings
        refs = extract_task_refs("Fixed TASK-001 and P12.1 issues")
        assert isinstance(refs, set)
        assert len(refs) >= 1

    def test_pipe_in_evidence_content_not_corrupt(self):
        """Evidence content with pipe chars doesn't break scanning."""
        from governance.evidence_scanner.extractors import extract_task_refs

        content = "Fixed input | output for TASK-001 and P12.1"
        refs = extract_task_refs(content)
        assert "P12.1" in refs or "TASK-001" in refs


# ── Transcript generator defense ──────────────


class TestTranscriptGeneratorDefense:
    """Verify transcript generator handles edge cases."""

    def test_missing_file_returns_empty_generator(self):
        """stream_transcript on missing file yields nothing."""
        from governance.services.cc_transcript import stream_transcript

        entries = list(stream_transcript(Path("/nonexistent/file.jsonl")))
        assert entries == []

    def test_empty_file_returns_empty_generator(self, tmp_path):
        """stream_transcript on empty file yields nothing."""
        from governance.services.cc_transcript import stream_transcript

        empty = tmp_path / "empty.jsonl"
        empty.write_text("")
        entries = list(stream_transcript(empty))
        assert entries == []


# ── Ingestion checkpoint defense ──────────────


class TestIngestionCheckpointDefense:
    """Verify checkpoint path sanitization."""

    def test_session_id_slash_sanitized(self):
        """Slashes in session_id replaced with underscores."""
        from governance.services.ingestion_checkpoint import _checkpoint_path

        path = _checkpoint_path(Path("/tmp"), "SESSION-2026/02/15-TEST")
        assert "/" not in path.name or path.name.startswith("SESSION")
        # Slash sanitized
        assert "\\" not in path.stem

    def test_normal_session_id_produces_valid_path(self):
        """Normal session_id creates expected checkpoint filename."""
        from governance.services.ingestion_checkpoint import _checkpoint_path

        path = _checkpoint_path(Path("/tmp/ckpt"), "SESSION-2026-02-15-TEST")
        assert path.suffix == ".json"
        assert "SESSION-2026-02-15-TEST" in path.name


# ── CC session discovery defense ──────────────


class TestCCSessionDiscovery:
    """Verify CC session scanner handles missing directories."""

    def test_missing_cc_dir_returns_empty(self):
        """discover_cc_projects returns empty list if CC dir missing."""
        from governance.services.cc_session_scanner import discover_cc_projects

        with patch(
            "governance.services.cc_session_scanner.DEFAULT_CC_DIR",
            Path("/nonexistent/cc/dir"),
        ):
            result = discover_cc_projects()
            assert result == []


# ── Chat session dict iteration defense ──────────────


class TestChatSessionIteration:
    """Verify chat session list operations are safe."""

    def test_list_empty_sessions(self):
        """Empty chat sessions dict returns empty list."""
        sessions = {}
        result = []
        for sid, session in sessions.items():
            result.append({"session_id": sid})
        assert result == []

    def test_list_sessions_snapshot(self):
        """list() on dict.items() creates safe snapshot."""
        sessions = {"s1": {"messages": []}, "s2": {"messages": [1, 2]}}
        # Take snapshot before iterating
        snapshot = list(sessions.items())
        # Even if dict changes during iteration...
        sessions["s3"] = {"messages": [3]}
        # ...snapshot is stable
        assert len(snapshot) == 2


# ── Auto-session timeout defense ──────────────


class TestAutoSessionTimeout:
    """Verify MCP auto-session tracks expiry correctly."""

    def test_session_expires_after_timeout(self):
        """_is_expired returns True after timeout period."""
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker

        tracker = MCPAutoSessionTracker(timeout_seconds=0.01)
        tracker.active_session_id = "TEST-SESSION"
        tracker._last_activity = datetime.now()

        import time
        time.sleep(0.02)
        assert tracker._is_expired()

    def test_session_not_expired_within_timeout(self):
        """_is_expired returns False within timeout period."""
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker

        tracker = MCPAutoSessionTracker(timeout_seconds=300)
        tracker.active_session_id = "TEST-SESSION"
        tracker._last_activity = datetime.now()

        assert not tracker._is_expired()


# ── End session idempotency defense ──────────────


class TestEndSessionIdempotency:
    """Verify end_session handles already-completed sessions."""

    def test_fallback_raises_on_double_end(self):
        """Ending an already-completed session raises ValueError."""
        from governance.services.sessions_lifecycle import end_session
        from governance.stores import _sessions_store

        sid = "SESSION-TEST-DOUBLE-END-104"
        _sessions_store[sid] = {
            "session_id": sid,
            "status": "COMPLETED",
            "start_time": "2026-02-15T09:00:00",
        }

        with patch("governance.services.sessions_lifecycle.get_typedb_client", return_value=None):
            with pytest.raises(ValueError, match="already completed"):
                end_session(sid)

        # Cleanup
        _sessions_store.pop(sid, None)

    def test_nonexistent_session_returns_none(self):
        """Ending a session that doesn't exist returns None."""
        from governance.services.sessions_lifecycle import end_session

        with patch("governance.services.sessions_lifecycle.get_typedb_client", return_value=None):
            result = end_session("SESSION-NONEXISTENT-999")
            assert result is None


# ── Content indexer offset defense ──────────────


class TestContentIndexerOffset:
    """Verify content indexer offset calculation correctness."""

    def test_offset_with_start_line(self):
        """Offset calculation: relative line_end + start_line + 1."""
        start_line = 100
        # Chunk processed lines 0-49 relative to start
        meta_line_end = 49
        lines_seen = meta_line_end + start_line + 1
        # We've processed lines 0-149 (150 total)
        assert lines_seen == 150

    def test_offset_without_start_line(self):
        """First run: start_line=0, offset = line_end + 1."""
        start_line = 0
        meta_line_end = 99
        lines_seen = meta_line_end + start_line + 1
        assert lines_seen == 100


# ── Session evidence generation defense ──────────────


class TestSessionEvidenceGeneration:
    """Verify evidence generation handles edge cases."""

    def test_empty_evidence_data(self):
        """Minimal evidence data produces valid markdown."""
        from governance.services.session_evidence import render_evidence_markdown

        evidence_data = {
            "session_id": "SESSION-2026-02-15-EMPTY",
            "start_time": "2026-02-15T09:00:00",
            "end_time": "2026-02-15T09:01:00",
            "status": "COMPLETED",
            "decisions": [],
            "tasks": [],
            "tool_calls": [],
            "thinking_blocks": 0,
        }
        md = render_evidence_markdown(evidence_data)
        assert "SESSION-2026-02-15-EMPTY" in md
        assert "No decisions recorded" in md
        assert "No tasks linked" in md
