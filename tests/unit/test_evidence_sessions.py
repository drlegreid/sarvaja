"""
Unit tests for evidence/sessions.py MCP tools.

Tests governance_list_sessions and governance_get_session.
Covers file glob, metadata parsing, filters, and edge cases.
"""

import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


_MOD = "governance.mcp_tools.evidence.sessions"


@pytest.fixture(autouse=True)
def force_json_output():
    """Force JSON output format for predictable test results."""
    old = os.environ.get("MCP_OUTPUT_FORMAT")
    os.environ["MCP_OUTPUT_FORMAT"] = "json"
    yield
    if old is None:
        os.environ.pop("MCP_OUTPUT_FORMAT", None)
    else:
        os.environ["MCP_OUTPUT_FORMAT"] = old


def _register_tools():
    """Register and return tools by name."""
    from governance.mcp_tools.evidence.sessions import register_session_tools

    tools = {}

    class MockMCP:
        def tool(self):
            def decorator(fn):
                tools[fn.__name__] = fn
                return fn
            return decorator

    register_session_tools(MockMCP())
    return tools


# ── governance_list_sessions ──────────────────────────────


class TestGovernanceListSessions:

    def test_registration(self):
        tools = _register_tools()
        assert "governance_list_sessions" in tools

    @patch(f"{_MOD}.glob.glob", return_value=[])
    def test_empty_directory(self, mock_glob):
        tools = _register_tools()
        result = json.loads(tools["governance_list_sessions"]())
        assert result["count"] == 0
        assert result["sessions"] == []

    @patch(f"{_MOD}.glob.glob")
    @patch(f"{_MOD}.Path")
    def test_parses_session_filename(self, mock_path_cls, mock_glob):
        tools = _register_tools()
        mock_glob.side_effect = [
            ["/evidence/SESSION-2026-02-10-TOPIC-ONE.md"],
            ["/evidence/SESSION-2026-02-10-TOPIC-ONE.md"],
        ]

        mock_path = MagicMock()
        mock_path.name = "SESSION-2026-02-10-TOPIC-ONE.md"
        mock_path.read_text.return_value = "# Session\n## Summary\nDid stuff\n"
        mock_path_cls.return_value = mock_path

        result = json.loads(tools["governance_list_sessions"]())
        assert result["count"] == 1
        session = result["sessions"][0]
        assert session["date"] == "2026-02-10"
        assert session["topic"] == "TOPIC-ONE"
        assert session["session_id"] == "SESSION-2026-02-10-TOPIC-ONE"

    @patch(f"{_MOD}.glob.glob")
    @patch(f"{_MOD}.Path")
    def test_summary_extraction(self, mock_path_cls, mock_glob):
        tools = _register_tools()
        mock_glob.side_effect = [
            ["/evidence/SESSION-2026-01-01-TEST.md"],
            ["/evidence/SESSION-2026-01-01-TEST.md"],
        ]

        mock_path = MagicMock()
        mock_path.name = "SESSION-2026-01-01-TEST.md"
        mock_path.read_text.return_value = (
            "# Title\n"
            "## Summary\n"
            "This is the summary text\n"
            "More content\n"
        )
        mock_path_cls.return_value = mock_path

        result = json.loads(tools["governance_list_sessions"]())
        assert result["sessions"][0]["summary"] == "This is the summary text"

    @patch(f"{_MOD}.glob.glob")
    @patch(f"{_MOD}.Path")
    def test_no_summary_fallback(self, mock_path_cls, mock_glob):
        tools = _register_tools()
        mock_glob.side_effect = [
            ["/evidence/SESSION-2026-01-01-TEST.md"],
            ["/evidence/SESSION-2026-01-01-TEST.md"],
        ]

        mock_path = MagicMock()
        mock_path.name = "SESSION-2026-01-01-TEST.md"
        mock_path.read_text.return_value = "# Title\nSome content\n"
        mock_path_cls.return_value = mock_path

        result = json.loads(tools["governance_list_sessions"]())
        assert result["sessions"][0]["summary"] == "No summary available"

    @patch(f"{_MOD}.glob.glob")
    @patch(f"{_MOD}.Path")
    def test_session_type_filter(self, mock_path_cls, mock_glob):
        tools = _register_tools()
        mock_glob.side_effect = [
            [
                "/evidence/SESSION-2026-01-01-PHASE8.md",
                "/evidence/SESSION-2026-01-02-DSP-CYCLE.md",
            ],
            [
                "/evidence/SESSION-2026-01-01-PHASE8.md",
                "/evidence/SESSION-2026-01-02-DSP-CYCLE.md",
            ],
        ]

        def path_factory(filepath):
            p = MagicMock()
            name = str(filepath).split("/")[-1]
            p.name = name
            p.read_text.return_value = "# x\n"
            return p

        mock_path_cls.side_effect = path_factory

        result = json.loads(tools["governance_list_sessions"](session_type="DSP"))
        assert result["count"] == 1
        assert "DSP" in result["sessions"][0]["topic"]

    @patch(f"{_MOD}.glob.glob")
    @patch(f"{_MOD}.Path")
    def test_limit_parameter(self, mock_path_cls, mock_glob):
        tools = _register_tools()
        files = [f"/evidence/SESSION-2026-01-0{i}-TEST.md" for i in range(1, 6)]
        mock_glob.side_effect = [files[:2], files]

        def path_factory(filepath):
            p = MagicMock()
            name = str(filepath).split("/")[-1]
            p.name = name
            p.read_text.return_value = "# x\n"
            return p

        mock_path_cls.side_effect = path_factory

        result = json.loads(tools["governance_list_sessions"](limit=2))
        assert result["count"] == 2
        assert result["total_available"] == 5

    @patch(f"{_MOD}.glob.glob")
    @patch(f"{_MOD}.Path")
    def test_parse_exception_skipped(self, mock_path_cls, mock_glob):
        """File parse errors should be skipped, not crash."""
        tools = _register_tools()
        mock_glob.side_effect = [
            ["/evidence/SESSION-2026-01-01-GOOD.md", "/evidence/SESSION-2026-01-02-BAD.md"],
            ["/evidence/SESSION-2026-01-01-GOOD.md", "/evidence/SESSION-2026-01-02-BAD.md"],
        ]

        def path_factory(filepath):
            p = MagicMock()
            if "BAD" in str(filepath):
                p.name = "SESSION-2026-01-02-BAD.md"
                p.read_text.side_effect = IOError("Permission denied")
            else:
                p.name = "SESSION-2026-01-01-GOOD.md"
                p.read_text.return_value = "# x\n"
            return p

        mock_path_cls.side_effect = path_factory

        result = json.loads(tools["governance_list_sessions"]())
        assert result["count"] == 1

    @patch(f"{_MOD}.glob.glob")
    @patch(f"{_MOD}.Path")
    def test_short_filename_parts(self, mock_path_cls, mock_glob):
        """Filenames with <4 parts get 'unknown' date."""
        tools = _register_tools()
        mock_glob.side_effect = [
            ["/evidence/SESSION-SHORT.md"],
            ["/evidence/SESSION-SHORT.md"],
        ]

        mock_path = MagicMock()
        mock_path.name = "SESSION-SHORT.md"
        mock_path.read_text.return_value = "# x\n"
        mock_path_cls.return_value = mock_path

        result = json.loads(tools["governance_list_sessions"]())
        assert result["count"] == 1
        assert result["sessions"][0]["date"] == "unknown"


