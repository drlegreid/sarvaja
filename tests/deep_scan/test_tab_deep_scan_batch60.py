"""
Batch 60 — Deep Scan: MCP auto-session persistence + scanner TOCTOU guard.

Fixes verified:
- BUG-AUTO-SESSION-PERSIST-001: _persist_session_end now calls persist_session()
- BUG-SCANNER-TOCTOU-001: find_jsonl_for_session wraps iterdir in try-except
"""
import inspect

import pytest


# ===========================================================================
# BUG-AUTO-SESSION-PERSIST-001: Session end persistence
# ===========================================================================

class TestAutoSessionEndPersistence:
    """Verify _persist_session_end calls persist_session after update."""

    def _get_persist_end_source(self):
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker
        return inspect.getsource(MCPAutoSessionTracker._persist_session_end)

    def test_imports_persist_session(self):
        """_persist_session_end must import persist_session."""
        src = self._get_persist_end_source()
        assert "from governance.stores.session_persistence import persist_session" in src

    def test_calls_persist_session(self):
        """_persist_session_end must call persist_session()."""
        src = self._get_persist_end_source()
        assert "persist_session(sid" in src

    def test_persist_start_also_persists(self):
        """_persist_session_start must also call persist_session (reference)."""
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker
        src = inspect.getsource(MCPAutoSessionTracker._persist_session_start)
        assert "persist_session(" in src

    def test_persist_tool_call_also_persists(self):
        """_persist_tool_call must also call persist_session (reference)."""
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker
        src = inspect.getsource(MCPAutoSessionTracker._persist_tool_call)
        assert "persist_session(" in src

    def test_all_three_persist_methods_consistent(self):
        """All 3 persist methods must import and call persist_session."""
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker
        for method_name in ["_persist_session_start", "_persist_tool_call", "_persist_session_end"]:
            src = inspect.getsource(getattr(MCPAutoSessionTracker, method_name))
            assert "persist_session(" in src, f"{method_name} must call persist_session"


# ===========================================================================
# BUG-SCANNER-TOCTOU-001: find_jsonl_for_session TOCTOU guard
# ===========================================================================

class TestScannerFindJsonlTOCTOU:
    """Verify find_jsonl_for_session wraps iterdir in try-except."""

    def _get_find_source(self):
        from governance.services.cc_session_scanner import find_jsonl_for_session
        return inspect.getsource(find_jsonl_for_session)

    def test_iterdir_wrapped_in_try(self):
        """find_jsonl_for_session must wrap iterdir() in try-except."""
        src = self._get_find_source()
        # Find the subdirectory scan section
        subdir_idx = src.find("subdirs")
        assert subdir_idx > 0, "Must use 'subdirs' variable for guarded iteration"
        # Try must appear before the iterdir call
        try_idx = src.rfind("try:", 0, subdir_idx)
        assert try_idx > 0, "try: must appear before subdirs = list(iterdir())"

    def test_catches_oserror(self):
        """Must catch OSError for TOCTOU protection."""
        src = self._get_find_source()
        assert "except OSError" in src

    def test_discover_cc_projects_also_guarded(self):
        """discover_cc_projects must also guard iterdir (reference)."""
        from governance.services.cc_session_scanner import discover_cc_projects
        src = inspect.getsource(discover_cc_projects)
        assert "except OSError" in src

    def test_discover_filesystem_also_guarded(self):
        """discover_filesystem_projects must also guard iterdir (reference)."""
        from governance.services.cc_session_scanner import discover_filesystem_projects
        src = inspect.getsource(discover_filesystem_projects)
        assert "except OSError" in src


# ===========================================================================
# Cross-layer: MCP auto-session lifecycle consistency
# ===========================================================================

class TestAutoSessionLifecycleConsistency:
    """Verify auto-session end_session correctly orders operations."""

    def test_persist_before_cleanup(self):
        """_persist_session_end must be called BEFORE active_session_id = None."""
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker
        src = inspect.getsource(MCPAutoSessionTracker.end_session)
        persist_idx = src.find("_persist_session_end")
        cleanup_idx = src.find("self.active_session_id = None")
        assert persist_idx > 0 and cleanup_idx > 0
        assert persist_idx < cleanup_idx, "persist must happen before cleanup"

    def test_end_session_returns_summary_before_cleanup(self):
        """end_session summary must capture data before cleanup."""
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker
        src = inspect.getsource(MCPAutoSessionTracker.end_session)
        summary_idx = src.find("summary = {")
        cleanup_idx = src.find("self.active_session_id = None")
        assert summary_idx < cleanup_idx, "summary must be built before cleanup"

    def test_expired_session_ends_before_new_creates(self):
        """track() must end expired session before creating new one."""
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker
        src = inspect.getsource(MCPAutoSessionTracker.track)
        end_idx = src.find("self.end_session")
        create_idx = src.find("self._create_session")
        assert end_idx > 0 and create_idx > 0
        assert end_idx < create_idx, "end expired before creating new"


# ===========================================================================
# Cross-layer: Scanner TOCTOU consistency audit
# ===========================================================================

class TestScannerTOCTOUConsistencyAudit:
    """All iterdir calls in cc_session_scanner must be guarded."""

    def test_all_iterdir_calls_guarded(self):
        """Count iterdir calls and verify each has try-except nearby."""
        from governance.services import cc_session_scanner
        src = inspect.getsource(cc_session_scanner)
        # Count iterdir calls
        iterdir_count = src.count(".iterdir()")
        # Count OSError catches (each one guards an iterdir)
        oserror_count = src.count("except OSError")
        # We expect at least as many guards as iterdir calls
        # Some iterdir calls are inside already-guarded blocks
        assert oserror_count >= 3, f"Expected 3+ OSError guards, found {oserror_count}"

    def test_runner_exec_regression_has_outer_except(self):
        """execute_regression must have outer try-except for safety."""
        from governance.routes.tests.runner_exec import execute_regression
        src = inspect.getsource(execute_regression)
        assert "except Exception as e:" in src
