"""
Unit tests for Core Document Viewing MCP Tools.

Per DOC-SIZE-01-v1: Tests for mcp_tools/evidence/documents_core.py module.
Tests: doc_get, docs_list, FILE_TYPE_MAP.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

_P = "governance.mcp_tools.evidence.documents_core"


class _CaptureMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, name=None):
        def decorator(fn):
            key = name or fn.__name__
            self.tools[key] = fn
            return fn
        return decorator


def _register():
    mcp = _CaptureMCP()
    from governance.mcp_tools.evidence.documents_core import register_core_document_tools
    register_core_document_tools(mcp)
    return mcp.tools


@pytest.fixture(autouse=True)
def _mock_format():
    with patch(f"{_P}.format_mcp_result", side_effect=lambda x: json.dumps(x)):
        yield


# ── FILE_TYPE_MAP ───────────────────────────────────────────────


class TestFileTypeMap:
    def test_markdown(self):
        from governance.mcp_tools.evidence.documents_core import FILE_TYPE_MAP
        assert FILE_TYPE_MAP[".md"]["type"] == "markdown"

    def test_python(self):
        from governance.mcp_tools.evidence.documents_core import FILE_TYPE_MAP
        assert FILE_TYPE_MAP[".py"]["type"] == "code"
        assert FILE_TYPE_MAP[".py"]["language"] == "Python"

    def test_typeql(self):
        from governance.mcp_tools.evidence.documents_core import FILE_TYPE_MAP
        assert FILE_TYPE_MAP[".tql"]["language"] == "TypeQL"

    def test_json(self):
        from governance.mcp_tools.evidence.documents_core import FILE_TYPE_MAP
        assert FILE_TYPE_MAP[".json"]["type"] == "json"


# ── doc_get ─────────────────────────────────────────────────────


class TestDocGet:
    def test_success(self, tmp_path):
        tools = _register()
        doc = tmp_path / "test.md"
        doc.write_text("# Title\nLine 2\nLine 3\n")
        result = json.loads(tools["doc_get"](path=str(doc)))
        assert result["line_count"] == 4  # includes trailing empty
        assert result["file_type"] == "markdown"
        assert result["syntax"] == "markdown"
        assert "# Title" in result["content"]

    def test_python_file(self, tmp_path):
        tools = _register()
        doc = tmp_path / "test.py"
        doc.write_text("def hello():\n    pass\n")
        result = json.loads(tools["doc_get"](path=str(doc)))
        assert result["file_type"] == "code"
        assert result["language"] == "Python"

    def test_not_found(self):
        tools = _register()
        result = json.loads(tools["doc_get"](path="/nonexistent/file.md"))
        assert "error" in result

    def test_relative_not_found(self):
        tools = _register()
        result = json.loads(tools["doc_get"](path="nonexistent_xyz_abc.md"))
        assert "error" in result
        assert "tried_paths" in result

    def test_pagination_offset(self, tmp_path):
        tools = _register()
        doc = tmp_path / "large.md"
        lines = [f"Line {i}" for i in range(20)]
        doc.write_text("\n".join(lines))
        result = json.loads(tools["doc_get"](path=str(doc), offset=5, max_lines=3))
        assert "pagination" in result
        assert result["pagination"]["offset"] == 5
        assert result["pagination"]["returned"] == 3
        assert result["pagination"]["has_more"] is True

    def test_pagination_max_lines(self, tmp_path):
        tools = _register()
        doc = tmp_path / "large.md"
        lines = [f"Line {i}" for i in range(10)]
        doc.write_text("\n".join(lines))
        result = json.loads(tools["doc_get"](path=str(doc), max_lines=3))
        assert "pagination" in result
        assert result["pagination"]["returned"] == 3

    def test_no_pagination_for_small_files(self, tmp_path):
        tools = _register()
        doc = tmp_path / "small.md"
        doc.write_text("Hello\n")
        result = json.loads(tools["doc_get"](path=str(doc)))
        assert "pagination" not in result

    def test_unlimited_lines(self, tmp_path):
        tools = _register()
        doc = tmp_path / "test.md"
        lines = [f"Line {i}" for i in range(600)]
        doc.write_text("\n".join(lines))
        result = json.loads(tools["doc_get"](path=str(doc), max_lines=0))
        assert result["line_count"] == 600

    def test_unknown_extension(self, tmp_path):
        tools = _register()
        doc = tmp_path / "test.xyz"
        doc.write_text("content\n")
        result = json.loads(tools["doc_get"](path=str(doc)))
        assert result["file_type"] == "unknown"
        assert result["syntax"] == "text"


# ── docs_list ───────────────────────────────────────────────────


class TestDocsList:
    def test_success(self, tmp_path):
        tools = _register()
        (tmp_path / "a.md").write_text("# A\n")
        (tmp_path / "b.md").write_text("# B\n")
        (tmp_path / "c.txt").write_text("text\n")
        result = json.loads(tools["docs_list"](directory=str(tmp_path), pattern="*.md"))
        assert result["count"] == 2

    def test_recursive(self, tmp_path):
        tools = _register()
        sub = tmp_path / "sub"
        sub.mkdir()
        (tmp_path / "a.md").write_text("# A\n")
        (sub / "b.md").write_text("# B\n")
        result = json.loads(tools["docs_list"](
            directory=str(tmp_path), pattern="*.md", recursive=True,
        ))
        assert result["count"] == 2

    def test_non_recursive(self, tmp_path):
        tools = _register()
        sub = tmp_path / "sub"
        sub.mkdir()
        (tmp_path / "a.md").write_text("# A\n")
        (sub / "b.md").write_text("# B\n")
        result = json.loads(tools["docs_list"](
            directory=str(tmp_path), pattern="*.md", recursive=False,
        ))
        assert result["count"] == 1

    def test_empty_directory(self, tmp_path):
        tools = _register()
        result = json.loads(tools["docs_list"](directory=str(tmp_path), pattern="*.md"))
        assert result["count"] == 0

    def test_directory_not_found(self):
        tools = _register()
        result = json.loads(tools["docs_list"](directory="/nonexistent_dir_xyz"))
        assert "error" in result

    def test_file_metadata(self, tmp_path):
        tools = _register()
        (tmp_path / "test.md").write_text("# Hello\nWorld\n")
        result = json.loads(tools["docs_list"](directory=str(tmp_path)))
        assert result["count"] == 1
        doc = result["documents"][0]
        assert doc["name"] == "test.md"
        assert doc["type"] == "markdown"
        assert doc["size"] > 0

    def test_legacy_aliases(self):
        tools = _register()
        assert "governance_get_document" in tools
        assert "governance_list_documents" in tools
