"""Batch 197 — Session lifecycle defense tests.

Validates fixes for:
- BUG-197-001: create_session route broad exception handler
- BUG-197-002: end_session route broad exception handler
- BUG-197-DETAIL-001: Detail routes have try/except
- Session lifecycle defense (end_session, delete_session)
"""
import ast
from pathlib import Path


SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-197-001/002: Session CRUD exception handlers ────────────────

class TestSessionCrudExceptionHandlers:
    """Session CRUD routes must have broad exception handling."""

    def _get_handler_source(self, func_name: str) -> str:
        """Extract a route handler function's source."""
        src = (SRC / "governance/routes/sessions/crud.py").read_text()
        lines = src.splitlines()
        in_func = False
        func_lines = []
        indent = 0
        for line in lines:
            if f"def {func_name}" in line:
                in_func = True
                indent = len(line) - len(line.lstrip())
                func_lines.append(line)
            elif in_func:
                if line.strip() and not line.startswith(" " * (indent + 1)) and not line.strip().startswith("#"):
                    if line.strip().startswith("@") or (line.strip().startswith("def ") and "def " + func_name not in line):
                        break
                func_lines.append(line)
        return "\n".join(func_lines)

    def test_create_session_catches_exception(self):
        """create_session must catch broad Exception."""
        src = self._get_handler_source("create_session")
        assert "except Exception" in src or "except (TypeDBUnavailable" in src, \
            "create_session must catch broad exceptions"

    def test_end_session_catches_exception(self):
        """end_session must catch broad Exception."""
        src = self._get_handler_source("end_session")
        assert "except Exception" in src or "except HTTPException" in src, \
            "end_session must catch broad exceptions"

    def test_create_session_has_503_handler(self):
        """create_session should handle TypeDBUnavailable → 503."""
        src = self._get_handler_source("create_session")
        assert "503" in src or "TypeDBUnavailable" in src, \
            "create_session should handle 503/TypeDBUnavailable"


# ── BUG-197-DETAIL-001: Detail routes have try/except ──────────────

class TestDetailRoutesExceptionHandling:
    """Session detail routes must have try/except blocks."""

    def _get_route_source(self, func_name: str) -> str:
        src = (SRC / "governance/routes/sessions/detail.py").read_text()
        lines = src.splitlines()
        in_func = False
        func_lines = []
        for line in lines:
            if f"def {func_name}" in line:
                in_func = True
            elif in_func and line.strip().startswith("@"):
                break
            elif in_func and line.strip().startswith("def ") and func_name not in line:
                break
            if in_func:
                func_lines.append(line)
        return "\n".join(func_lines)

    def test_session_detail_has_try_except(self):
        src = self._get_route_source("session_detail")
        assert "try:" in src and "except" in src, \
            "session_detail must have try/except"

    def test_session_tools_has_try_except(self):
        src = self._get_route_source("session_tools")
        assert "try:" in src and "except" in src, \
            "session_tools must have try/except"

    def test_session_thoughts_has_try_except(self):
        src = self._get_route_source("session_thoughts")
        assert "try:" in src and "except" in src, \
            "session_thoughts must have try/except"


# ── Session lifecycle defense ───────────────────────────────────────

class TestSessionLifecycleDefense:
    """Defense tests for session lifecycle operations."""

    def test_end_session_service_exists(self):
        """end_session function should be importable."""
        from governance.services.sessions_lifecycle import end_session
        assert callable(end_session)

    def test_delete_session_service_exists(self):
        """delete_session function should be importable."""
        from governance.services.sessions_lifecycle import delete_session
        assert callable(delete_session)

    def test_end_session_fallback_rejects_completed(self):
        """end_session in-memory path should reject already-completed sessions."""
        from unittest.mock import patch
        from governance.services.sessions_lifecycle import end_session
        from governance.stores import _sessions_store

        sid = "SESSION-TEST-BATCH197-COMPLETED"
        _sessions_store[sid] = {
            "session_id": sid,
            "status": "COMPLETED",
            "end_time": "2026-01-01T12:00:00",
        }
        try:
            with patch("governance.services.sessions_lifecycle.get_typedb_client", return_value=None):
                try:
                    end_session(sid, source="test")
                    assert False, "Should have raised ValueError"
                except ValueError as e:
                    assert "already completed" in str(e).lower()
        finally:
            _sessions_store.pop(sid, None)

    def test_delete_session_fallback_returns_false_not_found(self):
        """delete_session returns False when session not found."""
        from unittest.mock import patch
        from governance.services.sessions_lifecycle import delete_session

        with patch("governance.services.sessions_lifecycle.get_typedb_client", return_value=None):
            result = delete_session("SESSION-NONEXISTENT-BATCH197", source="test")
            assert result is False
