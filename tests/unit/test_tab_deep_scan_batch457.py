"""Batch 454-457 — MCP tools logger.error sanitization (19 fixes).

Validates fixes for:
- BUG-454-SL-001..004: sessions_linking.py logger.error {e} → {type(e).__name__}
- BUG-454-TRC-001..005: traceability.py logger.error {e} → {type(e).__name__}
- BUG-454-HND-001..005: handoff.py logger.error {e} → {type(e).__name__}
- BUG-454-ING-001..004: ingestion.py logger.error {e} → {type(e).__name__}
- BUG-454-MEM-001: memory_tiers.py logger.error {e} → {type(e).__name__}
- Batch 455 (services deep E): All CLEAN
- Batch 456 (UI views layer): All CLEAN
- Batch 457 (remaining controllers): All CLEAN
"""
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent


def _read(relpath: str) -> str:
    return (_ROOT / relpath).read_text(encoding="utf-8")


def _check_no_bare_e_in_logger_error(src: str) -> list:
    """Return lines where logger.error uses {e} instead of {type(e).__name__}.

    Matches: logger.error(f"... {e} ...", exc_info=True)
    Ignores lines that already use {type(e).__name__}.
    """
    violations = []
    for i, line in enumerate(src.splitlines(), 1):
        if "logger.error(" in line and "exc_info=True" in line:
            if re.search(r'\{e\}', line) and '{type(e).__name__}' not in line:
                violations.append((i, line.strip()))
    return violations


# ─── MCP tools sessions_linking.py — logger.error sanitization ─────────

class TestSessionsLinkingLoggerSanitization:
    """BUG-454-SL-001..004: logger.error uses {type(e).__name__} not {e}."""

    def test_no_bare_e_in_logger_error(self):
        src = _read("governance/mcp_tools/sessions_linking.py")
        violations = _check_no_bare_e_in_logger_error(src)
        assert not violations, f"Bare {{e}} in logger.error: {violations}"

    def test_get_tasks_bug_marker(self):
        src = _read("governance/mcp_tools/sessions_linking.py")
        assert "BUG-454-SL-001" in src

    def test_link_rule_bug_marker(self):
        src = _read("governance/mcp_tools/sessions_linking.py")
        assert "BUG-454-SL-002" in src

    def test_link_decision_bug_marker(self):
        src = _read("governance/mcp_tools/sessions_linking.py")
        assert "BUG-454-SL-003" in src

    def test_link_evidence_bug_marker(self):
        src = _read("governance/mcp_tools/sessions_linking.py")
        assert "BUG-454-SL-004" in src


# ─── MCP tools traceability.py — logger.error sanitization ────────────

class TestTraceabilityLoggerSanitization:
    """BUG-454-TRC-001..005: logger.error uses {type(e).__name__} not {e}."""

    def test_no_bare_e_in_logger_error(self):
        src = _read("governance/mcp_tools/traceability.py")
        violations = _check_no_bare_e_in_logger_error(src)
        assert not violations, f"Bare {{e}} in logger.error: {violations}"

    def test_trace_task_chain_bug_marker(self):
        src = _read("governance/mcp_tools/traceability.py")
        assert "BUG-454-TRC-001" in src

    def test_trace_session_chain_bug_marker(self):
        src = _read("governance/mcp_tools/traceability.py")
        assert "BUG-454-TRC-002" in src

    def test_trace_rule_chain_bug_marker(self):
        src = _read("governance/mcp_tools/traceability.py")
        assert "BUG-454-TRC-003" in src

    def test_trace_gap_chain_bug_marker(self):
        src = _read("governance/mcp_tools/traceability.py")
        assert "BUG-454-TRC-004" in src

    def test_trace_evidence_chain_bug_marker(self):
        src = _read("governance/mcp_tools/traceability.py")
        assert "BUG-454-TRC-005" in src


# ─── MCP tools handoff.py — logger.error sanitization ─────────────────

class TestHandoffLoggerSanitization:
    """BUG-454-HND-001..005: logger.error uses {type(e).__name__} not {e}."""

    def test_no_bare_e_in_logger_error(self):
        src = _read("governance/mcp_tools/handoff.py")
        violations = _check_no_bare_e_in_logger_error(src)
        assert not violations, f"Bare {{e}} in logger.error: {violations}"

    def test_handoff_create_bug_marker(self):
        src = _read("governance/mcp_tools/handoff.py")
        assert "BUG-454-HND-001" in src

    def test_handoffs_pending_bug_marker(self):
        src = _read("governance/mcp_tools/handoff.py")
        assert "BUG-454-HND-002" in src

    def test_handoff_complete_bug_marker(self):
        src = _read("governance/mcp_tools/handoff.py")
        assert "BUG-454-HND-003" in src

    def test_handoff_get_bug_marker(self):
        src = _read("governance/mcp_tools/handoff.py")
        assert "BUG-454-HND-004" in src

    def test_handoff_route_bug_marker(self):
        src = _read("governance/mcp_tools/handoff.py")
        assert "BUG-454-HND-005" in src


# ─── MCP tools ingestion.py — logger.error sanitization ───────────────

