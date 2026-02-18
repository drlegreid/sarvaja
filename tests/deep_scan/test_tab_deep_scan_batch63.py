"""
Batch 63 — Deep Scan: MCP agents/proposals TypeQL escaping + null safety.

Fixes verified:
- BUG-AGENT-ACTIVITY-ESCAPE-001: agent_id escaped in agent_activity MCP tool
- BUG-PROPOSAL-ESCAPE-001: status escaped in proposals_list TypeQL query
- BUG-PROPOSAL-KEYERROR-001: vote_weight uses .get() instead of direct access
- BUG-AGENT-NULL-001: Null guard on current.name/agent_type in update_agent_trust
- BUG-AGENT-ESCAPE-001: agent_id escaped in all TypeDB agent queries
"""
import inspect

import pytest


# ===========================================================================
# BUG-AGENT-ACTIVITY-ESCAPE-001: agent_id in MCP activity query
# ===========================================================================

class TestAgentActivityEscaping:
    """Verify agent_id escaped in agent_activity MCP tool."""

    def _get_source(self):
        from governance.mcp_tools.agents import register_agent_tools
        return inspect.getsource(register_agent_tools)

    def test_agent_id_escaped_in_activity(self):
        """agent_id must be escaped before TypeQL interpolation."""
        src = self._get_source()
        # Find the activity section — escape is ~16 lines deep
        activity_idx = src.find("def agent_activity")
        activity_section = src[activity_idx:activity_idx + 1200]
        assert "agent_id_escaped" in activity_section


# ===========================================================================
# BUG-PROPOSAL-ESCAPE-001: status in proposals_list
# ===========================================================================

class TestProposalListEscaping:
    """Verify status escaped in proposals_list TypeQL query."""

    def _get_source(self):
        from governance.mcp_tools.proposals import register_proposal_tools
        return inspect.getsource(register_proposal_tools)

    def test_status_escaped_in_proposals_list(self):
        """status must be escaped before TypeQL interpolation."""
        src = self._get_source()
        list_idx = src.find("def proposals_list")
        list_section = src[list_idx:list_idx + 1500]
        assert "replace" in list_section, "status must be escaped"

    def test_no_raw_status_in_query(self):
        """Must not have unescaped {status} in TypeQL query."""
        src = self._get_source()
        list_idx = src.find("def proposals_list")
        list_section = src[list_idx:list_idx + 1500]
        lines = list_section.split('\n')
        for line in lines:
            if 'proposal-status' in line and '{status}' in line:
                assert 'replace' in line, f"Unescaped: {line.strip()}"


# ===========================================================================
# BUG-PROPOSAL-KEYERROR-001: vote_weight safe access
# ===========================================================================

class TestProposalVoteWeightSafety:
    """Verify vote_weight uses .get() instead of direct key access."""

    def _get_source(self):
        from governance.mcp_tools.proposals import register_proposal_tools
        return inspect.getsource(register_proposal_tools)

    def test_vote_weight_uses_get(self):
        """vote_weight must use .get() with default."""
        src = self._get_source()
        vote_idx = src.find("def proposal_vote")
        vote_section = src[vote_idx:vote_idx + 2500]
        assert '.get("vote_weight"' in vote_section or ".get('vote_weight'" in vote_section

    def test_no_direct_key_access(self):
        """Must not have trust_data["vote_weight"] (direct access)."""
        src = self._get_source()
        assert 'trust_data["vote_weight"]' not in src


# ===========================================================================
# BUG-AGENT-NULL-001 + BUG-AGENT-ESCAPE-001: TypeDB agents escaping
# ===========================================================================

class TestAgentTypeDBEscaping:
    """Verify all agent TypeDB queries have proper escaping."""

    def _get_agents_source(self):
        from governance.typedb.queries.agents import AgentQueries
        return inspect.getsource(AgentQueries)

    def test_update_agent_trust_null_guard(self):
        """update_agent_trust must null-guard name/type before replace."""
        from governance.typedb.queries.agents import AgentQueries
        src = inspect.getsource(AgentQueries.update_agent_trust)
        assert '(current.name or "")' in src
        assert '(current.agent_type or "")' in src

    def test_insert_agent_escapes_agent_id(self):
        """insert_agent must escape agent_id."""
        from governance.typedb.queries.agents import AgentQueries
        src = inspect.getsource(AgentQueries.insert_agent)
        assert "agent_id_escaped" in src

    def test_delete_agent_escapes_agent_id(self):
        """delete_agent must escape agent_id."""
        from governance.typedb.queries.agents import AgentQueries
        src = inspect.getsource(AgentQueries.delete_agent)
        assert "agent_id_escaped" in src

    def test_update_agent_trust_escapes_agent_id(self):
        """update_agent_trust must escape agent_id."""
        from governance.typedb.queries.agents import AgentQueries
        src = inspect.getsource(AgentQueries.update_agent_trust)
        assert "agent_id_escaped" in src

    def test_all_write_methods_escape_agent_id(self):
        """All write methods must escape agent_id."""
        from governance.typedb.queries.agents import AgentQueries
        for method_name in ["insert_agent", "delete_agent", "update_agent_trust"]:
            src = inspect.getsource(getattr(AgentQueries, method_name))
            assert "agent_id_escaped" in src, f"{method_name} must escape agent_id"

    def test_total_escape_count(self):
        """AgentQueries must have comprehensive escaping."""
        src = self._get_agents_source()
        escape_count = src.count('.replace(')
        assert escape_count >= 7, f"Expected 7+ escape calls, found {escape_count}"


# ===========================================================================
# Cross-layer: MCP TypeQL escaping consistency
# ===========================================================================

class TestMCPTypeQLEscapingAudit:
    """Verify TypeQL escaping across all MCP tool files."""

    def test_trust_tool_escapes_agent_id(self):
        """Trust MCP tool must escape agent_id (fixed in batch 62)."""
        from governance.mcp_tools.trust import register_trust_tools
        src = inspect.getsource(register_trust_tools)
        assert "agent_id_escaped" in src

    def test_agents_tool_escapes_agent_id(self):
        """Agents MCP tool must escape agent_id in activity query."""
        from governance.mcp_tools.agents import register_agent_tools
        src = inspect.getsource(register_agent_tools)
        assert "agent_id_escaped" in src

    def test_proposals_tool_escapes_status(self):
        """Proposals MCP tool must escape status filter."""
        from governance.mcp_tools.proposals import register_proposal_tools
        src = inspect.getsource(register_proposal_tools)
        list_idx = src.find("proposals_list")
        assert "replace" in src[list_idx:list_idx + 1500]
