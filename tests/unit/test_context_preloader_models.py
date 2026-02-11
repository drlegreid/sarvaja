"""
Unit tests for Context Preloader Models.

Per DOC-SIZE-01-v1: Tests for extracted context_preloader/models.py module.
Tests: Decision, TechnologyChoice, ContextSummary.
"""

import pytest
from datetime import datetime

from governance.context_preloader.models import (
    Decision,
    TechnologyChoice,
    ContextSummary,
)


class TestDecision:
    """Tests for Decision dataclass."""

    def test_basic(self):
        d = Decision(
            id="DEC-001", name="Use TypeDB", status="APPROVED",
            date="2026-01-14", summary="Graph DB for governance",
        )
        assert d.id == "DEC-001"
        assert d.rationale == ""
        assert d.source_file == ""

    def test_with_all_fields(self):
        d = Decision(
            id="DEC-002", name="Rename project", status="IMPLEMENTED",
            date="2026-01-14", summary="Rename to Sarvaja",
            rationale="Sanskrit meaning", source_file="CLAUDE.md",
        )
        assert d.rationale == "Sanskrit meaning"


class TestTechnologyChoice:
    """Tests for TechnologyChoice dataclass."""

    def test_basic(self):
        tc = TechnologyChoice(
            area="Container Runtime",
            choice="Podman",
            not_using="Docker",
            rationale="xubuntu migration",
        )
        assert tc.area == "Container Runtime"
        assert tc.choice == "Podman"


class TestContextSummary:
    """Tests for ContextSummary dataclass."""

    def test_defaults(self):
        cs = ContextSummary()
        assert cs.decisions == []
        assert cs.technology_choices == []
        assert cs.active_phase is None
        assert cs.open_gaps_count == 0
        assert cs.loaded_at is not None

    def test_to_dict(self):
        cs = ContextSummary(
            decisions=[
                Decision("D-1", "Test", "APPROVED", "2026-01-01", "summary"),
            ],
            technology_choices=[
                TechnologyChoice("DB", "TypeDB", "Postgres", "graphs"),
            ],
            active_phase="P12",
            open_gaps_count=5,
        )
        d = cs.to_dict()
        assert len(d["decisions"]) == 1
        assert d["decisions"][0]["id"] == "D-1"
        assert len(d["technology_choices"]) == 1
        assert d["technology_choices"][0]["area"] == "DB"
        assert d["active_phase"] == "P12"
        assert d["open_gaps_count"] == 5

    def test_to_agent_prompt_empty(self):
        cs = ContextSummary()
        prompt = cs.to_agent_prompt()
        assert "Strategic Context" in prompt
        assert "Context loaded at" in prompt

    def test_to_agent_prompt_with_tech(self):
        cs = ContextSummary(
            technology_choices=[
                TechnologyChoice("Runtime", "Podman", "Docker", "migration"),
            ]
        )
        prompt = cs.to_agent_prompt()
        assert "Technology Decisions" in prompt
        assert "Podman" in prompt
        assert "Docker" in prompt

    def test_to_agent_prompt_with_decisions(self):
        cs = ContextSummary(
            decisions=[
                Decision("D-1", "Use TypeDB", "APPROVED", "2026-01-01", "graph DB"),
                Decision("D-2", "Old decision", "REJECTED", "2025-12-01", "rejected"),
            ]
        )
        prompt = cs.to_agent_prompt()
        assert "D-1" in prompt
        assert "Use TypeDB" in prompt
        # REJECTED decisions should not appear
        assert "D-2" not in prompt

    def test_to_agent_prompt_with_phase(self):
        cs = ContextSummary(active_phase="P12 - Integration")
        prompt = cs.to_agent_prompt()
        assert "P12 - Integration" in prompt

    def test_to_agent_prompt_tech_caps_at_6(self):
        cs = ContextSummary(
            technology_choices=[
                TechnologyChoice(f"Area{i}", f"Choice{i}", f"Not{i}", "r")
                for i in range(10)
            ]
        )
        prompt = cs.to_agent_prompt()
        # Should only include first 6
        assert "Choice5" in prompt
        assert "Choice6" not in prompt
