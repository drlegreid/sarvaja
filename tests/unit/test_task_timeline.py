"""Unit tests for task_timeline service — EPIC-ISSUE-EVIDENCE P18.

Tests multi-session chronological merge, filtering, pagination.
"""

import pytest
from unittest.mock import patch, MagicMock
from dataclasses import dataclass, field

from governance.services.task_timeline import (
    build_task_timeline,
    _collect_session_entries,
    _normalize_entry,
    _DETAIL_TRUNCATE,
)

_SVC = "governance.services.task_timeline"
_QUERIES = "governance.services.tasks_queries"
_INGESTION = "governance.services.cc_session_ingestion"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@dataclass
class FakeTask:
    task_id: str = "SRVJ-TEST-001"
    linked_sessions: list = field(default_factory=lambda: [])
    status: str = "DONE"

    def get(self, key, default=None):
        return getattr(self, key, default)


def _tool_call(name: str, ts: str, latency: int = 50) -> dict:
    return {
        "name": name,
        "timestamp": ts,
        "input_summary": f"input for {name}",
        "latency_ms": latency,
        "is_mcp": name.startswith("mcp__"),
    }


def _thought(content: str, ts: str, chars: int = 100) -> dict:
    return {
        "content": content,
        "timestamp": ts,
        "chars": chars,
    }


# ---------------------------------------------------------------------------
# build_task_timeline
# ---------------------------------------------------------------------------

class TestBuildTaskTimeline:
    """Tests for build_task_timeline()."""

    @patch(f"{_QUERIES}.get_task", return_value=None)
    def test_task_not_found(self, _mock):
        """Returns None for unknown task_id."""
        result = build_task_timeline("NONEXISTENT")
        assert result is None

    @patch(f"{_QUERIES}.get_task")
    def test_no_linked_sessions(self, mock_task):
        """Empty entries when task has no linked sessions."""
        mock_task.return_value = FakeTask(linked_sessions=[])
        result = build_task_timeline("SRVJ-TEST-001")
        assert result is not None
        assert result["entries"] == []
        assert result["total"] == 0
        assert result["session_ids"] == []

    @patch(f"{_INGESTION}.get_session_detail")
    @patch(f"{_QUERIES}.get_task")
    def test_single_session_tool_calls(self, mock_task, mock_detail):
        """Tool calls from a single session are returned."""
        mock_task.return_value = FakeTask(linked_sessions=["SESSION-A"])
        mock_detail.side_effect = lambda sid, zoom=1, page=1, per_page=20: {
            "tool_calls": [
                _tool_call("Edit", "2026-03-24T10:00:00"),
                _tool_call("Read", "2026-03-24T10:01:00"),
            ],
        } if zoom == 2 else {"thinking_blocks": []}

        result = build_task_timeline("SRVJ-TEST-001")
        assert result["total"] == 2
        assert result["entries"][0]["title"] == "Edit"
        assert result["entries"][1]["title"] == "Read"
        assert all(e["entry_type"] == "tool_call" for e in result["entries"])

    @patch(f"{_INGESTION}.get_session_detail")
    @patch(f"{_QUERIES}.get_task")
    def test_multiple_sessions_chronological(self, mock_task, mock_detail):
        """Entries from multiple sessions are merged by timestamp."""
        mock_task.return_value = FakeTask(
            linked_sessions=["SESSION-A", "SESSION-B"]
        )

        def _detail(sid, zoom=1, page=1, per_page=20):
            if sid == "SESSION-A":
                if zoom == 2:
                    return {"tool_calls": [
                        _tool_call("Edit", "2026-03-24T10:00:00"),
                        _tool_call("Write", "2026-03-24T10:10:00"),
                    ]}
                return {"thinking_blocks": []}
            else:
                if zoom == 2:
                    return {"tool_calls": [
                        _tool_call("Bash", "2026-03-24T10:05:00"),
                    ]}
                return {"thinking_blocks": [
                    _thought("Analyzing...", "2026-03-24T10:03:00"),
                ]}

        mock_detail.side_effect = _detail

        result = build_task_timeline("SRVJ-TEST-001")
        assert result["total"] == 4
        titles = [e["title"] for e in result["entries"]]
        assert titles == ["Edit", "Thinking (100 chars)", "Bash", "Write"]

    @patch(f"{_INGESTION}.get_session_detail")
    @patch(f"{_QUERIES}.get_task")
    def test_entry_type_filter(self, mock_task, mock_detail):
        """Filter to only 'thought' entries."""
        mock_task.return_value = FakeTask(linked_sessions=["SESSION-A"])
        mock_detail.side_effect = lambda sid, zoom=1, page=1, per_page=20: {
            "tool_calls": [_tool_call("Edit", "2026-03-24T10:00:00")],
        } if zoom == 2 else {
            "thinking_blocks": [_thought("Hmm...", "2026-03-24T10:01:00")],
        }

        result = build_task_timeline(
            "SRVJ-TEST-001", entry_types=["thought"]
        )
        assert result["total"] == 1
        assert result["entries"][0]["entry_type"] == "thought"

    @patch(f"{_INGESTION}.get_session_detail")
    @patch(f"{_QUERIES}.get_task")
    def test_pagination(self, mock_task, mock_detail):
        """Pagination returns correct slice and has_more flag."""
        mock_task.return_value = FakeTask(linked_sessions=["SESSION-A"])
        tools = [_tool_call(f"Tool{i}", f"2026-03-24T{10+i:02d}:00:00")
                 for i in range(5)]
        mock_detail.side_effect = lambda sid, zoom=1, page=1, per_page=20: {
            "tool_calls": tools,
        } if zoom == 2 else {"thinking_blocks": []}

        # Page 1, per_page=2
        r1 = build_task_timeline("SRVJ-TEST-001", page=1, per_page=2)
        assert len(r1["entries"]) == 2
        assert r1["total"] == 5
        assert r1["has_more"] is True

        # Page 3, per_page=2 — last page
        r3 = build_task_timeline("SRVJ-TEST-001", page=3, per_page=2)
        assert len(r3["entries"]) == 1
        assert r3["has_more"] is False

    @patch(f"{_INGESTION}.get_session_detail")
    @patch(f"{_QUERIES}.get_task")
    def test_session_ids_in_response(self, mock_task, mock_detail):
        """Response includes session_ids list."""
        mock_task.return_value = FakeTask(
            linked_sessions=["SESSION-A", "SESSION-B"]
        )
        mock_detail.return_value = {"tool_calls": [], "thinking_blocks": []}
        result = build_task_timeline("SRVJ-TEST-001")
        assert result["session_ids"] == ["SESSION-A", "SESSION-B"]

    @patch(f"{_INGESTION}.get_session_detail", side_effect=Exception("JSONL missing"))
    @patch(f"{_QUERIES}.get_task")
    def test_session_detail_fallback(self, mock_task, _mock_detail):
        """Gracefully handles session detail failure."""
        mock_task.return_value = FakeTask(linked_sessions=["SESSION-BROKEN"])
        result = build_task_timeline("SRVJ-TEST-001")
        assert result["entries"] == []
        assert result["total"] == 0


