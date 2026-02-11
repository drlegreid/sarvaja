"""
Unit tests for Rule Query MCP Tools.

Per RULE-012, GAP-MCP-004: Tests for rules_query, rules_query_by_tags,
rule_get, rule_get_deps, rules_find_conflicts, and wisdom_get.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from dataclasses import dataclass


def _json_format(data, **kw):
    return json.dumps(data, default=str)


class _CaptureMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


@dataclass
class _FakeRule:
    id: str = "RULE-001"
    name: str = "Test Rule"
    directive: str = "Do it"
    category: str = "governance"
    priority: str = "HIGH"
    status: str = "ACTIVE"
    applicability: str = None
    tags: str = ""
    applicable_roles: str = ""


@pytest.fixture(autouse=True)
def _force_json():
    with patch("governance.mcp_tools.rules_query.format_mcp_result", side_effect=_json_format):
        yield


@pytest.fixture(autouse=True)
def _disable_monitoring():
    with patch("governance.mcp_tools.rules_query.log_monitor_event"):
        yield


@pytest.fixture
def mcp_tools():
    mcp = _CaptureMCP()
    from governance.mcp_tools.rules_query import register_rule_query_tools
    register_rule_query_tools(mcp)
    return mcp.tools


def _mock_client(rules=None, connect=True):
    client = MagicMock()
    client.connect.return_value = connect
    client.get_all_rules.return_value = rules or []
    client.get_active_rules.return_value = rules or []
    return client


# ---------------------------------------------------------------------------
# rules_query
# ---------------------------------------------------------------------------
class TestRulesQuery:
    """Tests for rules_query tool."""

    @patch("governance.mcp_tools.rules_query.get_typedb_client")
    def test_typedb_connected(self, mock_get_client, mcp_tools):
        rules = [_FakeRule(), _FakeRule(id="RULE-002", category="testing")]
        mock_get_client.return_value = _mock_client(rules)
        result = json.loads(mcp_tools["rules_query"]())
        assert len(result) == 2

    @patch("governance.mcp_tools.rules_query.get_typedb_client")
    def test_filter_category(self, mock_get_client, mcp_tools):
        rules = [_FakeRule(category="governance"), _FakeRule(id="R-2", category="testing")]
        mock_get_client.return_value = _mock_client(rules)
        result = json.loads(mcp_tools["rules_query"](category="governance"))
        assert len(result) == 1

    @patch("governance.mcp_tools.rules_query.get_typedb_client")
    def test_filter_priority(self, mock_get_client, mcp_tools):
        rules = [_FakeRule(priority="HIGH"), _FakeRule(id="R-2", priority="LOW")]
        mock_get_client.return_value = _mock_client(rules)
        result = json.loads(mcp_tools["rules_query"](priority="HIGH"))
        assert len(result) == 1

    @patch("governance.mcp_tools.rules_query.get_all_markdown_rules")
    @patch("governance.mcp_tools.rules_query.get_typedb_client")
    def test_fallback_to_markdown(self, mock_get_client, mock_md, mcp_tools):
        mock_get_client.return_value = _mock_client(connect=False)
        mock_md.return_value = []
        result = json.loads(mcp_tools["rules_query"]())
        assert "error" in result

    @patch("governance.mcp_tools.rules_query.filter_markdown_rules")
    @patch("governance.mcp_tools.rules_query.markdown_rule_to_dict")
    @patch("governance.mcp_tools.rules_query.get_all_markdown_rules")
    @patch("governance.mcp_tools.rules_query.get_typedb_client")
    def test_markdown_fallback_with_rules(self, mock_client, mock_md, mock_to_dict, mock_filter, mcp_tools):
        mock_client.return_value = _mock_client(connect=False)
        fake_rule = MagicMock()
        mock_md.return_value = [fake_rule]
        mock_filter.return_value = [fake_rule]
        mock_to_dict.return_value = {"id": "R-1", "name": "Test"}
        result = json.loads(mcp_tools["rules_query"]())
        assert result["source"] == "markdown_fallback"
        assert len(result["rules"]) == 1


# ---------------------------------------------------------------------------
# rule_get
# ---------------------------------------------------------------------------
class TestRuleGet:
    """Tests for rule_get tool."""

    @patch("governance.mcp_tools.rules_query.get_typedb_client")
    def test_found_in_typedb(self, mock_get_client, mcp_tools):
        client = _mock_client()
        client.get_rule_by_id.return_value = _FakeRule()
        mock_get_client.return_value = client
        result = json.loads(mcp_tools["rule_get"](rule_id="RULE-001"))
        assert result["id"] == "RULE-001"

    @patch("governance.mcp_tools.rules_query.get_markdown_rule_by_id")
    @patch("governance.mcp_tools.rules_query.get_typedb_client")
    def test_fallback_to_markdown(self, mock_get_client, mock_md, mcp_tools):
        client = _mock_client()
        client.get_rule_by_id.return_value = None
        mock_get_client.return_value = client
        mock_md.return_value = None
        result = json.loads(mcp_tools["rule_get"](rule_id="RULE-999"))
        assert "error" in result
        assert "not found" in result["error"]

    @patch("governance.mcp_tools.rules_query.markdown_rule_to_dict")
    @patch("governance.mcp_tools.rules_query.get_markdown_rule_by_id")
    @patch("governance.mcp_tools.rules_query.get_typedb_client")
    def test_markdown_fallback_found(self, mock_client, mock_md, mock_to_dict, mcp_tools):
        client = _mock_client(connect=False)
        mock_client.return_value = client
        fake = MagicMock()
        mock_md.return_value = fake
        mock_to_dict.return_value = {"id": "R-1"}
        result = json.loads(mcp_tools["rule_get"](rule_id="R-1"))
        assert "warning" in result


# ---------------------------------------------------------------------------
# rule_get_deps
# ---------------------------------------------------------------------------
class TestRuleGetDeps:
    """Tests for rule_get_deps tool."""

    @patch("governance.mcp_tools.rules_query.get_typedb_client")
    def test_returns_deps(self, mock_get_client, mcp_tools):
        client = _mock_client()
        client.get_rule_dependencies.return_value = ["RULE-002", "RULE-003"]
        mock_get_client.return_value = client
        result = json.loads(mcp_tools["rule_get_deps"](rule_id="RULE-001"))
        assert result == ["RULE-002", "RULE-003"]

    @patch("governance.mcp_tools.rules_query.get_typedb_client")
    def test_connection_failed(self, mock_get_client, mcp_tools):
        mock_get_client.return_value = _mock_client(connect=False)
        result = json.loads(mcp_tools["rule_get_deps"](rule_id="RULE-001"))
        assert "error" in result


# ---------------------------------------------------------------------------
# rules_find_conflicts
# ---------------------------------------------------------------------------
class TestRulesFindConflicts:
    """Tests for rules_find_conflicts tool."""

    @patch("governance.mcp_tools.rules_query.get_typedb_client")
    def test_returns_conflicts(self, mock_get_client, mcp_tools):
        client = _mock_client()
        client.find_conflicts.return_value = [{"rule_a": "R-1", "rule_b": "R-2"}]
        mock_get_client.return_value = client
        result = json.loads(mcp_tools["rules_find_conflicts"]())
        assert len(result) == 1


# ---------------------------------------------------------------------------
# rules_query_by_tags
# ---------------------------------------------------------------------------
class TestRulesQueryByTags:
    """Tests for rules_query_by_tags tool."""

    @patch("governance.mcp_tools.rules_query.get_typedb_client")
    def test_filter_by_tags(self, mock_get_client, mcp_tools):
        rules = [
            _FakeRule(tags="governance,testing"),
            _FakeRule(id="R-2", tags="devops"),
        ]
        mock_get_client.return_value = _mock_client(rules)
        result = json.loads(mcp_tools["rules_query_by_tags"](tags="governance"))
        assert result["count"] == 1

    @patch("governance.mcp_tools.rules_query.get_typedb_client")
    def test_no_tags_returns_all(self, mock_get_client, mcp_tools):
        rules = [_FakeRule(), _FakeRule(id="R-2")]
        mock_get_client.return_value = _mock_client(rules)
        result = json.loads(mcp_tools["rules_query_by_tags"]())
        assert result["count"] == 2

    @patch("governance.mcp_tools.rules_query.get_typedb_client")
    def test_connection_failed(self, mock_get_client, mcp_tools):
        mock_get_client.return_value = _mock_client(connect=False)
        result = json.loads(mcp_tools["rules_query_by_tags"]())
        assert "error" in result
