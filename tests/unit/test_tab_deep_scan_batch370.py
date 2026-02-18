"""Defense tests for batch 370-373: str(e) info disclosure across 13 MCP/service files.

BUG-370-DSM-001: dsm.py — 6× str(e) → type(e).__name__ in MCP returns
BUG-370-AUD-001: audit.py — 4× str(e) → type(e).__name__ in MCP returns
BUG-370-GAP-001: gaps.py — 4× str(e) → type(e).__name__ in MCP returns
BUG-370-WKR-001: workspace_rules.py — 4× str(e) → type(e).__name__ in MCP returns
BUG-370-WKS-001: workspace_sync.py — 7× str(e) → type(e).__name__ in MCP returns
BUG-370-WFC-001: workflow_compliance.py — 2× str(e) → type(e).__name__
BUG-370-WKT-001: workspace_tasks.py — 2× str(e) → type(e).__name__
BUG-370-DOC-001: evidence/documents_core.py — 2× str(e) → type(e).__name__
BUG-370-DLK-001: evidence/documents_links.py — 1× str(e) → type(e).__name__
BUG-370-SES-001: evidence/sessions.py — 1× str(e) → type(e).__name__
BUG-370-PRP-001: proposals.py — 2× str(e) → type(e).__name__
BUG-370-BKF-001: evidence_backfill.py — 5× str(e) → type(e).__name__
BUG-370-IDX-001: cc_content_indexer.py — 1× str(e) → type(e).__name__
"""

import importlib
import inspect
import re
import pytest


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_source(module_path: str) -> str:
    """Import module and return its source code."""
    mod = importlib.import_module(module_path)
    return inspect.getsource(mod)


def _count_raw_str_e(source: str) -> int:
    """Count raw str(e) or {str(e)} or {e} patterns in error return paths.

    Only counts patterns inside format_mcp_result or HTTPException detail
    (not in logging calls which are fine).
    """
    # Find lines with format_mcp_result or HTTPException that contain str(e) or {e}
    count = 0
    for line in source.splitlines():
        stripped = line.strip()
        # Skip logging lines (those are fine — they SHOULD log full error)
        if "logger." in stripped:
            continue
        # Skip comments
        if stripped.startswith("#"):
            continue
        # Check for raw str(e) or {e} in error returns
        if "format_mcp_result" in stripped or "HTTPException" in stripped or '"error"' in stripped:
            if "str(e)" in stripped or re.search(r'\{e\}', stripped):
                # Exclude lines that use type(e).__name__
                if "type(e).__name__" not in stripped:
                    count += 1
    return count


# ── Test Classes ───────────────────────────────────────────────────────────────

class TestDsmErrorSanitization:
    """BUG-370-DSM-001: dsm.py error handlers use type(e).__name__."""

    def test_dsm_has_logger(self):
        src = _get_source("governance.mcp_tools.dsm")
        assert "logger = logging.getLogger" in src

    def test_dsm_has_bug_marker(self):
        src = _get_source("governance.mcp_tools.dsm")
        assert "BUG-370-DSM-001" in src

    def test_dsm_no_raw_str_e(self):
        src = _get_source("governance.mcp_tools.dsm")
        # All 6 handlers fixed
        assert _count_raw_str_e(src) == 0, "dsm.py still has raw str(e) in error returns"

    def test_dsm_exc_info_in_handlers(self):
        src = _get_source("governance.mcp_tools.dsm")
        assert src.count("exc_info=True") >= 6, "dsm.py should have exc_info=True in all 6 handlers"


class TestAuditErrorSanitization:
    """BUG-370-AUD-001: audit.py error handlers use type(e).__name__."""

    def test_audit_has_logger(self):
        src = _get_source("governance.mcp_tools.audit")
        assert "logger = logging.getLogger" in src

    def test_audit_has_bug_marker(self):
        src = _get_source("governance.mcp_tools.audit")
        assert "BUG-370-AUD-001" in src

    def test_audit_no_raw_str_e(self):
        src = _get_source("governance.mcp_tools.audit")
        assert _count_raw_str_e(src) == 0, "audit.py still has raw str(e) in error returns"

    def test_audit_exc_info_in_handlers(self):
        src = _get_source("governance.mcp_tools.audit")
        assert src.count("exc_info=True") >= 4


class TestGapsErrorSanitization:
    """BUG-370-GAP-001: gaps.py error handlers use type(e).__name__."""

    def test_gaps_has_bug_marker(self):
        src = _get_source("governance.mcp_tools.gaps")
        assert "BUG-370-GAP-001" in src

    def test_gaps_no_raw_str_e(self):
        src = _get_source("governance.mcp_tools.gaps")
        assert _count_raw_str_e(src) == 0, "gaps.py still has raw str(e) in error returns"


class TestWorkspaceRulesErrorSanitization:
    """BUG-370-WKR-001: workspace_rules.py error handlers sanitized."""

    def test_workspace_rules_has_bug_marker(self):
        src = _get_source("governance.mcp_tools.workspace_rules")
        assert "BUG-370-WKR-001" in src

    def test_workspace_rules_no_raw_str_e(self):
        src = _get_source("governance.mcp_tools.workspace_rules")
        assert _count_raw_str_e(src) == 0

    def test_workspace_rules_exc_info(self):
        src = _get_source("governance.mcp_tools.workspace_rules")
        assert src.count("exc_info=True") >= 4


class TestWorkspaceSyncErrorSanitization:
    """BUG-370-WKS-001: workspace_sync.py error handlers sanitized."""

    def test_workspace_sync_has_bug_marker(self):
        src = _get_source("governance.mcp_tools.workspace_sync")
        assert "BUG-370-WKS-001" in src

    def test_workspace_sync_no_raw_str_e(self):
        src = _get_source("governance.mcp_tools.workspace_sync")
        assert _count_raw_str_e(src) == 0

    def test_workspace_sync_exc_info(self):
        src = _get_source("governance.mcp_tools.workspace_sync")
        assert src.count("exc_info=True") >= 7


