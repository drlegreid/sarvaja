"""
Unit tests for Entity Document Viewing MCP Tools.

Batch 153: Tests for governance/mcp_tools/evidence/documents_entity.py
- doc_rule_get: markdown search, metadata extraction, TypeDB fallback
- doc_task_get: workspace document search, TypeDB fallback
"""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from governance.mcp_tools.evidence.documents_entity import register_entity_document_tools

_MOD = "governance.mcp_tools.evidence.documents_entity"


def _json_fmt(data):
    return json.dumps(data, indent=2, default=str)


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
    register_entity_document_tools(mcp)
    return mcp.tools


@pytest.fixture(autouse=True)
def _force_json():
    with patch(f"{_MOD}.format_mcp_result", side_effect=_json_fmt):
        yield


_RULE_MD = """\
# Rules Governance

## RULE-001: Evidence Requirement
**Category:** `Governance` | **Priority:** HIGH | **Status:** ACTIVE

### Directive
All sessions must produce evidence files.

---

## RULE-003: Trust Protocol
**Category:** `Trust` | **Priority:** CRITICAL | **Status:** ACTIVE

### Directive
Agents must maintain trust scores.
"""


# ── Registration ────────────────────────────────────────

class TestRegistration:
    def test_registers_tools(self):
        tools = _register()
        assert "doc_rule_get" in tools
        assert "doc_task_get" in tools


# ── doc_rule_get ────────────────────────────────────────

class TestDocRuleGet:
    def test_finds_rule_in_file(self, tmp_path):
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        (rules_dir / "RULES-GOVERNANCE.md").write_text(_RULE_MD)

        tools = _register()
        with patch(f"{_MOD}.RULES_DIR", rules_dir):
            result = json.loads(tools["doc_rule_get"](rule_id="RULE-001"))
        assert result["rule_id"] == "RULE-001"
        assert "evidence" in result["content"].lower()
        assert result["source_file"] == str(rules_dir / "RULES-GOVERNANCE.md")

    def test_extracts_metadata(self, tmp_path):
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        (rules_dir / "RULES-GOVERNANCE.md").write_text(_RULE_MD)

        tools = _register()
        with patch(f"{_MOD}.RULES_DIR", rules_dir):
            result = json.loads(tools["doc_rule_get"](rule_id="RULE-001"))
        # Metadata may be extracted depending on format
        assert "metadata" in result

    def test_not_found_falls_to_typedb(self, tmp_path):
        rules_dir = tmp_path / "empty_rules"
        rules_dir.mkdir()

        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.get_all_rules.return_value = []
        mock_client.close.return_value = None

        tools = _register()
        with patch(f"{_MOD}.RULES_DIR", rules_dir), \
             patch(f"{_MOD}.get_typedb_client", return_value=mock_client):
            result = json.loads(tools["doc_rule_get"](rule_id="RULE-999"))
        assert "error" in result

    def test_typedb_fallback_success(self, tmp_path):
        rules_dir = tmp_path / "empty_rules"
        rules_dir.mkdir()

        mock_rule = MagicMock()
        mock_rule.id = "RULE-999"
        mock_rule.name = "Test Rule"
        mock_rule.directive = "Test directive"
        mock_rule.category = "Test"
        mock_rule.priority = "HIGH"
        mock_rule.status = "ACTIVE"

        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.get_all_rules.return_value = [mock_rule]
        mock_client.close.return_value = None

        tools = _register()
        with patch(f"{_MOD}.RULES_DIR", rules_dir), \
             patch(f"{_MOD}.get_typedb_client", return_value=mock_client):
            result = json.loads(tools["doc_rule_get"](rule_id="RULE-999"))
        assert result["source"] == "typedb"
        assert result["name"] == "Test Rule"


# ── doc_task_get ────────────────────────────────────────

class TestDocTaskGet:
    def test_finds_task_in_backlog(self, tmp_path):
        backlog_dir = tmp_path / "backlog"
        backlog_dir.mkdir()
        (backlog_dir / "R&D-BACKLOG.md").write_text(
            "| P10.1 | Fix auth | TODO | HIGH |\n"
            "| P10.2 | Add tests | DONE | LOW |\n"
        )

        mock_client = MagicMock()
        mock_client.connect.return_value = False

        tools = _register()
        with patch(f"{_MOD}.BACKLOG_DIR", backlog_dir), \
             patch(f"{_MOD}.get_typedb_client", return_value=mock_client):
            result = json.loads(tools["doc_task_get"](task_id="P10.1"))
        assert result["task_id"] == "P10.1"
        assert len(result["sources"]) >= 1

    def test_not_found(self, tmp_path):
        backlog_dir = tmp_path / "backlog"
        backlog_dir.mkdir()
        (backlog_dir / "R&D-BACKLOG.md").write_text("| P10.1 | stuff |\n")

        mock_client = MagicMock()
        mock_client.connect.return_value = False

        tools = _register()
        with patch(f"{_MOD}.BACKLOG_DIR", backlog_dir), \
             patch(f"{_MOD}.get_typedb_client", return_value=mock_client):
            result = json.loads(tools["doc_task_get"](task_id="NONEXISTENT"))
        assert "error" in result

    def test_typedb_enrichment(self, tmp_path):
        backlog_dir = tmp_path / "backlog"
        backlog_dir.mkdir()

        mock_task = MagicMock()
        mock_task.id = "T-1"
        mock_task.name = "Test"
        mock_task.status = "DONE"
        mock_task.phase = "P10"
        mock_task.body = "desc"
        mock_task.linked_rules = []
        mock_task.linked_sessions = []

        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.get_task.return_value = mock_task
        mock_client.close.return_value = None

        tools = _register()
        with patch(f"{_MOD}.BACKLOG_DIR", backlog_dir), \
             patch(f"{_MOD}.get_typedb_client", return_value=mock_client):
            result = json.loads(tools["doc_task_get"](task_id="T-1"))
        assert "typedb" in result
        assert result["typedb"]["status"] == "DONE"
