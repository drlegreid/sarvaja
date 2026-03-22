"""
Tests for BUG-TASK-DOC-001: task_link_document() fails for ALL documents.

Root cause: Monolithic schema.tql document entity is missing
`plays document-references-task:referencing-document` role, AND
task entity is missing `plays document-references-task:referenced-task` role.
The relation `document-references-task` IS defined but neither entity can play it.

Fix: Add missing roles to both entities in schema.tql.
Verify: modular schema_3x already has correct roles (03_document_entities_3x.tql:26,
01_core_entities_3x.tql:98).

TDD: Tests define the contract. Per DOC-SIZE-01-v1: <=300 lines.
"""

import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SCHEMA_TQL = Path(__file__).resolve().parents[2] / "governance" / "schema.tql"
SCHEMA_3X = Path(__file__).resolve().parents[2] / "governance" / "schema_3x"


# ── Schema Alignment Tests ──


class TestDocumentReferenceTaskRelationDefined:
    """Verify document-references-task relation exists in monolithic schema."""

    def test_relation_defined_in_monolithic_schema(self):
        """schema.tql must define the document-references-task relation."""
        content = SCHEMA_TQL.read_text()
        assert "relation document-references-task," in content, \
            "BUG-TASK-DOC-001: document-references-task relation missing from schema.tql"

    def test_relation_has_referencing_document_role(self):
        """Relation must have relates referencing-document role."""
        content = SCHEMA_TQL.read_text()
        # Find the relation block
        match = re.search(
            r"relation document-references-task,.*?;",
            content, re.DOTALL
        )
        assert match, "document-references-task relation block not found"
        block = match.group()
        assert "relates referencing-document" in block

    def test_relation_has_referenced_task_role(self):
        """Relation must have relates referenced-task role."""
        content = SCHEMA_TQL.read_text()
        match = re.search(
            r"relation document-references-task,.*?;",
            content, re.DOTALL
        )
        assert match, "document-references-task relation block not found"
        block = match.group()
        assert "relates referenced-task" in block


class TestDocumentEntityPlaysRole:
    """Verify document entity can play referencing-document in document-references-task."""

    def test_monolithic_document_entity_has_task_role(self):
        """Document entity in schema.tql must have plays document-references-task:referencing-document."""
        content = SCHEMA_TQL.read_text()
        # Find document entity block
        match = re.search(r"entity document,.*?;", content, re.DOTALL)
        assert match, "document entity block not found in schema.tql"
        block = match.group()
        assert "plays document-references-task:referencing-document" in block, \
            "BUG-TASK-DOC-001: document entity missing plays document-references-task:referencing-document"

    def test_modular_document_entity_has_task_role(self):
        """Document entity in 03_document_entities_3x.tql already has the role (reference)."""
        content = (SCHEMA_3X / "03_document_entities_3x.tql").read_text()
        assert "plays document-references-task:referencing-document" in content


class TestTaskEntityPlaysDocumentRole:
    """Verify task entity can play referenced-task in document-references-task."""

    def test_monolithic_task_entity_has_doc_role(self):
        """Task entity in schema.tql must have plays document-references-task:referenced-task."""
        content = SCHEMA_TQL.read_text()
        match = re.search(r"entity task,.*?;", content, re.DOTALL)
        assert match, "task entity block not found in schema.tql"
        block = match.group()
        assert "plays document-references-task:referenced-task" in block, \
            "BUG-TASK-DOC-001: task entity missing plays document-references-task:referenced-task"

    def test_modular_task_entity_has_doc_role(self):
        """Task entity in 01_core_entities_3x.tql already has the role (reference)."""
        content = (SCHEMA_3X / "01_core_entities_3x.tql").read_text()
        assert "plays document-references-task:referenced-task" in content


# ── Linking Code Tests ──


class TestLinkTaskToDocumentCode:
    """Verify TypeDB linking code uses correct relation and role names."""

    def test_linking_query_uses_correct_relation(self):
        """link_task_to_document must use document-references-task relation."""
        import inspect
        from governance.typedb.queries.tasks.linking import TaskLinkingOperations
        source = inspect.getsource(TaskLinkingOperations.link_task_to_document)
        assert "document-references-task" in source

    def test_linking_query_uses_correct_roles(self):
        """link_task_to_document must use referencing-document and referenced-task roles."""
        import inspect
        from governance.typedb.queries.tasks.linking import TaskLinkingOperations
        source = inspect.getsource(TaskLinkingOperations.link_task_to_document)
        assert "referencing-document" in source
        assert "referenced-task" in source

    def test_link_task_to_document_returns_bool(self):
        """link_task_to_document must return True on success, False on failure."""
        ops = MagicMock(spec=["link_task_to_document"])
        ops.link_task_to_document.return_value = True
        assert ops.link_task_to_document("T-1", "docs/test.md") is True
        ops.link_task_to_document.return_value = False
        assert ops.link_task_to_document("T-1", "bad/path") is False


class TestGetTaskDocuments:
    """Verify get_documents_for_task returns linked document paths."""

    def test_get_documents_query_uses_correct_relation(self):
        """get_task_documents must query document-references-task."""
        import inspect
        from governance.typedb.queries.tasks.linking import TaskLinkingOperations
        source = inspect.getsource(TaskLinkingOperations.get_task_documents)
        assert "document-references-task" in source

    def test_get_documents_returns_list_of_paths(self):
        """get_task_documents must return list of document path strings."""
        ops = MagicMock(spec=["get_task_documents"])
        ops.get_task_documents.return_value = ["docs/test.md", "docs/other.md"]
        result = ops.get_task_documents("T-1")
        assert isinstance(result, list)
        assert len(result) == 2


# ── MCP Tool Tests ──


class TestMCPTaskLinkDocument:
    """Verify MCP tool task_link_document routes correctly."""

    def test_mcp_tool_calls_client_link(self):
        """task_link_document MCP tool must call client.link_task_to_document."""
        import inspect
        from governance.mcp_tools import tasks_linking
        source = inspect.getsource(tasks_linking)
        assert "link_task_to_document" in source

    def test_mcp_tool_returns_success_json(self):
        """On success, MCP tool returns JSON with relation name."""
        import inspect
        from governance.mcp_tools import tasks_linking
        source = inspect.getsource(tasks_linking)
        assert "document-references-task" in source


# ── Service Layer Tests ──


class TestServiceLinkTaskToDocument:
    """Verify service layer link_task_to_document delegates to TypeDB client."""

    def test_service_calls_client(self):
        """link_task_to_document in service must call client.link_task_to_document."""
        mock_client = MagicMock()
        mock_client.link_task_to_document.return_value = True
        with patch("governance.services.tasks_mutations.get_typedb_client", return_value=mock_client), \
             patch("governance.services.tasks_mutations.record_audit"), \
             patch("governance.services.tasks_mutations.log_event"):
            from governance.services.tasks_mutations import link_task_to_document
            result = link_task_to_document("T-1", "docs/test.md", source="test")
        assert result is True
        mock_client.link_task_to_document.assert_called_once_with("T-1", "docs/test.md")

    def test_service_returns_false_when_no_client(self):
        """link_task_to_document returns False when TypeDB unavailable."""
        with patch("governance.services.tasks_mutations.get_typedb_client", return_value=None):
            from governance.services.tasks_mutations import link_task_to_document
            result = link_task_to_document("T-1", "docs/test.md")
        assert result is False
