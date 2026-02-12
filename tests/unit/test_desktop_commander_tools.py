"""
Unit tests for Desktop Commander MCP Tools.

Per DOC-SIZE-01-v1: Tests for agent/external_mcp/desktop_commander.py module.
Tests: DesktopCommanderConfig, DesktopCommanderTools — read_file, write_file,
       list_directory, search_files, get_file_info, create_directory, move_file.
"""

import json

from agent.external_mcp.desktop_commander import (
    DesktopCommanderConfig,
    DesktopCommanderTools,
)


def _call(tools, method_name, *args, **kwargs):
    """Call an agno-wrapped tool method via its entrypoint."""
    fn = getattr(tools, method_name)
    if hasattr(fn, "entrypoint"):
        return fn.entrypoint(tools, *args, **kwargs)
    return fn(*args, **kwargs)


# ── DesktopCommanderConfig ─────────────────────────────────


class TestDesktopCommanderConfig:
    def test_defaults(self):
        cfg = DesktopCommanderConfig()
        assert cfg.allowed_directories is None
        assert cfg.file_read_limit == 1000

    def test_custom(self):
        cfg = DesktopCommanderConfig(
            allowed_directories=["/home", "/tmp"],
            file_read_limit=500,
        )
        assert cfg.allowed_directories == ["/home", "/tmp"]
        assert cfg.file_read_limit == 500


# ── DesktopCommanderTools init ─────────────────────────────


class TestDesktopCommanderToolsInit:
    def test_default_config(self):
        tools = DesktopCommanderTools()
        assert tools.name == "desktop_commander"
        assert tools.config.file_read_limit == 1000

    def test_custom_config(self):
        cfg = DesktopCommanderConfig(file_read_limit=200)
        tools = DesktopCommanderTools(config=cfg)
        assert tools.config.file_read_limit == 200

    def test_registers_seven_tools(self):
        tools = DesktopCommanderTools()
        assert len(tools.functions) == 7
        expected = {
            "read_file", "write_file", "list_directory",
            "search_files", "get_file_info", "create_directory", "move_file",
        }
        assert set(tools.functions.keys()) == expected


# ── read_file ──────────────────────────────────────────────


class TestReadFile:
    def test_basic(self):
        tools = DesktopCommanderTools()
        result = json.loads(_call(tools, "read_file", "/tmp/test.py"))
        assert result["action"] == "read_file"
        assert result["path"] == "/tmp/test.py"
        assert result["status"] == "simulated"

    def test_defaults(self):
        tools = DesktopCommanderTools()
        result = json.loads(_call(tools, "read_file", "/tmp/f.py"))
        assert result["offset"] == 0
        assert result["length"] == 1000

    def test_custom_offset_length(self):
        tools = DesktopCommanderTools()
        result = json.loads(_call(tools, "read_file", "/tmp/f.py", offset=50, length=200))
        assert result["offset"] == 50
        assert result["length"] == 200

    def test_message(self):
        tools = DesktopCommanderTools()
        result = json.loads(_call(tools, "read_file", "/tmp/f.py", length=10))
        assert "10 lines" in result["message"]
        assert "/tmp/f.py" in result["message"]


# ── write_file ─────────────────────────────────────────────


class TestWriteFile:
    def test_rewrite_mode(self):
        tools = DesktopCommanderTools()
        result = json.loads(_call(tools, "write_file", "/tmp/f.py", "hello world"))
        assert result["action"] == "write_file"
        assert result["mode"] == "rewrite"
        assert result["content_length"] == 11

    def test_append_mode(self):
        tools = DesktopCommanderTools()
        result = json.loads(_call(tools, "write_file", "/tmp/f.py", "data", mode="append"))
        assert result["mode"] == "append"

    def test_message_includes_length(self):
        tools = DesktopCommanderTools()
        result = json.loads(_call(tools, "write_file", "/tmp/f.py", "abc"))
        assert "3 chars" in result["message"]


# ── list_directory ─────────────────────────────────────────


class TestListDirectory:
    def test_basic(self):
        tools = DesktopCommanderTools()
        result = json.loads(_call(tools, "list_directory", "/home"))
        assert result["action"] == "list_directory"
        assert result["path"] == "/home"

    def test_default_depth(self):
        tools = DesktopCommanderTools()
        result = json.loads(_call(tools, "list_directory", "/tmp"))
        assert result["depth"] == 2

    def test_custom_depth(self):
        tools = DesktopCommanderTools()
        result = json.loads(_call(tools, "list_directory", "/tmp", depth=1))
        assert result["depth"] == 1


# ── search_files ───────────────────────────────────────────


class TestSearchFiles:
    def test_file_search(self):
        tools = DesktopCommanderTools()
        result = json.loads(_call(tools, "search_files", "/home", "*.py"))
        assert result["action"] == "search"
        assert result["pattern"] == "*.py"

    def test_content_search(self):
        tools = DesktopCommanderTools()
        result = json.loads(
            _call(tools, "search_files", "/src", "def main", search_type="content")
        )
        assert result["search_type"] == "content"

    def test_default_type(self):
        tools = DesktopCommanderTools()
        result = json.loads(_call(tools, "search_files", "/tmp", "x"))
        assert result["search_type"] == "files"

    def test_message(self):
        tools = DesktopCommanderTools()
        result = json.loads(_call(tools, "search_files", "/src", "test"))
        assert "'test'" in result["message"]
        assert "/src" in result["message"]


# ── get_file_info ──────────────────────────────────────────


class TestGetFileInfo:
    def test_basic(self):
        tools = DesktopCommanderTools()
        result = json.loads(_call(tools, "get_file_info", "/tmp/f.py"))
        assert result["action"] == "get_file_info"
        assert result["path"] == "/tmp/f.py"

    def test_message(self):
        tools = DesktopCommanderTools()
        result = json.loads(_call(tools, "get_file_info", "/some/path"))
        assert "/some/path" in result["message"]


# ── create_directory ───────────────────────────────────────


class TestCreateDirectory:
    def test_basic(self):
        tools = DesktopCommanderTools()
        result = json.loads(_call(tools, "create_directory", "/tmp/new_dir"))
        assert result["action"] == "create_directory"
        assert result["path"] == "/tmp/new_dir"

    def test_message(self):
        tools = DesktopCommanderTools()
        result = json.loads(_call(tools, "create_directory", "/some/dir"))
        assert "/some/dir" in result["message"]


# ── move_file ──────────────────────────────────────────────


class TestMoveFile:
    def test_basic(self):
        tools = DesktopCommanderTools()
        result = json.loads(_call(tools, "move_file", "/tmp/old.py", "/tmp/new.py"))
        assert result["action"] == "move_file"
        assert result["source"] == "/tmp/old.py"
        assert result["destination"] == "/tmp/new.py"

    def test_message(self):
        tools = DesktopCommanderTools()
        result = json.loads(_call(tools, "move_file", "/a", "/b"))
        assert "/a" in result["message"]
        assert "/b" in result["message"]
