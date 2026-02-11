"""
Unit tests for Session Memory Integration.

Per RULE-024: Tests for SessionContext, SessionMemoryManager,
and create_dsp_session_context helper.
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


# ---------------------------------------------------------------------------
# SessionContext
# ---------------------------------------------------------------------------
class TestSessionContext:
    """Tests for SessionContext dataclass."""

    def test_defaults(self):
        ctx = SessionContext(session_id="S-1")
        assert ctx.project == "sim-ai"
        assert ctx.date == date.today().isoformat()
        assert ctx.tasks_completed == []
        assert ctx.gaps_discovered == []
        assert ctx.decisions_made == []
        assert ctx.key_files_modified == []
        assert ctx.test_results == {}
        assert ctx.next_steps == []

    def test_explicit_fields(self):
        ctx = SessionContext(
            session_id="S-1", project="test", date="2026-01-01",
            phase="impl", tasks_completed=["T-1"],
        )
        assert ctx.project == "test"
        assert ctx.date == "2026-01-01"
        assert ctx.phase == "impl"

    def test_to_document_minimal(self):
        ctx = SessionContext(session_id="S-1")
        doc = ctx.to_document()
        assert "S-1" in doc
        assert "sim-ai Session" in doc

    def test_to_document_full(self):
        ctx = SessionContext(
            session_id="S-1", phase="validate",
            summary="Did things",
            tasks_completed=["T-1", "T-2"],
            tasks_in_progress=["T-3"],
            gaps_resolved=["GAP-1"],
            gaps_discovered=["GAP-2"],
            decisions_made=["DEC-1"],
            key_files_modified=["file.py"],
            test_results={"passed": 10, "failed": 2},
            next_steps=["Continue work"],
        )
        doc = ctx.to_document()
        assert "Did things" in doc
        assert "T-1, T-2" in doc
        assert "T-3" in doc
        assert "GAP-1" in doc
        assert "GAP-2" in doc
        assert "DEC-1" in doc
        assert "file.py" in doc
        assert "10 passed" in doc
        assert "Continue work" in doc

    def test_to_document_truncates_files(self):
        files = [f"file_{i}.py" for i in range(20)]
        ctx = SessionContext(session_id="S-1", key_files_modified=files)
        doc = ctx.to_document()
        # Should only show first 10
        assert "file_9.py" in doc
        assert "file_10.py" not in doc

    def test_to_document_truncates_next_steps(self):
        steps = [f"Step {i}" for i in range(10)]
        ctx = SessionContext(session_id="S-1", next_steps=steps)
        doc = ctx.to_document()
        assert "Step 4" in doc
        assert "Step 5" not in doc

    def test_to_metadata(self):
        ctx = SessionContext(
            session_id="S-1", phase="impl",
            tasks_completed=["T-1", "T-2"],
            gaps_resolved=["GAP-1"],
        )
        meta = ctx.to_metadata()
        assert meta["project"] == "sim-ai"
        assert meta["session_id"] == "S-1"
        assert meta["phase"] == "impl"
        assert meta["type"] == "session-context"
        assert meta["tasks_count"] == 2
        assert meta["gaps_resolved_count"] == 1

    def test_to_metadata_unknown_phase(self):
        ctx = SessionContext(session_id="S-1")
        assert ctx.to_metadata()["phase"] == "unknown"


# ---------------------------------------------------------------------------
# SessionMemoryManager
# ---------------------------------------------------------------------------
class TestSessionMemoryManager:
    """Tests for SessionMemoryManager class."""

    def test_init(self):
        mgr = SessionMemoryManager(project="test-proj")
        assert mgr.project == "test-proj"
        assert mgr.current_context is not None
        assert mgr.current_context.session_id.startswith("SESSION-")

    def test_set_phase(self):
        mgr = SessionMemoryManager()
        mgr.set_phase("validate")
        assert mgr.current_context.phase == "validate"

    def test_track_task_completed(self):
        mgr = SessionMemoryManager()
        mgr.track_task_completed("T-1")
        mgr.track_task_completed("T-1")  # duplicate
        mgr.track_task_completed("T-2")
        assert mgr.current_context.tasks_completed == ["T-1", "T-2"]

    def test_track_task_in_progress(self):
        mgr = SessionMemoryManager()
        mgr.track_task_in_progress("T-1")
        mgr.track_task_in_progress("T-1")  # dup
        assert mgr.current_context.tasks_in_progress == ["T-1"]

    def test_track_gap_resolved(self):
        mgr = SessionMemoryManager()
        mgr.track_gap_resolved("GAP-1")
        assert mgr.current_context.gaps_resolved == ["GAP-1"]

    def test_track_gap_discovered(self):
        mgr = SessionMemoryManager()
        mgr.track_gap_discovered("GAP-2")
        assert mgr.current_context.gaps_discovered == ["GAP-2"]

    def test_track_decision(self):
        mgr = SessionMemoryManager()
        mgr.track_decision("DEC-1")
        assert mgr.current_context.decisions_made == ["DEC-1"]

    def test_track_file_modified(self):
        mgr = SessionMemoryManager()
        mgr.track_file_modified("file.py")
        assert mgr.current_context.key_files_modified == ["file.py"]

    def test_set_test_results(self):
        mgr = SessionMemoryManager()
        mgr.set_test_results(100, 5, 3)
        assert mgr.current_context.test_results == {"passed": 100, "failed": 5, "skipped": 3}

    def test_set_summary(self):
        mgr = SessionMemoryManager()
        mgr.set_summary("Great progress")
        assert mgr.current_context.summary == "Great progress"

    def test_add_next_step(self):
        mgr = SessionMemoryManager()
        mgr.add_next_step("Fix bugs")
        mgr.add_next_step("Fix bugs")  # dup
        assert mgr.current_context.next_steps == ["Fix bugs"]

    def test_get_save_payload(self):
        mgr = SessionMemoryManager(project="test")
        payload = mgr.get_save_payload()
        assert payload["collection_name"] == "claude_memories"
        assert len(payload["documents"]) == 1
        assert len(payload["ids"]) == 1
        assert "test-session-" in payload["ids"][0]

    def test_get_recovery_query(self):
        mgr = SessionMemoryManager(project="test")
        query = mgr.get_recovery_query()
        assert query["collection_name"] == "claude_memories"
        assert "test" in query["query_texts"][0]
        assert query["n_results"] == 5

    def test_parse_recovery_results_empty(self):
        mgr = SessionMemoryManager()
        result = mgr.parse_recovery_results({"documents": [[]], "metadatas": [[]]})
        assert result["found"] is False
        assert result["sessions"] == []

    def test_parse_recovery_results_with_data(self):
        mgr = SessionMemoryManager()
        results = {
            "documents": [["doc content here"]],
            "metadatas": [[{"date": "2026-02-11", "phase": "impl", "type": "session-context"}]],
        }
        recovered = mgr.parse_recovery_results(results)
        assert recovered["found"] is True
        assert len(recovered["sessions"]) == 1
        assert recovered["last_phase"] == "impl"
        assert "doc content" in recovered["summary"]

    def test_generate_amnesia_report_not_found(self):
        mgr = SessionMemoryManager()
        report = mgr.generate_amnesia_report({"found": False})
        assert "No recent session context found" in report
        assert "AMNESIA Recovery Report" in report

    def test_generate_amnesia_report_found(self):
        mgr = SessionMemoryManager()
        recovered = {
            "found": True,
            "sessions": [{"content": "test"}],
            "last_phase": "validate",
            "summary": "Did things",
        }
        report = mgr.generate_amnesia_report(recovered)
        assert "Found 1 sessions" in report
        assert "validate" in report
        assert "Did things" in report

    def test_to_dict(self):
        mgr = SessionMemoryManager(project="test")
        d = mgr.to_dict()
        assert d["project"] == "test"
        assert d["collection"] == "claude_memories"
        assert d["current_context"] is not None


# ---------------------------------------------------------------------------
# create_dsp_session_context
# ---------------------------------------------------------------------------
class TestCreateDspSessionContext:
    """Tests for create_dsp_session_context helper."""

    def test_basic(self):
        ctx = create_dsp_session_context(
            cycle_id="DSP-2026-01-01",
            batch_id="B1",
            phases_completed=["scan", "analyze"],
            findings=[],
            checkpoints=[],
            metrics={},
        )
        assert ctx.session_id == "DSP-2026-01-01"
        assert ctx.phase == "DSP-B1"

    def test_extracts_task_findings(self):
        findings = [
            {"type": "task_completed", "description": "Fixed bug X"},
            {"type": "gap", "id": "GAP-1"},
            {"type": "other", "description": "ignored"},
        ]
        ctx = create_dsp_session_context("C1", "B1", [], findings, [], {})
        assert len(ctx.tasks_completed) == 1
        assert "Fixed bug X" in ctx.tasks_completed[0]
        assert "GAP-1" in ctx.gaps_discovered

    def test_extracts_metrics(self):
        metrics = {
            "gaps_resolved": ["GAP-1"],
            "tests_passed": 50,
            "tests_failed": 2,
            "tests_skipped": 1,
        }
        ctx = create_dsp_session_context("C1", None, [], [], [], metrics)
        assert ctx.gaps_resolved == ["GAP-1"]
        assert ctx.test_results["passed"] == 50
        assert ctx.test_results["failed"] == 2
        assert ctx.phase == "DSP"

    def test_summary_from_checkpoints(self):
        checkpoints = [
            {"description": "Step 1"},
            {"description": "Step 2"},
            {"description": "Step 3"},
            {"description": "Step 4"},
        ]
        ctx = create_dsp_session_context("C1", "B1", [], [], checkpoints, {})
        # Uses last 3 checkpoints
        assert "Step 2" in ctx.summary
        assert "Step 4" in ctx.summary

    def test_no_checkpoints(self):
        ctx = create_dsp_session_context("C1", "B1", [], [], [], {})
        assert ctx.summary is None


# ---------------------------------------------------------------------------
# Global manager
# ---------------------------------------------------------------------------
class TestGlobalManager:
    """Tests for get_session_memory and reset_session_memory."""

    def test_get_creates_singleton(self):
        reset_session_memory()
        mgr1 = get_session_memory()
        mgr2 = get_session_memory()
        assert mgr1 is mgr2

    def test_reset_clears(self):
        reset_session_memory()
        mgr1 = get_session_memory()
        reset_session_memory()
        mgr2 = get_session_memory()
        assert mgr1 is not mgr2
