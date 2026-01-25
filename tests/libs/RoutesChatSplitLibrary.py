"""
RF-004: Robot Framework Library for Routes Chat Split Tests.

Wraps tests/test_routes_chat_split.py for Robot Framework tests.
Per DOC-SIZE-01-v1: Files under 400 lines.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

ROUTES_DIR = PROJECT_ROOT / "governance" / "routes"


class RoutesChatSplitLibrary:
    """Robot Framework library for Routes Chat Split tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def chat_package_or_module_exists(self) -> Dict[str, Any]:
        """Check if chat routes exist as package or module."""
        chat_package = ROUTES_DIR / "chat"
        chat_file = ROUTES_DIR / "chat.py"
        return {
            "package_exists": chat_package.exists(),
            "file_exists": chat_file.exists(),
            "either_exists": chat_package.exists() or chat_file.exists()
        }

    def commands_module_exists(self) -> bool:
        """Check if commands module exists in chat package."""
        chat_package = ROUTES_DIR / "chat"
        commands_file = chat_package / "commands.py"
        return commands_file.exists() if chat_package.exists() else False

    def import_router(self) -> bool:
        """Try to import router from chat routes."""
        try:
            from governance.routes.chat import router
            return router is not None
        except ImportError:
            return False

    def router_has_routes(self) -> Dict[str, Any]:
        """Check router has registered routes."""
        try:
            from governance.routes.chat import router
            routes = [r.path for r in router.routes]
            has_chat = "/chat/send" in routes or any("/chat" in r for r in routes)
            return {"has_routes": has_chat, "routes": routes[:5]}
        except ImportError:
            return {"has_routes": False, "error": "Import failed"}

    def import_process_chat_command(self) -> bool:
        """Try to import process_chat_command."""
        try:
            from governance.routes.chat.commands import process_chat_command
            return process_chat_command is not None
        except ImportError:
            try:
                from governance.routes.chat import _process_chat_command
                return _process_chat_command is not None
            except ImportError:
                return False

    def _get_process_command(self):
        """Get the process_chat_command function."""
        try:
            from governance.routes.chat.commands import process_chat_command
            return process_chat_command
        except ImportError:
            from governance.routes.chat import _process_chat_command
            return _process_chat_command

    def test_command_status(self) -> Dict[str, Any]:
        """Test /status command."""
        try:
            func = self._get_process_command()
            result = func("/status", "AGENT-001")
            return {
                "result": result,
                "has_status": "Status" in result or "status" in result
            }
        except Exception as e:
            return {"error": str(e)}

    def test_command_help(self) -> Dict[str, Any]:
        """Test /help command."""
        try:
            func = self._get_process_command()
            result = func("/help", "AGENT-001")
            return {
                "result": result,
                "has_help": "help" in result.lower() or "commands" in result.lower()
            }
        except Exception as e:
            return {"error": str(e)}

    def test_command_unknown(self) -> Dict[str, Any]:
        """Test unknown command handling."""
        try:
            func = self._get_process_command()
            result = func("hello world", "AGENT-001")
            return {
                "result": result,
                "has_response": result is not None and len(result) > 0
            }
        except Exception as e:
            return {"error": str(e)}

    def check_modules_under_400_lines(self) -> Dict[str, Any]:
        """Check all modules in package are under 400 lines."""
        chat_package = ROUTES_DIR / "chat"
        results = {"all_under_limit": True, "files": {}}

        if not chat_package.exists():
            chat_file = ROUTES_DIR / "chat.py"
            if chat_file.exists():
                line_count = len(chat_file.read_text().splitlines())
                results["files"]["chat.py"] = line_count
                results["all_under_limit"] = line_count <= 400
            return results

        for py_file in chat_package.glob("*.py"):
            line_count = len(py_file.read_text().splitlines())
            results["files"][py_file.name] = line_count
            if line_count > 400:
                results["all_under_limit"] = False

        return results

    def router_is_api_router(self) -> bool:
        """Check router is FastAPI APIRouter."""
        try:
            from governance.routes.chat import router
            from fastapi import APIRouter
            return isinstance(router, APIRouter)
        except ImportError:
            return False

    def router_has_post_send(self) -> bool:
        """Check router has POST /chat/send route."""
        try:
            from governance.routes.chat import router
            post_routes = [r for r in router.routes if hasattr(r, 'methods') and 'POST' in r.methods]
            send_routes = [r for r in post_routes if '/send' in r.path]
            return len(send_routes) >= 1
        except ImportError:
            return False

    def router_has_get_sessions(self) -> bool:
        """Check router has GET /chat/sessions route."""
        try:
            from governance.routes.chat import router
            get_routes = [r for r in router.routes if hasattr(r, 'methods') and 'GET' in r.methods]
            session_routes = [r for r in get_routes if '/sessions' in r.path]
            return len(session_routes) >= 1
        except ImportError:
            return False
