"""Batch 139: Unit tests for CC session scanner + session repair."""
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


# ===== Module 1: cc_session_scanner.py =======================================

from governance.services.cc_session_scanner import (
    derive_project_slug,
    scan_jsonl_metadata,
    build_session_id,
    find_jsonl_for_session,
    DEFAULT_CC_DIR,
)


class TestDeriveProjectSlug:
    def test_long_path(self):
        d = Path("/tmp/-home-user-Documents-Vibe-sarvaja-platform")
        assert derive_project_slug(d) == "sarvaja-platform"

    def test_short_path(self):
        d = Path("/tmp/-home-project")
        assert derive_project_slug(d) == "home-project"

    def test_single_part(self):
        d = Path("/tmp/myproject")
        assert derive_project_slug(d) == "myproject"

    def test_uppercase_lowered(self):
        d = Path("/tmp/-Home-BigProject")
        assert derive_project_slug(d) == "home-bigproject"


class TestScanJsonlMetadata:
    def _write_jsonl(self, lines):
        f = tempfile.NamedTemporaryFile(suffix=".jsonl", mode="w", delete=False)
        for line in lines:
            f.write(json.dumps(line) + "\n")
        f.close()
        return Path(f.name)

    def test_empty_file(self):
        f = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
        f.close()
        assert scan_jsonl_metadata(Path(f.name)) is None

    def test_basic_scan(self):
        p = self._write_jsonl([
            {"type": "user", "timestamp": "2026-02-12T10:00:00Z", "sessionId": "abc-123"},
            {"type": "assistant", "timestamp": "2026-02-12T10:01:00Z",
             "message": {"content": [{"type": "tool_use", "name": "Read"}], "model": "claude-3"}},
            {"type": "assistant", "timestamp": "2026-02-12T10:02:00Z",
             "message": {"content": [{"type": "thinking", "thinking": "Let me think..."}]}},
        ])
        meta = scan_jsonl_metadata(p)
        assert meta is not None
        assert meta["user_count"] == 1
        assert meta["assistant_count"] == 2
        assert meta["tool_use_count"] == 1
        assert meta["thinking_chars"] == len("Let me think...")
        assert meta["session_uuid"] == "abc-123"
        assert meta["first_ts"] == "2026-02-12T10:00:00Z"
        assert meta["last_ts"] == "2026-02-12T10:02:00Z"
        p.unlink()

    def test_compaction_counted(self):
        p = self._write_jsonl([
            {"type": "user", "timestamp": "2026-01-01T00:00:00Z"},
            {"type": "system", "compactMetadata": {"tokens": 100}, "timestamp": "2026-01-01T01:00:00Z"},
            {"type": "system", "compactMetadata": {"tokens": 200}, "timestamp": "2026-01-01T02:00:00Z"},
        ])
        meta = scan_jsonl_metadata(p)
        assert meta["compaction_count"] == 2
        p.unlink()

    def test_git_branch_extracted(self):
        p = self._write_jsonl([
            {"type": "user", "timestamp": "2026-01-01T00:00:00Z", "gitBranch": "feature/x"},
        ])
        meta = scan_jsonl_metadata(p)
        assert meta["git_branch"] == "feature/x"
        p.unlink()

    def test_no_timestamp_returns_none(self):
        p = self._write_jsonl([
            {"type": "user"},  # no timestamp
        ])
        assert scan_jsonl_metadata(p) is None
        p.unlink()

    def test_invalid_json_skipped(self):
        f = tempfile.NamedTemporaryFile(suffix=".jsonl", mode="w", delete=False)
        f.write('{"type":"user","timestamp":"2026-01-01T00:00:00Z"}\n')
        f.write('not valid json\n')
        f.write('{"type":"assistant","timestamp":"2026-01-01T01:00:00Z","message":{}}\n')
        f.close()
        meta = scan_jsonl_metadata(Path(f.name))
        assert meta["user_count"] == 1
        assert meta["assistant_count"] == 1
        Path(f.name).unlink()

    def test_models_tracked(self):
        p = self._write_jsonl([
            {"type": "user", "timestamp": "2026-01-01T00:00:00Z"},
            {"type": "assistant", "timestamp": "2026-01-01T00:01:00Z",
             "message": {"content": [], "model": "claude-3-opus"}},
            {"type": "assistant", "timestamp": "2026-01-01T00:02:00Z",
             "message": {"content": [], "model": "claude-3-haiku"}},
        ])
        meta = scan_jsonl_metadata(p)
        assert "claude-3-haiku" in meta["models"]
        assert "claude-3-opus" in meta["models"]
        p.unlink()


class TestBuildSessionId:
    def test_basic(self):
        meta = {"first_ts": "2026-02-12T10:00:00Z", "slug": "test-session"}
        assert build_session_id(meta, "proj") == "SESSION-2026-02-12-CC-TEST-SESSION"

    def test_truncates_long_slug(self):
        meta = {"first_ts": "2026-01-01T00:00:00Z", "slug": "a" * 50}
        sid = build_session_id(meta, "proj")
        assert len(sid.split("-CC-")[1]) <= 30

    def test_spaces_replaced(self):
        meta = {"first_ts": "2026-01-01T00:00:00Z", "slug": "my session name"}
        sid = build_session_id(meta, "proj")
        assert " " not in sid


class TestFindJsonlForSession:
    @patch.object(Path, "is_dir", return_value=False)
    def test_no_cc_dir(self, _):
        assert find_jsonl_for_session({"session_id": "SESSION-2026-01-01-CC-TEST"}) is None


# ===== Module 2: session_repair.py ===========================================

