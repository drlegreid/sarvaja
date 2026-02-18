"""Batch 213 — API startup + lifecycle + transcript defense tests.

Validates fixes for:
- BUG-213-ORPHAN-ENDTIME-001: ISO timestamp for orphaned sessions
- BUG-213-LIFECYCLE-UPDATE-001: merge order prevents stale status overwrite
- BUG-213-TRANSCRIPT-ENCODING-001: encoding on file open
"""
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime


SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-213-ORPHAN-ENDTIME-001: ISO timestamp for orphaned sessions ──

class TestOrphanEndTimeTimestamp:
    """cleanup_orphaned_chat_sessions must use ISO timestamp, not string."""

    def test_no_string_literal_end_time_in_source(self):
        """Source must not contain 'orphan-cleanup-on-startup' string literal."""
        src = (SRC / "governance/api_startup.py").read_text()
        assert '"orphan-cleanup-on-startup"' not in src

    def test_iso_timestamp_in_source(self):
        """Source must use datetime for end_time."""
        src = (SRC / "governance/api_startup.py").read_text()
        # Find the cleanup function and check it uses isoformat
        in_func = False
        found_iso = False
        for line in src.splitlines():
            if "def cleanup_orphaned_chat_sessions" in line:
                in_func = True
            elif in_func and line.strip().startswith("async def "):
                break
            elif in_func and "isoformat()" in line and "end_time" in line:
                found_iso = True
        assert found_iso, "Must use .isoformat() for end_time in cleanup"


# ── BUG-213-LIFECYCLE-UPDATE-001: Merge order in end_session ─────────

class TestLifecycleUpdateOrder:
    """end_session must set status/end_time AFTER merging _sessions_store."""

    def test_merge_before_status_in_source(self):
        """Source must call .update() BEFORE setting status='COMPLETED'."""
        src = (SRC / "governance/services/sessions_lifecycle.py").read_text()
        # Find the update() and COMPLETED lines in the evidence generation block
        update_idx = None
        completed_idx = None
        for i, line in enumerate(src.splitlines()):
            if "session_dict.update(_sessions_store" in line:
                update_idx = i
            if update_idx and 'session_dict["status"] = "COMPLETED"' in line:
                completed_idx = i
                break
        assert update_idx is not None, "Must have session_dict.update()"
        assert completed_idx is not None, "Must have status=COMPLETED"
        assert update_idx < completed_idx, \
            f"update() at line {update_idx} must come BEFORE status=COMPLETED at line {completed_idx}"


# ── BUG-213-TRANSCRIPT-ENCODING-001: encoding on file open ──────────

class TestTranscriptEncoding:
    """cc_transcript.py must specify encoding on file open."""

    def test_encoding_in_source(self):
        """stream_transcript open must include encoding='utf-8'."""
        src = (SRC / "governance/services/cc_transcript.py").read_text()
        in_func = False
        found_encoding = False
        for line in src.splitlines():
            if "def stream_transcript" in line:
                in_func = True
            elif in_func and line.strip().startswith("def "):
                break
            elif in_func and "encoding" in line and "utf-8" in line:
                found_encoding = True
        assert found_encoding, "Must use encoding='utf-8' in file open"


# ── API startup defense ──────────────────────────────────────────────

class TestApiStartupDefense:
    """Defense tests for api_startup module."""

    def test_warmup_chromadb_callable(self):
        from governance.api_startup import warmup_chromadb_embeddings
        assert callable(warmup_chromadb_embeddings)

    def test_seed_data_callable(self):
        from governance.api_startup import seed_data
        assert callable(seed_data)

    def test_cleanup_orphaned_callable(self):
        from governance.api_startup import cleanup_orphaned_chat_sessions
        assert callable(cleanup_orphaned_chat_sessions)

    def test_discover_cc_sessions_callable(self):
        from governance.api_startup import discover_cc_sessions
        assert callable(discover_cc_sessions)

    def test_mcp_readiness_handler_callable(self):
        from governance.api_startup import mcp_readiness_handler
        assert callable(mcp_readiness_handler)

    def test_module_exists_helper(self):
        from governance.api_startup import _module_exists
        assert _module_exists("json") is True
        assert _module_exists("nonexistent_module_xyz") is False


