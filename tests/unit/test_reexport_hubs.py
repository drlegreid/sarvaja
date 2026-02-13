"""
Unit tests for Re-Export Hub Modules.

Batch 154: Quick import/re-export validation for:
- governance/pydantic_tools.py (re-exports from pydantic_schemas)
- governance/langgraph_workflow.py (re-exports from langgraph package)
- governance/hybrid_router.py (re-exports from hybrid package)
- governance/mcp_server_core.py (MCP server initialization)
- governance/mcp_tools/evidence/documents.py (re-export hub)
- governance/mcp_tools/evidence/common.py (shared path constants)
"""

from pathlib import Path

import pytest


# ── pydantic_tools.py re-exports ─────────────────────────

class TestPydanticToolsReexports:
    def test_imports_input_models(self):
        from governance.pydantic_tools import (
            RuleQueryConfig, DependencyConfig, TrustScoreRequest,
            ProposalConfig, ImpactAnalysisConfig, DSMCycleConfig,
        )
        assert RuleQueryConfig is not None
        assert DependencyConfig is not None

    def test_imports_output_models(self):
        from governance.pydantic_tools import (
            RuleQueryResult, DependencyResult, TrustScoreResult,
            ProposalResult, ImpactAnalysisResult, HealthCheckResult,
        )
        assert RuleQueryResult is not None

    def test_imports_typed_tools(self):
        from governance.pydantic_tools import (
            query_rules_typed, analyze_dependencies_typed,
            calculate_trust_score_typed, create_proposal_typed,
            analyze_impact_typed, health_check_typed,
        )
        assert callable(query_rules_typed)
        assert callable(health_check_typed)

    def test_imports_mcp_wrappers(self):
        from governance.pydantic_tools import (
            query_rules_mcp, analyze_dependencies_mcp,
            calculate_trust_score_mcp, analyze_impact_mcp,
            health_check_mcp,
        )
        assert callable(query_rules_mcp)

    def test_all_exports_defined(self):
        import governance.pydantic_tools as mod
        assert len(mod.__all__) >= 15


# ── langgraph_workflow.py re-exports ─────────────────────

class TestLanggraphWorkflowReexports:
    def test_imports_state(self):
        from governance.langgraph_workflow import (
            Vote, ProposalState,
            QUORUM_THRESHOLD, APPROVAL_THRESHOLD, DISPUTE_THRESHOLD,
            TRUST_WEIGHTS,
        )
        assert isinstance(QUORUM_THRESHOLD, (int, float))
        assert isinstance(TRUST_WEIGHTS, dict)

    def test_imports_nodes(self):
        from governance.langgraph_workflow import (
            submit_node, validate_node, assess_node, vote_node,
            decide_node, implement_node, complete_node, reject_node,
        )
        assert callable(submit_node)
        assert callable(reject_node)

    def test_imports_edges(self):
        from governance.langgraph_workflow import (
            check_validation, check_decision, check_status,
        )
        assert callable(check_validation)

    def test_imports_graph(self):
        from governance.langgraph_workflow import (
            build_proposal_graph, create_initial_state,
            run_proposal_workflow, LANGGRAPH_AVAILABLE,
        )
        assert callable(build_proposal_graph)
        assert callable(create_initial_state)

    def test_imports_mcp(self):
        from governance.langgraph_workflow import proposal_submit_mcp
        assert callable(proposal_submit_mcp)

    def test_all_exports_defined(self):
        import governance.langgraph_workflow as mod
        assert len(mod.__all__) >= 15


# ── hybrid_router.py re-exports ──────────────────────────

class TestHybridRouterReexports:
    def test_imports_models(self):
        from governance.hybrid_router import QueryType, QueryResult, SyncStatus
        assert QueryType is not None
        assert QueryResult is not None
        assert SyncStatus is not None

    def test_imports_router(self):
        from governance.hybrid_router import HybridQueryRouter
        assert HybridQueryRouter is not None

    def test_imports_sync_bridge(self):
        from governance.hybrid_router import MemorySyncBridge
        assert MemorySyncBridge is not None

    def test_all_exports_defined(self):
        import governance.hybrid_router as mod
        assert len(mod.__all__) == 5


# ── mcp_server_core.py ──────────────────────────────────

class TestMCPServerCore:
    def test_mcp_instance_exists(self):
        from governance.mcp_server_core import mcp
        assert mcp is not None
        assert mcp.name == "governance-core"

    def test_quality_flag_exists(self):
        import governance.mcp_server_core as mod
        assert hasattr(mod, "QUALITY_AVAILABLE")
        assert isinstance(mod.QUALITY_AVAILABLE, bool)


# ── evidence/documents.py hub ────────────────────────────

class TestDocumentsHub:
    def test_file_type_map_reexported(self):
        from governance.mcp_tools.evidence.documents import FILE_TYPE_MAP
        assert isinstance(FILE_TYPE_MAP, dict)
        assert ".md" in FILE_TYPE_MAP

    def test_register_document_tools_callable(self):
        from governance.mcp_tools.evidence.documents import register_document_tools
        assert callable(register_document_tools)


# ── evidence/common.py constants ─────────────────────────

class TestCommonConstants:
    def test_evidence_dir(self):
        from governance.mcp_tools.evidence.common import EVIDENCE_DIR
        assert EVIDENCE_DIR == Path("evidence")

    def test_docs_dir(self):
        from governance.mcp_tools.evidence.common import DOCS_DIR
        assert DOCS_DIR == Path("docs")

    def test_backlog_dir(self):
        from governance.mcp_tools.evidence.common import BACKLOG_DIR
        assert BACKLOG_DIR == Path("docs/backlog")

    def test_rules_dir(self):
        from governance.mcp_tools.evidence.common import RULES_DIR
        assert RULES_DIR == Path("docs/rules")

    def test_gaps_dir(self):
        from governance.mcp_tools.evidence.common import GAPS_DIR
        assert GAPS_DIR == Path("docs/gaps")

    def test_tasks_dir(self):
        from governance.mcp_tools.evidence.common import TASKS_DIR
        assert TASKS_DIR == Path("docs/tasks")

    def test_all_are_path_objects(self):
        from governance.mcp_tools.evidence.common import (
            EVIDENCE_DIR, DOCS_DIR, BACKLOG_DIR, RULES_DIR, GAPS_DIR, TASKS_DIR,
        )
        for p in [EVIDENCE_DIR, DOCS_DIR, BACKLOG_DIR, RULES_DIR, GAPS_DIR, TASKS_DIR]:
            assert isinstance(p, Path)