# ---------------------------------------------------------------------------
# _normalize_entry
# ---------------------------------------------------------------------------

class TestNormalizeEntry:

    def test_tool_call_icon_color(self):
        raw = _tool_call("Read", "2026-03-24T10:00:00", 42)
        entry = _normalize_entry(raw, "tool_call", "SESSION-A")
        assert entry["icon"] == "mdi-wrench"
        assert entry["color"] == "primary"
        assert entry["title"] == "Read"
        assert entry["duration_ms"] == 42
        assert entry["session_id"] == "SESSION-A"

    def test_thought_icon_color(self):
        raw = _thought("Deep analysis", "2026-03-24T10:00:00", 500)
        entry = _normalize_entry(raw, "thought", "SESSION-B")
        assert entry["icon"] == "mdi-head-cog"
        assert entry["color"] == "info"
        assert "500 chars" in entry["title"]
        assert entry["duration_ms"] is None

    def test_detail_truncation(self):
        raw = _tool_call("Read", "2026-03-24T10:00:00")
        raw["input_summary"] = "x" * 500
        entry = _normalize_entry(raw, "tool_call", "SESSION-A")
        assert len(entry["detail"]) == _DETAIL_TRUNCATE + 3  # +3 for "..."
        assert entry["detail"].endswith("...")

    def test_unknown_type_default_style(self):
        raw = {"timestamp": "2026-03-24T10:00:00", "title": "Custom"}
        entry = _normalize_entry(raw, "custom_type", "SESSION-A")
        assert entry["icon"] == "mdi-circle"
        assert entry["color"] == "grey"
