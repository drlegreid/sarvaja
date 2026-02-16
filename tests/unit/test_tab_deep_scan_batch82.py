"""
Batch 82 — MCP Server Implementations + Context Recovery.

Triage: 9 findings → 0 confirmed, ALL rejected.
Validates: null-safe iteration, vote_weight handling, TypeQL escaping,
resource cleanup, persist patterns, exception wrappers, trust fallbacks.
"""
import inspect

import pytest


# ===========================================================================
# Rejected: BUG-MCP-001 — Null-safe iteration (already uses `or []`)
# ===========================================================================

class TestProposalsNullSafeIteration:
    """Verify proposals_list and proposals_escalated use (results or [])."""

    def test_proposals_list_null_safe(self):
        """proposals_list iterates with (results or [])."""
        from governance.mcp_tools.proposals import register_proposal_tools
        src = inspect.getsource(register_proposal_tools)
        assert "(results or [])" in src

    def test_proposals_escalated_null_safe(self):
        """proposals_escalated iterates with (results or [])."""
        from governance.mcp_tools.proposals import register_proposal_tools
        src = inspect.getsource(register_proposal_tools)
        # Both occurrences
        assert src.count("(results or [])") >= 2


# ===========================================================================
# Rejected: BUG-PROPOSAL-KEYERROR-001 — vote_weight uses .get()
# ===========================================================================

class TestVoteWeightHandling:
    """Verify vote_weight uses .get() with default."""

    def test_vote_weight_uses_get(self):
        """proposal_vote uses .get() for vote_weight."""
        from governance.mcp_tools.proposals import register_proposal_tools
        src = inspect.getsource(register_proposal_tools)
        assert '.get("vote_weight"' in src

    def test_vote_weight_has_default(self):
        """vote_weight defaults to 0.5 for incomplete trust responses."""
        from governance.mcp_tools.proposals import register_proposal_tools
        src = inspect.getsource(register_proposal_tools)
        assert 'vote_weight", 0.5)' in src


# ===========================================================================
# Rejected: BUG-TRUST-ESCAPE-001 — Consistent escaping pattern
# ===========================================================================

class TestTrustToolEscaping:
    """Verify trust tool escapes agent_id before TypeQL."""

    def test_trust_tool_escapes_agent_id(self):
        """governance_get_trust_score escapes agent_id."""
        from governance.mcp_tools.trust import register_trust_tools
        src = inspect.getsource(register_trust_tools)
        assert 'replace(' in src
        assert 'agent_id_escaped' in src


# ===========================================================================
# Rejected: BUG-LINK-LEAK-001 — All linking tools use finally: close()
# ===========================================================================

class TestTaskLinkingResourceCleanup:
    """Verify all task linking tools properly close TypeDB client."""

    def test_all_link_tools_have_finally_close(self):
        """Every linking function closes client in finally block."""
        from governance.mcp_tools.tasks_linking import register_task_linking_tools
        src = inspect.getsource(register_task_linking_tools)
        # Count finally blocks (one per tool function)
        finally_count = src.count("finally:")
        close_count = src.count("client.close()")
        assert finally_count >= 5  # At least 5 linking tools
        assert close_count >= finally_count  # Each finally has a close


# ===========================================================================
# Rejected: BUG-AUTO-SESSION-PERSIST-001 — persist_session already called
# ===========================================================================

class TestAutoSessionPersistence:
    """Verify _persist_session_end calls persist_session."""

    def test_persist_session_end_calls_persist(self):
        """_persist_session_end persists after updating dict."""
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker
        src = inspect.getsource(MCPAutoSessionTracker._persist_session_end)
        assert "persist_session" in src

    def test_all_persist_methods_call_persist_session(self):
        """All 3 persist methods call persist_session()."""
        from governance.mcp_tools.auto_session import MCPAutoSessionTracker
        for method_name in ["_persist_session_start", "_persist_tool_call", "_persist_session_end"]:
            method = getattr(MCPAutoSessionTracker, method_name)
            src = inspect.getsource(method)
            assert "persist_session" in src, f"{method_name} missing persist_session call"


# ===========================================================================
# Rejected: BUG-MCP-TASK-001 — session_task already wrapped in try-except
# ===========================================================================

class TestSessionTaskExceptionWrapper:
    """Verify session_task has try-except like session_decision."""

    def test_session_task_has_try_except(self):
        """session_task is wrapped in try-except."""
        from governance.mcp_tools.sessions_core import register_session_core_tools
        src = inspect.getsource(register_session_core_tools)
        # Find the session_task function body
        task_start = src.find("def session_task(")
        task_end = src.find("def session_end(")
        task_src = src[task_start:task_end]
        assert "try:" in task_src
        assert "except Exception" in task_src

    def test_session_decision_also_wrapped(self):
        """session_decision has matching try-except pattern."""
        from governance.mcp_tools.sessions_core import register_session_core_tools
        src = inspect.getsource(register_session_core_tools)
        decision_start = src.find("def session_decision(")
        decision_end = src.find("def session_task(")
        decision_src = src[decision_start:decision_end]
        assert "try:" in decision_src
        assert "except Exception" in decision_src
