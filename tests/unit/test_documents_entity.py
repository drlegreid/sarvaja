"""
Unit tests for Entity Document Viewing MCP Tools.

Per DOC-SIZE-01-v1: Tests for governance/mcp_tools/evidence/documents_entity.py.
Tests: doc_rule_get (file match, metadata extraction, TypeDB fallback, not found),
       doc_task_get (file match, TypeDB fallback, not found).
"""

import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from governance.mcp_tools.evidence.documents_entity import register_entity_document_tools


class _CaptureMCP:
    """Captures @mcp.tool() decorated functions."""

    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


@pytest.fixture(autouse=True)
def _json_output(monkeypatch):
    """Force JSON output from format_mcp_result for easier assertions."""
    monkeypatch.setenv("MCP_OUTPUT_FORMAT", "json")


# ── doc_rule_get ───────────────────────────────────────────


class TestDocRuleGet:
    def _setup(self):
        mcp = _CaptureMCP()
        register_entity_document_tools(mcp)
        return mcp.tools["doc_rule_get"]

    def test_finds_rule_in_file(self, tmp_path):
        doc_rule_get = self._setup()
        content = (
            "# Rules\n\n"
            "## RULE-001: First Rule\n"
            "**Priority:** HIGH\n"
            "**Status:** ACTIVE\n"
            "**Category:** technical\n"
            "Some description here.\n\n"
            "## RULE-002: Second Rule\n"
            "Another rule.\n"
        )
        rule_file = tmp_path / "RULES-GOVERNANCE.md"
        rule_file.write_text(content, encoding="utf-8")

        with patch(
            "governance.mcp_tools.evidence.documents_entity.RULES_DIR", tmp_path
        ):
            raw = doc_rule_get("RULE-001")

        result = json.loads(raw)
        assert result["rule_id"] == "RULE-001"
        assert "First Rule" in result["content"]
        assert result["metadata"]["priority"] == "HIGH"
        assert result["metadata"]["status"] == "ACTIVE"
        assert result["metadata"]["category"] == "technical"

    def test_extracts_section_until_next_rule(self, tmp_path):
        doc_rule_get = self._setup()
        content = (
            "## RULE-001: Alpha\n"
            "Content for alpha.\n\n"
            "## RULE-002: Beta\n"
            "Content for beta.\n"
        )
        rule_file = tmp_path / "RULES-GOVERNANCE.md"
        rule_file.write_text(content, encoding="utf-8")

        with patch(
            "governance.mcp_tools.evidence.documents_entity.RULES_DIR", tmp_path
        ):
            raw = doc_rule_get("RULE-001")

        result = json.loads(raw)
        assert "alpha" in result["content"].lower()
        assert "beta" not in result["content"].lower()

    def test_last_rule_no_next(self, tmp_path):
        doc_rule_get = self._setup()
        content = "## RULE-099: Last Rule\nFinal content.\n"
        rule_file = tmp_path / "RULES-TECHNICAL.md"
        rule_file.write_text(content, encoding="utf-8")

        with patch(
            "governance.mcp_tools.evidence.documents_entity.RULES_DIR", tmp_path
        ):
            raw = doc_rule_get("RULE-099")

        result = json.loads(raw)
        assert result["rule_id"] == "RULE-099"
        assert "Final content" in result["content"]

    def test_searches_multiple_files(self, tmp_path):
        doc_rule_get = self._setup()
        (tmp_path / "RULES-GOVERNANCE.md").write_text("# Empty\n", encoding="utf-8")
        (tmp_path / "RULES-TECHNICAL.md").write_text("# Empty\n", encoding="utf-8")
        (tmp_path / "RULES-OPERATIONAL.md").write_text(
            "## RULE-050: Ops Rule\nOps content.\n", encoding="utf-8"
        )

        with patch(
            "governance.mcp_tools.evidence.documents_entity.RULES_DIR", tmp_path
        ):
            raw = doc_rule_get("RULE-050")

        result = json.loads(raw)
        assert result["rule_id"] == "RULE-050"

    def test_missing_metadata_fields(self, tmp_path):
        doc_rule_get = self._setup()
        content = "## RULE-010: No Metadata\nJust text.\n"
        rule_file = tmp_path / "RULES-GOVERNANCE.md"
        rule_file.write_text(content, encoding="utf-8")

        with patch(
            "governance.mcp_tools.evidence.documents_entity.RULES_DIR", tmp_path
        ):
            raw = doc_rule_get("RULE-010")

        result = json.loads(raw)
        assert result["metadata"]["rule_id"] == "RULE-010"
        assert "priority" not in result["metadata"]

    def test_typedb_fallback(self, tmp_path):
        doc_rule_get = self._setup()
        (tmp_path / "RULES-GOVERNANCE.md").write_text("# Empty\n", encoding="utf-8")
        (tmp_path / "RULES-TECHNICAL.md").write_text("# Empty\n", encoding="utf-8")
        (tmp_path / "RULES-OPERATIONAL.md").write_text("# Empty\n", encoding="utf-8")

        mock_rule = MagicMock()
        mock_rule.id = "RULE-999"
        mock_rule.name = "TypeDB Rule"
        mock_rule.directive = "Do something"
        mock_rule.category = "governance"
        mock_rule.priority = "HIGH"
        mock_rule.status = "ACTIVE"

        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.get_all_rules.return_value = [mock_rule]

        with patch(
            "governance.mcp_tools.evidence.documents_entity.RULES_DIR", tmp_path
        ), patch(
            "governance.mcp_tools.evidence.documents_entity.get_typedb_client",
            return_value=mock_client,
        ):
            raw = doc_rule_get("RULE-999")

        result = json.loads(raw)
        assert result["source"] == "typedb"
        assert result["name"] == "TypeDB Rule"

    def test_not_found_anywhere(self, tmp_path):
        doc_rule_get = self._setup()
        (tmp_path / "RULES-GOVERNANCE.md").write_text("# Empty\n", encoding="utf-8")
        (tmp_path / "RULES-TECHNICAL.md").write_text("# Empty\n", encoding="utf-8")
        (tmp_path / "RULES-OPERATIONAL.md").write_text("# Empty\n", encoding="utf-8")

        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.get_all_rules.return_value = []

        with patch(
            "governance.mcp_tools.evidence.documents_entity.RULES_DIR", tmp_path
        ), patch(
            "governance.mcp_tools.evidence.documents_entity.get_typedb_client",
            return_value=mock_client,
        ):
            raw = doc_rule_get("RULE-MISSING")

        result = json.loads(raw)
        assert "error" in result

    def test_typedb_exception_handled(self, tmp_path):
        doc_rule_get = self._setup()
        (tmp_path / "RULES-GOVERNANCE.md").write_text("# Empty\n", encoding="utf-8")
        (tmp_path / "RULES-TECHNICAL.md").write_text("# Empty\n", encoding="utf-8")
        (tmp_path / "RULES-OPERATIONAL.md").write_text("# Empty\n", encoding="utf-8")

        mock_client = MagicMock()
        mock_client.connect.side_effect = Exception("connection failed")

        with patch(
            "governance.mcp_tools.evidence.documents_entity.RULES_DIR", tmp_path
        ), patch(
            "governance.mcp_tools.evidence.documents_entity.get_typedb_client",
            return_value=mock_client,
        ):
            raw = doc_rule_get("RULE-X")

        result = json.loads(raw)
        assert "error" in result

    def test_missing_rule_file_skipped(self, tmp_path):
        doc_rule_get = self._setup()
        # No rule files at all — directory exists but empty

        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.get_all_rules.return_value = []

        with patch(
            "governance.mcp_tools.evidence.documents_entity.RULES_DIR", tmp_path
        ), patch(
            "governance.mcp_tools.evidence.documents_entity.get_typedb_client",
            return_value=mock_client,
        ):
            raw = doc_rule_get("RULE-1")

        result = json.loads(raw)
        assert "error" in result


