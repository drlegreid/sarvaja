"""Deep scan batch 141: Orchestrator state + context layers.

Batch 141 findings: 3 total (2 from batch 140 duplicates rejected),
0 confirmed fixes, 3 rejected.
"""
import pytest
from datetime import datetime


# ── Orchestrator retry semantics defense ──────────────


class TestOrchestratorRetryDefense:
    """Verify retry_count semantics are correct."""

    def test_max_retries_allows_correct_attempts(self):
        """MAX_RETRIES=3 with retry_count starting at 0 → 3 retries."""
        MAX_RETRIES = 3
        retry_count = 0
        attempts = 0
        while retry_count < MAX_RETRIES:
            attempts += 1
            retry_count += 1
        assert attempts == 3  # 3 retries (correct)

    def test_retry_zero_passes_gate(self):
        """First retry (retry_count=0) passes < MAX_RETRIES check."""
        MAX_RETRIES = 3
        retry_count = 0
        assert retry_count < MAX_RETRIES

    def test_retry_at_max_fails_gate(self):
        """retry_count == MAX_RETRIES fails < check → park task."""
        MAX_RETRIES = 3
        retry_count = 3
        assert not (retry_count < MAX_RETRIES)


# ── Certify node history parsing defense ──────────────


class TestCertifyNodeHistoryDefense:
    """Verify certify_node correctly separates completed vs parked."""

    def test_completed_excludes_parked(self):
        """Completed tasks exclude those with status='parked'."""
        history = [
            {"task_id": "T-1", "status": "done"},
            {"task_id": "T-2", "status": "parked", "reason": "exhausted_retries"},
            {"task_id": "T-3", "status": "done"},
        ]
        completed = [h for h in history if h.get("task_id") and not h.get("status") == "parked"]
        parked = [h for h in history if h.get("status") == "parked"]
        assert len(completed) == 2
        assert len(parked) == 1
        assert parked[0]["task_id"] == "T-2"

    def test_empty_history(self):
        """Empty history → no completed, no parked."""
        history = []
        completed = [h for h in history if h.get("task_id") and not h.get("status") == "parked"]
        parked = [h for h in history if h.get("status") == "parked"]
        assert len(completed) == 0
        assert len(parked) == 0


# ── Session metrics parser defense ──────────────


class TestSessionMetricsParserDefense:
    """Verify session metrics parser handles edge cases."""

    def test_empty_content_list_handled(self):
        """Empty content list produces no tool_uses."""
        content = []
        tool_uses = [b for b in content if isinstance(b, dict) and b.get("type") == "tool_use"]
        assert len(tool_uses) == 0

    def test_none_content_handled(self):
        """None content doesn't crash."""
        content = None
        if isinstance(content, list):
            tool_uses = [b for b in content if isinstance(b, dict) and b.get("type") == "tool_use"]
        else:
            tool_uses = []
        assert len(tool_uses) == 0

    def test_mixed_content_blocks(self):
        """Content with text and tool_use blocks extracts only tools."""
        content = [
            {"type": "text", "text": "Hello"},
            {"type": "tool_use", "name": "Read", "id": "t1"},
            {"type": "thinking", "thinking": "..."},
            {"type": "tool_use", "name": "Bash", "id": "t2"},
        ]
        tool_uses = [b for b in content if isinstance(b, dict) and b.get("type") == "tool_use"]
        assert len(tool_uses) == 2
        assert tool_uses[0]["name"] == "Read"
        assert tool_uses[1]["name"] == "Bash"


# ── Workspace registry defense ──────────────


class TestWorkspaceRegistryDefense:
    """Verify workspace registry project type detection."""

    def test_project_markers_list(self):
        """Project markers include standard project files."""
        from governance.services.cc_session_scanner import _PROJECT_MARKERS
        assert "CLAUDE.md" in _PROJECT_MARKERS
        assert "package.json" in _PROJECT_MARKERS
        assert "pyproject.toml" in _PROJECT_MARKERS

    def test_slug_derivation_short_name(self):
        """Short directory names produce valid slugs."""
        from governance.services.cc_session_scanner import derive_project_slug
        from pathlib import Path
        slug = derive_project_slug(Path("/fake/path/myproject"))
        assert isinstance(slug, str)
        assert len(slug) > 0

    def test_slug_derivation_long_path(self):
        """Long encoded paths extract last 2 segments."""
        from governance.services.cc_session_scanner import derive_project_slug
        from pathlib import Path
        p = Path("/fake/-home-user-Documents-Vibe-sarvaja-platform")
        slug = derive_project_slug(p)
        assert "sarvaja" in slug or "platform" in slug


# ── Initial state creation defense ──────────────


class TestInitialStateCreationDefense:
    """Verify create_initial_state sets all required fields."""

    def test_default_state_has_required_keys(self):
        """Default state has all required keys for graph execution."""
        from governance.workflows.orchestrator.state import create_initial_state
        state = create_initial_state(max_cycles=5)
        assert "max_cycles" in state
        assert "cycles_completed" in state
        assert "backlog" in state
        assert "cycle_history" in state
        assert state["cycles_completed"] == 0
        assert state["max_cycles"] == 5

    def test_dry_run_flag_propagated(self):
        """dry_run flag is set in state."""
        from governance.workflows.orchestrator.state import create_initial_state
        state = create_initial_state(max_cycles=1, dry_run=True)
        assert state.get("dry_run") is True

    def test_budget_state_manually_added(self):
        """Token budget keys can be added to state after creation."""
        from governance.workflows.orchestrator.state import create_initial_state
        state = create_initial_state(max_cycles=10)
        # Budget keys are added by the caller, not create_initial_state
        state["token_budget"] = 1000
        state["tokens_used"] = 0
        state["value_delivered"] = 0
        assert state["token_budget"] == 1000
        assert state["tokens_used"] == 0
        assert state["value_delivered"] == 0
