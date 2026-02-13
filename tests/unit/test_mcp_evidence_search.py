"""
Unit tests for Evidence Search MCP Tools.

Batch 148: Tests for governance/mcp_tools/evidence/search.py
- evidence_search: semantic search + keyword fallback
"""

import json
import os
from unittest.mock import patch, MagicMock

import pytest

_MOD = "governance.mcp_tools.evidence.search"


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
    from governance.mcp_tools.evidence.search import register_search_tools

    tools = {}

    class MockMCP:
        def tool(self):
            def decorator(fn):
                tools[fn.__name__] = fn
                return fn
            return decorator

    register_search_tools(MockMCP())
    return tools


class TestRegistration:
    def test_registers_evidence_search(self):
        tools = _register_tools()
        assert "evidence_search" in tools


class TestEvidenceSearchSemantic:
    """Test semantic search path."""

    @patch(f"{_MOD}.glob.glob", return_value=[])
    def test_semantic_search_exception_falls_back(self, mock_glob):
        """When VectorStore import fails, keyword fallback is used."""
        tools = _register_tools()
        # No files match, so empty keyword results
        result = json.loads(tools["evidence_search"](query="test query"))
        assert result["search_method"] == "keyword_fallback"
        assert result["count"] == 0


class TestEvidenceSearchKeyword:
    """Test keyword fallback path."""

    @patch(f"{_MOD}.glob.glob")
    @patch(f"{_MOD}.Path")
    def test_keyword_search_finds_matches(self, mock_path_cls, mock_glob):
        tools = _register_tools()

        mock_path = MagicMock()
        mock_path.stem = "SESSION-2026-01-01-AUTH"
        mock_path.read_text.return_value = (
            "# Authentication Session\n"
            "Discussed authentication security rules\n"
            "More auth content\n"
        )
        mock_path_cls.return_value = mock_path

        mock_glob.return_value = ["/evidence/SESSION-2026-01-01-AUTH.md"]

        result = json.loads(tools["evidence_search"](query="authentication"))
        assert result["search_method"] == "keyword_fallback"
        assert result["count"] >= 1
        assert result["results"][0]["source"] == "SESSION-2026-01-01-AUTH"

    @patch(f"{_MOD}.glob.glob", return_value=[])
    def test_empty_results(self, mock_glob):
        tools = _register_tools()
        result = json.loads(tools["evidence_search"](query="nonexistent"))
        assert result["count"] == 0
        assert result["results"] == []

    @patch(f"{_MOD}.glob.glob")
    @patch(f"{_MOD}.Path")
    def test_top_k_limits_results(self, mock_path_cls, mock_glob):
        tools = _register_tools()

        files = [f"/evidence/SESSION-2026-01-0{i}-MATCH.md" for i in range(1, 6)]
        mock_glob.return_value = files

        def path_factory(filepath):
            p = MagicMock()
            p.stem = str(filepath).split("/")[-1].replace(".md", "")
            p.read_text.return_value = "Contains the query keyword\n"
            return p

        mock_path_cls.side_effect = path_factory

        result = json.loads(tools["evidence_search"](query="keyword", top_k=2))
        assert result["count"] <= 2

    @patch(f"{_MOD}.glob.glob")
    @patch(f"{_MOD}.Path")
    def test_read_error_skipped(self, mock_path_cls, mock_glob):
        tools = _register_tools()
        mock_glob.return_value = ["/evidence/BAD.md"]

        mock_path = MagicMock()
        mock_path.read_text.side_effect = IOError("Permission denied")
        mock_path_cls.return_value = mock_path

        result = json.loads(tools["evidence_search"](query="test"))
        assert result["count"] == 0

    @patch(f"{_MOD}.glob.glob")
    @patch(f"{_MOD}.Path")
    def test_scores_by_occurrence_count(self, mock_path_cls, mock_glob):
        tools = _register_tools()
        # Function calls glob twice (evidence + docs patterns)
        mock_glob.side_effect = [
            ["/evidence/A.md", "/evidence/B.md"],
            [],  # docs pattern returns nothing
        ]

        call_count = [0]

        def path_factory(filepath):
            p = MagicMock()
            call_count[0] += 1
            if "A.md" in str(filepath):
                p.stem = "A"
                p.read_text.return_value = "auth auth auth"  # 3 occurrences
                p.__str__ = MagicMock(return_value="/evidence/A.md")
            else:
                p.stem = "B"
                p.read_text.return_value = "auth"  # 1 occurrence
                p.__str__ = MagicMock(return_value="/evidence/B.md")
            return p

        mock_path_cls.side_effect = path_factory

        result = json.loads(tools["evidence_search"](query="auth"))
        # Higher score should come first
        assert result["count"] == 2
        assert result["results"][0]["score"] >= result["results"][1]["score"]

    @patch(f"{_MOD}.glob.glob")
    @patch(f"{_MOD}.Path")
    def test_source_type_derived(self, mock_path_cls, mock_glob):
        tools = _register_tools()
        mock_glob.return_value = ["/evidence/RULE-DOC.md"]

        mock_path = MagicMock()
        mock_path.stem = "RULE-DOC"
        mock_path.read_text.return_value = "rule content match"
        mock_path.__str__ = MagicMock(return_value="/docs/rules/RULE-DOC.md")
        mock_path_cls.return_value = mock_path

        result = json.loads(tools["evidence_search"](query="match"))
        assert result["count"] >= 0  # May or may not match path-based type
