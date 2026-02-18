"""Batch 471-474 — Full governance+agent logger sanitization defense tests.

Validates BUG-471 through BUG-474: All logger.error/warning calls across
the entire governance/ and agent/ directories use {type(e).__name__} instead
of {e} to prevent exception detail leakage into log aggregation dashboards.

Coverage: 62+ source files, 186 total fixes across 4 batches.
"""
import re
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent
GOV = SRC / "governance"
AGENT = SRC / "agent"
SCRIPTS = SRC / "scripts"

# Helper: find all logger.error/warning f-string calls with raw {e}/{pe} etc.
_RAW_EXC_PATTERN = re.compile(
    r'logger\.(error|warning)\(f".*\{(e|ae|le|se|ue|pe)\}',
)


def _scan_file(filepath: Path) -> list:
    """Return list of line numbers with raw {e} in logger calls."""
    violations = []
    for i, line in enumerate(filepath.read_text().splitlines(), 1):
        if _RAW_EXC_PATTERN.search(line):
            violations.append(i)
    return violations


# ── Batch 471: MCP Tools ─────────────────────────────────────────────

class TestBatch471McpTools:
    """BUG-471: 49 fixes across 14 MCP tool files."""

    def test_mcp_workspace_sync(self):
        f = GOV / "mcp_tools" / "workspace_sync.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_mcp_dsm(self):
        f = GOV / "mcp_tools" / "dsm.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_mcp_evidence_backfill(self):
        f = GOV / "mcp_tools" / "evidence_backfill.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_mcp_gaps(self):
        f = GOV / "mcp_tools" / "gaps.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_mcp_workspace_rules(self):
        f = GOV / "mcp_tools" / "workspace_rules.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_mcp_audit(self):
        f = GOV / "mcp_tools" / "audit.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_mcp_auto_session(self):
        f = GOV / "mcp_tools" / "auto_session.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_mcp_proposals(self):
        f = GOV / "mcp_tools" / "proposals.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_mcp_workspace_tasks(self):
        f = GOV / "mcp_tools" / "workspace_tasks.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_mcp_workflow_compliance(self):
        f = GOV / "mcp_tools" / "workflow_compliance.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_mcp_tasks_crud_verify(self):
        f = GOV / "mcp_tools" / "tasks_crud_verify.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_bug_471_markers_present(self):
        src = (GOV / "mcp_tools" / "workspace_sync.py").read_text()
        assert "BUG-471" in src


# ── Batch 472: TypeDB Queries ────────────────────────────────────────

class TestBatch472TypedbQueries:
    """BUG-472: 43 fixes across 15 TypeDB query files."""

    def test_typedb_tasks_crud(self):
        f = GOV / "typedb" / "queries" / "tasks" / "crud.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_typedb_tasks_linking(self):
        f = GOV / "typedb" / "queries" / "tasks" / "linking.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_typedb_tasks_relationships(self):
        f = GOV / "typedb" / "queries" / "tasks" / "relationships.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_typedb_tasks_status(self):
        f = GOV / "typedb" / "queries" / "tasks" / "status.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_typedb_rules_crud(self):
        f = GOV / "typedb" / "queries" / "rules" / "crud.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_typedb_rules_inference(self):
        f = GOV / "typedb" / "queries" / "rules" / "inference.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_bug_472_markers_present(self):
        src = (GOV / "typedb" / "queries" / "tasks" / "crud.py").read_text()
        assert "BUG-472" in src


# ── Batch 473: Stores + Services + DSM + SFDC ────────────────────────

class TestBatch473StoresServicesDsm:
    """BUG-473: 38 fixes across 16 files."""

    def test_stores_typedb_access(self):
        f = GOV / "stores" / "typedb_access.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_stores_session_persistence(self):
        f = GOV / "stores" / "session_persistence.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_stores_audit(self):
        f = GOV / "stores" / "audit.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_services_agents_metrics(self):
        f = GOV / "services" / "agents_metrics.py"
        if f.exists():
            assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_services_session_repair(self):
        f = GOV / "services" / "session_repair.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_dsm_nodes_execution(self):
        f = GOV / "dsm" / "langgraph" / "nodes_execution.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_dsm_nodes_analysis(self):
        f = GOV / "dsm" / "langgraph" / "nodes_analysis.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_dsm_tracker_persistence(self):
        f = GOV / "dsm" / "tracker_persistence.py"
        if f.exists():
            assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_dsm_graph(self):
        f = GOV / "dsm" / "langgraph" / "graph.py"
        if f.exists():
            assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_sfdc_nodes_execution(self):
        f = GOV / "sfdc" / "langgraph" / "nodes_execution.py"
        if f.exists():
            assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_sfdc_nodes_analysis(self):
        f = GOV / "sfdc" / "langgraph" / "nodes_analysis.py"
        if f.exists():
            assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_bug_473_markers_present(self):
        src = (GOV / "stores" / "typedb_access.py").read_text()
        assert "BUG-473" in src


