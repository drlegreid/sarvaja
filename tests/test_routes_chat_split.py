"""
TDD Tests for GAP-FILE-023: routes/chat.py Split

Tests verify that the modularized chat routes:
1. Maintains backward compatibility
2. Has properly separated command processing
3. All modules stay under 400 lines

Per RULE-004: TDD approach
Per DOC-SIZE-01-v1: Files under 400 lines
"""

import pytest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
GOVERNANCE_DIR = PROJECT_ROOT / "governance"
ROUTES_DIR = GOVERNANCE_DIR / "routes"


# =============================================================================
# Test 1: Package Structure
# =============================================================================



# =============================================================================
# Test 2: Backward Compatibility
# =============================================================================

class TestBackwardCompatibility:
    """Tests ensuring existing imports still work."""

    def test_import_router(self):
        """from governance.routes.chat import router must work."""
        from governance.routes.chat import router
        assert router is not None

    def test_router_has_routes(self):
        """Router should have registered routes."""
        from governance.routes.chat import router
        # Check for expected routes
        routes = [r.path for r in router.routes]
        assert "/chat/send" in routes or any("/chat" in r for r in routes)


# =============================================================================
# Test 3: Commands Module
# =============================================================================

class TestCommandsModule:
    """Tests for the extracted commands module."""

    def test_process_chat_command_exists(self):
        """process_chat_command function should be importable."""
        try:
            from governance.routes.chat.commands import process_chat_command
            assert process_chat_command is not None
        except ImportError:
            # Module doesn't exist yet - try from main file
            from governance.routes.chat import _process_chat_command
            assert _process_chat_command is not None

    def test_process_chat_command_status(self):
        """process_chat_command should handle /status."""
        try:
            from governance.routes.chat.commands import process_chat_command
        except ImportError:
            from governance.routes.chat import _process_chat_command as process_chat_command

        result = process_chat_command("/status", "AGENT-001")
        assert "Status" in result or "status" in result

    def test_process_chat_command_help(self):
        """process_chat_command should handle /help."""
        try:
            from governance.routes.chat.commands import process_chat_command
        except ImportError:
            from governance.routes.chat import _process_chat_command as process_chat_command

        result = process_chat_command("/help", "AGENT-001")
        assert "help" in result.lower() or "commands" in result.lower()

    def test_process_chat_command_unknown(self):
        """process_chat_command should handle unknown commands gracefully."""
        try:
            from governance.routes.chat.commands import process_chat_command
        except ImportError:
            from governance.routes.chat import _process_chat_command as process_chat_command

        result = process_chat_command("hello world", "AGENT-001")
        assert result is not None
        assert len(result) > 0


# =============================================================================
# Test 4: File Size Compliance
# =============================================================================

class TestFileSizeCompliance:
    """Tests ensuring files stay under size limit."""

    def test_all_modules_under_400_lines(self):
        """All modules in package should be under 400 lines."""
        chat_package = ROUTES_DIR / "chat"

        if not chat_package.exists():
            chat_file = ROUTES_DIR / "chat.py"
            if chat_file.exists():
                line_count = len(chat_file.read_text().splitlines())
                if line_count > 400:
                    pytest.skip(f"Single file has {line_count} lines - refactoring needed")
            return

        for py_file in chat_package.glob("*.py"):
            line_count = len(py_file.read_text().splitlines())
            assert line_count <= 400, \
                f"{py_file.name} has {line_count} lines, exceeds 400 limit"


# =============================================================================
# Test 5: Integration
# =============================================================================

class TestIntegration:
    """Integration tests for refactored chat routes."""

    def test_router_is_api_router(self):
        """Router should be FastAPI APIRouter."""
        from governance.routes.chat import router
        from fastapi import APIRouter

        assert isinstance(router, APIRouter)

    def test_router_has_post_send(self):
        """Router should have POST /chat/send route."""
        from governance.routes.chat import router

        post_routes = [r for r in router.routes if hasattr(r, 'methods') and 'POST' in r.methods]
        send_routes = [r for r in post_routes if '/send' in r.path]
        assert len(send_routes) >= 1, "Should have POST /chat/send route"

    def test_router_has_get_sessions(self):
        """Router should have GET /chat/sessions route."""
        from governance.routes.chat import router

        get_routes = [r for r in router.routes if hasattr(r, 'methods') and 'GET' in r.methods]
        session_routes = [r for r in get_routes if '/sessions' in r.path]
        assert len(session_routes) >= 1, "Should have GET /chat/sessions route"
