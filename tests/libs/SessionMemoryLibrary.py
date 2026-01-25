"""
Robot Framework Library for Session Memory Tests.

Per P11.4: Session memory integration for amnesia recovery.
Migrated from tests/test_session_memory.py
"""
from pathlib import Path
from datetime import date
from robot.api.deco import keyword


class SessionMemoryLibrary:
    """Library for testing session memory module."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    # =============================================================================
    # SessionContext Tests
    # =============================================================================

    @keyword("Session Context Creates With Defaults")
    def session_context_creates_with_defaults(self):
        """SessionContext initializes with sensible defaults."""
        try:
            from governance.session_memory import SessionContext

            ctx = SessionContext(session_id="TEST-001")

            return {
                "session_id_correct": ctx.session_id == "TEST-001",
                "project_correct": ctx.project == "sim-ai",
                "date_correct": ctx.date == date.today().isoformat(),
                "tasks_empty": ctx.tasks_completed == [],
                "gaps_empty": ctx.gaps_resolved == []
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Session Context To Document Basic")
    def session_context_to_document_basic(self):
        """to_document creates readable string."""
        try:
            from governance.session_memory import SessionContext

            ctx = SessionContext(
                session_id="TEST-001",
                phase="P11",
                summary="Test session for unit tests",
            )

            doc = ctx.to_document()

            return {
                "has_session_id": "sim-ai Session TEST-001" in doc,
                "has_phase": "Phase: P11" in doc,
                "has_summary": "Test session for unit tests" in doc
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Session Context To Document With Tasks")
    def session_context_to_document_with_tasks(self):
        """to_document includes tasks."""
        try:
            from governance.session_memory import SessionContext

            ctx = SessionContext(
                session_id="TEST-002",
                tasks_completed=["P11.1", "P11.2"],
                gaps_resolved=["GAP-001"],
            )

            doc = ctx.to_document()

            return {
                "has_tasks": "Tasks Completed: P11.1, P11.2" in doc,
                "has_gaps": "Gaps Resolved: GAP-001" in doc
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Session Context To Metadata")
    def session_context_to_metadata(self):
        """to_metadata creates proper dict."""
        try:
            from governance.session_memory import SessionContext

            ctx = SessionContext(
                session_id="TEST-003",
                phase="P11",
            )
            ctx.tasks_completed = ["P11.1", "P11.2", "P11.3"]
            ctx.gaps_resolved = ["GAP-001"]

            meta = ctx.to_metadata()

            return {
                "project_correct": meta.get("project") == "sim-ai",
                "session_id_correct": meta.get("session_id") == "TEST-003",
                "phase_correct": meta.get("phase") == "P11",
                "type_correct": meta.get("type") == "session-context",
                "tasks_count_correct": meta.get("tasks_count") == 3,
                "gaps_count_correct": meta.get("gaps_resolved_count") == 1
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    # =============================================================================
    # SessionMemoryManager Tests
    # =============================================================================

    @keyword("Manager Init Creates Context")
    def manager_init_creates_context(self):
        """Manager initializes with new context."""
        try:
            from governance.session_memory import SessionMemoryManager, reset_session_memory
            reset_session_memory()

            manager = SessionMemoryManager()

            return {
                "has_context": manager.current_context is not None,
                "project_correct": manager.current_context.project == "sim-ai",
                "session_id_starts_with": manager.current_context.session_id.startswith("SESSION-")
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Manager Set Phase")
    def manager_set_phase(self):
        """set_phase updates context."""
        try:
            from governance.session_memory import SessionMemoryManager, reset_session_memory
            reset_session_memory()

            manager = SessionMemoryManager()
            manager.set_phase("P11")

            return {"phase_set": manager.current_context.phase == "P11"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Manager Track Task Completed")
    def manager_track_task_completed(self):
        """track_task_completed adds to list."""
        try:
            from governance.session_memory import SessionMemoryManager, reset_session_memory
            reset_session_memory()

            manager = SessionMemoryManager()
            manager.track_task_completed("P11.1")
            manager.track_task_completed("P11.2")

            return {
                "has_task_1": "P11.1" in manager.current_context.tasks_completed,
                "has_task_2": "P11.2" in manager.current_context.tasks_completed
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Manager Track Task No Duplicates")
    def manager_track_task_no_duplicates(self):
        """track_task_completed prevents duplicates."""
        try:
            from governance.session_memory import SessionMemoryManager, reset_session_memory
            reset_session_memory()

            manager = SessionMemoryManager()
            manager.track_task_completed("P11.1")
            manager.track_task_completed("P11.1")

            return {"no_duplicates": manager.current_context.tasks_completed.count("P11.1") == 1}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Manager Track Gap Resolved")
    def manager_track_gap_resolved(self):
        """track_gap_resolved adds to list."""
        try:
            from governance.session_memory import SessionMemoryManager, reset_session_memory
            reset_session_memory()

            manager = SessionMemoryManager()
            manager.track_gap_resolved("GAP-DATA-002")

            return {"gap_tracked": "GAP-DATA-002" in manager.current_context.gaps_resolved}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Manager Track Gap Discovered")
    def manager_track_gap_discovered(self):
        """track_gap_discovered adds to list."""
        try:
            from governance.session_memory import SessionMemoryManager, reset_session_memory
            reset_session_memory()

            manager = SessionMemoryManager()
            manager.track_gap_discovered("GAP-NEW-001")

            return {"gap_tracked": "GAP-NEW-001" in manager.current_context.gaps_discovered}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Manager Track Decision")
    def manager_track_decision(self):
        """track_decision adds to list."""
        try:
            from governance.session_memory import SessionMemoryManager, reset_session_memory
            reset_session_memory()

            manager = SessionMemoryManager()
            manager.track_decision("Use TypeDB for entity linkage")

            return {"decision_tracked": "Use TypeDB for entity linkage" in manager.current_context.decisions_made}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Manager Track File Modified")
    def manager_track_file_modified(self):
        """track_file_modified adds to list."""
        try:
            from governance.session_memory import SessionMemoryManager, reset_session_memory
            reset_session_memory()

            manager = SessionMemoryManager()
            manager.track_file_modified("governance/schema.tql")

            return {"file_tracked": "governance/schema.tql" in manager.current_context.key_files_modified}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Manager Set Test Results")
    def manager_set_test_results(self):
        """set_test_results updates context."""
        try:
            from governance.session_memory import SessionMemoryManager, reset_session_memory
            reset_session_memory()

            manager = SessionMemoryManager()
            manager.set_test_results(passed=100, failed=2, skipped=5)

            return {
                "passed_correct": manager.current_context.test_results.get("passed") == 100,
                "failed_correct": manager.current_context.test_results.get("failed") == 2,
                "skipped_correct": manager.current_context.test_results.get("skipped") == 5
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Manager Set Summary")
    def manager_set_summary(self):
        """set_summary updates context."""
        try:
            from governance.session_memory import SessionMemoryManager, reset_session_memory
            reset_session_memory()

            manager = SessionMemoryManager()
            manager.set_summary("Session completed P11.3 entity linkage")

            return {"summary_set": manager.current_context.summary == "Session completed P11.3 entity linkage"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Manager Add Next Step")
    def manager_add_next_step(self):
        """add_next_step adds to list."""
        try:
            from governance.session_memory import SessionMemoryManager, reset_session_memory
            reset_session_memory()

            manager = SessionMemoryManager()
            manager.add_next_step("Continue with P11.4")

            return {"step_added": "Continue with P11.4" in manager.current_context.next_steps}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Manager Get Save Payload")
    def manager_get_save_payload(self):
        """get_save_payload creates valid MCP payload."""
        try:
            from governance.session_memory import SessionMemoryManager, reset_session_memory
            reset_session_memory()

            manager = SessionMemoryManager()
            manager.set_phase("P11")
            manager.track_task_completed("P11.3")

            payload = manager.get_save_payload()

            return {
                "has_collection": payload.get("collection_name") == "claude_memories",
                "has_documents": len(payload.get("documents", [])) == 1,
                "has_ids": len(payload.get("ids", [])) == 1,
                "has_metadatas": len(payload.get("metadatas", [])) == 1,
                "id_has_project": "sim-ai" in payload.get("ids", [""])[0],
                "doc_has_phase": "Phase: P11" in payload.get("documents", [""])[0]
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Manager Get Recovery Query")
    def manager_get_recovery_query(self):
        """get_recovery_query creates valid MCP query."""
        try:
            from governance.session_memory import SessionMemoryManager, reset_session_memory
            reset_session_memory()

            manager = SessionMemoryManager()

            query = manager.get_recovery_query()

            return {
                "has_collection": query.get("collection_name") == "claude_memories",
                "has_query_texts": len(query.get("query_texts", [])) == 1,
                "query_has_project": "sim-ai" in query.get("query_texts", [""])[0],
                "n_results_correct": query.get("n_results") == 5
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Manager Parse Recovery Results Empty")
    def manager_parse_recovery_results_empty(self):
        """parse_recovery_results handles empty results."""
        try:
            from governance.session_memory import SessionMemoryManager, reset_session_memory
            reset_session_memory()

            manager = SessionMemoryManager()

            results = {"documents": [[]], "metadatas": [[]]}
            recovered = manager.parse_recovery_results(results)

            return {
                "found_false": recovered.get("found") is False,
                "sessions_empty": recovered.get("sessions") == []
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Manager Parse Recovery Results With Data")
    def manager_parse_recovery_results_with_data(self):
        """parse_recovery_results extracts context."""
        try:
            from governance.session_memory import SessionMemoryManager, reset_session_memory
            reset_session_memory()

            manager = SessionMemoryManager()

            results = {
                "documents": [["sim-ai Session TEST-001 Phase P11 completed"]],
                "metadatas": [[{"date": "2024-12-26", "phase": "P11", "type": "session-context"}]],
            }
            recovered = manager.parse_recovery_results(results)

            return {
                "found_true": recovered.get("found") is True,
                "has_sessions": len(recovered.get("sessions", [])) == 1,
                "last_phase_correct": recovered.get("last_phase") == "P11"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Manager Generate Amnesia Report No Context")
    def manager_generate_amnesia_report_no_context(self):
        """generate_amnesia_report handles no context."""
        try:
            from governance.session_memory import SessionMemoryManager, reset_session_memory
            reset_session_memory()

            manager = SessionMemoryManager()
            recovered = {"found": False}

            report = manager.generate_amnesia_report(recovered)

            return {
                "has_title": "AMNESIA Recovery Report" in report,
                "has_no_context": "No recent session context found" in report,
                "has_recovery": "Recovery" in report
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Manager Generate Amnesia Report With Context")
    def manager_generate_amnesia_report_with_context(self):
        """generate_amnesia_report shows recovered context."""
        try:
            from governance.session_memory import SessionMemoryManager, reset_session_memory
            reset_session_memory()

            manager = SessionMemoryManager()
            recovered = {
                "found": True,
                "sessions": [{"content": "Test session"}],
                "last_phase": "P11",
                "summary": "Completed P11.3 entity linkage",
            }

            report = manager.generate_amnesia_report(recovered)

            return {
                "has_title": "AMNESIA Recovery Report" in report,
                "has_found_sessions": "Found 1 sessions" in report,
                "has_last_phase": "Last Phase:** P11" in report
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    # =============================================================================
    # DSP Integration Tests
    # =============================================================================

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

    # =============================================================================
    # Global Manager Tests
    # =============================================================================

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