# ── Batch 474: Remaining Files ───────────────────────────────────────

class TestBatch474RemainingFiles:
    """BUG-474: 56 fixes across 20+ files."""

    def test_embedding_pipeline(self):
        f = GOV / "embedding_pipeline" / "pipeline.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_workspace_scanner(self):
        f = GOV / "workspace_scanner.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_vector_store(self):
        f = GOV / "vector_store" / "store.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_seed_typedb(self):
        f = GOV / "seed" / "typedb.py"
        if f.exists():
            assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_seed_sync(self):
        f = GOV / "seed" / "sync.py"
        if f.exists():
            assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_hybrid_router(self):
        f = GOV / "hybrid" / "router.py"
        if f.exists():
            assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_context_preloader(self):
        f = GOV / "context_preloader" / "preloader.py"
        if f.exists():
            assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_workflow_compliance_init(self):
        f = GOV / "workflow_compliance" / "__init__.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_workflow_compliance_api_client(self):
        f = GOV / "workflow_compliance" / "api_client.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_workflow_compliance_task_checks(self):
        f = GOV / "workflow_compliance" / "checks" / "task_checks.py"
        if f.exists():
            assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_workflow_compliance_workspace_checks(self):
        f = GOV / "workflow_compliance" / "checks" / "workspace_checks.py"
        if f.exists():
            assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_workflow_compliance_rule_checks(self):
        f = GOV / "workflow_compliance" / "checks" / "rule_checks.py"
        if f.exists():
            assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_file_watcher(self):
        f = GOV / "file_watcher" / "watcher.py"
        if f.exists():
            assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_rule_linker_db(self):
        f = GOV / "rule_linker_db.py"
        if f.exists():
            assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_api_startup(self):
        f = GOV / "api_startup.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_evidence_scanner_linking(self):
        f = GOV / "evidence_scanner" / "linking.py"
        if f.exists():
            assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_evidence_scanner_backfill(self):
        f = GOV / "evidence_scanner" / "backfill.py"
        if f.exists():
            assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_hybrid_vectordb(self):
        f = AGENT / "hybrid_vectordb.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_dashboard_data_loader(self):
        f = AGENT / "governance_ui" / "dashboard_data_loader.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_backfill_traceability(self):
        f = SCRIPTS / "backfill_traceability.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_bug_474_markers_present(self):
        src = (GOV / "embedding_pipeline" / "pipeline.py").read_text()
        assert "BUG-474" in src


# ── Meta: Full Codebase Sweep ────────────────────────────────────────

class TestFullCodebaseSweep:
    """Verify the entire codebase has zero raw {e} in logger calls."""

    def test_zero_violations_governance_directory(self):
        violations = {}
        for py_file in sorted(GOV.rglob("*.py")):
            if "__pycache__" in str(py_file):
                continue
            found = _scan_file(py_file)
            if found:
                violations[str(py_file.relative_to(SRC))] = found
        assert not violations, f"Raw {{e}} still present in: {violations}"

    def test_zero_violations_agent_directory(self):
        violations = {}
        for py_file in sorted(AGENT.rglob("*.py")):
            if "__pycache__" in str(py_file):
                continue
            found = _scan_file(py_file)
            if found:
                violations[str(py_file.relative_to(SRC))] = found
        assert not violations, f"Raw {{e}} still present in: {violations}"

    def test_zero_violations_scripts_directory(self):
        violations = {}
        for py_file in sorted(SCRIPTS.rglob("*.py")):
            if "__pycache__" in str(py_file):
                continue
            found = _scan_file(py_file)
            if found:
                violations[str(py_file.relative_to(SRC))] = found
        assert not violations, f"Raw {{e}} still present in: {violations}"
