"""Batch 429 — sessions controller response.text leak, tool_calls XSS,
cc_session_ingestion bare except, cc_session_scanner bare except,
decisions debug→warning upgrade tests.

Validates fixes for:
- BUG-426-SES-001: sessions controller response.text leak fix
- BUG-427-XSS-001: tool_calls.py mustache→v_text for tool_name
- BUG-428-DEC-001: decisions.py debug→warning + exc_info
- BUG-429-ING-001: cc_session_ingestion.py bare except logging
- BUG-429-SCN-001: cc_session_scanner.py bare except OSError logging
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


def _check_exc_info(src, fragment):
    """Find logger line containing fragment, verify exc_info=True."""
    idx = src.index(fragment)
    block = src[idx:idx + 300]
    assert "exc_info=True" in block, f"Missing exc_info=True near: {fragment}"


def _check_warning_level(src, fragment):
    """Verify line containing fragment uses logger.warning (not debug)."""
    idx = src.index(fragment)
    line_start = src.rindex("\n", 0, idx) + 1
    line_end = src.index("\n", idx)
    line = src[line_start:line_end]
    assert "logger.warning" in line, f"Expected logger.warning in: {line.strip()}"


# ── BUG-426-SES-001: sessions controller response.text leak ───────────

class TestSessionsControllerResponseLeak:
    def test_no_response_text_in_error_message(self):
        src = (SRC / "agent/governance_ui/controllers/sessions.py").read_text()
        # Find the save_session error handling section
        idx = src.index("API Error: {response.status_code}")
        block = src[idx:idx + 100]
        # Should NOT contain response.text
        assert "response.text" not in block, "response.text leak still present in error message"

    def test_bug_marker_present(self):
        src = (SRC / "agent/governance_ui/controllers/sessions.py").read_text()
        assert "BUG-426-SES-001" in src


# ── BUG-427-XSS-001: tool_calls.py mustache→v_text ────────────────────

class TestToolCallsXSSGuard:
    def test_tool_name_uses_v_text(self):
        src = (SRC / "agent/governance_ui/views/sessions/tool_calls.py").read_text()
        # Find the expansion panel title section with tool_name
        idx = src.index("font-weight-medium")
        # Go backwards to find the Span call
        block = src[max(0, idx - 200):idx + 50]
        assert 'v_text="call.tool_name"' in block, "tool_name should use v_text binding"

    def test_no_mustache_tool_name(self):
        src = (SRC / "agent/governance_ui/views/sessions/tool_calls.py").read_text()
        assert '{{ call.tool_name }}' not in src, "Raw mustache {{ call.tool_name }} still present"

    def test_bug_marker_present(self):
        src = (SRC / "agent/governance_ui/views/sessions/tool_calls.py").read_text()
        assert "BUG-427-XSS-001" in src


# ── BUG-428-DEC-001: decisions.py debug→warning + exc_info ────────────

class TestDecisionsLogUpgrade:
    def test_typedb_stats_warning_level(self):
        src = (SRC / "governance/mcp_tools/decisions.py").read_text()
        _check_warning_level(src, "Failed to get TypeDB statistics")

    def test_typedb_stats_exc_info(self):
        src = (SRC / "governance/mcp_tools/decisions.py").read_text()
        _check_exc_info(src, "Failed to get TypeDB statistics")

    def test_no_debug_for_typedb_stats(self):
        src = (SRC / "governance/mcp_tools/decisions.py").read_text()
        assert 'logger.debug(f"Failed to get TypeDB statistics' not in src

    def test_bug_marker_present(self):
        src = (SRC / "governance/mcp_tools/decisions.py").read_text()
        assert "BUG-428-DEC-001" in src


# ── BUG-429-ING-001: cc_session_ingestion.py bare except logging ──────

class TestIngestionBareExceptFix:
    def test_active_status_exc_info(self):
        src = (SRC / "governance/services/cc_session_ingestion.py").read_text()
        _check_exc_info(src, "Failed to determine session active status")

    def test_no_bare_except_without_logging(self):
        src = (SRC / "governance/services/cc_session_ingestion.py").read_text()
        # The old pattern was "except Exception:" with no logging
        # Now should have "except Exception as e:" with logger.warning
        idx = src.index("Failed to determine session active status")
        block = src[max(0, idx - 300):idx + 200]
        assert "except Exception as e:" in block, "Should capture exception variable"

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/cc_session_ingestion.py").read_text()
        assert "BUG-429-ING-001" in src


# ── BUG-429-SCN-001: cc_session_scanner.py bare except OSError logging ─

class TestScannerBareExceptFix:
    def test_directory_scan_exc_info(self):
        src = (SRC / "governance/services/cc_session_scanner.py").read_text()
        _check_exc_info(src, "Directory scan failed for")

    def test_captures_exception_variable(self):
        src = (SRC / "governance/services/cc_session_scanner.py").read_text()
        idx = src.index("Directory scan failed for")
        block = src[max(0, idx - 200):idx + 50]
        assert "except OSError as e:" in block, "Should capture OSError variable"

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/cc_session_scanner.py").read_text()
        assert "BUG-429-SCN-001" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch429Imports:
    def test_sessions_controller_importable(self):
        import agent.governance_ui.controllers.sessions
        assert agent.governance_ui.controllers.sessions is not None

    def test_tool_calls_importable(self):
        import agent.governance_ui.views.sessions.tool_calls
        assert agent.governance_ui.views.sessions.tool_calls is not None

    def test_decisions_importable(self):
        import governance.mcp_tools.decisions
        assert governance.mcp_tools.decisions is not None

    def test_cc_session_ingestion_importable(self):
        import governance.services.cc_session_ingestion
        assert governance.services.cc_session_ingestion is not None

    def test_cc_session_scanner_importable(self):
        import governance.services.cc_session_scanner
        assert governance.services.cc_session_scanner is not None
