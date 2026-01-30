"""
Tests for merging trust dashboard into agents tab.

Per PLAN-UI-OVERHAUL-001 Task 5.4: Merge Trust+Agents.
TDD: Tests written before implementation.
"""

import pytest
import inspect


class TestTrustAgentsMerge:
    """Verify trust info is integrated into agents list view."""

    def test_agents_list_has_governance_stats(self):
        """Agents list should include governance stats summary."""
        from agent.governance_ui.views.agents import list as agents_list
        source = inspect.getsource(agents_list)
        assert 'trust' in source.lower() and 'avg' in source.lower(), (
            "Agents list should show average trust stats"
        )

    def test_agents_list_shows_proposals_count(self):
        """Agents list should show pending proposals count."""
        from agent.governance_ui.views.agents import list as agents_list
        source = inspect.getsource(agents_list)
        assert 'proposal' in source.lower(), (
            "Agents list should show proposals metric"
        )
