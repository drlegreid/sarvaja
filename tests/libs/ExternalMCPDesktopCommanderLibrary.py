"""
Robot Framework Library for External MCP Desktop Commander Tools Tests.

Per: RULE-007 (MCP Tool Matrix), DOC-SIZE-01-v1.
Split from tests/test_external_mcp_tools.py
"""
import json
from pathlib import Path
from robot.api.deco import keyword


def call_tool(tools, method_name, *args, **kwargs):
    """Call a tool method, handling both agno and stub cases."""
    method = getattr(tools, method_name)
    if hasattr(method, 'entrypoint'):
        return method.entrypoint(tools, *args, **kwargs)
    else:
        return method(*args, **kwargs)


class ExternalMCPDesktopCommanderLibrary:
    """Library for Desktop Commander tools tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    # =========================================================================
    # DesktopCommanderConfig Tests
    # =========================================================================

    @keyword("Desktop Commander Default Config")
    def desktop_commander_default_config(self):
        """Test default configuration values."""
        try:
            from agent.external_mcp_tools import DesktopCommanderConfig
            config = DesktopCommanderConfig()
            return {
                "allowed_directories_none": config.allowed_directories is None,
                "file_read_limit_1000": config.file_read_limit == 1000
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Desktop Commander Custom Config")
    def desktop_commander_custom_config(self):
        """Test custom configuration."""
        try:
            from agent.external_mcp_tools import DesktopCommanderConfig
            config = DesktopCommanderConfig(
                allowed_directories=["C:\\Projects", "D:\\Data"],
                file_read_limit=500
            )
            return {
                "allowed_directories_count": len(config.allowed_directories) == 2,
                "file_read_limit_500": config.file_read_limit == 500
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # DesktopCommanderTools Tests
    # =========================================================================

    @keyword("Desktop Commander Toolkit Creation")
    def desktop_commander_toolkit_creation(self):
        """Test toolkit can be created."""
        try:
            from agent.external_mcp_tools import DesktopCommanderTools
            tools = DesktopCommanderTools()
            return {
                "name_correct": tools.name == "desktop_commander"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Desktop Commander Tool Registration")
    def desktop_commander_tool_registration(self):
        """Test all tools are registered."""
        try:
            from agent.external_mcp_tools import DesktopCommanderTools
            tools = DesktopCommanderTools()
            expected_tools = [
                "read_file", "write_file", "list_directory",
                "search_files", "get_file_info", "create_directory", "move_file"
            ]
            results = {}
            for tool_name in expected_tools:
                results[f"{tool_name}_registered"] = tool_name in tools.functions
            return results
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Desktop Commander Read File Tool")
    def desktop_commander_read_file_tool(self):
        """Test read_file tool returns valid JSON."""
        try:
            from agent.external_mcp_tools import DesktopCommanderTools
            tools = DesktopCommanderTools()
            result = call_tool(tools, 'read_file', path="C:\\test.txt", offset=10, length=50)
            parsed = json.loads(result)
            return {
                "action_read_file": parsed["action"] == "read_file",
                "path_correct": parsed["path"] == "C:\\test.txt",
                "offset_correct": parsed["offset"] == 10,
                "length_correct": parsed["length"] == 50
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("Desktop Commander Write File Tool")
    def desktop_commander_write_file_tool(self):
        """Test write_file tool returns valid JSON."""
        try:
            from agent.external_mcp_tools import DesktopCommanderTools
            tools = DesktopCommanderTools()
            result = call_tool(tools, 'write_file', path="C:\\output.txt", content="Hello World", mode="append")
            parsed = json.loads(result)
            return {
                "action_write_file": parsed["action"] == "write_file",
                "content_length_11": parsed["content_length"] == 11,
                "mode_append": parsed["mode"] == "append"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("Desktop Commander List Directory Tool")
    def desktop_commander_list_directory_tool(self):
        """Test list_directory tool returns valid JSON."""
        try:
            from agent.external_mcp_tools import DesktopCommanderTools
            tools = DesktopCommanderTools()
            result = call_tool(tools, 'list_directory', path="C:\\Projects", depth=1)
            parsed = json.loads(result)
            return {
                "action_list_directory": parsed["action"] == "list_directory",
                "path_correct": parsed["path"] == "C:\\Projects",
                "depth_1": parsed["depth"] == 1
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("Desktop Commander Search Files Tool")
    def desktop_commander_search_files_tool(self):
        """Test search_files tool returns valid JSON."""
        try:
            from agent.external_mcp_tools import DesktopCommanderTools
            tools = DesktopCommanderTools()
            result = call_tool(tools, 'search_files', path="C:\\Code", pattern="*.py", search_type="files")
            parsed = json.loads(result)
            return {
                "action_search": parsed["action"] == "search",
                "pattern_py": parsed["pattern"] == "*.py",
                "search_type_files": parsed["search_type"] == "files"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("Desktop Commander Search Content")
    def desktop_commander_search_content(self):
        """Test search_files for content."""
        try:
            from agent.external_mcp_tools import DesktopCommanderTools
            tools = DesktopCommanderTools()
            result = call_tool(tools, 'search_files', path="C:\\Code", pattern="TODO", search_type="content")
            parsed = json.loads(result)
            return {
                "search_type_content": parsed["search_type"] == "content"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("Desktop Commander Get File Info Tool")
    def desktop_commander_get_file_info_tool(self):
        """Test get_file_info tool returns valid JSON."""
        try:
            from agent.external_mcp_tools import DesktopCommanderTools
            tools = DesktopCommanderTools()
            result = call_tool(tools, 'get_file_info', path="C:\\test.txt")
            parsed = json.loads(result)
            return {
                "action_get_file_info": parsed["action"] == "get_file_info",
                "path_correct": parsed["path"] == "C:\\test.txt"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("Desktop Commander Create Directory Tool")
    def desktop_commander_create_directory_tool(self):
        """Test create_directory tool returns valid JSON."""
        try:
            from agent.external_mcp_tools import DesktopCommanderTools
            tools = DesktopCommanderTools()
            result = call_tool(tools, 'create_directory', path="C:\\NewFolder")
            parsed = json.loads(result)
            return {
                "action_create_directory": parsed["action"] == "create_directory",
                "path_correct": parsed["path"] == "C:\\NewFolder"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("Desktop Commander Move File Tool")
    def desktop_commander_move_file_tool(self):
        """Test move_file tool returns valid JSON."""
        try:
            from agent.external_mcp_tools import DesktopCommanderTools
            tools = DesktopCommanderTools()
            result = call_tool(tools, 'move_file', source="C:\\old.txt", destination="C:\\new.txt")
            parsed = json.loads(result)
            return {
                "action_move_file": parsed["action"] == "move_file",
                "source_correct": parsed["source"] == "C:\\old.txt",
                "destination_correct": parsed["destination"] == "C:\\new.txt"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except json.JSONDecodeError:
            return {"valid_json": False}
