"""
Unit tests for MCP Pre-flight Validation.

Per GAP-CONTEXT-EFFICIENCY-001, TACTIC-2-C:
Tests that MCP modules load without duplicate tool registrations.

Usage:
    pytest tests/unit/test_mcp_preflight.py -v
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / ".claude"))

# Check if hooks modules are available
HOOKS_AVAILABLE = False
try:
    from hooks.core.base import HookResult  # noqa: F401
    from hooks.checkers.mcp_preflight import MCPPreflightChecker, check_mcp_preflight
    HOOKS_AVAILABLE = True
except ImportError:
    MCPPreflightChecker = None
    check_mcp_preflight = None


@pytest.mark.skipif(not HOOKS_AVAILABLE, reason="Hooks modules not available")
class TestMCPPreflightChecker:
    """Test MCP pre-flight validation."""

    def test_checker_initializes(self):
        """MCPPreflightChecker initializes with project root."""
        checker = MCPPreflightChecker(PROJECT_ROOT)
        assert checker.project_root == PROJECT_ROOT

    def test_no_duplicate_tools(self):
        """MCP modules have no duplicate tool registrations."""
        checker = MCPPreflightChecker(PROJECT_ROOT)
        duplicates = checker.find_duplicate_tools()

        # Should have no duplicates (critical for MCP startup)
        assert len(duplicates) == 0, (
            f"Found duplicate tool registrations: {duplicates}\n"
            "Each tool name must be unique across all MCP modules.\n"
            "Fix by removing or renaming duplicate functions."
        )

    def test_module_syntax_valid(self):
        """MCP modules have valid Python syntax."""
        checker = MCPPreflightChecker(PROJECT_ROOT)
        errors = checker.check_module_syntax()

        assert len(errors) == 0, (
            f"Found syntax errors in MCP modules: {errors}\n"
            "Fix syntax errors before MCP servers can start."
        )

    def test_preflight_check_passes(self):
        """Full pre-flight check passes."""
        result = check_mcp_preflight()

        assert result.success, (
            f"MCP pre-flight failed: {result.message}\n"
            f"Issues: {result.details.get('issues', [])}"
        )

    def test_tool_extraction_from_file(self, tmp_path):
        """Tool functions are correctly extracted from Python files."""
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

        assert "governance_test_tool" in tool_names
        assert "governance_another_tool" in tool_names
        assert "regular_function" not in tool_names

    def test_duplicate_detection(self, tmp_path):
        """Duplicate tools are detected across files."""
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

        assert "governance_duplicate_tool" in duplicates
        assert len(duplicates["governance_duplicate_tool"]) == 2


@pytest.mark.skipif(not HOOKS_AVAILABLE, reason="Hooks modules not available")
class TestMCPPreflightIntegration:
    """Integration tests for MCP pre-flight with real codebase."""

    def test_all_mcp_modules_exist(self):
        """All configured MCP modules exist."""
        checker = MCPPreflightChecker(PROJECT_ROOT)

        missing = []
        for module_path in checker.MCP_MODULES:
            full_path = PROJECT_ROOT / module_path
            if not full_path.exists():
                missing.append(module_path)

        # Allow some modules to not exist (claude_mem may be optional)
        critical_missing = [m for m in missing if "governance" in m]
        assert len(critical_missing) == 0, f"Missing critical MCP modules: {critical_missing}"

    def test_tool_count_reasonable(self):
        """Tool count is within reasonable range."""
        checker = MCPPreflightChecker(PROJECT_ROOT)
        tool_count = checker._count_tools_scanned()

        # Should have tools but not an unreasonable number
        assert tool_count > 0, "No tools found - MCP modules may not be configured"
        assert tool_count < 500, f"Too many tools ({tool_count}) - may indicate parsing issue"
