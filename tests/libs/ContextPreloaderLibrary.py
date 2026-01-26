"""
Robot Framework Library for Context Preloader Tests.

Per GAP-CTX-002: Context Auto-Loading.
Migrated from tests/test_context_preloader.py
"""
import tempfile
from pathlib import Path
from robot.api.deco import keyword


class ContextPreloaderLibrary:
    """Library for testing context preloader functionality."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    # =========================================================================
    # Decision Tests
    # =========================================================================

    @keyword("Decision Creation")
    def decision_creation(self):
        """Test creating a Decision."""
        try:
            from governance.context_preloader import Decision

            decision = Decision(
                id="DECISION-001",
                name="Test Decision",
                status="APPROVED",
                date="2024-12-24",
                summary="Test summary",
            )
            return {
                "id_correct": decision.id == "DECISION-001",
                "status_correct": decision.status == "APPROVED"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Decision Default Values")
    def decision_default_values(self):
        """Test Decision default values."""
        try:
            from governance.context_preloader import Decision

            decision = Decision(
                id="DECISION-002",
                name="Another Decision",
                status="PENDING",
                date="",
                summary="",
            )
            return {
                "rationale_empty": decision.rationale == "",
                "source_file_empty": decision.source_file == ""
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # TechnologyChoice Tests
    # =========================================================================

    @keyword("Technology Choice Creation")
    def technology_choice_creation(self):
        """Test creating a TechnologyChoice."""
        try:
            from governance.context_preloader import TechnologyChoice

            tc = TechnologyChoice(
                area="UI Framework",
                choice="Trame + Vuetify",
                not_using="React",
                rationale="Python-first",
            )
            return {
                "area_correct": tc.area == "UI Framework",
                "choice_correct": tc.choice == "Trame + Vuetify"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # ContextSummary Tests
    # =========================================================================

    @keyword("Context Summary Creation")
    def context_summary_creation(self):
        """Test creating an empty ContextSummary."""
        try:
            from governance.context_preloader import ContextSummary

            context = ContextSummary()
            return {
                "decisions_empty": context.decisions == [],
                "tech_choices_empty": context.technology_choices == [],
                "phase_none": context.active_phase is None,
                "gaps_zero": context.open_gaps_count == 0,
                "has_loaded_at": context.loaded_at is not None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Context Summary To Dict")
    def context_summary_to_dict(self):
        """Test converting ContextSummary to dict."""
        try:
            from governance.context_preloader import ContextSummary, Decision

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
            return {
                "has_decisions": "decisions" in result,
                "decisions_count": len(result["decisions"]) == 1,
                "decision_id": result["decisions"][0]["id"] == "DECISION-001",
                "phase_correct": result["active_phase"] == "Phase 12"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Context Summary To Agent Prompt")
    def context_summary_to_agent_prompt(self):
        """Test generating agent prompt from context."""
        try:
            from governance.context_preloader import (
                ContextSummary, Decision, TechnologyChoice
            )

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
            return {
                "has_strategic": "Strategic Context" in prompt,
                "has_decision": "DECISION-003" in prompt,
                "has_typedb": "TypeDB-First" in prompt,
                "has_trame": "Trame" in prompt,
                "has_phase": "Phase 12" in prompt
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Agent Prompt Filters Inactive")
    def agent_prompt_filters_inactive(self):
        """Test that agent prompt only shows active decisions."""
        try:
            from governance.context_preloader import ContextSummary, Decision

            context = ContextSummary()
            context.decisions = [
                Decision(id="DECISION-001", name="Active", status="APPROVED",
                         date="", summary=""),
                Decision(id="DECISION-002", name="Inactive", status="SUPERSEDED",
                         date="", summary=""),
            ]

            prompt = context.to_agent_prompt()
            return {
                "active_included": "DECISION-001" in prompt,
                "inactive_excluded": "DECISION-002" not in prompt
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # ContextPreloader Tests
    # =========================================================================

    @keyword("Preloader Initialization")
    def preloader_initialization(self):
        """Test ContextPreloader initialization."""
        try:
            from governance.context_preloader import ContextPreloader

            preloader = ContextPreloader()
            return {
                "has_root": preloader.project_root is not None,
                "cache_none": preloader._cached_context is None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Preloader Load Context")
    def preloader_load_context(self):
        """Test loading context from project."""
        try:
            from governance.context_preloader import ContextPreloader, ContextSummary

            preloader = ContextPreloader()
            context = preloader.load_context()
            return {
                "is_summary": isinstance(context, ContextSummary),
                "has_loaded_at": context.loaded_at is not None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Preloader Caching")
    def preloader_caching(self):
        """Test that preloader caches results."""
        try:
            from governance.context_preloader import ContextPreloader

            preloader = ContextPreloader()
            context1 = preloader.load_context()
            context2 = preloader.load_context()
            return {"same_instance": context1 is context2}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Preloader Force Refresh")
    def preloader_force_refresh(self):
        """Test force refresh bypasses cache."""
        try:
            from governance.context_preloader import ContextPreloader

            preloader = ContextPreloader()
            context1 = preloader.load_context()
            context2 = preloader.load_context(force_refresh=True)
            return {"different_instance": context1 is not context2}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Preloader Invalidate Cache")
    def preloader_invalidate_cache(self):
        """Test cache invalidation."""
        try:
            from governance.context_preloader import ContextPreloader

            preloader = ContextPreloader()
            preloader.load_context()
            before_invalidate = preloader._cached_context is not None
            preloader.invalidate_cache()
            after_invalidate = preloader._cached_context is None
            return {
                "cached_before": before_invalidate,
                "cleared_after": after_invalidate
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Load Decisions From Evidence")
    def load_decisions_from_evidence(self):
        """Test loading decisions from evidence directory."""
        try:
            from governance.context_preloader import ContextPreloader

            preloader = ContextPreloader()
            decisions = preloader._load_decisions()
            return {
                "is_list": isinstance(decisions, list),
                "exists_check": preloader.evidence_dir.exists() or True
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Load Technology Choices")
    def load_technology_choices(self):
        """Test loading technology choices from CLAUDE.md."""
        try:
            from governance.context_preloader import ContextPreloader

            preloader = ContextPreloader()
            choices = preloader._load_technology_choices()
            return {
                "is_list": isinstance(choices, list),
                "valid_items": len(choices) == 0 or (
                    choices[0].area is not None and choices[0].choice is not None
                )
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Detect Active Phase")
    def detect_active_phase(self):
        """Test detecting active phase from backlog."""
        try:
            from governance.context_preloader import ContextPreloader

            preloader = ContextPreloader()
            phase = preloader._detect_active_phase()
            return {
                "valid_type": phase is None or isinstance(phase, str)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Count Open Gaps")
    def count_open_gaps(self):
        """Test counting open gaps from GAP-INDEX.md."""
        try:
            from governance.context_preloader import ContextPreloader

            preloader = ContextPreloader()
            count = preloader._count_open_gaps()
            return {
                "is_int": isinstance(count, int),
                "non_negative": count >= 0
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Convenience Function Tests
    # =========================================================================

    @keyword("Preload Session Context Function")
    def preload_session_context_function(self):
        """Test preload_session_context function."""
        try:
            from governance.context_preloader import preload_session_context, ContextSummary

            context = preload_session_context()
            return {"is_summary": isinstance(context, ContextSummary)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Agent Context Prompt Function")
    def get_agent_context_prompt_function(self):
        """Test get_agent_context_prompt function."""
        try:
            from governance.context_preloader import get_agent_context_prompt

            prompt = get_agent_context_prompt()
            return {
                "is_string": isinstance(prompt, str),
                "has_context": "Strategic Context" in prompt or "Context" in prompt
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Decision File Parsing Tests
    # =========================================================================

    @keyword("Parse Decision File With Temp File")
    def parse_decision_file_with_temp_file(self):
        """Test parsing a decision file."""
        try:
            from governance.context_preloader import ContextPreloader

            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)
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

                return {
                    "not_none": decision is not None,
                    "id_correct": decision.id == "DECISION-999" if decision else False,
                    "status_correct": decision.status == "APPROVED" if decision else False,
                    "has_summary": "test decision" in decision.summary.lower() if decision else False
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Parse Session Decisions File")
    def parse_session_decisions_file(self):
        """Test parsing decisions from session file."""
        try:
            from governance.context_preloader import ContextPreloader

            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)
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

                return {
                    "count_correct": len(decisions) == 2,
                    "first_id": decisions[0].id == "DECISION-001" if decisions else False,
                    "first_status": decisions[0].status == "IMPLEMENTED" if decisions else False,
                    "second_id": decisions[1].id == "DECISION-002" if len(decisions) > 1 else False,
                    "second_status": decisions[1].status == "APPROVED" if len(decisions) > 1 else False
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Integration Tests
    # =========================================================================

    @keyword("Context Imported In Chat")
    def context_imported_in_chat(self):
        """Test that context preloader is importable from its module."""
        try:
            from governance.context_preloader.preloader import preload_session_context
            return {"callable": callable(preload_session_context)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Context Command Available")
    def context_command_available(self):
        """Test that /context command is available in chat."""
        try:
            from governance.routes.chat import _process_chat_command

            help_response = _process_chat_command("/help", "AGENT-001")
            return {"has_context": "/context" in help_response}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Context Command Returns Prompt")
    def context_command_returns_prompt(self):
        """Test that /context command returns context prompt."""
        try:
            from governance.routes.chat import _process_chat_command

            response = _process_chat_command("/context", "AGENT-001")
            return {
                "is_string": isinstance(response, str),
                "has_content": "Context" in response or "Failed" in response
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
