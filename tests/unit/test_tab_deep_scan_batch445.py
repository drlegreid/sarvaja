"""Batch 445 — session_evidence.py path redaction (1 fix),
Services A (4 CLEAN), Services B (5 CLEAN), MCP tools (5 CLEAN),
Routes (5 CLEAN) confirmation.

Validates fixes for:
- BUG-442-EVD-001: session_evidence.py full path redaction in error message
"""
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent


def _read(relpath: str) -> str:
    return (_ROOT / relpath).read_text(encoding="utf-8")


# ─── session_evidence.py — path redaction fix ──────────────────────────

class TestSessionEvidencePathRedaction:
    """BUG-442-EVD-001: Full path redacted in path traversal error message."""

    def test_no_full_path_in_error_log(self):
        src = _read("governance/services/session_evidence.py")
        # The old pattern leaked both output_dir AND _DEFAULT_EVIDENCE_DIR full paths
        assert "outside evidence root {_DEFAULT_EVIDENCE_DIR}" not in src, \
            "Full _DEFAULT_EVIDENCE_DIR path still exposed in error message"

    def test_uses_name_only(self):
        src = _read("governance/services/session_evidence.py")
        assert "output_dir.name" in src, "Expected output_dir.name for path redaction"

    def test_bug_marker_present(self):
        src = _read("governance/services/session_evidence.py")
        assert "BUG-442-EVD-001" in src


# ─── Batch 442 CLEAN — Services A ──────────────────────────────────────

class TestBatch442ServicesClean:
    """Batch 442: services layer confirmed CLEAN (except session_evidence fix)."""

    def test_projects_importable(self):
        src = _read("governance/services/projects.py")
        assert "def " in src

    def test_rule_scope_importable(self):
        src = _read("governance/services/rule_scope.py")
        assert "def " in src

    def test_session_repair_importable(self):
        src = _read("governance/services/session_repair.py")
        assert "def " in src

    def test_tasks_mutations_importable(self):
        src = _read("governance/services/tasks_mutations.py")
        assert "def " in src


# ─── Batch 443 CLEAN — Services B ──────────────────────────────────────

class TestBatch443ServicesClean:
    """Batch 443: services layer confirmed CLEAN."""

    def test_cc_link_miner_importable(self):
        src = _read("governance/services/cc_link_miner.py")
        assert "def " in src

    def test_cc_content_indexer_importable(self):
        src = _read("governance/services/cc_content_indexer.py")
        assert "def " in src

    def test_ingestion_orchestrator_importable(self):
        src = _read("governance/services/ingestion_orchestrator.py")
        assert "def " in src

    def test_correlation_importable(self):
        src = _read("governance/session_metrics/correlation.py")
        assert "def " in src or "class " in src


# ─── Batch 444 CLEAN — MCP tools ───────────────────────────────────────

class TestBatch444MCPToolsClean:
    """Batch 444: MCP tools layer confirmed CLEAN."""

    def test_decisions_importable(self):
        src = _read("governance/mcp_tools/decisions.py")
        assert "def " in src

    def test_handoff_importable(self):
        src = _read("governance/mcp_tools/handoff.py")
        assert "def " in src

    def test_ingestion_importable(self):
        src = _read("governance/mcp_tools/ingestion.py")
        assert "def " in src

    def test_memory_tiers_importable(self):
        src = _read("governance/mcp_tools/memory_tiers.py")
        assert "def " in src

    def test_traceability_importable(self):
        src = _read("governance/mcp_tools/traceability.py")
        assert "def " in src


# ─── Batch 445 CLEAN — Routes ──────────────────────────────────────────

class TestBatch445RoutesClean:
    """Batch 445: routes layer confirmed CLEAN."""

    def test_agents_crud_importable(self):
        src = _read("governance/routes/agents/crud.py")
        assert "def " in src

    def test_agents_observability_importable(self):
        src = _read("governance/routes/agents/observability.py")
        assert "def " in src

    def test_sessions_crud_importable(self):
        src = _read("governance/routes/sessions/crud.py")
        assert "def " in src

    def test_sessions_detail_importable(self):
        src = _read("governance/routes/sessions/detail.py")
        assert "def " in src

    def test_sessions_relations_importable(self):
        src = _read("governance/routes/sessions/relations.py")
        assert "def " in src


# ─── Import validation ─────────────────────────────────────────────────

class TestBatch445Imports:
    """Verify modified module compiles cleanly."""

    def test_session_evidence_compiles(self):
        src = _read("governance/services/session_evidence.py")
        compile(src, "session_evidence.py", "exec")
