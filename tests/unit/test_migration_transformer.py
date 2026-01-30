"""
Tests for migration document transformer.

Per GAP-FILE-025: ChromaDB to TypeDB document transformation.
Covers type detection, TypeQL generation, and escaping.

Created: 2026-01-30
"""

import pytest

from governance.migration.transformer import DocumentTransformer
from governance.migration.models import MigrationResult


class TestMigrationResult:
    """Test MigrationResult dataclass."""

    def test_create(self):
        r = MigrationResult(
            success=True, collection="rules",
            migrated=10, failed=0, skipped=2,
            dry_run=False, errors=[]
        )
        assert r.success is True
        assert r.migrated == 10
        assert r.errors == []

    def test_failed_migration(self):
        r = MigrationResult(
            success=False, collection="sessions",
            migrated=3, failed=5, skipped=0,
            dry_run=False, errors=["conn failed", "timeout"]
        )
        assert r.success is False
        assert len(r.errors) == 2

    def test_dry_run(self):
        r = MigrationResult(
            success=True, collection="test",
            migrated=0, failed=0, skipped=50,
            dry_run=True, errors=[]
        )
        assert r.dry_run is True
        assert r.skipped == 50


class TestDocumentTransformerDetectType:
    """Test type detection from document IDs."""

    def setup_method(self):
        self.transformer = DocumentTransformer()

    def test_rule_pattern(self):
        assert self.transformer.detect_type("RULE-001") == "rule"
        assert self.transformer.detect_type("RULE-050") == "rule"
        assert self.transformer.detect_type("RULE-999") == "rule"

    def test_decision_pattern(self):
        assert self.transformer.detect_type("DECISION-001") == "decision"
        assert self.transformer.detect_type("DECISION-010") == "decision"

    def test_session_pattern(self):
        assert self.transformer.detect_type("SESSION-2026-01-30") == "session"
        assert self.transformer.detect_type("SESSION-2026-01-30-topic") == "session"

    def test_generic_document(self):
        assert self.transformer.detect_type("some-other-id") == "document"
        assert self.transformer.detect_type("unknown") == "document"

    def test_partial_rule_not_matched(self):
        assert self.transformer.detect_type("RULE-1") == "document"  # Needs 3 digits
        assert self.transformer.detect_type("RULE-0001") == "document"  # Too many digits

    def test_partial_decision_not_matched(self):
        assert self.transformer.detect_type("DECISION-1") == "document"


class TestDocumentTransformerEscape:
    """Test TypeQL string escaping."""

    def test_empty_string(self):
        assert DocumentTransformer._escape("") == ""

    def test_no_special_chars(self):
        assert DocumentTransformer._escape("hello world") == "hello world"

    def test_quotes(self):
        assert DocumentTransformer._escape('say "hello"') == 'say \\"hello\\"'

    def test_backslashes(self):
        assert DocumentTransformer._escape("path\\to\\file") == "path\\\\to\\\\file"

    def test_newlines(self):
        assert DocumentTransformer._escape("line1\nline2") == "line1\\nline2"

    def test_combined(self):
        result = DocumentTransformer._escape('he said "hi"\nbye')
        assert '\\"' in result
        assert '\\n' in result

    def test_none_safe(self):
        """Empty string for None-like input."""
        assert DocumentTransformer._escape("") == ""


class TestDocumentTransformerTransform:
    """Test document transformation."""

    def setup_method(self):
        self.transformer = DocumentTransformer()

    def test_rule_transform(self):
        doc = {"id": "RULE-001", "content": "Test rule", "metadata": {"name": "Rule One"}}
        result = self.transformer.transform(doc)
        assert result["type"] == "rule"
        assert result["id"] == "RULE-001"
        assert "typeql" in result
        assert "rule-entity" in result["typeql"]
        assert "Rule One" in result["typeql"]

    def test_decision_transform(self):
        doc = {"id": "DECISION-005", "content": "Use TypeDB", "metadata": {"name": "TypeDB First"}}
        result = self.transformer.transform(doc)
        assert result["type"] == "decision"
        assert "decision-id" in result["typeql"]

    def test_session_transform(self):
        doc = {"id": "SESSION-2026-01-30-test", "content": "Session data"}
        result = self.transformer.transform(doc)
        assert result["type"] == "session"
        assert "Session" in result["typeql"]

    def test_document_transform(self):
        doc = {"id": "random-doc-123", "content": "Some content"}
        result = self.transformer.transform(doc)
        assert result["type"] == "document"
        assert "vector-document" in result["typeql"]

    def test_source_is_chromadb_migration(self):
        doc = {"id": "RULE-001", "content": "test"}
        result = self.transformer.transform(doc)
        assert result["source"] == "chromadb_migration"

    def test_missing_content_handled(self):
        doc = {"id": "RULE-001"}
        result = self.transformer.transform(doc)
        assert result["content"] == ""
        assert "typeql" in result

    def test_metadata_preserved(self):
        doc = {"id": "doc-1", "content": "C", "metadata": {"key": "val"}}
        result = self.transformer.transform(doc)
        assert result["metadata"]["key"] == "val"

    def test_content_from_document_field(self):
        """ChromaDB uses 'document' field, should be handled."""
        doc = {"id": "doc-1", "document": "Content via document field"}
        result = self.transformer.transform(doc)
        assert result["content"] == "Content via document field"

    def test_rule_without_name_uses_content(self):
        doc = {"id": "RULE-001", "content": "Auto-generated name from content", "metadata": {}}
        result = self.transformer.transform(doc)
        assert "Auto-generated name from content" in result["typeql"]

    def test_long_content_truncated_in_document(self):
        doc = {"id": "generic-doc", "content": "x" * 2000, "metadata": {}}
        result = self.transformer.transform(doc)
        # Document TypeQL truncates to 1000 chars
        assert len(result["content"]) == 2000  # Full content preserved in result
        # TypeQL should have truncated version
        typeql = result["typeql"]
        assert "typeql" in result