# ── Sessions lifecycle defense ───────────────────────────────────────

class TestSessionsLifecycleDefense:
    """Defense tests for sessions_lifecycle module."""

    def test_end_session_callable(self):
        from governance.services.sessions_lifecycle import end_session
        assert callable(end_session)

    def test_delete_session_callable(self):
        from governance.services.sessions_lifecycle import delete_session
        assert callable(delete_session)

    def test_delete_nonexistent_returns_false(self):
        from governance.services.sessions_lifecycle import delete_session
        with patch("governance.services.sessions_lifecycle.get_typedb_client", return_value=None), \
             patch("governance.services.sessions_lifecycle._sessions_store", {}):
            result = delete_session("SESSION-NONEXISTENT")
        assert result is False

    def test_end_session_fallback_sets_completed(self):
        """Fallback path should set status=COMPLETED and end_time."""
        from governance.services.sessions_lifecycle import end_session
        store = {
            "SESSION-TEST-001": {
                "session_id": "SESSION-TEST-001",
                "status": "ACTIVE",
                "topic": "test",
                "tool_calls": [],
                "thoughts": [],
            }
        }
        with patch("governance.services.sessions_lifecycle.get_typedb_client", return_value=None), \
             patch("governance.services.sessions_lifecycle._sessions_store", store), \
             patch("governance.services.sessions_lifecycle.record_audit"), \
             patch("governance.services.sessions_lifecycle.log_event"), \
             patch("governance.services.sessions_lifecycle.generate_session_evidence", return_value=None):
            result = end_session("SESSION-TEST-001")
        assert result["status"] == "COMPLETED"
        assert "end_time" in result
        # Verify end_time is ISO format
        datetime.fromisoformat(result["end_time"])

    def test_end_already_completed_raises(self):
        """Ending a COMPLETED session should raise ValueError."""
        from governance.services.sessions_lifecycle import end_session
        import pytest
        store = {
            "S1": {"session_id": "S1", "status": "COMPLETED"}
        }
        with patch("governance.services.sessions_lifecycle.get_typedb_client", return_value=None), \
             patch("governance.services.sessions_lifecycle._sessions_store", store):
            with pytest.raises(ValueError, match="already completed"):
                end_session("S1")


# ── CC Transcript defense ────────────────────────────────────────────

class TestCcTranscriptDefense:
    """Defense tests for cc_transcript module."""

    def test_stream_transcript_callable(self):
        from governance.services.cc_transcript import stream_transcript
        assert callable(stream_transcript)

    def test_get_transcript_page_callable(self):
        from governance.services.cc_transcript import get_transcript_page
        assert callable(get_transcript_page)

    def test_build_synthetic_transcript_callable(self):
        from governance.services.cc_transcript import build_synthetic_transcript
        assert callable(build_synthetic_transcript)

    def test_extract_user_text_string(self):
        from governance.services.cc_transcript import _extract_user_text
        assert _extract_user_text("hello") == "hello"

    def test_extract_user_text_list(self):
        from governance.services.cc_transcript import _extract_user_text
        content = [{"type": "text", "text": "hello"}, {"type": "text", "text": "world"}]
        assert _extract_user_text(content) == "hello\nworld"

    def test_extract_user_text_none(self):
        from governance.services.cc_transcript import _extract_user_text
        assert _extract_user_text(None) is None

    def test_truncate_under_limit(self):
        from governance.services.cc_transcript import _truncate
        text, truncated = _truncate("hello", 100)
        assert text == "hello"
        assert truncated is False

    def test_truncate_over_limit(self):
        from governance.services.cc_transcript import _truncate
        text, truncated = _truncate("a" * 200, 50)
        assert len(text) < 200
        assert truncated is True
        assert "truncated" in text

    def test_stream_transcript_missing_file(self):
        from governance.services.cc_transcript import stream_transcript
        entries = list(stream_transcript(Path("/nonexistent/path.jsonl")))
        assert entries == []

    def test_synthetic_transcript_empty_session(self):
        from governance.services.cc_transcript import build_synthetic_transcript
        result = build_synthetic_transcript({})
        assert result["entries"] == []
        assert result["total"] == 0
