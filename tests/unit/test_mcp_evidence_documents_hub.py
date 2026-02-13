"""
Unit tests for Evidence Documents Hub + Common Constants.

Batch 154: Tests for governance/mcp_tools/evidence/documents.py (re-export hub)
and governance/mcp_tools/evidence/common.py (shared path constants).
"""

from pathlib import Path
from unittest.mock import patch, call

import pytest

from governance.mcp_tools.evidence.common import (
    EVIDENCE_DIR, DOCS_DIR, BACKLOG_DIR, RULES_DIR, GAPS_DIR, TASKS_DIR,
)
from governance.mcp_tools.evidence.documents import (
    register_document_tools,
    FILE_TYPE_MAP,
)


# ── common.py constants ─────────────────────────────────

class TestCommonConstants:
    def test_evidence_dir(self):
        assert EVIDENCE_DIR == Path("evidence")

    def test_docs_dir(self):
        assert DOCS_DIR == Path("docs")

    def test_backlog_dir(self):
        assert BACKLOG_DIR == Path("docs/backlog")

    def test_rules_dir(self):
        assert RULES_DIR == Path("docs/rules")

    def test_gaps_dir(self):
        assert GAPS_DIR == Path("docs/gaps")

    def test_tasks_dir(self):
        assert TASKS_DIR == Path("docs/tasks")

    def test_all_are_path_objects(self):
        for p in [EVIDENCE_DIR, DOCS_DIR, BACKLOG_DIR, RULES_DIR, GAPS_DIR, TASKS_DIR]:
            assert isinstance(p, Path)


# ── documents.py re-export hub ───────────────────────────

class TestDocumentsHub:
    def test_file_type_map_reexported(self):
        assert isinstance(FILE_TYPE_MAP, dict)
        assert ".md" in FILE_TYPE_MAP

    @patch("governance.mcp_tools.evidence.documents.register_validate_document_tools")
    @patch("governance.mcp_tools.evidence.documents.register_link_document_tools")
    @patch("governance.mcp_tools.evidence.documents.register_entity_document_tools")
    @patch("governance.mcp_tools.evidence.documents.register_core_document_tools")
    def test_register_delegates_to_all_four(self, mock_core, mock_entity,
                                             mock_links, mock_validate):
        fake_mcp = object()
        register_document_tools(fake_mcp)
        mock_core.assert_called_once_with(fake_mcp)
        mock_entity.assert_called_once_with(fake_mcp)
        mock_links.assert_called_once_with(fake_mcp)
        mock_validate.assert_called_once_with(fake_mcp)

    @patch("governance.mcp_tools.evidence.documents.register_validate_document_tools")
    @patch("governance.mcp_tools.evidence.documents.register_link_document_tools")
    @patch("governance.mcp_tools.evidence.documents.register_entity_document_tools")
    @patch("governance.mcp_tools.evidence.documents.register_core_document_tools")
    def test_register_order(self, mock_core, mock_entity, mock_links, mock_validate):
        """Core → Entity → Links → Validate registration order."""
        call_order = []
        mock_core.side_effect = lambda m: call_order.append("core")
        mock_entity.side_effect = lambda m: call_order.append("entity")
        mock_links.side_effect = lambda m: call_order.append("links")
        mock_validate.side_effect = lambda m: call_order.append("validate")

        register_document_tools(object())
        assert call_order == ["core", "entity", "links", "validate"]
