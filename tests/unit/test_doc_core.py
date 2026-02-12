"""
Unit tests for Core Document Viewing MCP Tools.

Per DOC-SIZE-01-v1: Tests for mcp_tools/evidence/documents_core.py module.
Tests: doc_get, docs_list, FILE_TYPE_MAP.
"""

import json
import pytest
from unittest.mock import patch
from pathlib import Path

from governance.mcp_tools.evidence.documents_core import (
    FILE_TYPE_MAP,
    register_core_document_tools,
)


def _json_format(data, **kwargs):
    """Force JSON output for test assertions."""
    return json.dumps(data, indent=2, default=str)


class _CaptureMCP:
    """Captures tools registered via @mcp.tool()."""

    def __init__(self):
        self.tools = {}

    def tool(self, name=None):
        if callable(name):
            self.tools[name.__name__] = name
            return name

        def decorator(fn):
            key = name if name else fn.__name__
            self.tools[key] = fn
            return fn
        return decorator


def _register():
    mcp = _CaptureMCP()
    register_core_document_tools(mcp)
    return mcp


@pytest.fixture(autouse=True)
def _force_json_output():
    """Patch format_mcp_result to return JSON for all tests."""
    with patch(
        "governance.mcp_tools.evidence.documents_core.format_mcp_result",
        side_effect=_json_format,
    ):
        yield


# ---------------------------------------------------------------------------
# FILE_TYPE_MAP
# ---------------------------------------------------------------------------
class TestFileTypeMap:
    """Tests for FILE_TYPE_MAP constant."""

    def test_markdown_type(self):
        assert FILE_TYPE_MAP[".md"]["type"] == "markdown"

    def test_python_type(self):
        info = FILE_TYPE_MAP[".py"]
        assert info["type"] == "code"
        assert info["language"] == "Python"

    def test_json_type(self):
        assert FILE_TYPE_MAP[".json"]["type"] == "json"

    def test_yaml_variants(self):
        assert FILE_TYPE_MAP[".yaml"]["type"] == "yaml"
        assert FILE_TYPE_MAP[".yml"]["type"] == "yaml"

    def test_typeql_type(self):
        assert FILE_TYPE_MAP[".tql"]["syntax"] == "typeql"

    def test_log_type(self):
        assert FILE_TYPE_MAP[".log"]["type"] == "log"

    def test_shell_type(self):
        assert FILE_TYPE_MAP[".sh"]["language"] == "Shell"


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
class TestRegistration:
    """Tests for tool registration."""

    def test_registers_doc_get(self):
        mcp = _register()
        assert "doc_get" in mcp.tools

    def test_registers_docs_list(self):
        mcp = _register()
        assert "docs_list" in mcp.tools

    def test_registers_legacy_aliases(self):
        mcp = _register()
        assert "governance_get_document" in mcp.tools
        assert "governance_list_documents" in mcp.tools

    def test_total_tool_count(self):
        mcp = _register()
        assert len(mcp.tools) == 4  # 2 primary + 2 legacy aliases


# ---------------------------------------------------------------------------
# doc_get
# ---------------------------------------------------------------------------
class TestDocGet:
    """Tests for doc_get tool."""

    def test_reads_existing_file(self, tmp_path):
        test_file = tmp_path / "test.md"
        test_file.write_text("# Hello\nWorld\nLine 3")
        mcp = _register()
        result = json.loads(mcp.tools["doc_get"](str(test_file)))
        assert result["line_count"] == 3
        assert result["file_type"] == "markdown"
        assert "# Hello" in result["content"]

    def test_nonexistent_file_returns_error(self):
        mcp = _register()
        result = json.loads(mcp.tools["doc_get"]("/nonexistent/file.md"))
        assert "error" in result

    def test_pagination_offset(self, tmp_path):
        test_file = tmp_path / "big.md"
        test_file.write_text("\n".join(f"Line {i}" for i in range(20)))
        mcp = _register()
        result = json.loads(mcp.tools["doc_get"](str(test_file), max_lines=5, offset=10))
        assert "pagination" in result
        assert result["pagination"]["offset"] == 10
        assert result["pagination"]["returned"] == 5

    def test_pagination_has_more(self, tmp_path):
        test_file = tmp_path / "big.md"
        test_file.write_text("\n".join(f"Line {i}" for i in range(20)))
        mcp = _register()
        result = json.loads(mcp.tools["doc_get"](str(test_file), max_lines=5))
        assert result["pagination"]["has_more"] is True

    def test_detects_python_file_type(self, tmp_path):
        test_file = tmp_path / "script.py"
        test_file.write_text("print('hello')")
        mcp = _register()
        result = json.loads(mcp.tools["doc_get"](str(test_file)))
        assert result["file_type"] == "code"
        assert result["language"] == "Python"

    def test_unknown_extension(self, tmp_path):
        test_file = tmp_path / "data.xyz"
        test_file.write_text("custom data")
        mcp = _register()
        result = json.loads(mcp.tools["doc_get"](str(test_file)))
        assert result["file_type"] == "unknown"

    def test_no_pagination_when_small(self, tmp_path):
        test_file = tmp_path / "small.md"
        test_file.write_text("one\ntwo\nthree")
        mcp = _register()
        result = json.loads(mcp.tools["doc_get"](str(test_file)))
        assert "pagination" not in result


# ---------------------------------------------------------------------------
# docs_list
# ---------------------------------------------------------------------------
class TestDocsList:
    """Tests for docs_list tool."""

    def test_lists_files_in_directory(self, tmp_path):
        (tmp_path / "a.md").write_text("A")
        (tmp_path / "b.md").write_text("B")
        (tmp_path / "c.txt").write_text("C")
        mcp = _register()
        result = json.loads(mcp.tools["docs_list"](directory=str(tmp_path), pattern="*.md"))
        assert result["count"] == 2

    def test_recursive_search(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (tmp_path / "a.md").write_text("A")
        (sub / "b.md").write_text("B")
        mcp = _register()
        result = json.loads(mcp.tools["docs_list"](
            directory=str(tmp_path), pattern="*.md", recursive=True
        ))
        assert result["count"] == 2

    def test_nonexistent_directory(self):
        mcp = _register()
        result = json.loads(mcp.tools["docs_list"](directory="/nonexistent/dir"))
        assert "error" in result

    def test_documents_have_metadata(self, tmp_path):
        (tmp_path / "test.md").write_text("Content")
        mcp = _register()
        result = json.loads(mcp.tools["docs_list"](directory=str(tmp_path), pattern="*.md"))
        doc = result["documents"][0]
        assert "name" in doc
        assert "size" in doc
        assert "type" in doc
        assert doc["type"] == "markdown"

    def test_empty_directory(self, tmp_path):
        mcp = _register()
        result = json.loads(mcp.tools["docs_list"](directory=str(tmp_path), pattern="*.md"))
        assert result["count"] == 0
        assert result["documents"] == []
