"""
Unit tests for Context Preloader.

Per DOC-SIZE-01-v1: Tests for governance/context_preloader/preloader.py.
Tests: ContextPreloader — load_context, _load_decisions, _parse_decision_file,
       _parse_session_decisions_file, _load_technology_choices,
       _detect_active_phase, _count_open_gaps, invalidate_cache,
       get_context_preloader, preload_session_context, get_agent_context_prompt.
"""

import time
from pathlib import Path
from unittest.mock import patch

import pytest

from governance.context_preloader.preloader import (
    ContextPreloader,
    get_context_preloader,
    preload_session_context,
    get_agent_context_prompt,
)
from governance.context_preloader.models import Decision, TechnologyChoice


@pytest.fixture
def tmp_project(tmp_path):
    """Create a minimal project structure for testing."""
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text("# Project\n")
    return tmp_path


@pytest.fixture
def preloader(tmp_project):
    return ContextPreloader(project_root=tmp_project)


# ── _parse_decision_file ──────────────────────────────────


class TestParseDecisionFile:
    def test_parses_standard_file(self, preloader, tmp_project):
        fp = tmp_project / "evidence" / "DECISION-001.md"
        fp.write_text(
            "# TypeDB First\n\n"
            "**Status**: APPROVED\n"
            "**Date**: 2026-01-01\n\n"
            "## Summary\nUse TypeDB as primary store.\n"
        )
        d = preloader._parse_decision_file(fp)
        assert d is not None
        assert d.id == "DECISION-001"
        assert d.name == "TypeDB First"
        assert d.status == "APPROVED"
        assert d.date == "2026-01-01"
        assert "TypeDB" in d.summary

    def test_missing_fields_defaults(self, preloader, tmp_project):
        fp = tmp_project / "evidence" / "DECISION-002.md"
        fp.write_text("No structured content here.\n")
        d = preloader._parse_decision_file(fp)
        assert d is not None
        assert d.status == "UNKNOWN"
        assert d.date == ""

    def test_invalid_file_returns_none(self, preloader, tmp_project):
        fp = tmp_project / "evidence" / "DECISION-003.md"
        fp.write_text("")
        # Make file unreadable by mocking read_text to raise
        with patch.object(Path, "read_text", side_effect=Exception("read error")):
            d = preloader._parse_decision_file(fp)
        assert d is None


# ── _parse_session_decisions_file ─────────────────────────


class TestParseSessionDecisionsFile:
    def test_parses_multiple_decisions(self, preloader, tmp_project):
        fp = tmp_project / "evidence" / "SESSION-DECISIONS-2026-01.md"
        fp.write_text(
            "# Session Decisions\n\n"
            "## DECISION-010: Rename Project\n"
            "**Status**: IMPLEMENTED\n"
            "**Date**: 2026-01-14\n"
            "**Decision**: Rename from sim.ai to sarvaja.\n\n"
            "## DECISION-011: Use Podman\n"
            "**Status**: APPROVED\n"
            "**Date**: 2026-01-09\n"
            "**Decision**: Migrate to podman from docker.\n"
        )
        results = preloader._parse_session_decisions_file(fp)
        assert len(results) == 2
        assert results[0].id == "DECISION-010"
        assert results[0].name == "Rename Project"
        assert results[1].id == "DECISION-011"

    def test_empty_file(self, preloader, tmp_project):
        fp = tmp_project / "evidence" / "SESSION-DECISIONS-EMPTY.md"
        fp.write_text("# Empty\n")
        assert preloader._parse_session_decisions_file(fp) == []

    def test_exception_returns_empty(self, preloader, tmp_project):
        fp = tmp_project / "evidence" / "SESSION-DECISIONS-BAD.md"
        fp.write_text("")
        with patch.object(Path, "read_text", side_effect=Exception("io")):
            assert preloader._parse_session_decisions_file(fp) == []


# ── _load_decisions ───────────────────────────────────────


class TestLoadDecisions:
    def test_deduplicates_by_latest_date(self, preloader, tmp_project):
        # Same decision ID in two files — later date wins
        (tmp_project / "evidence" / "DECISION-001.md").write_text(
            "# Old\n**Status**: DRAFT\n**Date**: 2025-01-01\n"
        )
        (tmp_project / "evidence" / "SESSION-DECISIONS-2026.md").write_text(
            "## DECISION-001: Updated\n**Status**: APPROVED\n**Date**: 2026-06-01\n"
            "**Decision**: Updated version.\n"
        )
        decisions = preloader._load_decisions()
        assert len(decisions) == 1
        assert decisions[0].status == "APPROVED"

    def test_missing_evidence_dir(self, tmp_path):
        p = ContextPreloader(project_root=tmp_path)
        assert p._load_decisions() == []