# ── doc_task_get ───────────────────────────────────────────


class TestDocTaskGet:
    def _setup(self):
        mcp = _CaptureMCP()
        register_entity_document_tools(mcp)
        return mcp.tools["doc_task_get"]

    def test_finds_task_in_backlog(self, tmp_path):
        doc_task_get = self._setup()
        content = "| P10.1 | Build auth | HIGH | OPEN |\n"
        backlog_file = tmp_path / "R&D-BACKLOG.md"
        backlog_file.write_text(content, encoding="utf-8")

        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.get_task.return_value = None

        with patch(
            "governance.mcp_tools.evidence.documents_entity.BACKLOG_DIR", tmp_path
        ), patch(
            "governance.mcp_tools.evidence.documents_entity.get_typedb_client",
            return_value=mock_client,
        ):
            raw = doc_task_get("P10.1")

        result = json.loads(raw)
        assert result["task_id"] == "P10.1"
        assert len(result["sources"]) >= 1
        assert "P10.1" in result["sources"][0]["line"]

    def test_typedb_task_found(self, tmp_path):
        doc_task_get = self._setup()

        mock_task = MagicMock()
        mock_task.id = "T-1"
        mock_task.name = "Test Task"
        mock_task.status = "IN_PROGRESS"
        mock_task.phase = "P10"
        mock_task.body = "Task body"
        mock_task.linked_rules = ["R-1"]
        mock_task.linked_sessions = ["S-1"]

        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.get_task.return_value = mock_task

        with patch(
            "governance.mcp_tools.evidence.documents_entity.BACKLOG_DIR",
            tmp_path,
        ), patch(
            "governance.mcp_tools.evidence.documents_entity.get_typedb_client",
            return_value=mock_client,
        ):
            raw = doc_task_get("T-1")

        result = json.loads(raw)
        assert result["typedb"]["id"] == "T-1"
        assert result["typedb"]["status"] == "IN_PROGRESS"

    def test_not_found_anywhere(self, tmp_path):
        doc_task_get = self._setup()

        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.get_task.return_value = None

        with patch(
            "governance.mcp_tools.evidence.documents_entity.BACKLOG_DIR",
            tmp_path,
        ), patch(
            "governance.mcp_tools.evidence.documents_entity.get_typedb_client",
            return_value=mock_client,
        ):
            raw = doc_task_get("MISSING-99")

        result = json.loads(raw)
        assert "error" in result

    def test_typedb_exception_handled(self, tmp_path):
        doc_task_get = self._setup()

        mock_client = MagicMock()
        mock_client.connect.side_effect = Exception("db down")

        with patch(
            "governance.mcp_tools.evidence.documents_entity.BACKLOG_DIR",
            tmp_path,
        ), patch(
            "governance.mcp_tools.evidence.documents_entity.get_typedb_client",
            return_value=mock_client,
        ):
            raw = doc_task_get("T-FAIL")

        result = json.loads(raw)
        assert "error" in result

    def test_multiple_matches_in_file(self, tmp_path):
        doc_task_get = self._setup()
        content = (
            "| P10.1 | Task A | HIGH | OPEN |\n"
            "| P10.2 | Task B | MED | DONE |\n"
            "| P10.1 | Task A ref | LOW | WIP |\n"
        )
        backlog_file = tmp_path / "R&D-BACKLOG.md"
        backlog_file.write_text(content, encoding="utf-8")

        mock_client = MagicMock()
        mock_client.connect.return_value = True
        mock_client.get_task.return_value = None

        with patch(
            "governance.mcp_tools.evidence.documents_entity.BACKLOG_DIR", tmp_path
        ), patch(
            "governance.mcp_tools.evidence.documents_entity.get_typedb_client",
            return_value=mock_client,
        ):
            raw = doc_task_get("P10.1")

        result = json.loads(raw)
        assert len(result["sources"]) == 2