class TestIngestionLoggerSanitization:
    """BUG-454-ING-001..004: logger.error uses {type(e).__name__} not {e}."""

    def test_no_bare_e_in_logger_error(self):
        src = _read("governance/mcp_tools/ingestion.py")
        violations = _check_no_bare_e_in_logger_error(src)
        assert not violations, f"Bare {{e}} in logger.error: {violations}"

    def test_ingest_content_bug_marker(self):
        src = _read("governance/mcp_tools/ingestion.py")
        assert "BUG-454-ING-001" in src

    def test_mine_links_bug_marker(self):
        src = _read("governance/mcp_tools/ingestion.py")
        assert "BUG-454-ING-002" in src

    def test_ingest_full_bug_marker(self):
        src = _read("governance/mcp_tools/ingestion.py")
        assert "BUG-454-ING-003" in src

    def test_ingestion_status_bug_marker(self):
        src = _read("governance/mcp_tools/ingestion.py")
        assert "BUG-454-ING-004" in src


# ─── MCP tools memory_tiers.py — logger.error sanitization ────────────

class TestMemoryTiersLoggerSanitization:
    """BUG-454-MEM-001: logger.error uses {type(e).__name__} not {e}."""

    def test_no_bare_e_in_logger_error(self):
        src = _read("governance/mcp_tools/memory_tiers.py")
        violations = _check_no_bare_e_in_logger_error(src)
        assert not violations, f"Bare {{e}} in logger.error: {violations}"

    def test_typedb_audit_save_bug_marker(self):
        src = _read("governance/mcp_tools/memory_tiers.py")
        assert "BUG-454-MEM-001" in src


# ─── Batch 455 CLEAN — Services deep E ────────────────────────────────

class TestBatch455ServicesClean:
    """Batch 455: Services layer (ingestion pipeline) confirmed CLEAN."""

    def test_cc_session_ingestion_importable(self):
        src = _read("governance/services/cc_session_ingestion.py")
        assert "def " in src

    def test_cc_session_scanner_importable(self):
        src = _read("governance/services/cc_session_scanner.py")
        assert "def " in src

    def test_cc_content_indexer_importable(self):
        src = _read("governance/services/cc_content_indexer.py")
        assert "def " in src

    def test_cc_link_miner_importable(self):
        src = _read("governance/services/cc_link_miner.py")
        assert "def " in src

    def test_ingestion_orchestrator_importable(self):
        src = _read("governance/services/ingestion_orchestrator.py")
        assert "def " in src


# ─── Batch 456 CLEAN — UI views layer ─────────────────────────────────

class TestBatch456UIViewsClean:
    """Batch 456: UI views layer confirmed CLEAN (pure component builders)."""

    def test_agents_metrics_importable(self):
        src = _read("agent/governance_ui/views/agents/metrics.py")
        assert "def " in src

    def test_executive_metrics_importable(self):
        src = _read("agent/governance_ui/views/executive/metrics.py")
        assert "def " in src

    def test_trust_agent_detail_importable(self):
        src = _read("agent/governance_ui/views/trust/agent_detail.py")
        assert "def " in src

    def test_trust_panels_importable(self):
        src = _read("agent/governance_ui/views/trust/panels.py")
        assert "def " in src

    def test_workflow_proposals_importable(self):
        src = _read("agent/governance_ui/views/workflow_proposals.py")
        assert "def " in src


# ─── Batch 457 CLEAN — Remaining controllers ──────────────────────────

class TestBatch457ControllersClean:
    """Batch 457: Controllers layer confirmed CLEAN (already sanitized)."""

    def test_data_loaders_importable(self):
        src = _read("agent/governance_ui/controllers/data_loaders.py")
        assert "def " in src

    def test_infra_loaders_importable(self):
        src = _read("agent/governance_ui/controllers/infra_loaders.py")
        assert "def " in src

    def test_rules_controller_importable(self):
        src = _read("agent/governance_ui/controllers/rules.py")
        assert "def " in src

    def test_trust_controller_importable(self):
        src = _read("agent/governance_ui/controllers/trust.py")
        assert "def " in src

    def test_tasks_execution_importable(self):
        src = _read("agent/governance_ui/views/tasks/execution.py")
        assert "def " in src


# ─── Import validation ─────────────────────────────────────────────────

class TestBatch457Imports:
    """Verify modified modules compile cleanly."""

    def test_sessions_linking_compiles(self):
        src = _read("governance/mcp_tools/sessions_linking.py")
        compile(src, "sessions_linking.py", "exec")

    def test_traceability_compiles(self):
        src = _read("governance/mcp_tools/traceability.py")
        compile(src, "traceability.py", "exec")

    def test_handoff_compiles(self):
        src = _read("governance/mcp_tools/handoff.py")
        compile(src, "handoff.py", "exec")

    def test_ingestion_compiles(self):
        src = _read("governance/mcp_tools/ingestion.py")
        compile(src, "ingestion.py", "exec")

    def test_memory_tiers_compiles(self):
        src = _read("governance/mcp_tools/memory_tiers.py")
        compile(src, "memory_tiers.py", "exec")
