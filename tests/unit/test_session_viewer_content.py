"""
Unit tests for Session Viewer Content Mixin.

Per DOC-SIZE-01-v1: Tests for extracted session_viewer_content.py.
Tests: _parse_sections (pure function), parse_session_id.
"""

import re
import pytest

from agent.session_viewer_content import (
    _parse_sections,
    SessionContentMixin,
)


class TestParseSections:
    """Tests for _parse_sections() pure function."""

    def test_empty_content(self):
        result = _parse_sections("")
        assert len(result) == 0

    def test_single_h1(self):
        content = "# Title\nSome content"
        result = _parse_sections(content)
        assert len(result) == 1
        assert result[0]["title"] == "Title"
        assert result[0]["level"] == 1
        assert "Some content" in result[0]["content"]

    def test_multiple_sections(self):
        content = """# Section 1
Content 1

## Section 2
Content 2

### Section 3
Content 3"""
        result = _parse_sections(content)
        assert len(result) == 3
        assert result[0]["level"] == 1
        assert result[1]["level"] == 2
        assert result[2]["level"] == 3

    def test_introduction_section(self):
        content = "Some text before heading\n# Heading\nAfter"
        result = _parse_sections(content)
        assert result[0]["title"] == "Introduction"
        assert result[1]["title"] == "Heading"

    def test_no_headings(self):
        content = "Just plain text\nwith multiple lines"
        result = _parse_sections(content)
        assert len(result) == 1
        assert result[0]["title"] == "Introduction"


class TestSessionContentMixin:
    """Tests for SessionContentMixin.parse_session_id()."""

    def _make_host(self):
        class Host(SessionContentMixin):
            SESSION_PATTERN = re.compile(
                r"SESSION-(\d{4})-(\d{2})-(\d{2})-(?:(CHAT|DSM|MCP-AUTO)-)?(.+)"
            )
            def _call_mcp_tool(self, tool_name, **kwargs):
                return {}
        return Host()

    def test_parse_session_id(self):
        host = self._make_host()
        result = host.parse_session_id("SESSION-2026-02-11-CHAT-TEST")
        assert result["date"] == "2026-02-11"
        assert result["phase"] == "CHAT"
        assert result["topic"] == "TEST"

    def test_parse_session_no_phase(self):
        host = self._make_host()
        result = host.parse_session_id("SESSION-2026-02-11-TOPIC-NAME")
        assert result["date"] == "2026-02-11"
        assert result["topic"] == "TOPIC-NAME"

    def test_parse_invalid_session_id(self):
        host = self._make_host()
        result = host.parse_session_id("NOT-A-SESSION")
        assert result["date"] == ""
        assert result["phase"] == ""
