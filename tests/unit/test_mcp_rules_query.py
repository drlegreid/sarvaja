"""
Unit tests for Rule Query MCP Tools.

Per DOC-SIZE-01-v1: Tests for mcp_tools/rules_query.py module.
Tests: rules_query, rules_query_by_tags, wisdom_get, rule_get,
       rule_get_deps, rules_find_conflicts.
"""

import json
from dataclasses import dataclass, field, asdict
from unittest.mock import MagicMock, patch

import pytest

_P = "governance.mcp_tools.rules_query"


@dataclass
class _MockRule:
    id: str = "TEST-01-v1"
    name: str = "Test Rule"
    category: str = "TEST"
    priority: str = "HIGH"
    status: str = "ACTIVE"
    directive: str = "Do X"
    applicability: str = "MANDATORY"
    tags: str = "test,governance"
    applicable_roles: str = "PLATFORM,QUALITY"
    created_date: str = "2026-01-01"


class _CaptureMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


def _register():
    mcp = _CaptureMCP()
    from governance.mcp_tools.rules_query import register_rule_query_tools
    register_rule_query_tools(mcp)
    return mcp.tools


@pytest.fixture(autouse=True)
def _mock_format():
    with patch(f"{_P}.format_mcp_result", side_effect=lambda x: json.dumps(x, default=str)):
        yield


@pytest.fixture(autouse=True)
def _mock_monitor():
    with patch(f"{_P}.log_monitor_event"):
        yield


def _mock_client(rules=None, connect=True):
    c = MagicMock()
    c.connect.return_value = connect
    c.get_all_rules.return_value = rules or []
    c.get_active_rules.return_value = [r for r in (rules or []) if r.status == "ACTIVE"]
    return c


# ── rules_query ──────────────────────────────────────────────────


class TestRulesQuery:
    def test_all_rules(self):
        tools = _register()
        client = _mock_client([_MockRule()])
        with patch(f"{_P}.get_typedb_client", return_value=client):
            result = json.loads(tools["rules_query"]())
        assert len(result) == 1

    def test_filter_by_category(self):
        tools = _register()
        rules = [_MockRule(id="R-1", category="TEST"), _MockRule(id="R-2", category="ARCH")]
        client = _mock_client(rules)
        with patch(f"{_P}.get_typedb_client", return_value=client):
            result = json.loads(tools["rules_query"](category="TEST"))
        assert len(result) == 1

    def test_filter_by_active_status(self):
        tools = _register()
        rules = [_MockRule(status="ACTIVE"), _MockRule(id="R-2", status="DEPRECATED")]
        client = _mock_client(rules)
        with patch(f"{_P}.get_typedb_client", return_value=client):
            result = json.loads(tools["rules_query"](status="ACTIVE"))
        assert len(result) == 1

    def test_filter_by_priority(self):
        tools = _register()
        rules = [_MockRule(priority="HIGH"), _MockRule(id="R-2", priority="LOW")]
        client = _mock_client(rules)
        with patch(f"{_P}.get_typedb_client", return_value=client):
            result = json.loads(tools["rules_query"](priority="HIGH"))
        assert len(result) == 1

    def test_fallback_to_markdown(self):
        tools = _register()
        client = _mock_client(connect=False)
        mock_md = [MagicMock()]
        with patch(f"{_P}.get_typedb_client", return_value=client), \
             patch(f"{_P}.get_all_markdown_rules", return_value=mock_md), \
             patch(f"{_P}.filter_markdown_rules", return_value=mock_md), \
             patch(f"{_P}.markdown_rule_to_dict", return_value={"id": "R-1"}):
            result = json.loads(tools["rules_query"]())
        assert result["source"] == "markdown_fallback"

    def test_fallback_no_markdown(self):
        tools = _register()
        client = _mock_client(connect=False)
        with patch(f"{_P}.get_typedb_client", return_value=client), \
             patch(f"{_P}.get_all_markdown_rules", return_value=[]):
            result = json.loads(tools["rules_query"]())
        assert "error" in result

    def test_exception_triggers_fallback(self):
        tools = _register()
        client = MagicMock()
        client.connect.return_value = True
        client.get_all_rules.side_effect = Exception("DB error")
        client.close.return_value = None
        with patch(f"{_P}.get_typedb_client", return_value=client), \
             patch(f"{_P}.get_all_markdown_rules", return_value=[]), \
             patch(f"{_P}.filter_markdown_rules", return_value=[]):
            result = json.loads(tools["rules_query"]())
        assert "error" in result


