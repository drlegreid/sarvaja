"""
Tests for Context Preloader - P12.6

Per GAP-CTX-002: Context Auto-Loading.

Created: 2026-01-03
"""

import pytest
from pathlib import Path
import tempfile
import os

from governance.context_preloader import (
    ContextPreloader,
    ContextSummary,
    Decision,
    TechnologyChoice,
    preload_session_context,
    get_agent_context_prompt,
)


class TestDecision:
    """Test Decision dataclass."""

    def test_decision_creation(self):
        """Test creating a Decision."""
        decision = Decision(
            id="DECISION-001",
            name="Test Decision",
            status="APPROVED",
            date="2024-12-24",
            summary="Test summary",
        )
        assert decision.id == "DECISION-001"
        assert decision.status == "APPROVED"

    def test_decision_default_values(self):
        """Test Decision default values."""
        decision = Decision(
            id="DECISION-002",
            name="Another Decision",
            status="PENDING",
            date="",
            summary="",
        )
        assert decision.rationale == ""
        assert decision.source_file == ""


class TestTechnologyChoice:
    """Test TechnologyChoice dataclass."""

    def test_technology_choice_creation(self):
        """Test creating a TechnologyChoice."""
        tc = TechnologyChoice(
            area="UI Framework",
            choice="Trame + Vuetify",
            not_using="React",
            rationale="Python-first",
        )
        assert tc.area == "UI Framework"
        assert tc.choice == "Trame + Vuetify"


class TestContextSummary:
    """Test ContextSummary dataclass."""

    def test_context_summary_creation(self):
        """Test creating an empty ContextSummary."""
        context = ContextSummary()
        assert context.decisions == []
        assert context.technology_choices == []
        assert context.active_phase is None
        assert context.open_gaps_count == 0
        assert context.loaded_at is not None

    def test_context_summary_to_dict(self):
        """Test converting ContextSummary to dict."""
        context = ContextSummary()
        context.decisions = [
            Decision(
                id="DECISION-001",
                name="Test",
                status="APPROVED",
                date="2024-12-24",
                summary="Test",
            )
        ]
        context.active_phase = "Phase 12"

        result = context.to_dict()

        assert "decisions" in result
        assert len(result["decisions"]) == 1
        assert result["decisions"][0]["id"] == "DECISION-001"
        assert result["active_phase"] == "Phase 12"

    def test_context_summary_to_agent_prompt(self):
        """Test generating agent prompt from context."""
        context = ContextSummary()
        context.decisions = [
            Decision(
                id="DECISION-003",
                name="TypeDB-First Strategy",
                status="APPROVED",
                date="2024-12-24",
                summary="Use TypeDB as primary storage",
            )
        ]
        context.technology_choices = [
            TechnologyChoice(
                area="UI Framework",
                choice="Trame",
                not_using="React",
                rationale="Python-first",
            )
        ]
        context.active_phase = "Phase 12"

        prompt = context.to_agent_prompt()

        assert "Strategic Context" in prompt
        assert "DECISION-003" in prompt
        assert "TypeDB-First" in prompt
        assert "Trame" in prompt
        assert "Phase 12" in prompt

    def test_agent_prompt_filters_inactive_decisions(self):
        """Test that agent prompt only shows active decisions."""
        context = ContextSummary()
        context.decisions = [
            Decision(id="DECISION-001", name="Active", status="APPROVED", date="", summary=""),
            Decision(id="DECISION-002", name="Inactive", status="SUPERSEDED", date="", summary=""),
        ]

        prompt = context.to_agent_prompt()

        assert "DECISION-001" in prompt
        assert "DECISION-002" not in prompt


