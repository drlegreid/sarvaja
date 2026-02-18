"""Batch 240 — MCP tools layer defense tests.

Validates fixes for:
- BUG-240-HND-001: Path traversal sanitization in handoff_get
- BUG-240-DEC-001: Socket leak prevention in governance_health
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-240-HND-001: Path traversal in handoff_get ──────────────────

class TestHandoffGetSanitization:
    """handoff_get must sanitize inputs like handoff_complete."""

    def test_handoff_get_has_re_sub(self):
        src = (SRC / "governance/mcp_tools/handoff.py").read_text()
        idx = src.index("def handoff_get")
        block = src[idx:idx + 500]
        assert "re.sub(" in block

    def test_handoff_get_has_safe_task(self):
        src = (SRC / "governance/mcp_tools/handoff.py").read_text()
        idx = src.index("def handoff_get")
        block = src[idx:idx + 500]
        assert "safe_task" in block

    def test_handoff_get_has_safe_from(self):
        src = (SRC / "governance/mcp_tools/handoff.py").read_text()
        idx = src.index("def handoff_get")
        block = src[idx:idx + 500]
        assert "safe_from" in block

    def test_handoff_get_has_safe_to(self):
        src = (SRC / "governance/mcp_tools/handoff.py").read_text()
        idx = src.index("def handoff_get")
        block = src[idx:idx + 500]
        assert "safe_to" in block

    def test_handoff_get_no_raw_task_id_in_filename(self):
        """Filename must use safe_task, not raw task_id."""
        src = (SRC / "governance/mcp_tools/handoff.py").read_text()
        idx = src.index("def handoff_get")
        block = src[idx:idx + 800]
        # Find the f-string filename line — should use safe_task not task_id
        assert "HANDOFF-{safe_task}" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/mcp_tools/handoff.py").read_text()
        assert "BUG-240-HND-001" in src


# ── BUG-240-DEC-001: Socket leak in governance_health ────────────────

class TestSocketLeakPrevention:
    """Socket close must be in try/finally block."""

    def test_socket_in_try_finally(self):
        src = (SRC / "governance/mcp_tools/decisions.py").read_text()
        idx = src.index("socket.socket(socket.AF_INET")
        block = src[idx:idx + 400]
        assert "finally:" in block
        assert "sock.close()" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/mcp_tools/decisions.py").read_text()
        assert "BUG-240-DEC-001" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch240Imports:
    def test_handoff_importable(self):
        import governance.mcp_tools.handoff
        assert governance.mcp_tools.handoff is not None

    def test_decisions_importable(self):
        import governance.mcp_tools.decisions
        assert governance.mcp_tools.decisions is not None

    def test_common_importable(self):
        import governance.mcp_tools.common
        assert governance.mcp_tools.common is not None

    def test_agents_importable(self):
        import governance.mcp_tools.agents
        assert governance.mcp_tools.agents is not None

    def test_rules_crud_importable(self):
        import governance.mcp_tools.rules_crud
        assert governance.mcp_tools.rules_crud is not None

    def test_rules_query_importable(self):
        import governance.mcp_tools.rules_query
        assert governance.mcp_tools.rules_query is not None

    def test_tasks_crud_importable(self):
        import governance.mcp_tools.tasks_crud
        assert governance.mcp_tools.tasks_crud is not None

    def test_sessions_linking_importable(self):
        import governance.mcp_tools.sessions_linking
        assert governance.mcp_tools.sessions_linking is not None

    def test_ingestion_importable(self):
        import governance.mcp_tools.ingestion
        assert governance.mcp_tools.ingestion is not None

    def test_memory_tiers_importable(self):
        import governance.mcp_tools.memory_tiers
        assert governance.mcp_tools.memory_tiers is not None

    def test_traceability_importable(self):
        import governance.mcp_tools.traceability
        assert governance.mcp_tools.traceability is not None

    def test_trust_importable(self):
        import governance.mcp_tools.trust
        assert governance.mcp_tools.trust is not None

    def test_rules_archive_importable(self):
        import governance.mcp_tools.rules_archive
        assert governance.mcp_tools.rules_archive is not None
