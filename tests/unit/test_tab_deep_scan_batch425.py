"""Batch 425 — tasks_crud_verify exc_info, tasks/crud exc_info,
chat endpoints exc_info + log upgrades, session_bridge exc_info,
embedding pipeline exc_info, projects log upgrades tests.

Validates fixes for:
- BUG-422-VER-001: tasks_crud_verify.py JSONDecodeError exc_info
- BUG-423-TCR-001: tasks/crud.py create_task conflict exc_info
- BUG-424-CHT-001..005: chat/endpoints.py exc_info + debug→warning
- BUG-424-BRG-001..006: session_bridge.py exc_info + debug→warning
- BUG-424-PIP-001..002: embedding pipeline exc_info
- BUG-425-PRJ-001..005: projects.py debug→warning + exc_info
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


def _check_exc_info(src, fragment):
    """Find logger line containing fragment, verify exc_info=True."""
    idx = src.index(fragment)
    block = src[idx:idx + 300]
    assert "exc_info=True" in block, f"Missing exc_info=True near: {fragment}"


def _check_warning_level(src, fragment):
    """Verify line containing fragment uses logger.warning (not debug)."""
    idx = src.index(fragment)
    line_start = src.rindex("\n", 0, idx) + 1
    line_end = src.index("\n", idx)
    line = src[line_start:line_end]
    assert "logger.warning" in line, f"Expected logger.warning in: {line.strip()}"


# ── BUG-422-VER-001: tasks_crud_verify.py JSONDecodeError exc_info ────

class TestTasksCrudVerifyExcInfo:
    def test_json_decode_exc_info(self):
        src = (SRC / "governance/mcp_tools/tasks_crud_verify.py").read_text()
        _check_exc_info(src, "session_sync_todos invalid JSON")

    def test_bug_marker_present(self):
        src = (SRC / "governance/mcp_tools/tasks_crud_verify.py").read_text()
        assert "BUG-422-VER-001" in src


# ── BUG-423-TCR-001: tasks/crud.py create_task conflict exc_info ──────

class TestTasksCrudRouteExcInfo:
    def test_create_task_conflict_exc_info(self):
        src = (SRC / "governance/routes/tasks/crud.py").read_text()
        _check_exc_info(src, "create_task conflict")

    def test_bug_marker_present(self):
        src = (SRC / "governance/routes/tasks/crud.py").read_text()
        assert "BUG-423-TCR-001" in src


# ── BUG-424-CHT-001..005: chat/endpoints.py exc_info + log upgrades ───

class TestChatEndpointsExcInfo:
    def test_preload_context_exc_info(self):
        src = (SRC / "governance/routes/chat/endpoints.py").read_text()
        _check_exc_info(src, "Failed to preload context")

    def test_start_governance_exc_info(self):
        src = (SRC / "governance/routes/chat/endpoints.py").read_text()
        _check_exc_info(src, "Failed to start governance session")

    def test_record_tool_call_warning(self):
        src = (SRC / "governance/routes/chat/endpoints.py").read_text()
        _check_warning_level(src, "Failed to record chat tool call")

    def test_record_tool_call_exc_info(self):
        src = (SRC / "governance/routes/chat/endpoints.py").read_text()
        _check_exc_info(src, "Failed to record chat tool call")

    def test_record_thought_warning(self):
        src = (SRC / "governance/routes/chat/endpoints.py").read_text()
        _check_warning_level(src, "Failed to record chat thought")

    def test_record_thought_exc_info(self):
        src = (SRC / "governance/routes/chat/endpoints.py").read_text()
        _check_exc_info(src, "Failed to record chat thought")

    def test_end_governance_warning(self):
        src = (SRC / "governance/routes/chat/endpoints.py").read_text()
        _check_warning_level(src, "Failed to end governance session")

    def test_end_governance_exc_info(self):
        src = (SRC / "governance/routes/chat/endpoints.py").read_text()
        _check_exc_info(src, "Failed to end governance session")

    def test_bug_markers_present(self):
        src = (SRC / "governance/routes/chat/endpoints.py").read_text()
        for i in range(1, 6):
            assert f"BUG-424-CHT-00{i}" in src, f"Missing BUG-424-CHT-00{i}"


# ── BUG-424-BRG-001..006: session_bridge.py exc_info additions ────────

class TestSessionBridgeExcInfo:
    def test_typedb_create_exc_info(self):
        src = (SRC / "governance/routes/chat/session_bridge.py").read_text()
        _check_exc_info(src, "TypeDB session create failed")

    def test_typedb_end_exc_info(self):
        src = (SRC / "governance/routes/chat/session_bridge.py").read_text()
        _check_exc_info(src, "TypeDB session end failed")

    def test_generate_session_log_exc_info(self):
        src = (SRC / "governance/routes/chat/session_bridge.py").read_text()
        _check_exc_info(src, "Failed to generate session log")

    def test_evidence_linking_exc_info(self):
        src = (SRC / "governance/routes/chat/session_bridge.py").read_text()
        _check_exc_info(src, "Evidence linking failed for")

    def test_chromadb_sync_exc_info(self):
        src = (SRC / "governance/routes/chat/session_bridge.py").read_text()
        _check_exc_info(src, "Failed to sync session to ChromaDB")

    def test_post_session_validation_warning(self):
        src = (SRC / "governance/routes/chat/session_bridge.py").read_text()
        _check_warning_level(src, "Post-session validation failed")

    def test_post_session_validation_exc_info(self):
        src = (SRC / "governance/routes/chat/session_bridge.py").read_text()
        _check_exc_info(src, "Post-session validation failed")

    def test_bug_markers_present(self):
        src = (SRC / "governance/routes/chat/session_bridge.py").read_text()
        for i in range(1, 7):
            assert f"BUG-424-BRG-00{i}" in src, f"Missing BUG-424-BRG-00{i}"


# ── BUG-424-PIP-001..002: embedding pipeline exc_info ─────────────────

class TestEmbeddingPipelineExcInfo:
    def test_json_parse_exc_info(self):
        src = (SRC / "governance/embedding_pipeline/pipeline.py").read_text()
        _check_exc_info(src, "Failed to parse session")

    def test_fetch_session_exc_info(self):
        src = (SRC / "governance/embedding_pipeline/pipeline.py").read_text()
        _check_exc_info(src, "Failed to fetch session")

    def test_bug_markers_present(self):
        src = (SRC / "governance/embedding_pipeline/pipeline.py").read_text()
        assert "BUG-424-PIP-001" in src
        assert "BUG-424-PIP-002" in src


# ── BUG-425-PRJ-001..005: projects.py debug→warning + exc_info ────────

class TestProjectsLogUpgrades:
    def test_client_unavailable_warning(self):
        src = (SRC / "governance/services/projects.py").read_text()
        _check_warning_level(src, "TypeDB client unavailable")

    def test_client_unavailable_exc_info(self):
        src = (SRC / "governance/services/projects.py").read_text()
        _check_exc_info(src, "TypeDB client unavailable")

    def test_session_count_enrichment_get_warning(self):
        src = (SRC / "governance/services/projects.py").read_text()
        # get_project path — find first occurrence
        idx = src.index("Session count enrichment failed for")
        block = src[idx:idx + 100]
        assert "exc_info=True" in block

    def test_plan_count_enrichment_get_warning(self):
        src = (SRC / "governance/services/projects.py").read_text()
        idx = src.index("Plan count enrichment failed for")
        block = src[idx:idx + 100]
        assert "exc_info=True" in block

    def test_session_count_enrichment_list_warning(self):
        src = (SRC / "governance/services/projects.py").read_text()
        # list_projects path — find second occurrence
        first_idx = src.index("Session count enrichment failed for")
        second_idx = src.index("Session count enrichment failed for", first_idx + 1)
        block = src[second_idx:second_idx + 100]
        assert "exc_info=True" in block

    def test_plan_count_enrichment_list_warning(self):
        src = (SRC / "governance/services/projects.py").read_text()
        first_idx = src.index("Plan count enrichment failed for")
        second_idx = src.index("Plan count enrichment failed for", first_idx + 1)
        block = src[second_idx:second_idx + 100]
        assert "exc_info=True" in block

    def test_no_debug_loggers_in_except_blocks(self):
        """Verify no logger.debug remains in except blocks of projects.py."""
        src = (SRC / "governance/services/projects.py").read_text()
        # All previously debug loggers should now be warning
        assert "logger.debug(f\"TypeDB client unavailable" not in src
        assert "logger.debug(f\"Session count enrichment" not in src
        assert "logger.debug(f\"Plan count enrichment" not in src

    def test_bug_markers_present(self):
        src = (SRC / "governance/services/projects.py").read_text()
        for i in range(1, 6):
            assert f"BUG-425-PRJ-00{i}" in src, f"Missing BUG-425-PRJ-00{i}"


# ── Module import defense tests ──────────────────────────────────────

class TestBatch425Imports:
    def test_tasks_crud_verify_importable(self):
        import governance.mcp_tools.tasks_crud_verify
        assert governance.mcp_tools.tasks_crud_verify is not None

    def test_tasks_crud_route_importable(self):
        import governance.routes.tasks.crud
        assert governance.routes.tasks.crud is not None

    def test_chat_endpoints_importable(self):
        import governance.routes.chat.endpoints
        assert governance.routes.chat.endpoints is not None

    def test_session_bridge_importable(self):
        import governance.routes.chat.session_bridge
        assert governance.routes.chat.session_bridge is not None

    def test_embedding_pipeline_importable(self):
        import governance.embedding_pipeline.pipeline
        assert governance.embedding_pipeline.pipeline is not None

    def test_projects_importable(self):
        import governance.services.projects
        assert governance.services.projects is not None
