"""
RF-004: Robot Framework Library for MCP Pre-flight Validation.

Wraps hooks/checkers/mcp_preflight.py for Robot Framework tests.
Per GAP-CONTEXT-EFFICIENCY-001, TACTIC-2-C: Test duplicate tool registrations.
"""

import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / ".claude"))


class MCPPreflightLibrary:
    """Robot Framework library for MCP Pre-flight testing."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self._checker = None
        self._hooks_available = False
        try:
            from hooks.checkers.mcp_preflight import MCPPreflightChecker
            self._hooks_available = True
        except ImportError:
            pass

    def hooks_available(self) -> bool:
        """Check if hooks modules are available."""
        return self._hooks_available

    def checker_initializes(self) -> Dict[str, Any]:
        """Test MCPPreflightChecker initializes with project root."""
        if not self._hooks_available:
            return {"skipped": True, "reason": "Hooks modules not available"}

        from hooks.checkers.mcp_preflight import MCPPreflightChecker
        checker = MCPPreflightChecker(PROJECT_ROOT)
        return {
            "project_root_matches": checker.project_root == PROJECT_ROOT,
            "project_root": str(checker.project_root)
        }

    def find_duplicate_tools(self) -> Dict[str, Any]:
        """Test no duplicate tool registrations exist."""
        if not self._hooks_available:
            return {"skipped": True, "reason": "Hooks modules not available"}

        from hooks.checkers.mcp_preflight import MCPPreflightChecker
        checker = MCPPreflightChecker(PROJECT_ROOT)
        duplicates = checker.find_duplicate_tools()
        return {
            "no_duplicates": len(duplicates) == 0,
            "duplicate_count": len(duplicates),
            "duplicates": list(duplicates.keys()) if duplicates else []
        }

    def check_module_syntax(self) -> Dict[str, Any]:
        """Test MCP modules have valid Python syntax."""
        if not self._hooks_available:
            return {"skipped": True, "reason": "Hooks modules not available"}

        from hooks.checkers.mcp_preflight import MCPPreflightChecker
        checker = MCPPreflightChecker(PROJECT_ROOT)
        errors = checker.check_module_syntax()
        return {
            "no_errors": len(errors) == 0,
            "error_count": len(errors),
            "errors": errors[:5] if errors else []
        }

    def preflight_check_passes(self) -> Dict[str, Any]:
        """Test full pre-flight check passes."""
        if not self._hooks_available:
            return {"skipped": True, "reason": "Hooks modules not available"}

        from hooks.checkers.mcp_preflight import check_mcp_preflight
        result = check_mcp_preflight()
        return {
            "success": result.success,
            "message": result.message,
            "issues": result.details.get("issues", [])[:5]
        }

    def tool_extraction_from_file(self) -> Dict[str, Any]:
        """Test tool functions are correctly extracted from Python files."""
        if not self._hooks_available:
            return {"skipped": True, "reason": "Hooks modules not available"}

        from hooks.checkers.mcp_preflight import MCPPreflightChecker

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            checker = MCPPreflightChecker(tmp_path)

            # Create a test file with tool functions
            test_file = tmp_path / "test_tools.py"
            test_file.write_text('''
from mcp import tool

@tool
def governance_test_tool():
    """A test tool."""
    pass

def governance_another_tool():
    """Another governance tool (by naming convention)."""
    pass

def regular_function():
    """Not a tool."""
    pass
''')
            tools = checker._extract_tool_functions(test_file)
            tool_names = [t[0] for t in tools]

            return {
                "has_decorated_tool": "governance_test_tool" in tool_names,
                "has_convention_tool": "governance_another_tool" in tool_names,
                "excludes_regular": "regular_function" not in tool_names,
                "tool_names": tool_names
            }

    def duplicate_detection(self) -> Dict[str, Any]:
        """Test duplicate tools are detected across files."""
        if not self._hooks_available:
            return {"skipped": True, "reason": "Hooks modules not available"}

        from hooks.checkers.mcp_preflight import MCPPreflightChecker

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            checker = MCPPreflightChecker(tmp_path)

            # Create tool directory
            tool_dir = tmp_path / "governance" / "mcp_tools"
            tool_dir.mkdir(parents=True)

            # Create two files with duplicate tool
            (tool_dir / "file1.py").write_text('''
def governance_duplicate_tool():
    pass
''')
            (tool_dir / "file2.py").write_text('''
def governance_duplicate_tool():
    pass
''')
            # Update checker to scan our test directory
            checker.MCP_TOOL_DIRS = ["governance/mcp_tools"]
            duplicates = checker.find_duplicate_tools()

            return {
                "detected_duplicate": "governance_duplicate_tool" in duplicates,
                "file_count": len(duplicates.get("governance_duplicate_tool", [])),
                "duplicates": list(duplicates.keys())
            }

    def all_mcp_modules_exist(self) -> Dict[str, Any]:
        """Test all configured MCP modules exist."""
        if not self._hooks_available:
            return {"skipped": True, "reason": "Hooks modules not available"}

        from hooks.checkers.mcp_preflight import MCPPreflightChecker
        checker = MCPPreflightChecker(PROJECT_ROOT)

        missing = []
        for module_path in checker.MCP_MODULES:
            full_path = PROJECT_ROOT / module_path
            if not full_path.exists():
                missing.append(module_path)

        # Allow some modules to not exist (claude_mem may be optional)
        critical_missing = [m for m in missing if "governance" in m]
        return {
            "no_critical_missing": len(critical_missing) == 0,
            "missing_count": len(missing),
            "critical_missing": critical_missing[:5]
        }

    def tool_count_reasonable(self) -> Dict[str, Any]:
        """Test tool count is within reasonable range."""
        if not self._hooks_available:
            return {"skipped": True, "reason": "Hooks modules not available"}

        from hooks.checkers.mcp_preflight import MCPPreflightChecker
        checker = MCPPreflightChecker(PROJECT_ROOT)
        tool_count = checker._count_tools_scanned()

        return {
            "has_tools": tool_count > 0,
            "count_reasonable": tool_count < 500,
            "tool_count": tool_count
        }