class TestWorkflowComplianceErrorSanitization:
    """BUG-370-WFC-001: workflow_compliance.py error handlers sanitized."""

    def test_workflow_compliance_has_bug_marker(self):
        src = _get_source("governance.mcp_tools.workflow_compliance")
        assert "BUG-370-WFC-001" in src

    def test_workflow_compliance_no_raw_str_e(self):
        src = _get_source("governance.mcp_tools.workflow_compliance")
        assert _count_raw_str_e(src) == 0


class TestWorkspaceTasksErrorSanitization:
    """BUG-370-WKT-001: workspace_tasks.py error handlers sanitized."""

    def test_workspace_tasks_has_bug_marker(self):
        src = _get_source("governance.mcp_tools.workspace_tasks")
        assert "BUG-370-WKT-001" in src

    def test_workspace_tasks_no_raw_str_e(self):
        src = _get_source("governance.mcp_tools.workspace_tasks")
        assert _count_raw_str_e(src) == 0


class TestDocumentsCoreErrorSanitization:
    """BUG-370-DOC-001: evidence/documents_core.py error handlers sanitized."""

    def test_documents_core_has_logger(self):
        src = _get_source("governance.mcp_tools.evidence.documents_core")
        assert "logger = logging.getLogger" in src

    def test_documents_core_has_bug_marker(self):
        src = _get_source("governance.mcp_tools.evidence.documents_core")
        assert "BUG-370-DOC-001" in src

    def test_documents_core_no_raw_str_e(self):
        src = _get_source("governance.mcp_tools.evidence.documents_core")
        assert _count_raw_str_e(src) == 0


class TestDocumentsLinksErrorSanitization:
    """BUG-370-DLK-001: evidence/documents_links.py error handlers sanitized."""

    def test_documents_links_has_logger(self):
        src = _get_source("governance.mcp_tools.evidence.documents_links")
        assert "logger = logging.getLogger" in src

    def test_documents_links_has_bug_marker(self):
        src = _get_source("governance.mcp_tools.evidence.documents_links")
        assert "BUG-370-DLK-001" in src

    def test_documents_links_no_raw_str_e(self):
        src = _get_source("governance.mcp_tools.evidence.documents_links")
        assert _count_raw_str_e(src) == 0


class TestSessionsErrorSanitization:
    """BUG-370-SES-001: evidence/sessions.py error handlers sanitized."""

    def test_sessions_has_bug_marker(self):
        src = _get_source("governance.mcp_tools.evidence.sessions")
        assert "BUG-370-SES-001" in src

    def test_sessions_no_raw_str_e(self):
        src = _get_source("governance.mcp_tools.evidence.sessions")
        assert _count_raw_str_e(src) == 0


class TestProposalsErrorSanitization:
    """BUG-370-PRP-001: proposals.py error handlers sanitized."""

    def test_proposals_has_logger(self):
        src = _get_source("governance.mcp_tools.proposals")
        assert "logger = logging.getLogger" in src

    def test_proposals_has_bug_marker(self):
        src = _get_source("governance.mcp_tools.proposals")
        assert "BUG-370-PRP-001" in src

    def test_proposals_no_raw_str_e(self):
        src = _get_source("governance.mcp_tools.proposals")
        assert _count_raw_str_e(src) == 0


class TestEvidenceBackfillErrorSanitization:
    """BUG-370-BKF-001: evidence_backfill.py error handlers sanitized."""

    def test_evidence_backfill_has_bug_marker(self):
        src = _get_source("governance.mcp_tools.evidence_backfill")
        assert "BUG-370-BKF-001" in src

    def test_evidence_backfill_no_raw_str_e(self):
        src = _get_source("governance.mcp_tools.evidence_backfill")
        assert _count_raw_str_e(src) == 0

    def test_evidence_backfill_exc_info(self):
        src = _get_source("governance.mcp_tools.evidence_backfill")
        assert src.count("exc_info=True") >= 5


class TestContentIndexerErrorSanitization:
    """BUG-370-IDX-001: cc_content_indexer.py delete_session_content sanitized."""

    def test_content_indexer_has_bug_marker(self):
        src = _get_source("governance.services.cc_content_indexer")
        assert "BUG-370-IDX-001" in src

    def test_content_indexer_delete_no_raw_str_e(self):
        src = _get_source("governance.services.cc_content_indexer")
        # Check specifically the delete_session_content function
        fn_start = src.index("def delete_session_content")
        fn_src = src[fn_start:]
        assert "str(e)" not in fn_src, "delete_session_content still has raw str(e)"
        assert "type(e).__name__" in fn_src


class TestBatch370Imports:
    """Verify all 13 fixed modules import cleanly."""

    @pytest.mark.parametrize("module_path", [
        "governance.mcp_tools.dsm",
        "governance.mcp_tools.audit",
        "governance.mcp_tools.gaps",
        "governance.mcp_tools.workspace_rules",
        "governance.mcp_tools.workspace_sync",
        "governance.mcp_tools.workflow_compliance",
        "governance.mcp_tools.workspace_tasks",
        "governance.mcp_tools.evidence.documents_core",
        "governance.mcp_tools.evidence.documents_links",
        "governance.mcp_tools.evidence.sessions",
        "governance.mcp_tools.proposals",
        "governance.mcp_tools.evidence_backfill",
        "governance.services.cc_content_indexer",
    ])
    def test_module_imports(self, module_path):
        mod = importlib.import_module(module_path)
        assert mod is not None
