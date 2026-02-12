"""
Unit tests for Compat - Document Viewing Exports.

Per DOC-SIZE-01-v1: Tests for compat/documents.py module.
Tests: governance_get_document, governance_list_documents,
       governance_get_rule_document, governance_get_task_document.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch


class TestGovernanceGetDocument:
    """Tests for governance_get_document()."""

    def test_absolute_path(self, tmp_path):
        doc = tmp_path / "test.md"
        doc.write_text("# Hello\nWorld")
        from governance.compat.documents import governance_get_document
        result = json.loads(governance_get_document(str(doc)))
        assert result["content"] == "# Hello\nWorld"
        assert result["filename"] == "test.md"
        assert result["truncated"] is False

    def test_not_found(self):
        from governance.compat.documents import governance_get_document
        result = json.loads(governance_get_document("/nonexistent/file.md"))
        assert "error" in result

    def test_truncation(self, tmp_path):
        doc = tmp_path / "long.md"
        doc.write_text("\n".join(f"Line {i}" for i in range(100)))
        from governance.compat.documents import governance_get_document
        result = json.loads(governance_get_document(str(doc), max_lines=10))
        assert result["truncated"] is True
        assert result["line_count"] == 100

    def test_no_truncation_when_short(self, tmp_path):
        doc = tmp_path / "short.md"
        doc.write_text("one\ntwo\nthree")
        from governance.compat.documents import governance_get_document
        result = json.loads(governance_get_document(str(doc), max_lines=500))
        assert result["truncated"] is False


class TestGovernanceListDocuments:
    """Tests for governance_list_documents()."""

    def test_lists_files(self, tmp_path):
        (tmp_path / "a.md").write_text("A")
        (tmp_path / "b.md").write_text("B")
        (tmp_path / "c.txt").write_text("C")  # won't match *.md
        from governance.compat.documents import governance_list_documents
        result = json.loads(governance_list_documents(str(tmp_path), "*.md"))
        assert result["count"] == 2

    def test_not_found_dir(self):
        from governance.compat.documents import governance_list_documents
        result = json.loads(governance_list_documents("/nonexistent/dir"))
        assert "error" in result

    def test_recursive(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (tmp_path / "top.md").write_text("T")
        (sub / "nested.md").write_text("N")
        from governance.compat.documents import governance_list_documents
        result = json.loads(governance_list_documents(str(tmp_path), "*.md", recursive=True))
        assert result["count"] == 2

    def test_non_recursive(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (tmp_path / "top.md").write_text("T")
        (sub / "nested.md").write_text("N")
        from governance.compat.documents import governance_list_documents
        result = json.loads(governance_list_documents(str(tmp_path), "*.md", recursive=False))
        assert result["count"] == 1

    def test_has_size_bytes(self, tmp_path):
        (tmp_path / "a.md").write_text("Hello World")
        from governance.compat.documents import governance_list_documents
        result = json.loads(governance_list_documents(str(tmp_path), "*.md"))
        assert result["documents"][0]["size_bytes"] > 0


class TestGovernanceGetRuleDocument:
    """Tests for governance_get_rule_document()."""

    def test_not_found(self, tmp_path):
        with patch("governance.compat.documents.RULES_DIR", tmp_path):
            from governance.compat.documents import governance_get_rule_document
            result = json.loads(governance_get_rule_document("NONEXIST-RULE"))
            assert "error" in result

    def test_finds_rule_in_file(self, tmp_path):
        rule_file = tmp_path / "RULES-GOVERNANCE.md"
        rule_file.write_text("# Rules\n\n## RULE-001: Test Rule\nDescription here\n\n## RULE-002: Other\n")
        with patch("governance.compat.documents.RULES_DIR", tmp_path):
            from governance.compat.documents import governance_get_rule_document
            result = json.loads(governance_get_rule_document("RULE-001"))
            assert result["rule_id"] == "RULE-001"
            assert "Description here" in result["content"]


class TestGovernanceGetTaskDocument:
    """Tests for governance_get_task_document()."""

    def test_not_found(self, tmp_path):
        with patch("governance.compat.documents.BACKLOG_DIR", tmp_path):
            from governance.compat.documents import governance_get_task_document
            result = json.loads(governance_get_task_document("TASK-999"))
            assert "error" in result

    def test_finds_task_in_table(self, tmp_path):
        backlog = tmp_path / "R&D-BACKLOG.md"
        backlog.write_text("| ID | Status | Desc |\n| RD-001 | TODO | Fix bug |\n")
        with patch("governance.compat.documents.BACKLOG_DIR", tmp_path):
            from governance.compat.documents import governance_get_task_document
            result = json.loads(governance_get_task_document("RD-001"))
            assert result["task_id"] == "RD-001"
            assert len(result["sources"]) >= 1
