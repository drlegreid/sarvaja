"""Batch 413 — DSM state sanitization, stores exc_info, TypeDB query exc_info,
vector store exc_info, embedding pipeline exc_info, parser exc_info tests.

Validates fixes for:
- BUG-410-NOD-001..003: nodes_analysis.py str(e)→type(e).__name__ + exc_info
- BUG-410-DSM-001: dsm/langgraph/graph.py str(e)→type(e).__name__ + exc_info
- BUG-411-RTY-001: stores/retry.py exc_info on final failure
- BUG-411-TDB-001..004: stores/typedb_access.py exc_info additions
- BUG-412-TCR-001..003: typedb/queries/tasks/crud.py exc_info additions
- BUG-412-RCR-001: typedb/queries/rules/crud.py exc_info on archive
- BUG-412-INF-001: typedb/queries/rules/inference.py exc_info on dependency
- BUG-413-VS-001..005: vector_store/store.py exc_info additions
- BUG-413-EP-001..003: embedding_pipeline/pipeline.py exc_info additions
- BUG-413-PAR-001..002: session_metrics/parser.py exc_info additions
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


def _check_exc_info(src, fragment, level="error"):
    """Find logger line containing fragment, verify exc_info=True."""
    idx = src.index(fragment)
    line_end = src.index("\n", idx)
    line_start = src.rindex("\n", 0, idx) + 1
    line = src[line_start:line_end]
    assert "exc_info=True" in line, f"Missing exc_info=True in: {line.strip()}"


def _check_no_str_e_in_block(src, start_marker, end_marker="\ndef "):
    """Verify no str(e) in a code block."""
    idx = src.index(start_marker)
    end = src.find(end_marker, idx + 10)
    block = src[idx:end] if end != -1 else src[idx:]
    assert "str(e)" not in block, f"str(e) found in block starting at {start_marker}"


# ── BUG-410-NOD-001..003: nodes_analysis.py str(e) sanitization ──────

class TestNodesAnalysisSanitization:
    def test_audit_no_str_e(self):
        src = (SRC / "governance/dsm/langgraph/nodes_analysis.py").read_text()
        _check_no_str_e_in_block(src, "def audit_node")

    def test_hypothesize_no_str_e(self):
        src = (SRC / "governance/dsm/langgraph/nodes_analysis.py").read_text()
        _check_no_str_e_in_block(src, "def hypothesize_node")

    def test_measure_no_str_e(self):
        src = (SRC / "governance/dsm/langgraph/nodes_analysis.py").read_text()
        _check_no_str_e_in_block(src, "def measure_node")

    def test_audit_exc_info(self):
        src = (SRC / "governance/dsm/langgraph/nodes_analysis.py").read_text()
        _check_exc_info(src, "AUDIT phase failed")

    def test_hypothesize_exc_info(self):
        src = (SRC / "governance/dsm/langgraph/nodes_analysis.py").read_text()
        _check_exc_info(src, "HYPOTHESIZE phase failed")

    def test_measure_exc_info(self):
        src = (SRC / "governance/dsm/langgraph/nodes_analysis.py").read_text()
        _check_exc_info(src, "MEASURE phase failed")

    def test_bug_markers_present(self):
        src = (SRC / "governance/dsm/langgraph/nodes_analysis.py").read_text()
        for i in range(1, 4):
            assert f"BUG-410-NOD-00{i}" in src, f"Missing BUG-410-NOD-00{i}"


# ── BUG-410-DSM-001: graph.py str(e) sanitization ────────────────────

class TestDSMGraphSanitization:
    def test_graph_node_failure_no_str_e(self):
        src = (SRC / "governance/dsm/langgraph/graph.py").read_text()
        # Find the error_message assignment near "Node" failure
        idx = src.index("error_message")
        line_end = src.index("\n", idx)
        line = src[idx:line_end]
        assert "str(e)" not in line, f"str(e) in error_message: {line}"
        assert "type(e).__name__" in line

    def test_graph_failure_exc_info(self):
        src = (SRC / "governance/dsm/langgraph/graph.py").read_text()
        _check_exc_info(src, "Node {node_name} failed")

    def test_bug_marker_present(self):
        src = (SRC / "governance/dsm/langgraph/graph.py").read_text()
        assert "BUG-410-DSM-001" in src


# ── BUG-411-RTY-001: retry.py exc_info on final failure ──────────────

class TestRetryExcInfo:
    def test_final_failure_exc_info(self):
        src = (SRC / "governance/stores/retry.py").read_text()
        # Multi-line logger call: check exc_info within 3 lines of fragment
        idx = src.index("after {max_attempts} attempts")
        block = src[idx:idx + 200]
        assert "exc_info=True" in block, f"Missing exc_info=True near: {block[:80]}"

    def test_bug_marker_present(self):
        src = (SRC / "governance/stores/retry.py").read_text()
        assert "BUG-411-RTY-001" in src


# ── BUG-411-TDB-001..004: typedb_access.py exc_info additions ────────

class TestTypeDBAccessExcInfo:
    def test_task_query_exc_info(self):
        src = (SRC / "governance/stores/typedb_access.py").read_text()
        _check_exc_info(src, "TypeDB task query failed", level="warning")

    def test_task_get_exc_info(self):
        src = (SRC / "governance/stores/typedb_access.py").read_text()
        _check_exc_info(src, "TypeDB task get failed", level="warning")

    def test_session_query_exc_info(self):
        src = (SRC / "governance/stores/typedb_access.py").read_text()
        _check_exc_info(src, "TypeDB session query failed", level="warning")

    def test_session_get_exc_info(self):
        src = (SRC / "governance/stores/typedb_access.py").read_text()
        _check_exc_info(src, "TypeDB session get failed", level="warning")

    def test_bug_markers_present(self):
        src = (SRC / "governance/stores/typedb_access.py").read_text()
        for i in range(1, 5):
            assert f"BUG-411-TDB-00{i}" in src, f"Missing BUG-411-TDB-00{i}"


# ── BUG-412-TCR-001..003: TypeDB tasks/crud.py exc_info additions ────

class TestTypeDBTasksCrudExcInfo:
    def test_insert_exc_info(self):
        src = (SRC / "governance/typedb/queries/tasks/crud.py").read_text()
        _check_exc_info(src, "Failed to insert task")

    def test_update_exc_info(self):
        src = (SRC / "governance/typedb/queries/tasks/crud.py").read_text()
        _check_exc_info(src, "Failed to update task")

    def test_delete_exc_info(self):
        src = (SRC / "governance/typedb/queries/tasks/crud.py").read_text()
        _check_exc_info(src, "Failed to delete task")

    def test_bug_markers_present(self):
        src = (SRC / "governance/typedb/queries/tasks/crud.py").read_text()
        for i in range(1, 4):
            assert f"BUG-412-TCR-00{i}" in src, f"Missing BUG-412-TCR-00{i}"


# ── BUG-412-RCR-001: rules/crud.py archive exc_info ──────────────────

class TestTypeDBRulesCrudExcInfo:
    def test_archive_warning_exc_info(self):
        src = (SRC / "governance/typedb/queries/rules/crud.py").read_text()
        _check_exc_info(src, "Could not archive rule", level="warning")

    def test_bug_marker_present(self):
        src = (SRC / "governance/typedb/queries/rules/crud.py").read_text()
        assert "BUG-412-RCR-001" in src


# ── BUG-412-INF-001: rules/inference.py dependency exc_info ───────────

class TestTypeDBInferenceExcInfo:
    def test_dependency_warning_exc_info(self):
        src = (SRC / "governance/typedb/queries/rules/inference.py").read_text()
        _check_exc_info(src, "Failed to create dependency", level="warning")

    def test_bug_marker_present(self):
        src = (SRC / "governance/typedb/queries/rules/inference.py").read_text()
        assert "BUG-412-INF-001" in src


# ── BUG-413-VS-001..005: vector_store/store.py exc_info additions ────

class TestVectorStoreExcInfo:
    def test_connect_exc_info(self):
        src = (SRC / "governance/vector_store/store.py").read_text()
        _check_exc_info(src, "Failed to connect to TypeDB")

    def test_insert_exc_info(self):
        src = (SRC / "governance/vector_store/store.py").read_text()
        _check_exc_info(src, "Insert failed")

    def test_insert_batch_exc_info(self):
        src = (SRC / "governance/vector_store/store.py").read_text()
        _check_exc_info(src, "Failed to insert {doc.id}", level="warning")

    def test_parse_vector_exc_info(self):
        src = (SRC / "governance/vector_store/store.py").read_text()
        _check_exc_info(src, "Failed to parse vector", level="warning")

    def test_delete_exc_info(self):
        src = (SRC / "governance/vector_store/store.py").read_text()
        _check_exc_info(src, "Delete failed")

    def test_bug_markers_present(self):
        src = (SRC / "governance/vector_store/store.py").read_text()
        for i in range(1, 6):
            assert f"BUG-413-VS-00{i}" in src, f"Missing BUG-413-VS-00{i}"


# ── BUG-413-EP-001..003: embedding_pipeline/pipeline.py exc_info ─────

class TestEmbeddingPipelineExcInfo:
    def test_embed_rules_exc_info(self):
        src = (SRC / "governance/embedding_pipeline/pipeline.py").read_text()
        _check_exc_info(src, "Error embedding rules")

    def test_embed_decisions_exc_info(self):
        src = (SRC / "governance/embedding_pipeline/pipeline.py").read_text()
        _check_exc_info(src, "Error embedding decisions")

    def test_embed_sessions_exc_info(self):
        src = (SRC / "governance/embedding_pipeline/pipeline.py").read_text()
        _check_exc_info(src, "Error embedding sessions")

    def test_bug_markers_present(self):
        src = (SRC / "governance/embedding_pipeline/pipeline.py").read_text()
        for i in range(1, 4):
            assert f"BUG-413-EP-00{i}" in src, f"Missing BUG-413-EP-00{i}"


# ── BUG-413-PAR-001..002: parser.py exc_info additions ───────────────

class TestParserExcInfo:
    def test_parse_log_file_exc_info(self):
        src = (SRC / "governance/session_metrics/parser.py").read_text()
        assert "BUG-413-PAR-001" in src

    def test_parse_log_file_extended_exc_info(self):
        src = (SRC / "governance/session_metrics/parser.py").read_text()
        assert "BUG-413-PAR-002" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch413Imports:
    def test_nodes_analysis_importable(self):
        import governance.dsm.langgraph.nodes_analysis
        assert governance.dsm.langgraph.nodes_analysis is not None

    def test_retry_importable(self):
        import governance.stores.retry
        assert governance.stores.retry is not None

    def test_typedb_access_importable(self):
        import governance.stores.typedb_access
        assert governance.stores.typedb_access is not None

    def test_vector_store_importable(self):
        import governance.vector_store.store
        assert governance.vector_store.store is not None

    def test_embedding_pipeline_importable(self):
        import governance.embedding_pipeline.pipeline
        assert governance.embedding_pipeline.pipeline is not None

    def test_parser_importable(self):
        import governance.session_metrics.parser
        assert governance.session_metrics.parser is not None
