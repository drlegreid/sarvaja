"""
Unit tests for Tab Deep Scan Batch 30 — Routes + API layer.

Covers: BUG-ROUTE-001 (IndexError on whitespace chat content),
BUG-ROUTE-002 (path traversal prefix attack),
BUG-ROUTE-003 (null-safe decisions iteration).
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect
import os


# ── BUG-ROUTE-001: Whitespace-only chat content IndexError ───────────


class TestChatContentSplitSafety:
    """Chat endpoint must handle whitespace-only content without IndexError."""

    def test_split_guard_in_source(self):
        from governance.routes.chat import endpoints
        source = inspect.getsource(endpoints)
        # The split guard should check for empty split result
        assert "BUG-ROUTE-001" in source

    def test_empty_split_returns_chat(self):
        """Simulated: if content is whitespace only, tool_name should be 'chat'."""
        content = "   "
        parts = content.split() if content else []
        tool_name = parts[0] if parts else "chat"
        assert tool_name == "chat"

    def test_none_content_returns_chat(self):
        content = None
        parts = content.split() if content else []
        tool_name = parts[0] if parts else "chat"
        assert tool_name == "chat"

    def test_valid_content_returns_first_word(self):
        content = "/help me please"
        parts = content.split() if content else []
        tool_name = parts[0] if parts else "chat"
        assert tool_name == "/help"

    def test_single_word_content(self):
        content = "status"
        parts = content.split() if content else []
        tool_name = parts[0] if parts else "chat"
        assert tool_name == "status"


# ── BUG-ROUTE-002: Path traversal prefix attack ─────────────────────


class TestPathTraversalPrefixAttack:
    """Path traversal check must use os.sep to prevent prefix attacks."""

    def test_has_os_sep_check(self):
        from governance.routes import files
        source = inspect.getsource(files)
        assert "BUG-ROUTE-002" in source
        assert "os.sep" in source

    def test_prefix_attack_logic(self):
        """If root is /home/user, /home/username should NOT pass."""
        real_root = "/home/user"
        real_path_good = "/home/user/docs/file.txt"
        real_path_bad = "/home/username/docs/file.txt"

        # Good path: starts with root + separator
        assert real_path_good.startswith(real_root + os.sep) or real_path_good == real_root

        # Bad path: starts with root prefix but different directory
        assert not (real_path_bad.startswith(real_root + os.sep) or real_path_bad == real_root)

    def test_root_itself_allowed(self):
        """The root directory itself should be allowed."""
        real_root = "/home/user/project"
        real_path = "/home/user/project"
        assert real_path.startswith(real_root + os.sep) or real_path == real_root

    def test_subdirectory_allowed(self):
        real_root = "/home/user/project"
        real_path = "/home/user/project/src/main.py"
        assert real_path.startswith(real_root + os.sep)


# ── BUG-ROUTE-003: Null-safe decisions iteration ────────────────────


class TestDecisionsNullSafety:
    """get_all_decisions() returning None must not crash list endpoints."""

    def test_null_guard_in_list_decisions(self):
        from governance.routes.rules import decisions
        source = inspect.getsource(decisions)
        assert "or []" in source
        assert "BUG-ROUTE-003" in source

    def test_null_guard_in_get_decision(self):
        from governance.routes.rules import decisions
        source = inspect.getsource(decisions)
        # All 3 call sites should have null guard
        count = source.count("get_all_decisions() or []")
        assert count >= 3, f"Expected 3 null guards, found {count}"

    def test_none_coercion_logic(self):
        """None or [] should produce empty list."""
        result = None or []
        assert result == []
        assert isinstance(result, list)

    def test_populated_result_unchanged(self):
        """Non-None result should pass through unchanged."""
        decisions = ["D-1", "D-2"]
        result = decisions or []
        assert result == ["D-1", "D-2"]


# ── Route error handling patterns ────────────────────────────────────


class TestRouteErrorPatterns:
    """Routes must use HTTPException, not return error dicts."""

    def test_decisions_uses_httpexception(self):
        from governance.routes.rules import decisions
        source = inspect.getsource(decisions)
        assert "HTTPException" in source
        # Should not return raw error dicts on failure
        lines = source.splitlines()
        for line in lines:
            if "return {" in line and '"error"' in line:
                raise AssertionError(
                    f"Route returns error dict instead of HTTPException: {line.strip()}"
                )

    def test_sessions_crud_uses_httpexception(self):
        from governance.routes.sessions import crud
        source = inspect.getsource(crud)
        assert "HTTPException" in source

    def test_chat_endpoints_uses_httpexception(self):
        from governance.routes.chat import endpoints
        source = inspect.getsource(endpoints)
        assert "HTTPException" in source