# ── _load_technology_choices ──────────────────────────────


class TestLoadTechnologyChoices:
    def test_parses_table(self, preloader, tmp_project):
        (tmp_project / "CLAUDE.md").write_text(
            "# Project\n\n"
            "## Technology Decisions\n"
            "| Decision | Choice | NOT Using | Rationale |\n"
            "|----------|--------|-----------|----------|\n"
            "| **Container** | Podman | Docker | Rootless |\n"
            "| **DB** | TypeDB | Postgres | Graph |\n"
        )
        choices = preloader._load_technology_choices()
        assert len(choices) == 2
        assert choices[0].area == "Container"
        assert choices[0].choice == "Podman"
        assert choices[1].area == "DB"

    def test_no_tech_section(self, preloader, tmp_project):
        (tmp_project / "CLAUDE.md").write_text("# No tech section\n")
        assert preloader._load_technology_choices() == []

    def test_missing_claude_md(self, tmp_path):
        p = ContextPreloader(project_root=tmp_path)
        assert p._load_technology_choices() == []


# ── _detect_active_phase ──────────────────────────────────


class TestDetectActivePhase:
    def test_finds_active_phase(self, preloader, tmp_project):
        phases = tmp_project / "docs" / "backlog" / "phases"
        phases.mkdir(parents=True)
        (phases / "PHASE-01.md").write_text("# Phase 1\nStatus: DONE\n")
        (phases / "PHASE-02.md").write_text("# Phase 2\nStatus: IN PROGRESS\n")
        assert preloader._detect_active_phase() == "Phase 02"

    def test_no_phases_dir(self, preloader):
        assert preloader._detect_active_phase() is None

    def test_no_in_progress(self, preloader, tmp_project):
        phases = tmp_project / "docs" / "backlog" / "phases"
        phases.mkdir(parents=True)
        (phases / "PHASE-01.md").write_text("# Phase 1\nStatus: DONE\n")
        assert preloader._detect_active_phase() is None


# ── _count_open_gaps ──────────────────────────────────────


class TestCountOpenGaps:
    def test_counts_open(self, preloader, tmp_project):
        gaps = tmp_project / "docs" / "gaps"
        gaps.mkdir(parents=True)
        (gaps / "GAP-INDEX.md").write_text(
            "| Gap | Status |\n| GAP-001 | OPEN |\n| GAP-002 | CLOSED |\n| GAP-003 | OPEN |\n"
        )
        assert preloader._count_open_gaps() == 2

    def test_no_gap_file(self, preloader):
        assert preloader._count_open_gaps() == 0


# ── load_context + caching ────────────────────────────────


class TestLoadContext:
    def test_returns_context_summary(self, preloader):
        ctx = preloader.load_context()
        assert hasattr(ctx, "decisions")
        assert hasattr(ctx, "technology_choices")
        assert hasattr(ctx, "active_phase")

    def test_caches_result(self, preloader):
        ctx1 = preloader.load_context()
        ctx2 = preloader.load_context()
        assert ctx1 is ctx2

    def test_force_refresh(self, preloader):
        ctx1 = preloader.load_context()
        ctx2 = preloader.load_context(force_refresh=True)
        assert ctx1 is not ctx2

    def test_invalidate_cache(self, preloader):
        ctx1 = preloader.load_context()
        preloader.invalidate_cache()
        ctx2 = preloader.load_context()
        assert ctx1 is not ctx2


# ── Module-level helpers ──────────────────────────────────


class TestModuleHelpers:
    def test_get_context_preloader_returns_singleton(self):
        import governance.context_preloader.preloader as mod
        mod._preloader = None  # reset
        p1 = get_context_preloader()
        p2 = get_context_preloader()
        assert p1 is p2
        mod._preloader = None  # cleanup

    def test_preload_session_context(self):
        with patch.object(ContextPreloader, "load_context") as mock_load:
            from governance.context_preloader.models import ContextSummary
            mock_load.return_value = ContextSummary()
            result = preload_session_context()
            assert result is not None

    def test_get_agent_context_prompt(self):
        with patch("governance.context_preloader.preloader.preload_session_context") as mock_ctx:
            from governance.context_preloader.models import ContextSummary
            ctx = ContextSummary(active_phase="Phase 12")
            mock_ctx.return_value = ctx
            prompt = get_agent_context_prompt()
            assert "Phase 12" in prompt
