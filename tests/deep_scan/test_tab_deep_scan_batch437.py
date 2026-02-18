"""Batch 437 — agents.py 7x exc_info additions, sessions.py 1x exc_info,
sessions_lifecycle.py 1x exc_info, MCP tools A+B CLEAN confirmation.

Validates fixes for:
- BUG-436-AGT-001: agents.py persist_agent_status exc_info
- BUG-436-AGT-002: agents.py create_agent TypeDB exc_info
- BUG-436-AGT-003: agents.py list_agents TypeDB exc_info
- BUG-436-AGT-004: agents.py get_agent TypeDB exc_info
- BUG-436-AGT-005: agents.py delete_agent TypeDB exc_info
- BUG-436-AGT-006: agents.py toggle_agent_status TypeDB exc_info
- BUG-436-SES-001: sessions.py status sync exc_info
- BUG-436-SLC-001: sessions_lifecycle.py evidence link exc_info

Batch 434 (MCP tools A): All 5 CLEAN
Batch 435 (MCP tools B): All 5 CLEAN
Batch 437 (Services B): All 5 CLEAN
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


def _check_exc_info(src, fragment):
    """Find logger line containing fragment, verify exc_info=True."""
    idx = src.index(fragment)
    block = src[idx:idx + 300]
    assert "exc_info=True" in block, f"Missing exc_info=True near: {fragment}"


# ── BUG-436-AGT-001: persist_agent_status exc_info ─────────────────────

class TestAgentsPersistStatusExcInfo:
    def test_persist_status_exc_info(self):
        src = (SRC / "governance/services/agents.py").read_text()
        _check_exc_info(src, "Failed to persist agent status for")

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/agents.py").read_text()
        assert "BUG-436-AGT-001" in src


# ── BUG-436-AGT-002: create_agent TypeDB exc_info ──────────────────────

class TestAgentsCreateExcInfo:
    def test_create_agent_exc_info(self):
        src = (SRC / "governance/services/agents.py").read_text()
        _check_exc_info(src, "TypeDB agent create failed for")

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/agents.py").read_text()
        assert "BUG-436-AGT-002" in src


# ── BUG-436-AGT-003: list_agents TypeDB exc_info ───────────────────────

class TestAgentsListExcInfo:
    def test_list_agents_exc_info(self):
        src = (SRC / "governance/services/agents.py").read_text()
        _check_exc_info(src, "TypeDB agents query failed, using fallback")

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/agents.py").read_text()
        assert "BUG-436-AGT-003" in src


# ── BUG-436-AGT-004: get_agent TypeDB exc_info ─────────────────────────

class TestAgentsGetExcInfo:
    def test_get_agent_exc_info(self):
        src = (SRC / "governance/services/agents.py").read_text()
        _check_exc_info(src, "TypeDB agent query failed, using fallback")

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/agents.py").read_text()
        assert "BUG-436-AGT-004" in src


# ── BUG-436-AGT-005: delete_agent TypeDB exc_info ──────────────────────

class TestAgentsDeleteExcInfo:
    def test_delete_agent_exc_info(self):
        src = (SRC / "governance/services/agents.py").read_text()
        _check_exc_info(src, "TypeDB delete failed for agent")

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/agents.py").read_text()
        assert "BUG-436-AGT-005" in src


# ── BUG-436-AGT-006: toggle_agent_status TypeDB exc_info ───────────────

class TestAgentsToggleExcInfo:
    def test_toggle_exc_info(self):
        src = (SRC / "governance/services/agents.py").read_text()
        _check_exc_info(src, "TypeDB toggle_agent_status failed for")

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/agents.py").read_text()
        assert "BUG-436-AGT-006" in src


# ── BUG-436-SES-001: sessions.py status sync exc_info ──────────────────

class TestSessionsStatusSyncExcInfo:
    def test_status_sync_exc_info(self):
        src = (SRC / "governance/services/sessions.py").read_text()
        _check_exc_info(src, "Status sync failed for")

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/sessions.py").read_text()
        assert "BUG-436-SES-001" in src


# ── BUG-436-SLC-001: sessions_lifecycle.py evidence link exc_info ──────

class TestSessionsLifecycleEvidenceLinkExcInfo:
    def test_evidence_link_exc_info(self):
        src = (SRC / "governance/services/sessions_lifecycle.py").read_text()
        _check_exc_info(src, "TypeDB evidence link failed")

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/sessions_lifecycle.py").read_text()
        assert "BUG-436-SLC-001" in src


# ── Batch 434-435 CLEAN confirmation (MCP tools) ──────────────────────

class TestBatch434MCPToolsClean:
    def test_rules_crud_hardened(self):
        src = (SRC / "governance/mcp_tools/rules_crud.py").read_text()
        assert "exc_info=True" in src

    def test_rules_query_hardened(self):
        src = (SRC / "governance/mcp_tools/rules_query.py").read_text()
        assert "exc_info=True" in src

    def test_trust_hardened(self):
        src = (SRC / "governance/mcp_tools/trust.py").read_text()
        assert "exc_info=True" in src


class TestBatch435MCPToolsClean:
    def test_tasks_crud_hardened(self):
        src = (SRC / "governance/mcp_tools/tasks_crud.py").read_text()
        assert "exc_info=True" in src

    def test_traceability_hardened(self):
        src = (SRC / "governance/mcp_tools/traceability.py").read_text()
        assert "exc_info=True" in src


# ── Module import defense tests ─────────────────────────────────────────

class TestBatch437Imports:
    def test_agents_importable(self):
        import governance.services.agents
        assert governance.services.agents is not None

    def test_sessions_importable(self):
        import governance.services.sessions
        assert governance.services.sessions is not None

    def test_sessions_lifecycle_importable(self):
        import governance.services.sessions_lifecycle
        assert governance.services.sessions_lifecycle is not None

    def test_ingestion_orchestrator_importable(self):
        import governance.services.ingestion_orchestrator
        assert governance.services.ingestion_orchestrator is not None

    def test_ingestion_checkpoint_importable(self):
        import governance.services.ingestion_checkpoint
        assert governance.services.ingestion_checkpoint is not None
