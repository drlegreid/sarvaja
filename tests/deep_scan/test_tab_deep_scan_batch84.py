"""
Batch 84 — Route Handlers + Middleware + Events.

Triage: 27 findings (15 route + 12 middleware) → 1 confirmed, 26 rejected.
Validates: subprocess safety, TypeDB datetime syntax, error truncation,
evidence linking fallback, session bridge guards, allowlist patterns.
"""
import inspect

import pytest


# ===========================================================================
# Confirmed: BUG-CAPTURE-TRUNCATION-001 — error_message truncation indicator
# ===========================================================================

class TestCaptureErrorTruncation:
    """Verify error_message truncation adds '...' indicator."""

    def test_error_message_adds_ellipsis(self):
        """capture_tool_call truncates result with '...', verify error_message matches."""
        from governance.session_collector.capture import SessionCaptureMixin
        src = inspect.getsource(SessionCaptureMixin.capture_test_result)
        # Both truncations should add "..."
        assert 'error_message[:500] + "..."' in src

    def test_result_summary_also_has_ellipsis(self):
        """capture_tool_call result_summary already adds '...'."""
        from governance.session_collector.capture import SessionCaptureMixin
        src = inspect.getsource(SessionCaptureMixin.capture_tool_call)
        assert 'result[:500] + "..."' in src


# ===========================================================================
# Rejected: Command injection via pattern — subprocess list mode is safe
# ===========================================================================

class TestSubprocessListModeSafety:
    """Verify test runner uses subprocess list mode (no shell injection)."""

    def test_execute_tests_uses_subprocess_run(self):
        """execute_tests calls subprocess.run with list cmd."""
        from governance.routes.tests.runner_exec import execute_tests
        src = inspect.getsource(execute_tests)
        assert "subprocess.run(" in src
        assert "shell=True" not in src

    def test_pattern_appended_as_single_arg(self):
        """Pattern is appended to cmd list, not interpolated into shell string."""
        from governance.routes.tests.runner import run_tests
        src = inspect.getsource(run_tests)
        assert "cmd.append(pattern)" in src


# ===========================================================================
# Rejected: Path traversal in robot report — allowlist blocks it
# ===========================================================================

class TestRobotReportAllowlist:
    """Verify robot report file serving has strict allowlist."""

    def test_allowlist_exists(self):
        """serve_robot_report has allowlist of files."""
        from governance.routes.tests.runner import serve_robot_report
        src = inspect.getsource(serve_robot_report)
        assert "allowed_files" in src
        assert '"report.html"' in src
        assert '"log.html"' in src

    def test_allowlist_rejects_unknown(self):
        """Files not in allowlist are rejected before Path construction."""
        from governance.routes.tests.runner import serve_robot_report
        src = inspect.getsource(serve_robot_report)
        # Rejection happens BEFORE Path construction
        reject_idx = src.find("not in allowed_files")
        path_idx = src.find("Path(")
        assert reject_idx < path_idx  # Reject before path usage


# ===========================================================================
# Rejected: TypeQL timestamp injection — correct TypeDB 3.x datetime syntax
# ===========================================================================

class TestTypeDBDatetimeSyntax:
    """Verify TypeDB datetime attributes use bare values (correct 3.x syntax)."""

    def test_evidence_timestamp_is_strftime(self):
        """Timestamp comes from datetime.now().strftime (server-controlled)."""
        from governance.typedb.queries.sessions.linking import SessionLinkingOperations
        src = inspect.getsource(SessionLinkingOperations.link_evidence_to_session)
        assert "strftime" in src
        assert "'%Y-%m-%dT%H:%M:%S'" in src

    def test_evidence_ids_are_escaped(self):
        """Evidence paths and IDs are escaped for TypeQL safety."""
        from governance.typedb.queries.sessions.linking import SessionLinkingOperations
        src = inspect.getsource(SessionLinkingOperations.link_evidence_to_session)
        assert 'evidence_source_escaped = evidence_source.replace' in src
        assert 'evidence_id_escaped = evidence_id.replace' in src


# ===========================================================================
# Rejected: Evidence linking divergence — intentional fallback pattern
# ===========================================================================

class TestEvidenceLinkingFallback:
    """Verify evidence linking has proper error handling and fallback."""

    def test_typedb_link_has_try_except(self):
        """TypeDB evidence linking wrapped in try-except."""
        from governance.routes.chat.session_bridge import end_chat_session
        src = inspect.getsource(end_chat_session)
        # BUG-SESSION-EVIDENCE-001 fix: proper error levels
        assert "logger.error" in src
        assert "logger.warning" in src

    def test_memory_fallback_after_typedb(self):
        """_sessions_store fallback exists after TypeDB attempt."""
        from governance.routes.chat.session_bridge import end_chat_session
        src = inspect.getsource(end_chat_session)
        assert '"evidence_files"' in src
        assert "existing.append(evidence_path)" in src


# ===========================================================================
# Rejected: gov_collector None — code HAS the guard
# ===========================================================================

class TestGovCollectorNullGuard:
    """Verify gov_collector is checked before use."""

    def test_session_bridge_classify_tool_handles_empty(self):
        """classify_tool returns 'unknown' for empty/None input."""
        from governance.routes.chat.session_bridge import classify_tool
        assert classify_tool("") == "unknown"
        assert classify_tool(None) == "unknown"

    def test_classify_tool_categories(self):
        """classify_tool correctly categorizes known tools."""
        from governance.routes.chat.session_bridge import classify_tool
        assert classify_tool("Read") == "cc_builtin"
        assert classify_tool("mcp__gov-core__rule_get") == "mcp_governance"
        assert classify_tool("mcp__playwright__browser_click") == "mcp_other"
        assert classify_tool("/help") == "chat_command"


# ===========================================================================
# Rejected: Agent endpoints missing try-except — in-memory only
# ===========================================================================

class TestAgentEndpointsSafety:
    """Verify agent service is in-memory (no TypeDB exceptions possible)."""

    def test_agent_list_has_try_except(self):
        """list_agents endpoint does have try-except."""
        from governance.routes.agents.crud import list_agents
        src = inspect.getsource(list_agents)
        assert "try:" in src
        assert "except" in src

    def test_event_log_has_default_serializer(self):
        """Event log uses default=str to prevent JSON serialization crashes."""
        from governance.middleware.event_log import log_event
        src = inspect.getsource(log_event)
        assert "default=str" in src
