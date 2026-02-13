"""
Unit tests for Core Document Viewing MCP Tools.

Batch 153: Tests for governance/mcp_tools/evidence/documents_core.py
- doc_get: path resolution, pagination, file type detection
- docs_list: directory listing, pattern matching, recursive
- FILE_TYPE_MAP: extension → type mapping
"""

import json
from unittest.mock import patch, MagicMock

import pytest

from governance.mcp_tools.evidence.documents_core import (
    register_core_document_tools,
    FILE_TYPE_MAP,
)

_MOD = "governance.mcp_tools.evidence.documents_core"


def _json_fmt(data):
    return json.dumps(data, indent=2, default=str)


class _CaptureMCP:
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
    return mcp.tools


@pytest.fixture(autouse=True)
def _force_json():
    with patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt):
        yield


# ── Registration ────────────────────────────────────────

class TestRegistration:
    def test_registers_tools(self):
        tools = _register()
        assert "doc_get" in tools
        assert "docs_list" in tools


# ── FILE_TYPE_MAP ───────────────────────────────────────

class TestFileTypeMap:
    def test_markdown(self):
        assert FILE_TYPE_MAP[".md"]["type"] == "markdown"

    def test_python(self):
        assert FILE_TYPE_MAP[".py"]["type"] == "code"
        assert FILE_TYPE_MAP[".py"]["language"] == "Python"

    def test_json(self):
        assert FILE_TYPE_MAP[".json"]["type"] == "json"

    def test_typeql(self):
        assert FILE_TYPE_MAP[".tql"]["language"] == "TypeQL"


# ── doc_get ─────────────────────────────────────────────

class TestDocGet:
    def test_absolute_path_found(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("line1\nline2\nline3")
        tools = _register()
        result = json.loads(tools["doc_get"](path=str(f)))
        assert result["line_count"] == 3
        assert result["file_type"] == "markdown"
        assert "line1" in result["content"]

    def test_file_not_found(self):
        tools = _register()
        result = json.loads(tools["doc_get"](path="/nonexistent/file.md"))
        assert "error" in result

    def test_pagination_offset(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("\n".join(f"line{i}" for i in range(10)))
        tools = _register()
        result = json.loads(tools["doc_get"](path=str(f), offset=5))
        assert "pagination" in result
        assert result["pagination"]["offset"] == 5

    def test_pagination_max_lines(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("\n".join(f"line{i}" for i in range(10)))
        tools = _register()
        result = json.loads(tools["doc_get"](path=str(f), max_lines=3))
        assert "pagination" in result
        assert result["pagination"]["returned"] == 3
        assert result["pagination"]["has_more"] is True

    def test_python_file_type(self, tmp_path):
        f = tmp_path / "test.py"
        f.write_text("print('hello')")
        tools = _register()
        result = json.loads(tools["doc_get"](path=str(f)))
        assert result["file_type"] == "code"
        assert result["language"] == "Python"

    def test_unknown_extension(self, tmp_path):
        f = tmp_path / "test.xyz"
        f.write_text("data")
        tools = _register()
        result = json.loads(tools["doc_get"](path=str(f)))
        assert result["file_type"] == "unknown"

    def test_no_pagination_info_when_all_fits(self, tmp_path):
        f = tmp_path / "small.md"
        f.write_text("just one line")
        tools = _register()
        result = json.loads(tools["doc_get"](path=str(f)))
        assert "pagination" not in result


# ── docs_list ───────────────────────────────────────────

class TestDocsList:
    def test_list_files(self, tmp_path):
        (tmp_path / "a.md").write_text("a")
        (tmp_path / "b.md").write_text("b")
        (tmp_path / "c.txt").write_text("c")
        tools = _register()
        result = json.loads(tools["docs_list"](
            directory=str(tmp_path), pattern="*.md"))
        assert result["count"] == 2

    def test_directory_not_found(self):
        tools = _register()
        result = json.loads(tools["docs_list"](directory="/nonexistent"))
        assert "error" in result

    def test_recursive_search(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (tmp_path / "a.md").write_text("a")
        (sub / "b.md").write_text("b")
        tools = _register()
        result = json.loads(tools["docs_list"](
            directory=str(tmp_path), pattern="*.md", recursive=True))
        assert result["count"] == 2

    def test_non_recursive_skips_subdirs(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (tmp_path / "a.md").write_text("a")
        (sub / "b.md").write_text("b")
        tools = _register()
        result = json.loads(tools["docs_list"](
            directory=str(tmp_path), pattern="*.md", recursive=False))
        assert result["count"] == 1

    def test_includes_file_metadata(self, tmp_path):
        (tmp_path / "test.md").write_text("content")
        tools = _register()
        result = json.loads(tools["docs_list"](
            directory=str(tmp_path), pattern="*.md"))
        doc = result["documents"][0]
        assert "name" in doc
        assert "size" in doc
        assert doc["type"] == "markdown"