# ── rules_query_by_tags ──────────────────────────────────────────


class TestRulesQueryByTags:
    def test_by_tags(self):
        tools = _register()
        client = _mock_client([_MockRule(tags="test,governance")])
        with patch(f"{_P}.get_typedb_client", return_value=client):
            result = json.loads(tools["rules_query_by_tags"](tags="test"))
        assert result["count"] == 1

    def test_no_matching_tags(self):
        tools = _register()
        client = _mock_client([_MockRule(tags="test")])
        with patch(f"{_P}.get_typedb_client", return_value=client):
            result = json.loads(tools["rules_query_by_tags"](tags="nonexistent"))
        assert result["count"] == 0

    def test_by_agent_role(self):
        tools = _register()
        client = _mock_client([_MockRule(applicable_roles="PLATFORM,QUALITY")])
        with patch(f"{_P}.get_typedb_client", return_value=client):
            result = json.loads(tools["rules_query_by_tags"](agent_role="PLATFORM"))
        assert result["count"] == 1

    def test_connection_failure(self):
        tools = _register()
        client = _mock_client(connect=False)
        with patch(f"{_P}.get_typedb_client", return_value=client):
            result = json.loads(tools["rules_query_by_tags"]())
        assert "error" in result


# ── rule_get ─────────────────────────────────────────────────────


class TestRuleGet:
    def test_found_in_typedb(self):
        tools = _register()
        client = MagicMock()
        client.connect.return_value = True
        rule = _MockRule()
        client.get_rule_by_id.return_value = rule
        with patch(f"{_P}.get_typedb_client", return_value=client):
            result = json.loads(tools["rule_get"](rule_id="TEST-01-v1"))
        assert result["id"] == "TEST-01-v1"

    def test_fallback_to_markdown(self):
        tools = _register()
        client = MagicMock()
        client.connect.return_value = True
        client.get_rule_by_id.return_value = None
        md_rule = MagicMock()
        with patch(f"{_P}.get_typedb_client", return_value=client), \
             patch(f"{_P}.get_markdown_rule_by_id", return_value=md_rule), \
             patch(f"{_P}.markdown_rule_to_dict", return_value={"id": "R-1"}):
            result = json.loads(tools["rule_get"](rule_id="R-1"))
        assert "warning" in result

    def test_not_found_anywhere(self):
        tools = _register()
        client = MagicMock()
        client.connect.return_value = True
        client.get_rule_by_id.return_value = None
        with patch(f"{_P}.get_typedb_client", return_value=client), \
             patch(f"{_P}.get_markdown_rule_by_id", return_value=None):
            result = json.loads(tools["rule_get"](rule_id="NONEXISTENT"))
        assert "error" in result


# ── rule_get_deps ────────────────────────────────────────────────


class TestRuleGetDeps:
    def test_success(self):
        tools = _register()
        client = MagicMock()
        client.connect.return_value = True
        client.get_rule_dependencies.return_value = {"depends_on": ["R-2"]}
        with patch(f"{_P}.get_typedb_client", return_value=client):
            result = json.loads(tools["rule_get_deps"](rule_id="R-1"))
        assert result["depends_on"] == ["R-2"]

    def test_connection_failure(self):
        tools = _register()
        client = MagicMock()
        client.connect.return_value = False
        with patch(f"{_P}.get_typedb_client", return_value=client):
            result = json.loads(tools["rule_get_deps"](rule_id="R-1"))
        assert "error" in result


# ── rules_find_conflicts ─────────────────────────────────────────


class TestRulesFindConflicts:
    def test_success(self):
        tools = _register()
        client = MagicMock()
        client.connect.return_value = True
        client.find_conflicts.return_value = [{"rule_a": "R-1", "rule_b": "R-2"}]
        with patch(f"{_P}.get_typedb_client", return_value=client):
            result = json.loads(tools["rules_find_conflicts"]())
        assert len(result) == 1
