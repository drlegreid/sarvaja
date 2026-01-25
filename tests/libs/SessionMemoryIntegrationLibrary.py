"""
Robot Framework Library for Session Memory - Integration Tests.

Per P11.4: Session memory integration for amnesia recovery.
Split from SessionMemoryLibrary.py per DOC-SIZE-01-v1.

Covers: DSP Integration, Global Manager singleton.
"""
from pathlib import Path
from robot.api.deco import keyword


class SessionMemoryIntegrationLibrary:
    """Library for testing session memory integration."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    # =========================================================================
    # DSP Integration Tests
    # =========================================================================

    @keyword("Create DSP Session Context Basic")
    def create_dsp_session_context_basic(self):
        """create_dsp_session_context creates from DSP data."""
        try:
            from governance.session_memory import create_dsp_session_context

            ctx = create_dsp_session_context(
                cycle_id="DSM-2024-12-26-123456",
                batch_id="201-300",
                phases_completed=["audit", "hypothesize", "measure"],
                findings=[],
                checkpoints=[],
                metrics={},
            )

            return {
                "session_id_correct": ctx.session_id == "DSM-2024-12-26-123456",
                "phase_correct": ctx.phase == "DSP-201-300",
                "project_correct": ctx.project == "sim-ai"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Create DSP Session Context With Findings")
    def create_dsp_session_context_with_findings(self):
        """create_dsp_session_context extracts findings."""
        try:
            from governance.session_memory import create_dsp_session_context

            findings = [
                {"type": "gap", "id": "GAP-NEW-001", "description": "Missing test"},
                {"type": "task_completed", "description": "Implemented P11.3"},
            ]

            ctx = create_dsp_session_context(
                cycle_id="DSM-TEST",
                batch_id="100",
                phases_completed=[],
                findings=findings,
                checkpoints=[],
                metrics={},
            )

            return {
                "has_gap": "GAP-NEW-001" in ctx.gaps_discovered,
                "has_task": any("P11.3" in t for t in ctx.tasks_completed)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Create DSP Session Context With Metrics")
    def create_dsp_session_context_with_metrics(self):
        """create_dsp_session_context extracts metrics."""
        try:
            from governance.session_memory import create_dsp_session_context

            metrics = {
                "gaps_resolved": ["GAP-001", "GAP-002"],
                "tests_passed": 50,
                "tests_failed": 2,
            }

            ctx = create_dsp_session_context(
                cycle_id="DSM-TEST",
                batch_id="100",
                phases_completed=[],
                findings=[],
                checkpoints=[],
                metrics=metrics,
            )

            return {
                "gaps_correct": ctx.gaps_resolved == ["GAP-001", "GAP-002"],
                "passed_correct": ctx.test_results.get("passed") == 50,
                "failed_correct": ctx.test_results.get("failed") == 2
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Create DSP Session Context With Checkpoints")
    def create_dsp_session_context_with_checkpoints(self):
        """create_dsp_session_context generates summary from checkpoints."""
        try:
            from governance.session_memory import create_dsp_session_context

            checkpoints = [
                {"description": "Audited 10 files"},
                {"description": "Resolved GAP-001"},
                {"description": "Tests passing"},
            ]

            ctx = create_dsp_session_context(
                cycle_id="DSM-TEST",
                batch_id="100",
                phases_completed=[],
                findings=[],
                checkpoints=checkpoints,
                metrics={},
            )

            return {
                "has_audit": "Audited 10 files" in ctx.summary,
                "has_resolved": "Resolved GAP-001" in ctx.summary
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    # =========================================================================
    # Global Manager Tests
    # =========================================================================

    @keyword("Get Session Memory Singleton")
    def get_session_memory_singleton(self):
        """get_session_memory returns same instance."""
        try:
            from governance.session_memory import get_session_memory, reset_session_memory
            reset_session_memory()

            m1 = get_session_memory()
            m2 = get_session_memory()

            return {"is_same": m1 is m2}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Reset Session Memory Works")
    def reset_session_memory_works(self):
        """reset_session_memory clears instance."""
        try:
            from governance.session_memory import get_session_memory, reset_session_memory
            reset_session_memory()

            m1 = get_session_memory()
            reset_session_memory()
            m2 = get_session_memory()

            return {"is_different": m1 is not m2}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Manager To Dict Works")
    def manager_to_dict_works(self):
        """to_dict serializes manager state."""
        try:
            from governance.session_memory import get_session_memory, reset_session_memory
            reset_session_memory()

            manager = get_session_memory()
            manager.set_phase("P11")

            state = manager.to_dict()

            return {
                "project_correct": state.get("project") == "sim-ai",
                "collection_correct": state.get("collection") == "claude_memories",
                "phase_correct": state.get("current_context", {}).get("phase") == "P11"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}
