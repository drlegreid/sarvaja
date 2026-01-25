"""
Robot Framework Library for ChromaDB Sync Tests.

Per P2.6: Hybrid TypeDB + ChromaDB architecture.
Migrated from tests/test_chromadb_sync.py
"""
from pathlib import Path
from robot.api.deco import keyword


class ChromadbSyncLibrary:
    """Library for testing ChromaDB sync state."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.governance_dir = self.project_root / "governance"

    # =============================================================================
    # Current State Tests (Active)
    # =============================================================================

    @keyword("TypeDB Client Exists")
    def typedb_client_exists(self):
        """TypeDB client module must exist."""
        client_file = self.governance_dir / "client.py"
        return {"exists": client_file.exists()}

    @keyword("MCP Servers Exist")
    def mcp_servers_exist(self):
        """Governance MCP servers must exist (split per RULE-036)."""
        mcp_files = [
            self.governance_dir / "mcp_server_core.py",
            self.governance_dir / "mcp_server_agents.py",
            self.governance_dir / "mcp_server_sessions.py",
            self.governance_dir / "mcp_server_tasks.py",
        ]
        results = {}
        for mcp_file in mcp_files:
            results[mcp_file.name] = mcp_file.exists()

        return {
            "core_exists": results.get("mcp_server_core.py", False),
            "agents_exists": results.get("mcp_server_agents.py", False),
            "sessions_exists": results.get("mcp_server_sessions.py", False),
            "tasks_exists": results.get("mcp_server_tasks.py", False)
        }

    @keyword("Schema Has Rule Count")
    def schema_has_rule_count(self):
        """TypeDB schema should have rules defined."""
        data_file = self.governance_dir / "data.tql"
        if not data_file.exists():
            return {"skipped": True, "reason": "data.tql not found"}

        content = data_file.read_text()
        rule_count = content.count("isa rule-entity")

        return {
            "has_rules": rule_count > 0,
            "rule_count": rule_count
        }

    @keyword("Env Vars Configurable")
    def env_vars_configurable(self):
        """TypeDB and ChromaDB should be configurable via environment variables."""
        base_file = self.governance_dir / "typedb" / "base.py"
        if not base_file.exists():
            return {"skipped": True, "reason": "typedb/base.py not found"}

        content = base_file.read_text()

        return {
            "has_typedb_host": 'os.getenv("TYPEDB_HOST"' in content,
            "has_typedb_port": 'os.getenv("TYPEDB_PORT"' in content
        }

    # =============================================================================
    # TDD Stubs (Skipped - Deferred to P2.6)
    # =============================================================================

    @keyword("Sync Rules To ChromaDB Stub")
    def sync_rules_to_chromadb_stub(self):
        """TDD stub - sync rules to ChromaDB (P2.6 deferred)."""
        return {"skipped": True, "reason": "P2.6 - Hybrid router not implemented (DECISION-003)"}

    @keyword("Sync Decisions To ChromaDB Stub")
    def sync_decisions_to_chromadb_stub(self):
        """TDD stub - sync decisions to ChromaDB (P2.6 deferred)."""
        return {"skipped": True, "reason": "P2.6 - Hybrid router not implemented (DECISION-003)"}

    @keyword("Route Inference Query To TypeDB Stub")
    def route_inference_query_to_typedb_stub(self):
        """TDD stub - route inference to TypeDB (P2.6 deferred)."""
        return {"skipped": True, "reason": "P2.6 - Hybrid router not implemented (DECISION-003)"}

    @keyword("Route Semantic Query To ChromaDB Stub")
    def route_semantic_query_to_chromadb_stub(self):
        """TDD stub - route semantic to ChromaDB (P2.6 deferred)."""
        return {"skipped": True, "reason": "P2.6 - Hybrid router not implemented (DECISION-003)"}
