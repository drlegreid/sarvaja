"""
Unit tests for Tab Deep Scan Batch 32 — Session metrics + evidence + heuristics.

Covers: BUG-TRANSCRIPT-001 (file I/O error handling in cc_transcript),
BUG-REPAIR-001 (KeyError safety in session_repair),
BUG-HEURISTIC-001 (silent swallowing in heuristic_runner),
BUG-HEURISTIC-002 (hardcoded date in heuristic_checks_session),
BUG-STORE-006 (silent swallowing in runner_store).
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect
import json
import tempfile
from pathlib import Path


# ── BUG-TRANSCRIPT-001: File I/O error handling ─────────────────────


class TestTranscriptFileIOSafety:
    """stream_transcript must handle missing/unreadable files."""

    def test_has_exists_check(self):
        from governance.services import cc_transcript
        source = inspect.getsource(cc_transcript.stream_transcript)
        assert "filepath.exists()" in source or "not filepath.exists()" in source

    def test_has_permission_error_guard(self):
        from governance.services import cc_transcript
        source = inspect.getsource(cc_transcript.stream_transcript)
        assert "PermissionError" in source

    def test_has_ioerror_guard(self):
        from governance.services import cc_transcript
        source = inspect.getsource(cc_transcript.stream_transcript)
        assert "IOError" in source

    def test_missing_file_returns_empty(self):
        """stream_transcript on non-existent file should yield nothing."""
        from governance.services.cc_transcript import stream_transcript
        entries = list(stream_transcript(Path("/tmp/nonexistent_transcript_file.jsonl")))
        assert entries == []

    def test_valid_file_still_works(self):
        """stream_transcript on valid file should yield entries."""
        from governance.services.cc_transcript import stream_transcript
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            obj = {
                "timestamp": "2026-02-16T10:00:00",
                "type": "assistant",
                "message": {
                    "content": [{"type": "text", "text": "Hello world"}],
                    "model": "test-model",
                },
            }
            f.write(json.dumps(obj) + "\n")
            f.flush()
            entries = list(stream_transcript(Path(f.name)))
        assert len(entries) == 1
        assert entries[0].entry_type == "assistant_text"

    def test_has_finally_close(self):
        """File handle must be closed in finally block."""
        from governance.services import cc_transcript
        source = inspect.getsource(cc_transcript.stream_transcript)
        assert "finally:" in source
        assert "f.close()" in source

    def test_bugfix_marker(self):
        from governance.services import cc_transcript
        source = inspect.getsource(cc_transcript.stream_transcript)
        assert "BUG-TRANSCRIPT-001" in source


# ── BUG-REPAIR-001: KeyError safety in session_repair ────────────────


class TestSessionRepairKeyErrorSafety:
    """session_repair functions must use .get() not direct dict access."""

    def test_no_bare_bracket_session_id(self):
        """No s['session_id'] or s["session_id"] patterns allowed."""
        from governance.services import session_repair
        source = inspect.getsource(session_repair)
        # Allow s.get("session_id", ...) but not s["session_id"]
        assert 's["session_id"]' not in source
        assert "s['session_id']" not in source

    def test_detect_identical_timestamps_with_missing_key(self):
        """detect_identical_timestamps must not crash on missing session_id."""
        from governance.services.session_repair import detect_identical_timestamps
        sessions = [
            {"start_time": "2026-01-01T09:00:00", "end_time": "2026-01-01T13:00:00"},
            {"start_time": "2026-01-01T09:00:00", "end_time": "2026-01-01T13:00:00"},
        ]
        result = detect_identical_timestamps(sessions)
        assert isinstance(result, list)
        assert "unknown" in result  # Should use "unknown" fallback

    def test_detect_missing_agent_with_missing_key(self):
        """detect_missing_agent must not crash on missing session_id."""
        from governance.services.session_repair import detect_missing_agent
        sessions = [{"description": "test"}]  # No session_id key
        result = detect_missing_agent(sessions)
        assert isinstance(result, list)
        assert "unknown" in result

    def test_detect_negative_durations_with_missing_key(self):
        """detect_negative_durations must not crash on missing session_id."""
        from governance.services.session_repair import detect_negative_durations
        sessions = [{"start_time": "2026-01-01T13:00:00", "end_time": "2026-01-01T09:00:00"}]
        result = detect_negative_durations(sessions)
        assert isinstance(result, list)
        assert "unknown" in result

    def test_detect_unrealistic_durations_with_missing_key(self):
        from governance.services.session_repair import detect_unrealistic_durations
        sessions = [{
            "start_time": "2026-01-01T09:00:00",
            "end_time": "2026-01-03T09:00:00",  # 48h
        }]
        result = detect_unrealistic_durations(sessions)
        assert isinstance(result, list)
        assert "unknown" in result

    def test_build_repair_plan_with_missing_key(self):
        from governance.services.session_repair import build_repair_plan
        sessions = [{"agent_id": None, "start_time": "", "end_time": ""}]
        result = build_repair_plan(sessions)
        assert isinstance(result, list)
        # Should have a plan item with "unknown" session_id
        if result:
            assert result[0].get("session_id") == "unknown"

    def test_bugfix_marker(self):
        from governance.services import session_repair
        source = inspect.getsource(session_repair)
        assert "BUG-REPAIR-001" in source


# ── BUG-HEURISTIC-001: Silent swallowing in heuristic_runner ────────


class TestHeuristicRunnerLogging:
    """heuristic_runner must log instead of silently swallowing exceptions."""

    def test_no_bare_except_pass(self):
        """No except Exception: pass patterns allowed."""
        from governance.routes.tests import heuristic_runner
        source = inspect.getsource(heuristic_runner)
        lines = source.splitlines()
        for i, line in enumerate(lines):
            if "except Exception" in line and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                assert next_line != "pass", \
                    f"Bare except:pass at line {i + 1}: {line.strip()}"

    def test_has_tool_call_log(self):
        from governance.routes.tests import heuristic_runner
        source = inspect.getsource(heuristic_runner)
        assert "Failed to record heuristic tool call" in source

    def test_has_session_end_log(self):
        from governance.routes.tests import heuristic_runner
        source = inspect.getsource(heuristic_runner)
        assert "Failed to end heuristic session" in source

    def test_bugfix_marker(self):
        from governance.routes.tests import heuristic_runner
        source = inspect.getsource(heuristic_runner)
        assert "BUG-HEURISTIC-001" in source


# ── BUG-HEURISTIC-002: Hardcoded date in backfill detection ─────────


class TestBackfillDateDetection:
    """_is_backfilled_session must use dynamic date, not hardcoded."""

    def test_no_hardcoded_2026_02(self):
        """Should not contain hardcoded 'SESSION-2026-02' string."""
        from governance.routes.tests import heuristic_checks_session
        source = inspect.getsource(heuristic_checks_session._is_backfilled_session)
        assert 'sid.startswith("SESSION-2026-02")' not in source

    def test_uses_dynamic_cutoff(self):
        from governance.routes.tests import heuristic_checks_session
        source = inspect.getsource(heuristic_checks_session._is_backfilled_session)
        assert "timedelta" in source

    def test_old_session_no_agent_is_backfilled(self):
        """Session from 2025 without agent_id should be detected as backfilled."""
        from governance.routes.tests.heuristic_checks_session import _is_backfilled_session
        session = {"session_id": "SESSION-2025-06-15-OLD", "agent_id": None, "description": ""}
        assert _is_backfilled_session(session) is True

    def test_recent_session_with_agent_not_backfilled(self):
        """Recent session with agent_id should NOT be detected as backfilled."""
        from datetime import datetime
        from governance.routes.tests.heuristic_checks_session import _is_backfilled_session
        today = datetime.now().strftime("%Y-%m-%d")
        session = {
            "session_id": f"SESSION-{today}-WORK",
            "agent_id": "code-agent",
            "description": "Real work",
        }
        assert _is_backfilled_session(session) is False

    def test_bugfix_marker(self):
        from governance.routes.tests import heuristic_checks_session
        source = inspect.getsource(heuristic_checks_session._is_backfilled_session)
        assert "BUG-HEURISTIC-002" in source


# ── BUG-STORE-006: Silent swallowing in runner_store ─────────────────


class TestRunnerStoreLogging:
    """runner_store must log instead of silently swallowing errors."""

    def test_load_has_logging(self):
        from governance.routes.tests import runner_store
        source = inspect.getsource(runner_store._load_persisted_results)
        assert "logger.debug" in source

    def test_no_bare_except_pass_in_load(self):
        from governance.routes.tests import runner_store
        source = inspect.getsource(runner_store._load_persisted_results)
        lines = source.splitlines()
        for i, line in enumerate(lines):
            if "except Exception" in line and i + 1 < len(lines):
                next_stripped = lines[i + 1].strip()
                assert next_stripped != "continue" or "logger" in source[source.index(line):], \
                    f"Bare except:continue without logging at line {i + 1}"

    def test_bugfix_marker(self):
        from governance.routes.tests import runner_store
        source = inspect.getsource(runner_store)
        assert "BUG-STORE-006" in source


# ── Transcript pagination correctness ─────────────────────────────────


class TestTranscriptPagination:
    """get_transcript_page must paginate correctly."""

    def test_page_1_gets_first_entries(self):
        """Page 1 should return the first per_page entries."""
        from governance.services.cc_transcript import get_transcript_page
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            for i in range(5):
                obj = {
                    "timestamp": f"2026-02-16T10:{i:02d}:00",
                    "type": "assistant",
                    "message": {
                        "content": [{"type": "text", "text": f"Entry {i}"}],
                    },
                }
                f.write(json.dumps(obj) + "\n")
            f.flush()
            result = get_transcript_page(Path(f.name), page=1, per_page=3)
        assert len(result["entries"]) == 3
        assert result["total"] == 5
        assert result["has_more"] is True
        assert result["entries"][0]["content"] == "Entry 0"

    def test_page_2_gets_remaining(self):
        from governance.services.cc_transcript import get_transcript_page
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            for i in range(5):
                obj = {
                    "timestamp": f"2026-02-16T10:{i:02d}:00",
                    "type": "assistant",
                    "message": {
                        "content": [{"type": "text", "text": f"Entry {i}"}],
                    },
                }
                f.write(json.dumps(obj) + "\n")
            f.flush()
            result = get_transcript_page(Path(f.name), page=2, per_page=3)
        assert len(result["entries"]) == 2
        assert result["has_more"] is False
        assert result["entries"][0]["content"] == "Entry 3"

    def test_empty_file_returns_zero(self):
        from governance.services.cc_transcript import get_transcript_page
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write("")
            f.flush()
            result = get_transcript_page(Path(f.name))
        assert result["total"] == 0
        assert result["entries"] == []
        assert result["has_more"] is False