# ── governance_get_session ────────────────────────────────


class TestGovernanceGetSession:

    def test_registration(self):
        tools = _register_tools()
        assert "governance_get_session" in tools

    def test_session_not_found(self):
        tools = _register_tools()
        mock_dir = MagicMock()
        mock_file = MagicMock()
        mock_file.exists.return_value = False
        mock_dir.__truediv__ = MagicMock(return_value=mock_file)

        with patch(f"{_MOD}.EVIDENCE_DIR", mock_dir):
            result = json.loads(tools["governance_get_session"]("SESSION-2026-01-01-X"))
        assert "error" in result
        assert "not found" in result["error"]

    def test_session_found_returns_content(self):
        tools = _register_tools()
        content = (
            "# Session\n"
            "**Date:** 2026-02-10\n"
            "**Session ID:** SESSION-2026-02-10-TEST\n"
            "**Status:** COMPLETED\n"
            "## Details\n"
            "Some details here.\n"
        )
        mock_dir = MagicMock()
        mock_file = MagicMock()
        mock_file.exists.return_value = True
        mock_file.read_text.return_value = content
        mock_dir.__truediv__ = MagicMock(return_value=mock_file)

        with patch(f"{_MOD}.EVIDENCE_DIR", mock_dir):
            result = json.loads(tools["governance_get_session"]("SESSION-2026-02-10-TEST"))
        assert result["session_id"] == "SESSION-2026-02-10-TEST"
        assert result["content"] == content
        assert result["metadata"]["date"] == "2026-02-10"
        assert result["metadata"]["status"] == "COMPLETED"
        assert result["lines"] == 7  # trailing newline adds empty final line

    def test_already_has_md_extension(self):
        tools = _register_tools()
        mock_dir = MagicMock()
        mock_file = MagicMock()
        mock_file.exists.return_value = True
        mock_file.read_text.return_value = "# x\n"
        mock_dir.__truediv__ = MagicMock(return_value=mock_file)

        with patch(f"{_MOD}.EVIDENCE_DIR", mock_dir):
            result = json.loads(tools["governance_get_session"]("SESSION-2026-01-01-X.md"))
        assert result["session_id"] == "SESSION-2026-01-01-X"

    def test_read_exception_returns_error(self):
        tools = _register_tools()
        mock_dir = MagicMock()
        mock_file = MagicMock()
        mock_file.exists.return_value = True
        mock_file.read_text.side_effect = IOError("Disk error")
        mock_dir.__truediv__ = MagicMock(return_value=mock_file)

        with patch(f"{_MOD}.EVIDENCE_DIR", mock_dir):
            result = json.loads(tools["governance_get_session"]("SESSION-2026-01-01-X"))
        assert "error" in result
        assert "Failed to read" in result["error"]

    def test_metadata_parsing_partial(self):
        """File with only Date metadata."""
        tools = _register_tools()
        content = "# Session\n**Date:** 2026-02-10\nContent here.\n"
        mock_dir = MagicMock()
        mock_file = MagicMock()
        mock_file.exists.return_value = True
        mock_file.read_text.return_value = content
        mock_dir.__truediv__ = MagicMock(return_value=mock_file)

        with patch(f"{_MOD}.EVIDENCE_DIR", mock_dir):
            result = json.loads(tools["governance_get_session"]("SESSION-2026-02-10-X"))
        assert result["metadata"]["date"] == "2026-02-10"
        assert "status" not in result["metadata"]
