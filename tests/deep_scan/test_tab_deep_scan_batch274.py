"""Batch 274-277 — Checkpoint race, path traversal guard, atomic metrics,
rules_crud guards, traceability logging, taxonomy_get handler, ingestion status.

Validates fixes for:
- BUG-274-CKPT-001: delete_checkpoint TOCTOU race → try/except pattern
- BUG-274-CKPT-002: _checkpoint_path resolve()+startswith() guard
- BUG-274-AGENT-001: Atomic metrics write via temp+replace
- BUG-276-RCRUD-001: rule_update empty update guard
- BUG-276-RCRUD-002: asdict(None) guard in rule_create applicability path
- BUG-276-TRACE-001: Silent exception swallowing → logger.debug
- BUG-276-TCRUD-001: taxonomy_get wrapped in try/except
- BUG-277-DETAIL-001: ingestion_status wrapped in try/except
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-274-CKPT-001: delete_checkpoint TOCTOU race ──────────────────

class TestDeleteCheckpointRace:
    """delete_checkpoint must use try/except, not if exists/unlink."""

    def test_no_exists_check(self):
        """Must NOT have if path.exists(): path.unlink() pattern."""
        src = (SRC / "governance/services/ingestion_checkpoint.py").read_text()
        idx = src.index("def delete_checkpoint")
        block = src[idx:idx + 600]
        # The old pattern should be gone
        assert "if path.exists():" not in block

    def test_uses_try_except(self):
        src = (SRC / "governance/services/ingestion_checkpoint.py").read_text()
        idx = src.index("def delete_checkpoint")
        block = src[idx:idx + 600]
        assert "try:" in block
        assert "path.unlink()" in block

    def test_catches_file_not_found(self):
        src = (SRC / "governance/services/ingestion_checkpoint.py").read_text()
        idx = src.index("def delete_checkpoint")
        block = src[idx:idx + 600]
        assert "FileNotFoundError" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/ingestion_checkpoint.py").read_text()
        assert "BUG-274-CKPT-001" in src


# ── BUG-274-CKPT-002: _checkpoint_path path traversal guard ──────────

class TestCheckpointPathTraversal:
    """_checkpoint_path must validate resolved path stays inside directory."""

    def test_resolve_guard_present(self):
        src = (SRC / "governance/services/ingestion_checkpoint.py").read_text()
        idx = src.index("def _checkpoint_path")
        block = src[idx:idx + 600]
        assert ".resolve()" in block

    def test_startswith_guard_present(self):
        src = (SRC / "governance/services/ingestion_checkpoint.py").read_text()
        idx = src.index("def _checkpoint_path")
        block = src[idx:idx + 600]
        assert "startswith" in block

    def test_raises_on_traversal(self):
        src = (SRC / "governance/services/ingestion_checkpoint.py").read_text()
        idx = src.index("def _checkpoint_path")
        block = src[idx:idx + 600]
        assert "ValueError" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/services/ingestion_checkpoint.py").read_text()
        assert "BUG-274-CKPT-002" in src


# ── BUG-274-AGENT-001: Atomic metrics write ──────────────────────────

class TestAtomicMetricsWrite:
    """_save_agent_metrics must use temp file + os.replace pattern."""

    def test_tempfile_import(self):
        src = (SRC / "governance/stores/agents.py").read_text()
        assert "import tempfile" in src

    def test_mkstemp_used(self):
        src = (SRC / "governance/stores/agents.py").read_text()
        idx = src.index("def _save_agent_metrics")
        block = src[idx:idx + 800]
        assert "mkstemp" in block

    def test_os_replace_used(self):
        src = (SRC / "governance/stores/agents.py").read_text()
        idx = src.index("def _save_agent_metrics")
        block = src[idx:idx + 800]
        assert "os.replace" in block

    def test_cleanup_on_failure(self):
        """Temp file cleaned up on write failure."""
        src = (SRC / "governance/stores/agents.py").read_text()
        idx = src.index("def _save_agent_metrics")
        block = src[idx:idx + 800]
        assert "os.unlink(temp_path)" in block

    def test_no_bare_truncating_write(self):
        """Must NOT have bare open(file, 'w') pattern."""
        src = (SRC / "governance/stores/agents.py").read_text()
        idx = src.index("def _save_agent_metrics")
        block = src[idx:idx + 800]
        assert 'open(_AGENT_METRICS_FILE, "w")' not in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/stores/agents.py").read_text()
        assert "BUG-274-AGENT-001" in src


# ── BUG-276-RCRUD-001: rule_update empty update guard ────────────────

class TestRuleUpdateEmptyGuard:
    """rule_update must reject calls with all-None params."""

    def test_any_guard_present(self):
        src = (SRC / "governance/mcp_tools/rules_crud.py").read_text()
        idx = src.index("def rule_update")
        block = src[idx:idx + 1500]
        assert "not any([" in block

    def test_error_message(self):
        src = (SRC / "governance/mcp_tools/rules_crud.py").read_text()
        idx = src.index("def rule_update")
        block = src[idx:idx + 1500]
        assert "No update fields provided" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/mcp_tools/rules_crud.py").read_text()
        assert "BUG-276-RCRUD-001" in src


# ── BUG-276-RCRUD-002: asdict(None) crash guard ─────────────────────

class TestRuleCreateAsdictGuard:
    """rule_create must guard against update_rule returning None."""

    def test_update_result_checked(self):
        src = (SRC / "governance/mcp_tools/rules_crud.py").read_text()
        idx = src.index("def rule_create")
        block = src[idx:idx + 2500]
        assert "if updated:" in block

    def test_no_bare_assignment(self):
        """Must NOT have bare 'rule = client.update_rule(...)' without check."""
        src = (SRC / "governance/mcp_tools/rules_crud.py").read_text()
        idx = src.index("def rule_create")
        block = src[idx:idx + 2500]
        # The old bare pattern should be gone
        assert "rule = client.update_rule(" not in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/mcp_tools/rules_crud.py").read_text()
        assert "BUG-276-RCRUD-002" in src


# ── BUG-276-TRACE-001: Traceability logging ──────────────────────────

class TestTraceabilityLogging:
    """Silent except blocks in traceability.py must log."""

    def test_logger_imported(self):
        src = (SRC / "governance/mcp_tools/traceability.py").read_text()
        assert "import logging" in src
        assert "logger = logging.getLogger" in src

    def test_trace_rule_chain_logs(self):
        src = (SRC / "governance/mcp_tools/traceability.py").read_text()
        idx = src.index("def trace_rule_chain")
        block = src[idx:idx + 1800]
        assert "logger.debug" in block

    def test_trace_gap_chain_logs(self):
        src = (SRC / "governance/mcp_tools/traceability.py").read_text()
        idx = src.index("def trace_gap_chain")
        block = src[idx:idx + 1500]
        assert "logger.debug" in block

    def test_trace_evidence_chain_logs(self):
        src = (SRC / "governance/mcp_tools/traceability.py").read_text()
        idx = src.index("def trace_evidence_chain")
        block = src[idx:idx + 2500]
        # Both inner queries should log
        assert block.count("logger.debug") >= 2

    def test_no_bare_except_without_logging(self):
        """All inner except Exception blocks must have 'as e' + logging."""
        src = (SRC / "governance/mcp_tools/traceability.py").read_text()
        lines = src.split("\n")
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped == "except Exception:":
                assert False, f"Bare 'except Exception:' without 'as e' at line {i+1}"

    def test_bug_marker_present(self):
        src = (SRC / "governance/mcp_tools/traceability.py").read_text()
        assert "BUG-276-TRACE-001" in src


# ── BUG-276-TCRUD-001: taxonomy_get exception handler ────────────────

class TestTaxonomyGetHandler:
    """taxonomy_get must have exception handling."""

    def test_try_except_present(self):
        src = (SRC / "governance/mcp_tools/tasks_crud.py").read_text()
        idx = src.index("def taxonomy_get")
        block = src[idx:idx + 1500]
        assert "try:" in block
        assert "except Exception" in block

    def test_error_message(self):
        src = (SRC / "governance/mcp_tools/tasks_crud.py").read_text()
        idx = src.index("def taxonomy_get")
        block = src[idx:idx + 1500]
        assert "taxonomy_get failed" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/mcp_tools/tasks_crud.py").read_text()
        assert "BUG-276-TCRUD-001" in src


# ── BUG-277-DETAIL-001: ingestion_status exception handler ───────────

class TestIngestionStatusHandler:
    """ingestion_status endpoint must have exception handling."""

    def test_try_except_present(self):
        src = (SRC / "governance/routes/sessions/detail.py").read_text()
        idx = src.index("def ingestion_status")
        block = src[idx:idx + 600]
        assert "try:" in block
        assert "except Exception" in block

    def test_logs_error(self):
        src = (SRC / "governance/routes/sessions/detail.py").read_text()
        idx = src.index("def ingestion_status")
        block = src[idx:idx + 600]
        assert "logger.error" in block

    def test_raises_http_exception(self):
        src = (SRC / "governance/routes/sessions/detail.py").read_text()
        idx = src.index("def ingestion_status")
        block = src[idx:idx + 600]
        assert "HTTPException" in block
        assert "500" in block

    def test_no_raw_exception_in_response(self):
        """Error response must NOT include raw exception details."""
        src = (SRC / "governance/routes/sessions/detail.py").read_text()
        idx = src.index("def ingestion_status")
        block = src[idx:idx + 800]
        # The detail should be a fixed string, not f"...{e}"
        assert "Failed to retrieve ingestion status" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/routes/sessions/detail.py").read_text()
        assert "BUG-277-DETAIL-001" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch274Imports:
    def test_checkpoint_importable(self):
        import governance.services.ingestion_checkpoint
        assert governance.services.ingestion_checkpoint is not None

    def test_agents_store_importable(self):
        import governance.stores.agents
        assert governance.stores.agents is not None

    def test_rules_crud_importable(self):
        import governance.mcp_tools.rules_crud
        assert governance.mcp_tools.rules_crud is not None

    def test_traceability_importable(self):
        import governance.mcp_tools.traceability
        assert governance.mcp_tools.traceability is not None

    def test_tasks_crud_importable(self):
        import governance.mcp_tools.tasks_crud
        assert governance.mcp_tools.tasks_crud is not None

    def test_detail_importable(self):
        import governance.routes.sessions.detail
        assert governance.routes.sessions.detail is not None