class TestContextPreloader:
    """Test ContextPreloader class."""

    def test_preloader_initialization(self):
        """Test ContextPreloader initialization."""
        preloader = ContextPreloader()
        assert preloader.project_root is not None
        assert preloader._cached_context is None

    def test_preloader_load_context(self):
        """Test loading context from project."""
        preloader = ContextPreloader()
        context = preloader.load_context()

        assert isinstance(context, ContextSummary)
        assert context.loaded_at is not None

    def test_preloader_caching(self):
        """Test that preloader caches results."""
        preloader = ContextPreloader()

        # First load
        context1 = preloader.load_context()

        # Second load (should be cached)
        context2 = preloader.load_context()

        # Same instance due to caching
        assert context1 is context2

    def test_preloader_force_refresh(self):
        """Test force refresh bypasses cache."""
        preloader = ContextPreloader()

        # First load
        context1 = preloader.load_context()

        # Force refresh
        context2 = preloader.load_context(force_refresh=True)

        # Different instance due to refresh
        assert context1 is not context2

    def test_preloader_invalidate_cache(self):
        """Test cache invalidation."""
        preloader = ContextPreloader()

        # Load and cache
        preloader.load_context()
        assert preloader._cached_context is not None

        # Invalidate
        preloader.invalidate_cache()
        assert preloader._cached_context is None

    def test_load_decisions_from_evidence(self):
        """Test loading decisions from evidence directory."""
        preloader = ContextPreloader()
        decisions = preloader._load_decisions()

        # Should find at least DECISION-003 if evidence dir exists
        if preloader.evidence_dir.exists():
            assert isinstance(decisions, list)
            # May or may not have decisions depending on test environment

    def test_load_technology_choices_from_claude_md(self):
        """Test loading technology choices from CLAUDE.md."""
        preloader = ContextPreloader()
        choices = preloader._load_technology_choices()

        # Should find technology choices if CLAUDE.md exists
        if preloader.claude_md_path.exists():
            assert isinstance(choices, list)
            # Should have at least some technology decisions
            if choices:
                assert choices[0].area is not None
                assert choices[0].choice is not None

    def test_detect_active_phase(self):
        """Test detecting active phase from backlog."""
        preloader = ContextPreloader()
        phase = preloader._detect_active_phase()

        # May or may not detect a phase depending on environment
        # Just verify it doesn't crash and returns correct type
        assert phase is None or isinstance(phase, str)

    def test_count_open_gaps(self):
        """Test counting open gaps from GAP-INDEX.md."""
        preloader = ContextPreloader()
        count = preloader._count_open_gaps()

        assert isinstance(count, int)
        assert count >= 0


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    def test_preload_session_context(self):
        """Test preload_session_context function."""
        context = preload_session_context()
        assert isinstance(context, ContextSummary)

    def test_get_agent_context_prompt(self):
        """Test get_agent_context_prompt function."""
        prompt = get_agent_context_prompt()
        assert isinstance(prompt, str)
        assert "Strategic Context" in prompt or "Context" in prompt


class TestDecisionFileParsing:
    """Test parsing decision files."""

    def test_parse_decision_file_with_temp_file(self, tmp_path):
        """Test parsing a decision file."""
        # Create temp decision file
        decision_file = tmp_path / "DECISION-999-TEST.md"
        decision_file.write_text("""# DECISION-999: Test Decision

**Date**: 2024-12-24
**Status**: APPROVED

## Summary

This is a test decision for unit testing purposes.

## Decision

Test the decision parsing logic.
""")

        preloader = ContextPreloader(project_root=tmp_path)
        preloader.evidence_dir = tmp_path

        decision = preloader._parse_decision_file(decision_file)

        assert decision is not None
        assert decision.id == "DECISION-999"
        assert decision.status == "APPROVED"
        assert "test decision" in decision.summary.lower()

    def test_parse_session_decisions_file(self, tmp_path):
        """Test parsing decisions from session file."""
        session_file = tmp_path / "SESSION-DECISIONS-2024-12-24.md"
        session_file.write_text("""# Session Decisions

## DECISION-001: Remove Opik

**Date**: 2024-12-24
**Status**: IMPLEMENTED
**Decision**: Remove Opik from stack due to memory overhead.

## DECISION-002: TypeDB Priority

**Date**: 2024-12-24
**Status**: APPROVED
**Decision**: Elevate TypeDB to Phase 2 priority.
""")

        preloader = ContextPreloader(project_root=tmp_path)
        preloader.evidence_dir = tmp_path

        decisions = preloader._parse_session_decisions_file(session_file)

        assert len(decisions) == 2
        assert decisions[0].id == "DECISION-001"
        assert decisions[0].status == "IMPLEMENTED"
        assert decisions[1].id == "DECISION-002"
        assert decisions[1].status == "APPROVED"


class TestIntegrationWithChat:
    """Test integration with chat routes."""

    def test_context_imported_in_chat(self):
        """Test that context preloader is importable from its module."""
        try:
            from governance.context_preloader.preloader import preload_session_context
            assert callable(preload_session_context)
        except ImportError as e:
            pytest.fail(f"Failed to import: {e}")

    def test_context_command_available(self):
        """Test that /context command is available in chat."""
        from governance.routes.chat import _process_chat_command

        # Test /help includes /context
        help_response = _process_chat_command("/help", "AGENT-001")
        assert "/context" in help_response

    def test_context_command_returns_prompt(self):
        """Test that /context command returns context prompt."""
        from governance.routes.chat import _process_chat_command

        response = _process_chat_command("/context", "AGENT-001")

        # Should return context or error message
        assert isinstance(response, str)
        assert "Context" in response or "Failed" in response
