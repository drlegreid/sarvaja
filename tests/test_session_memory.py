"""
Tests for Session Memory Integration - P11.4
Per: GAP-ARCH-011, GAP-PROC-001, RULE-024
"""

import pytest
from datetime import date
from governance.session_memory import (
    SessionContext,
    SessionMemoryManager,
    create_dsp_session_context,
    get_session_memory,
    reset_session_memory,
)


class TestSessionContext:
    """Tests for SessionContext dataclass."""

    def test_creates_with_defaults(self):
        """SessionContext initializes with sensible defaults."""
        ctx = SessionContext(session_id="TEST-001")

        assert ctx.session_id == "TEST-001"
        assert ctx.project == "sim-ai"
        assert ctx.date == date.today().isoformat()
        assert ctx.tasks_completed == []
        assert ctx.gaps_resolved == []

    def test_to_document_basic(self):
        """to_document creates readable string."""
        ctx = SessionContext(
            session_id="TEST-001",
            phase="P11",
            summary="Test session for unit tests",
        )

        doc = ctx.to_document()

        assert "sim-ai Session TEST-001" in doc
        assert "Phase: P11" in doc
        assert "Test session for unit tests" in doc

    def test_to_document_with_tasks(self):
        """to_document includes tasks."""
        ctx = SessionContext(
            session_id="TEST-002",
            tasks_completed=["P11.1", "P11.2"],
            gaps_resolved=["GAP-001"],
        )

        doc = ctx.to_document()

        assert "Tasks Completed: P11.1, P11.2" in doc
        assert "Gaps Resolved: GAP-001" in doc

    def test_to_metadata(self):
        """to_metadata creates proper dict."""
        ctx = SessionContext(
            session_id="TEST-003",
            phase="P11",
        )
        ctx.tasks_completed = ["P11.1", "P11.2", "P11.3"]
        ctx.gaps_resolved = ["GAP-001"]

        meta = ctx.to_metadata()

        assert meta["project"] == "sim-ai"
        assert meta["session_id"] == "TEST-003"
        assert meta["phase"] == "P11"
        assert meta["type"] == "session-context"
        assert meta["tasks_count"] == 3
        assert meta["gaps_resolved_count"] == 1


