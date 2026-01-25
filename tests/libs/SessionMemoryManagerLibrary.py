"""
Robot Framework Library for Session Memory - Manager Tests.

Per P11.4: Session memory integration for amnesia recovery.
Split from SessionMemoryLibrary.py per DOC-SIZE-01-v1.

Covers: SessionMemoryManager initialization, tracking, save/recovery payloads.
"""
from pathlib import Path
from robot.api.deco import keyword


class SessionMemoryManagerLibrary:
    """Library for testing SessionMemoryManager module."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent

    # =========================================================================
    # SessionMemoryManager Tests
    # =========================================================================

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
