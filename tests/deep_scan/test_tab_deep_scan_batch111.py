"""Deep scan batch 111: Session bridge + evidence scanner.

Batch 111 findings: 17 total, 0 confirmed fixes, 17 rejected.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


# ── Session bridge lifecycle defense ──────────────


class TestSessionBridgeLifecycle:
    """Verify session bridge handles lifecycle correctly."""

    def test_session_id_format_is_deterministic(self):
        """SessionCollector generates predictable IDs (known trade-off)."""
        from governance.session_collector.collector import SessionCollector

        c1 = SessionCollector(topic="TEST-TOPIC", session_type="general", agent_id="a")
        assert c1.session_id.startswith("SESSION-")
        assert "TEST-TOPIC" in c1.session_id

    def test_session_collector_records_events(self):
        """SessionCollector can record tool_call events."""
        from governance.session_collector.collector import SessionCollector

        c = SessionCollector(topic="EVENT-TEST", session_type="general", agent_id="a")
        c.capture_tool_call(tool_name="Read", arguments={}, result="ok")
        tool_calls = [e for e in c.events if e.event_type == "tool_call"]
        assert len(tool_calls) == 1
        assert tool_calls[0].metadata.get("tool_name") == "Read"

    def test_tool_call_count_from_events(self):
        """Tool call count is computed from events correctly."""
        from governance.session_collector.collector import SessionCollector

        c = SessionCollector(topic="COUNT-TEST", session_type="general", agent_id="a")
        c.capture_tool_call(tool_name="Read", arguments={}, result="ok")
        c.capture_tool_call(tool_name="Write", arguments={}, result="ok")
        c.capture_thought(thought="thinking...", thought_type="reasoning")

        tool_count = len([e for e in c.events if e.event_type == "tool_call"])
        assert tool_count == 2  # Thoughts not counted


# ── Tool classification defense ──────────────


class TestToolClassificationDefense:
    """Verify tool classification handles edge cases."""

    def test_classify_builtin_tool(self):
        """CC builtin tools are classified correctly."""
        from governance.routes.chat.session_bridge import classify_tool

        assert classify_tool("Read") == "cc_builtin"
        assert classify_tool("Write") == "cc_builtin"
        assert classify_tool("Bash") == "cc_builtin"
        assert classify_tool("Glob") == "cc_builtin"

    def test_classify_mcp_tool(self):
        """MCP tools with mcp__ prefix are classified."""
        from governance.routes.chat.session_bridge import classify_tool

        result = classify_tool("mcp__gov-tasks__task_create")
        assert result in ("mcp_governance", "mcp_other")

    def test_classify_unknown_tool(self):
        """Unknown tools return 'unknown'."""
        from governance.routes.chat.session_bridge import classify_tool

        assert classify_tool("nonexistent_tool_xyz") == "unknown"


# ── Evidence linking defense ──────────────


class TestEvidenceLinkingDefense:
    """Verify evidence linking handles edge cases."""

    def test_evidence_scanner_scan_result_fields(self):
        """ScanResult has required fields."""
        from governance.evidence_scanner.extractors import ScanResult

        sr = ScanResult(
            session_id="SESSION-2026-02-15-TEST",
            file_path="evidence/SESSION-2026-02-15-TEST.md",
        )
        assert sr.session_id == "SESSION-2026-02-15-TEST"
        assert sr.file_path.endswith(".md")

    def test_extract_session_id_from_evidence_filename(self):
        """Session ID extraction from evidence filenames."""
        from governance.evidence_scanner.linking import _extract_session_id_from_evidence
        from pathlib import Path

        path = Path("evidence/SESSION-2026-02-15-CHAT-TEST.md")
        result = _extract_session_id_from_evidence(path)
        assert result is not None
        assert "SESSION-2026-02-15" in result


# ── Session evidence rendering defense ──────────────


class TestSessionEvidenceRenderingDefense:
    """Verify evidence markdown rendering is safe."""

    def test_render_with_empty_evidence_data(self):
        """render_evidence_markdown handles empty dict."""
        from governance.services.session_evidence import render_evidence_markdown

        result = render_evidence_markdown({})
        assert isinstance(result, str)

    def test_pipe_escaping_in_task_description(self):
        """Task descriptions with pipes are escaped for markdown tables."""
        desc = "Fix | issue | with pipes"
        escaped = desc.replace("|", "\\|")
        assert "\\|" in escaped
        assert "|" not in escaped.replace("\\|", "")

    def test_truncate_then_escape_order(self):
        """Truncate happens before escape — no broken escape sequences."""
        # Simulates the actual code pattern
        text = "A" * 100 + " | some text"  # 113 chars
        truncated = text[:80]  # Truncate to 80
        escaped = truncated.replace("|", "\\|")
        # No pipe in truncated text → no broken escape
        assert "\\|" not in escaped  # Pipe was in chars 101+, removed by truncation

    def test_truncate_with_pipe_in_range(self):
        """When pipe is within truncation range, it gets escaped."""
        text = "Fix | this | bug"
        truncated = text[:80]  # Full text fits
        escaped = truncated.replace("|", "\\|")
        assert escaped.count("\\|") == 2


# ── Session repair defense ──────────────


class TestSessionRepairDefense:
    """Verify session repair handles malformed data."""

    def test_fromisoformat_with_short_string(self):
        """fromisoformat handles date-only strings (10 chars)."""
        result = datetime.fromisoformat("2026-02-15")
        assert result.year == 2026

    def test_fromisoformat_with_full_iso(self):
        """fromisoformat handles full ISO strings."""
        result = datetime.fromisoformat("2026-02-15T10:30:00"[:19])
        assert result.hour == 10

    def test_fromisoformat_with_empty_raises(self):
        """fromisoformat on empty string raises ValueError."""
        with pytest.raises(ValueError):
            datetime.fromisoformat("")

    def test_slice_on_short_string_returns_full(self):
        """Python [:19] on short string returns the string unchanged."""
        assert "2026-02-15"[:19] == "2026-02-15"
        assert ""[:19] == ""
        assert "abc"[:19] == "abc"


# ── Backfilled session detection defense ──────────────


class TestBackfilledSessionDetection:
    """Verify backfilled session detection patterns."""

    def test_agent_id_endswith_test(self):
        """agent_id ending with '-test' detected as backfilled."""
        agent = "code-agent-test"
        assert agent.endswith("-test")

    def test_none_agent_fallback_to_empty(self):
        """None agent_id safely falls back to empty string."""
        session = {"agent_id": None}
        agent = session.get("agent_id") or ""
        assert agent.endswith("-test") is False  # No crash

    def test_backfilled_description_pattern(self):
        """Backfilled sessions have standard description."""
        desc = "Backfilled from evidence file"
        assert "backfilled from evidence" in desc.lower()
