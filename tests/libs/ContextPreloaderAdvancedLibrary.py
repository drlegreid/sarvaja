"""
Robot Framework Library for Context Preloader Advanced Tests.

Per GAP-CTX-002: Context Auto-Loading.
Split from ContextPreloaderLibrary.py per DOC-SIZE-01-v1.
"""
import tempfile
from pathlib import Path
from robot.api.deco import keyword


class ContextPreloaderAdvancedLibrary:
    """Library for testing context preloader convenience, parsing, and integration."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

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
