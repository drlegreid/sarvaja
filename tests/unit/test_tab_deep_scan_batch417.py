"""Batch 417 — routes exc_info, scanner log levels, path redaction,
traceability log levels, memory tier log levels, tracker phase warning tests.

Validates fixes for:
- BUG-414-CRD-001..002: sessions/crud.py exc_info additions
- BUG-414-REL-001: sessions/relations.py exc_info addition
- BUG-415-SCN-001..002: cc_session_scanner.py exc_info + debug→warning
- BUG-415-ORC-001: ingestion_orchestrator.py path redaction
- BUG-415-IDX-001: cc_content_indexer.py path redaction
- BUG-416-TRC-001..004: traceability.py debug→warning + exc_info
- BUG-416-MEM-001..003: memory_tiers.py debug→warning + exc_info
- BUG-417-TRK-001: dsm/tracker.py bind ValueError + log warning
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


def _check_exc_info(src, fragment, level="error"):
    """Find logger line containing fragment, verify exc_info=True."""
    idx = src.index(fragment)
    # Check within 200 chars (handles multi-line logger calls)
    block = src[idx:idx + 300]
    assert "exc_info=True" in block, f"Missing exc_info=True near: {fragment}"


def _check_warning_level(src, fragment):
    """Verify line containing fragment uses logger.warning (not debug)."""
    idx = src.index(fragment)
    line_start = src.rindex("\n", 0, idx) + 1
    line_end = src.index("\n", idx)
    line = src[line_start:line_end]
    assert "logger.warning" in line, f"Expected logger.warning in: {line.strip()}"


# ── BUG-414-CRD-001..002: sessions/crud.py exc_info additions ────────

class TestSessionsCrudExcInfoBatch417:
    def test_malformed_session_exc_info(self):
        src = (SRC / "governance/routes/sessions/crud.py").read_text()
        _check_exc_info(src, "Skipping malformed session")

    def test_end_session_conflict_exc_info(self):
        src = (SRC / "governance/routes/sessions/crud.py").read_text()
        _check_exc_info(src, "end_session conflict")

    def test_end_session_no_type_name_leak(self):
        src = (SRC / "governance/routes/sessions/crud.py").read_text()
        # Find the end_session conflict handler
        idx = src.index("end_session conflict")
        block = src[idx:idx + 300]
        assert "type(e).__name__" not in block, "type(e).__name__ still in end_session conflict response"

    def test_bug_markers_present(self):
        src = (SRC / "governance/routes/sessions/crud.py").read_text()
        assert "BUG-414-CRD-001" in src
        assert "BUG-414-CRD-002" in src


# ── BUG-414-REL-001: sessions/relations.py exc_info addition ──────────

class TestSessionsRelationsExcInfo:
    def test_typedb_fallback_exc_info(self):
        src = (SRC / "governance/routes/sessions/relations.py").read_text()
        _check_exc_info(src, "TypeDB evidence query failed, using fallback")

    def test_bug_marker_present(self):
        src = (SRC / "governance/routes/sessions/relations.py").read_text()
        assert "BUG-414-REL-001" in src


# ── BUG-415-SCN-001..002: cc_session_scanner.py exc_info + log level ──

class TestSessionScannerFixes:
    def test_scan_failure_exc_info(self):
        src = (SRC / "governance/services/cc_session_scanner.py").read_text()
        _check_exc_info(src, "Failed to scan")

    def test_directory_iteration_warning_level(self):
        src = (SRC / "governance/services/cc_session_scanner.py").read_text()
        _check_warning_level(src, "CC directory iteration failed")

    def test_directory_iteration_exc_info(self):
        src = (SRC / "governance/services/cc_session_scanner.py").read_text()
        _check_exc_info(src, "CC directory iteration failed")

    def test_bug_markers_present(self):
        src = (SRC / "governance/services/cc_session_scanner.py").read_text()
        assert "BUG-415-SCN-001" in src
        assert "BUG-415-SCN-002" in src


# ── BUG-415-ORC-001: ingestion_orchestrator.py path redaction ──────────

class TestOrchestatorPathRedaction:
    def test_estimate_success_no_str_path(self):
        src = (SRC / "governance/services/ingestion_orchestrator.py").read_text()
        # Find the success return block
        idx = src.index("est_chunks")
        block = src[idx:idx + 300]
        assert "path.name" in block, "Success response should use path.name, not str(path)"

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/ingestion_orchestrator.py").read_text()
        assert "BUG-415-ORC-001" in src


# ── BUG-415-IDX-001: cc_content_indexer.py path redaction ─────────────

class TestContentIndexerPathRedaction:
    def test_error_uses_path_name(self):
        src = (SRC / "governance/services/cc_content_indexer.py").read_text()
        # Find the file-not-found error path
        idx = src.index("JSONL file not found")
        block = src[idx:idx + 200]
        assert "Path(jsonl_path).name" in block, "Error should use Path(jsonl_path).name"

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/cc_content_indexer.py").read_text()
        assert "BUG-415-IDX-001" in src


# ── BUG-416-TRC-001..004: traceability.py debug→warning + exc_info ───

class TestTraceabilityLogLevel:
    def test_rule_chain_warning_level(self):
        src = (SRC / "governance/mcp_tools/traceability.py").read_text()
        _check_warning_level(src, "trace_rule_chain query failed")

    def test_rule_chain_exc_info(self):
        src = (SRC / "governance/mcp_tools/traceability.py").read_text()
        _check_exc_info(src, "trace_rule_chain query failed")

    def test_gap_chain_warning_level(self):
        src = (SRC / "governance/mcp_tools/traceability.py").read_text()
        _check_warning_level(src, "trace_gap_chain query failed")

    def test_gap_chain_exc_info(self):
        src = (SRC / "governance/mcp_tools/traceability.py").read_text()
        _check_exc_info(src, "trace_gap_chain query failed")

    def test_evidence_task_warning_level(self):
        src = (SRC / "governance/mcp_tools/traceability.py").read_text()
        _check_warning_level(src, "trace_evidence_chain task query failed")

    def test_evidence_task_exc_info(self):
        src = (SRC / "governance/mcp_tools/traceability.py").read_text()
        _check_exc_info(src, "trace_evidence_chain task query failed")

    def test_evidence_session_warning_level(self):
        src = (SRC / "governance/mcp_tools/traceability.py").read_text()
        _check_warning_level(src, "trace_evidence_chain session query failed")

    def test_evidence_session_exc_info(self):
        src = (SRC / "governance/mcp_tools/traceability.py").read_text()
        _check_exc_info(src, "trace_evidence_chain session query failed")

    def test_bug_markers_present(self):
        src = (SRC / "governance/mcp_tools/traceability.py").read_text()
        for i in range(1, 5):
            assert f"BUG-416-TRC-00{i}" in src, f"Missing BUG-416-TRC-00{i}"


# ── BUG-416-MEM-001..003: memory_tiers.py debug→warning + exc_info ───

class TestMemoryTiersLogLevel:
    def test_chromadb_save_warning_level(self):
        src = (SRC / "governance/mcp_tools/memory_tiers.py").read_text()
        _check_warning_level(src, "ChromaDB save failed, falling back to L1")

    def test_chromadb_save_exc_info(self):
        src = (SRC / "governance/mcp_tools/memory_tiers.py").read_text()
        _check_exc_info(src, "ChromaDB save failed, falling back to L1")

    def test_chromadb_recall_warning_level(self):
        src = (SRC / "governance/mcp_tools/memory_tiers.py").read_text()
        _check_warning_level(src, "ChromaDB recall failed")

    def test_chromadb_recall_exc_info(self):
        src = (SRC / "governance/mcp_tools/memory_tiers.py").read_text()
        _check_exc_info(src, "ChromaDB recall failed")

    def test_audit_recall_warning_level(self):
        src = (SRC / "governance/mcp_tools/memory_tiers.py").read_text()
        _check_warning_level(src, "Audit recall failed")

    def test_audit_recall_exc_info(self):
        src = (SRC / "governance/mcp_tools/memory_tiers.py").read_text()
        _check_exc_info(src, "Audit recall failed")

    def test_bug_markers_present(self):
        src = (SRC / "governance/mcp_tools/memory_tiers.py").read_text()
        for i in range(1, 4):
            assert f"BUG-416-MEM-00{i}" in src, f"Missing BUG-416-MEM-00{i}"


# ── BUG-417-TRK-001: tracker.py bind ValueError + log warning ────────

class TestTrackerPhaseWarning:
    def test_phase_warning_exc_info(self):
        src = (SRC / "governance/dsm/tracker.py").read_text()
        _check_exc_info(src, "unrecognised phase value")

    def test_phase_warning_level(self):
        src = (SRC / "governance/dsm/tracker.py").read_text()
        # Find the logger call (not the comment line)
        idx = src.index("DSMTracker: unrecognised phase value")
        line_start = src.rindex("\n", 0, idx) + 1
        line_end = src.index("\n", idx)
        line = src[line_start:line_end]
        assert "logger.warning" in line, f"Expected logger.warning in: {line.strip()}"

    def test_bug_marker_present(self):
        src = (SRC / "governance/dsm/tracker.py").read_text()
        assert "BUG-417-TRK-001" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch417Imports:
    def test_sessions_crud_importable(self):
        import governance.routes.sessions.crud
        assert governance.routes.sessions.crud is not None

    def test_sessions_relations_importable(self):
        import governance.routes.sessions.relations
        assert governance.routes.sessions.relations is not None

    def test_cc_session_scanner_importable(self):
        import governance.services.cc_session_scanner
        assert governance.services.cc_session_scanner is not None

    def test_ingestion_orchestrator_importable(self):
        import governance.services.ingestion_orchestrator
        assert governance.services.ingestion_orchestrator is not None

    def test_traceability_importable(self):
        import governance.mcp_tools.traceability
        assert governance.mcp_tools.traceability is not None

    def test_memory_tiers_importable(self):
        import governance.mcp_tools.memory_tiers
        assert governance.mcp_tools.memory_tiers is not None

    def test_tracker_importable(self):
        import governance.dsm.tracker
        assert governance.dsm.tracker is not None