class TestSessionMemoryManager:
    """Tests for SessionMemoryManager."""

    def setup_method(self):
        """Reset global manager before each test."""
        reset_session_memory()

    def test_init_creates_context(self):
        """Manager initializes with new context."""
        manager = SessionMemoryManager()

        assert manager.current_context is not None
        assert manager.current_context.project == "sim-ai"
        assert manager.current_context.session_id.startswith("SESSION-")

    def test_set_phase(self):
        """set_phase updates context."""
        manager = SessionMemoryManager()
        manager.set_phase("P11")

        assert manager.current_context.phase == "P11"

    def test_track_task_completed(self):
        """track_task_completed adds to list."""
        manager = SessionMemoryManager()
        manager.track_task_completed("P11.1")
        manager.track_task_completed("P11.2")

        assert "P11.1" in manager.current_context.tasks_completed
        assert "P11.2" in manager.current_context.tasks_completed

    def test_track_task_no_duplicates(self):
        """track_task_completed prevents duplicates."""
        manager = SessionMemoryManager()
        manager.track_task_completed("P11.1")
        manager.track_task_completed("P11.1")

        assert manager.current_context.tasks_completed.count("P11.1") == 1

    def test_track_gap_resolved(self):
        """track_gap_resolved adds to list."""
        manager = SessionMemoryManager()
        manager.track_gap_resolved("GAP-DATA-002")

        assert "GAP-DATA-002" in manager.current_context.gaps_resolved

    def test_track_gap_discovered(self):
        """track_gap_discovered adds to list."""
        manager = SessionMemoryManager()
        manager.track_gap_discovered("GAP-NEW-001")

        assert "GAP-NEW-001" in manager.current_context.gaps_discovered

    def test_track_decision(self):
        """track_decision adds to list."""
        manager = SessionMemoryManager()
        manager.track_decision("Use TypeDB for entity linkage")

        assert "Use TypeDB for entity linkage" in manager.current_context.decisions_made

    def test_track_file_modified(self):
        """track_file_modified adds to list."""
        manager = SessionMemoryManager()
        manager.track_file_modified("governance/schema.tql")

        assert "governance/schema.tql" in manager.current_context.key_files_modified

    def test_set_test_results(self):
        """set_test_results updates context."""
        manager = SessionMemoryManager()
        manager.set_test_results(passed=100, failed=2, skipped=5)

        assert manager.current_context.test_results["passed"] == 100
        assert manager.current_context.test_results["failed"] == 2
        assert manager.current_context.test_results["skipped"] == 5

    def test_set_summary(self):
        """set_summary updates context."""
        manager = SessionMemoryManager()
        manager.set_summary("Session completed P11.3 entity linkage")

        assert manager.current_context.summary == "Session completed P11.3 entity linkage"

    def test_add_next_step(self):
        """add_next_step adds to list."""
        manager = SessionMemoryManager()
        manager.add_next_step("Continue with P11.4")

        assert "Continue with P11.4" in manager.current_context.next_steps

    def test_get_save_payload(self):
        """get_save_payload creates valid MCP payload."""
        manager = SessionMemoryManager()
        manager.set_phase("P11")
        manager.track_task_completed("P11.3")

        payload = manager.get_save_payload()

        assert payload["collection_name"] == "claude_memories"
        assert len(payload["documents"]) == 1
        assert len(payload["ids"]) == 1
        assert len(payload["metadatas"]) == 1
        assert "sim-ai" in payload["ids"][0]
        assert "Phase: P11" in payload["documents"][0]

    def test_get_recovery_query(self):
        """get_recovery_query creates valid MCP query."""
        manager = SessionMemoryManager()

        query = manager.get_recovery_query()

        assert query["collection_name"] == "claude_memories"
        assert len(query["query_texts"]) == 1
        assert "sim-ai" in query["query_texts"][0]
        assert query["n_results"] == 5

    def test_parse_recovery_results_empty(self):
        """parse_recovery_results handles empty results."""
        manager = SessionMemoryManager()

        results = {"documents": [[]], "metadatas": [[]]}
        recovered = manager.parse_recovery_results(results)

        assert recovered["found"] is False
        assert recovered["sessions"] == []

    def test_parse_recovery_results_with_data(self):
        """parse_recovery_results extracts context."""
        manager = SessionMemoryManager()

        results = {
            "documents": [["sim-ai Session TEST-001 Phase P11 completed"]],
            "metadatas": [[{"date": "2024-12-26", "phase": "P11", "type": "session-context"}]],
        }
        recovered = manager.parse_recovery_results(results)

        assert recovered["found"] is True
        assert len(recovered["sessions"]) == 1
        assert recovered["last_phase"] == "P11"

    def test_generate_amnesia_report_no_context(self):
        """generate_amnesia_report handles no context."""
        manager = SessionMemoryManager()
        recovered = {"found": False}

        report = manager.generate_amnesia_report(recovered)

        assert "AMNESIA Recovery Report" in report
        assert "No recent session context found" in report
        assert "Recovery:" in report

    def test_generate_amnesia_report_with_context(self):
        """generate_amnesia_report shows recovered context."""
        manager = SessionMemoryManager()
        recovered = {
            "found": True,
            "sessions": [{"content": "Test session"}],
            "last_phase": "P11",
            "summary": "Completed P11.3 entity linkage",
        }

        report = manager.generate_amnesia_report(recovered)

        assert "AMNESIA Recovery Report" in report
        assert "Found 1 sessions" in report
        assert "Last Phase:** P11" in report


class TestDSPIntegration:
    """Tests for DSP tracker integration."""

    def test_create_dsp_session_context_basic(self):
        """create_dsp_session_context creates from DSP data."""
        ctx = create_dsp_session_context(
            cycle_id="DSM-2024-12-26-123456",
            batch_id="201-300",
            phases_completed=["audit", "hypothesize", "measure"],
            findings=[],
            checkpoints=[],
            metrics={},
        )

        assert ctx.session_id == "DSM-2024-12-26-123456"
        assert ctx.phase == "DSP-201-300"
        assert ctx.project == "sim-ai"

    def test_create_dsp_session_context_with_findings(self):
        """create_dsp_session_context extracts findings."""
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

        assert "GAP-NEW-001" in ctx.gaps_discovered
        assert any("P11.3" in t for t in ctx.tasks_completed)

    def test_create_dsp_session_context_with_metrics(self):
        """create_dsp_session_context extracts metrics."""
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

        assert ctx.gaps_resolved == ["GAP-001", "GAP-002"]
        assert ctx.test_results["passed"] == 50
        assert ctx.test_results["failed"] == 2

    def test_create_dsp_session_context_with_checkpoints(self):
        """create_dsp_session_context generates summary from checkpoints."""
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

        assert "Audited 10 files" in ctx.summary
        assert "Resolved GAP-001" in ctx.summary


class TestGlobalManager:
    """Tests for global manager instance."""

    def setup_method(self):
        """Reset before each test."""
        reset_session_memory()

    def test_get_session_memory_singleton(self):
        """get_session_memory returns same instance."""
        m1 = get_session_memory()
        m2 = get_session_memory()

        assert m1 is m2

    def test_reset_session_memory(self):
        """reset_session_memory clears instance."""
        m1 = get_session_memory()
        reset_session_memory()
        m2 = get_session_memory()

        assert m1 is not m2

    def test_to_dict(self):
        """to_dict serializes manager state."""
        manager = get_session_memory()
        manager.set_phase("P11")

        state = manager.to_dict()

        assert state["project"] == "sim-ai"
        assert state["collection"] == "claude_memories"
        assert state["current_context"]["phase"] == "P11"
