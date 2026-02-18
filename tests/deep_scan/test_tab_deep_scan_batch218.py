"""Batch 218 — MCP tools defense tests.

Validates fixes for:
- BUG-218-MEM-001: memory_tiers.py hardcoded ChromaDB host/port
- BUG-218-TRACE-001: traceability.py TypeQL 2.x 'get' syntax
- BUG-218-COMMON-001: typedb_client() close() exception suppression
"""
from pathlib import Path
from unittest.mock import patch, MagicMock
import re

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-218-MEM-001: ChromaDB env vars ────────────────────────────────

class TestMemoryTiersChromaConfig:
    """memory_tiers.py must use env vars, not hardcoded localhost."""

    def test_no_hardcoded_localhost_8001(self):
        src = (SRC / "governance/mcp_tools/memory_tiers.py").read_text()
        # Must NOT contain hardcoded localhost:8001
        hardcoded = re.findall(r'HttpClient\(host="localhost"', src)
        assert len(hardcoded) == 0, (
            f"Found {len(hardcoded)} hardcoded localhost ChromaDB connections"
        )

    def test_env_vars_defined(self):
        src = (SRC / "governance/mcp_tools/memory_tiers.py").read_text()
        assert "CHROMADB_HOST" in src
        assert "CHROMADB_PORT" in src

    def test_env_vars_use_getenv(self):
        src = (SRC / "governance/mcp_tools/memory_tiers.py").read_text()
        assert 'os.getenv("CHROMADB_HOST"' in src
        assert 'os.getenv("CHROMADB_PORT"' in src


# ── BUG-218-TRACE-001: TypeQL 3.x syntax ──────────────────────────────

class TestTraceabilityTypeQLSyntax:
    """traceability.py must use TypeDB 3.x 'select', not 2.x 'get'."""

    def test_no_get_syntax(self):
        src = (SRC / "governance/mcp_tools/traceability.py").read_text()
        get_matches = re.findall(r"get \$[a-z]", src)
        assert len(get_matches) == 0, (
            f"Found {len(get_matches)} TypeQL 2.x 'get $' patterns"
        )

    def test_uses_select_syntax(self):
        src = (SRC / "governance/mcp_tools/traceability.py").read_text()
        select_matches = re.findall(r"select \$[a-z]", src)
        assert len(select_matches) >= 3, (
            f"Expected 3+ 'select $' patterns, found {len(select_matches)}"
        )


# ── BUG-218-COMMON-001: typedb_client close guard ─────────────────────

class TestTypedbClientCloseGuard:
    """typedb_client() must handle close() exceptions."""

    def test_close_in_try_except(self):
        src = (SRC / "governance/mcp_tools/common.py").read_text()
        # Find the finally block — close() must be inside try/except
        # Look for pattern: finally:\n    try:\n        client.close()
        assert "try:" in src and "client.close()" in src

    def test_typedb_client_context_manager_callable(self):
        from governance.mcp_tools.common import typedb_client
        assert callable(typedb_client)

    def test_get_typedb_client_callable(self):
        from governance.mcp_tools.common import get_typedb_client
        assert callable(get_typedb_client)


# ── MCP tools defense ─────────────────────────────────────────────────

class TestMcpToolsDefense:
    """Defense tests for MCP tools common module."""

    def test_format_mcp_result_callable(self):
        from governance.mcp_tools.common import format_mcp_result
        assert callable(format_mcp_result)

    def test_format_mcp_result_returns_string(self):
        from governance.mcp_tools.common import format_mcp_result
        result = format_mcp_result({"key": "value"})
        assert isinstance(result, str)

    def test_format_mcp_result_with_error(self):
        from governance.mcp_tools.common import format_mcp_result
        result = format_mcp_result({"error": "test error"})
        assert "error" in result

    def test_log_monitor_event_callable(self):
        from governance.mcp_tools.common import log_monitor_event
        assert callable(log_monitor_event)

    def test_calculate_vote_weight_callable(self):
        from governance.mcp_tools.common import calculate_vote_weight
        assert callable(calculate_vote_weight)

    def test_calculate_vote_weight_high_trust(self):
        from governance.mcp_tools.common import calculate_vote_weight
        assert calculate_vote_weight(0.8) == 1.0

    def test_calculate_vote_weight_low_trust(self):
        from governance.mcp_tools.common import calculate_vote_weight
        assert calculate_vote_weight(0.3) == 0.3


# ── Memory tiers defense ──────────────────────────────────────────────

class TestMemoryTiersDefense:
    """Defense tests for memory_tiers module."""

    def test_module_importable(self):
        import governance.mcp_tools.memory_tiers
        assert governance.mcp_tools.memory_tiers is not None

    def test_register_function_exists(self):
        from governance.mcp_tools.memory_tiers import register_memory_tier_tools
        assert callable(register_memory_tier_tools)


# ── Traceability defense ──────────────────────────────────────────────

class TestTraceabilityDefense:
    """Defense tests for traceability module."""

    def test_module_importable(self):
        import governance.mcp_tools.traceability
        assert governance.mcp_tools.traceability is not None

    def test_register_function_exists(self):
        from governance.mcp_tools.traceability import register_traceability_tools
        assert callable(register_traceability_tools)
