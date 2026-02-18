"""Deep scan batch 186: UI views layer.

Batch 186 findings: 8 total, 4 confirmed fixes, 4 deferred.
- BUG-186-001: VIcon v_text instead of icon prop (icon never renders).
- BUG-186-002: Static key="idx" in tasks/execution.py (Vue diffing broken).
- BUG-186-003: Static key="idx" in agents/metrics.py (Vue diffing broken).
- BUG-186-004: Static key="idx" in session_transcript.py (Vue diffing broken).
"""
import pytest
from pathlib import Path


# ── VIcon prop defense ──────────────


class TestVIconPropDefense:
    """Verify VIcon uses icon prop, not v_text for dynamic icon names."""

    def test_metrics_icon_uses_icon_prop(self):
        """agents/metrics.py uses icon= for dynamic icon name."""
        root = Path(__file__).parent.parent.parent
        src = (root / "agent/governance_ui/views/agents/metrics.py").read_text()
        # Find the trust history icon section
        start = src.index("event.change > 0 ? 'mdi-arrow-up'")
        # Look backwards for the prop name
        before = src[max(0, start - 100):start]
        assert "icon=" in before or "icon=(" in before
        # Should NOT have v_text for this section
        assert "v_text=(" not in before


# ── Vue key binding defense ──────────────


class TestVueKeyBindingDefense:
    """Verify v_for loops use dynamic :key binding, not static key."""

    def test_execution_timeline_dynamic_key(self):
        """tasks/execution.py uses :key for timeline items."""
        root = Path(__file__).parent.parent.parent
        src = (root / "agent/governance_ui/views/tasks/execution.py").read_text()
        # Should have dynamic key binding
        assert '":key"' in src or "':key'" in src
        # Should NOT have static key="idx"
        lines = src.split("\n")
        for line in lines:
            stripped = line.strip()
            if stripped == 'key="idx",' or stripped == "key='idx',":
                pytest.fail(f"Static key='idx' found: {stripped}")

    def test_metrics_timeline_dynamic_key(self):
        """agents/metrics.py uses :key for trust history timeline."""
        root = Path(__file__).parent.parent.parent
        src = (root / "agent/governance_ui/views/agents/metrics.py").read_text()
        # Find VTimelineItem with trust_history
        start = src.index("v_for=\"(event, idx) in selected_agent.trust_history\"")
        section = src[start:start + 300]
        assert '":key"' in section or "':key'" in section

    def test_transcript_entries_dynamic_key(self):
        """session_transcript.py uses :key for entry loop."""
        root = Path(__file__).parent.parent.parent
        src = (root / "agent/governance_ui/views/sessions/session_transcript.py").read_text()
        # Find the v_for loop
        start = src.index("v_for=\"(entry, idx)")
        section = src[start:start + 300]
        assert '":key"' in section or "':key'" in section


# ── Session transcript structure defense ──────────────


class TestTranscriptStructureDefense:
    """Verify session transcript component structure."""

    def test_transcript_module_importable(self):
        """session_transcript module is importable."""
        from agent.governance_ui.views.sessions import session_transcript
        assert session_transcript is not None

    def test_build_transcript_card_exists(self):
        """build_session_transcript_card function exists."""
        from agent.governance_ui.views.sessions.session_transcript import (
            build_session_transcript_card,
        )
        assert callable(build_session_transcript_card)


# ── Views structure defense ──────────────


class TestViewsStructureDefense:
    """Verify view modules exist and have key functions."""

    def test_session_detail_importable(self):
        """sessions/detail.py is importable."""
        from agent.governance_ui.views.sessions import detail
        assert detail is not None

    def test_task_execution_importable(self):
        """tasks/execution.py is importable."""
        from agent.governance_ui.views.tasks import execution
        assert execution is not None

    def test_agent_metrics_importable(self):
        """agents/metrics.py is importable."""
        from agent.governance_ui.views.agents import metrics
        assert metrics is not None