from governance.services.session_repair import (
    parse_session_date,
    generate_timestamps,
    detect_identical_timestamps,
    detect_missing_agent,
    assign_default_agent,
    detect_unrealistic_durations,
    cap_duration,
    is_backfilled_session,
    build_repair_plan,
    apply_repair,
)


class TestParseSessionDate:
    def test_standard(self):
        assert parse_session_date("SESSION-2026-02-12-TOPIC") == "2026-02-12"

    def test_numeric(self):
        assert parse_session_date("SESSION-2024-12-26-001") == "2024-12-26"

    def test_no_match(self):
        assert parse_session_date("TASK-001") is None


class TestGenerateTimestamps:
    def test_produces_pair(self):
        start, end = generate_timestamps("2026-02-12")
        assert "09:00:00" in start
        s = datetime.fromisoformat(start)
        e = datetime.fromisoformat(end)
        assert (e - s).total_seconds() == 4 * 3600


class TestDetectIdenticalTimestamps:
    def test_finds_duplicates(self):
        sessions = [
            {"session_id": "S1", "start_time": "2026-01-01T09:00:00", "end_time": "2026-01-01T13:00:00"},
            {"session_id": "S2", "start_time": "2026-01-01T09:00:00", "end_time": "2026-01-01T13:00:00"},
            {"session_id": "S3", "start_time": "2026-01-02T09:00:00", "end_time": "2026-01-02T13:00:00"},
        ]
        flagged = detect_identical_timestamps(sessions)
        assert "S1" in flagged and "S2" in flagged
        assert "S3" not in flagged

    def test_no_duplicates(self):
        sessions = [
            {"session_id": "S1", "start_time": "2026-01-01T09:00", "end_time": "2026-01-01T13:00"},
        ]
        assert detect_identical_timestamps(sessions) == []


class TestDetectMissingAgent:
    def test_finds_missing(self):
        sessions = [
            {"session_id": "S1", "agent_id": "code-agent"},
            {"session_id": "S2", "agent_id": ""},
            {"session_id": "S3"},
        ]
        missing = detect_missing_agent(sessions)
        assert "S2" in missing and "S3" in missing
        assert "S1" not in missing


class TestAssignDefaultAgent:
    def test_assigns_when_missing(self):
        s = assign_default_agent({"session_id": "S1"})
        assert s["agent_id"] == "code-agent"

    def test_keeps_existing(self):
        s = assign_default_agent({"session_id": "S1", "agent_id": "my-agent"})
        assert s["agent_id"] == "my-agent"

    def test_does_not_mutate_original(self):
        orig = {"session_id": "S1"}
        assign_default_agent(orig)
        assert "agent_id" not in orig


class TestDetectUnrealisticDurations:
    def test_flags_long(self):
        sessions = [{"session_id": "S1",
                      "start_time": "2026-01-01T00:00:00",
                      "end_time": "2026-01-03T00:00:00"}]  # 48h
        assert "S1" in detect_unrealistic_durations(sessions)

    def test_ok_duration(self):
        sessions = [{"session_id": "S1",
                      "start_time": "2026-01-01T09:00:00",
                      "end_time": "2026-01-01T17:00:00"}]  # 8h
        assert detect_unrealistic_durations(sessions) == []


class TestCapDuration:
    def test_caps_long_duration(self):
        s = cap_duration({
            "start_time": "2026-01-01T00:00:00",
            "end_time": "2026-01-03T00:00:00",
        }, max_hours=8)
        expected_end = (datetime(2026, 1, 1) + timedelta(hours=8)).isoformat()
        assert s["end_time"] == expected_end

    def test_no_cap_needed(self):
        s = cap_duration({
            "start_time": "2026-01-01T09:00:00",
            "end_time": "2026-01-01T13:00:00",
        }, max_hours=8)
        assert s["end_time"] == "2026-01-01T13:00:00"

    def test_missing_times(self):
        s = cap_duration({"start_time": ""})
        assert s.get("end_time") is None


class TestIsBackfilledSession:
    def test_by_description(self):
        assert is_backfilled_session({"description": "Backfilled from evidence file"})

    def test_by_agent(self):
        assert is_backfilled_session({"agent_id": "my-agent-test"})

    def test_normal_session(self):
        assert not is_backfilled_session({"description": "Normal work", "agent_id": "code-agent"})


class TestBuildRepairPlan:
    def test_produces_plan(self):
        sessions = [
            {"session_id": "SESSION-2026-01-01-TOPIC", "agent_id": "",
             "description": "Backfilled from evidence file",
             "start_time": "2026-01-01T09:00:00", "end_time": "2026-01-01T13:00:00"},
        ]
        plan = build_repair_plan(sessions)
        assert len(plan) == 1
        assert "agent_id" in plan[0]["fixes"]
        assert "timestamp" in plan[0]["fixes"]

    def test_no_issues(self):
        sessions = [
            {"session_id": "SESSION-2026-01-01-TOPIC", "agent_id": "code-agent",
             "description": "Normal work",
             "start_time": "2026-01-01T09:00:00", "end_time": "2026-01-01T13:00:00"},
        ]
        assert build_repair_plan(sessions) == []


class TestApplyRepair:
    def test_dry_run(self):
        item = {"session_id": "S1", "fixes": {"agent_id": "code-agent"}}
        r = apply_repair(item, dry_run=True)
        assert r["dry_run"] is True
        assert r["applied"] is False

    @patch("governance.services.sessions.update_session")
    def test_apply(self, mock_update):
        item = {"session_id": "S1", "fixes": {"agent_id": "code-agent"}}
        r = apply_repair(item, dry_run=False)
        assert r["applied"] is True
        mock_update.assert_called_once_with("S1", agent_id="code-agent")
