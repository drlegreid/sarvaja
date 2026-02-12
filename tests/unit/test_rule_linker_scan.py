"""
Unit tests for Rule Document Scanning.

Per DOC-SIZE-01-v1: Tests for rule_linker_scan.py module.
Tests: RuleDocument, extract_rule_ids, scan_rule_documents.
"""

import os
import pytest
from unittest.mock import patch

from governance.rule_linker_scan import (
    RuleDocument,
    extract_rule_ids,
    scan_rule_documents,
)


class TestRuleDocument:
    """Tests for RuleDocument dataclass."""

    def test_basic(self):
        doc = RuleDocument(
            document_id="DOC-TEST",
            title="Test",
            path="docs/rules/test.md",
            document_type="rule-document",
            storage="filesystem",
        )
        assert doc.document_id == "DOC-TEST"
        assert doc.rule_ids is None
        assert doc.last_modified is None

    def test_with_rule_ids(self):
        doc = RuleDocument(
            document_id="DOC-TEST",
            title="Test",
            path="docs/rules/test.md",
            document_type="rule-document",
            storage="filesystem",
            rule_ids=["RULE-001", "RULE-002"],
        )
        assert len(doc.rule_ids) == 2


class TestExtractRuleIds:
    """Tests for extract_rule_ids()."""

    def test_legacy_ids(self):
        content = "This references RULE-001 and RULE-042."
        ids = extract_rule_ids(content)
        assert "RULE-001" in ids
        assert "RULE-042" in ids

    def test_sorted_by_number(self):
        content = "RULE-042 then RULE-001 then RULE-010"
        ids = extract_rule_ids(content)
        assert ids == ["RULE-001", "RULE-010", "RULE-042"]

    def test_unique(self):
        content = "RULE-001 appears twice: RULE-001"
        ids = extract_rule_ids(content)
        assert ids.count("RULE-001") == 1

    def test_no_rules(self):
        content = "No rules referenced here."
        ids = extract_rule_ids(content)
        assert ids == []

    def test_semantic_ids_with_mapping(self):
        # This test only works if SEMANTIC_TO_LEGACY has entries
        from governance.rule_linker_ids import SEMANTIC_TO_LEGACY
        if SEMANTIC_TO_LEGACY:
            semantic_id = next(iter(SEMANTIC_TO_LEGACY.keys()))
            content = f"Rule: {semantic_id}"
            ids = extract_rule_ids(content)
            assert SEMANTIC_TO_LEGACY[semantic_id] in ids

    def test_unknown_semantic_id_ignored(self):
        content = "Reference to UNKNOWN-TEST-99-v99"
        ids = extract_rule_ids(content)
        # Unknown semantic IDs should not be added
        assert all(i.startswith("RULE-") for i in ids)


class TestScanRuleDocuments:
    """Tests for scan_rule_documents()."""

    def test_empty_dir(self, tmp_path):
        rules_dir = tmp_path / "docs" / "rules"
        rules_dir.mkdir(parents=True)
        with patch("governance.rule_linker_scan.WORKSPACE_ROOT", str(tmp_path)):
            docs = scan_rule_documents()
            assert docs == []

    def test_finds_markdown(self, tmp_path):
        rules_dir = tmp_path / "docs" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "test.md").write_text("# Test\nContent with RULE-001")
        with patch("governance.rule_linker_scan.WORKSPACE_ROOT", str(tmp_path)):
            docs = scan_rule_documents()
            assert len(docs) == 1
            assert docs[0].document_type == "rule-document"
            assert "RULE-001" in (docs[0].rule_ids or [])

    def test_skips_non_md(self, tmp_path):
        rules_dir = tmp_path / "docs" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "test.txt").write_text("Not markdown")
        (rules_dir / "test.md").write_text("# Is markdown")
        with patch("governance.rule_linker_scan.WORKSPACE_ROOT", str(tmp_path)):
            docs = scan_rule_documents()
            assert len(docs) == 1

    def test_scans_subdirs(self, tmp_path):
        rules_dir = tmp_path / "docs" / "rules"
        leaf = rules_dir / "leaf"
        leaf.mkdir(parents=True)
        (rules_dir / "top.md").write_text("# Top")
        (leaf / "nested.md").write_text("# Nested")
        with patch("governance.rule_linker_scan.WORKSPACE_ROOT", str(tmp_path)):
            docs = scan_rule_documents(include_subdirs=True)
            assert len(docs) == 2

    def test_no_subdirs(self, tmp_path):
        rules_dir = tmp_path / "docs" / "rules"
        leaf = rules_dir / "leaf"
        leaf.mkdir(parents=True)
        (rules_dir / "top.md").write_text("# Top")
        (leaf / "nested.md").write_text("# Nested")
        with patch("governance.rule_linker_scan.WORKSPACE_ROOT", str(tmp_path)):
            docs = scan_rule_documents(include_subdirs=False)
            assert len(docs) == 1

    def test_extracts_title(self, tmp_path):
        rules_dir = tmp_path / "docs" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "test.md").write_text("# My Rule Title\nBody text")
        with patch("governance.rule_linker_scan.WORKSPACE_ROOT", str(tmp_path)):
            docs = scan_rule_documents()
            assert docs[0].title == "My Rule Title"

    def test_missing_rules_dir(self, tmp_path):
        with patch("governance.rule_linker_scan.WORKSPACE_ROOT", str(tmp_path)):
            docs = scan_rule_documents()
            assert docs == []

    def test_doc_id_format(self, tmp_path):
        rules_dir = tmp_path / "docs" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "my-rules.md").write_text("# Rules")
        with patch("governance.rule_linker_scan.WORKSPACE_ROOT", str(tmp_path)):
            docs = scan_rule_documents()
            assert docs[0].document_id.startswith("DOC-")

    def test_skips_hidden_files(self, tmp_path):
        rules_dir = tmp_path / "docs" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / ".hidden.md").write_text("# Hidden")
        (rules_dir / "visible.md").write_text("# Visible")
        with patch("governance.rule_linker_scan.WORKSPACE_ROOT", str(tmp_path)):
            docs = scan_rule_documents()
            assert len(docs) == 1
            assert docs[0].title == "Visible"
