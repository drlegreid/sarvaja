"""Deep scan batch 192: MCP tools layer.

Batch 192 findings: 22 total, 10 confirmed fixes, 12 deferred.
- BUG-192-001: agents.py 5 functions try/finally without except.
- BUG-192-002: rules_archive.py 2 functions try/finally without except.
- BUG-192-003: rules_query.py 2 functions try/finally without except.
- BUG-192-004: trust.py 1 function try/finally without except.
"""
import pytest
from pathlib import Path


# ── MCP agents exception safety defense ──────────────


class TestAgentsMcpExceptionSafety:
    """Verify agents.py MCP tools have try/except/finally."""

    def _get_agents_src(self):
        root = Path(__file__).parent.parent.parent
        return (root / "governance/mcp_tools/agents.py").read_text()

    def test_agent_create_has_except(self):
        """agent_create has except block."""
        src = self._get_agents_src()
        start = src.index("def agent_create")
        rest = src[start:]
        end = rest.index("\n    @mcp", 10) if "\n    @mcp" in rest[10:] else len(rest)
        func = rest[:end]
        assert "except Exception" in func

    def test_agent_get_has_except(self):
        """agent_get has except block."""
        src = self._get_agents_src()
        start = src.index("def agent_get")
        rest = src[start:]
        end = rest.index("\n    @mcp", 10) if "\n    @mcp" in rest[10:] else len(rest)
        func = rest[:end]
        assert "except Exception" in func

    def test_agents_list_has_except(self):
        """agents_list has except block."""
        src = self._get_agents_src()
        start = src.index("def agents_list")
        rest = src[start:]
        end = rest.index("\n    @mcp", 10) if "\n    @mcp" in rest[10:] else len(rest)
        func = rest[:end]
        assert "except Exception" in func

    def test_agent_trust_update_has_except(self):
        """agent_trust_update has except block."""
        src = self._get_agents_src()
        start = src.index("def agent_trust_update")
        rest = src[start:]
        end = rest.index("\n    @mcp", 10) if "\n    @mcp" in rest[10:] else len(rest)
        func = rest[:end]
        assert "except Exception" in func

    def test_agents_dashboard_has_except(self):
        """agents_dashboard has except block."""
        src = self._get_agents_src()
        start = src.index("def agents_dashboard")
        rest = src[start:]
        end = rest.index("\n    @mcp", 10) if "\n    @mcp" in rest[10:] else len(rest)
        func = rest[:end]
        assert "except Exception" in func


# ── MCP rules archive exception safety defense ──────────────


class TestRulesArchiveMcpExceptionSafety:
    """Verify rules_archive.py MCP tools have try/except/finally."""

    def _get_src(self):
        root = Path(__file__).parent.parent.parent
        return (root / "governance/mcp_tools/rules_archive.py").read_text()

    def test_rules_list_archived_has_except(self):
        """rules_list_archived has except block."""
        src = self._get_src()
        start = src.index("def rules_list_archived")
        rest = src[start:]
        end = rest.index("\n    @mcp", 10) if "\n    @mcp" in rest[10:] else len(rest)
        func = rest[:end]
        assert "except Exception" in func

    def test_rule_get_archived_has_except(self):
        """rule_get_archived has except block."""
        src = self._get_src()
        start = src.index("def rule_get_archived")
        rest = src[start:]
        end = rest.index("\n    @mcp", 10) if "\n    @mcp" in rest[10:] else len(rest)
        func = rest[:end]
        assert "except Exception" in func

    def test_rule_restore_has_except(self):
        """rule_restore has except block (existing)."""
        src = self._get_src()
        start = src.index("def rule_restore")
        func = src[start:]
        assert "except Exception" in func


# ── MCP rules query exception safety defense ──────────────


class TestRulesQueryMcpExceptionSafety:
    """Verify rules_query.py MCP tools have try/except/finally."""

    def _get_src(self):
        root = Path(__file__).parent.parent.parent
        return (root / "governance/mcp_tools/rules_query.py").read_text()

    def test_rule_get_deps_has_except(self):
        """rule_get_deps has except block."""
        src = self._get_src()
        start = src.index("def rule_get_deps")
        rest = src[start:]
        end = rest.index("\n    @mcp", 10) if "\n    @mcp" in rest[10:] else len(rest)
        func = rest[:end]
        assert "except Exception" in func

    def test_rules_find_conflicts_has_except(self):
        """rules_find_conflicts has except block."""
        src = self._get_src()
        start = src.index("def rules_find_conflicts")
        func = src[start:]
        assert "except Exception" in func


# ── MCP trust exception safety defense ──────────────


class TestTrustMcpExceptionSafety:
    """Verify trust.py MCP tools have try/except/finally."""

    def test_governance_get_trust_score_has_except(self):
        """governance_get_trust_score has except block."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/mcp_tools/trust.py").read_text()
        start = src.index("def governance_get_trust_score")
        rest = src[start:]
        end = rest.index("\n    #", 10) if "\n    #" in rest[10:] else len(rest)
        func = rest[:end]
        assert "except Exception" in func
