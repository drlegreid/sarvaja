"""
Tests for TypeDB-Document Sync Verification (EPIC-GOV-RULES-V3 P8).

TDD: Written BEFORE implementation.

Scenarios per plan BDD:
  - All sources match → empty discrepancies
  - TypeDB-only rules detected (no leaf file)
  - Leaf-only files detected (no TypeDB entry)
  - Index missing rules detected
  - API exposes sync report with counts
  - MCP tool provides same report
"""

import json
import os
from unittest.mock import patch, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_rule_dict(rule_id: str, name: str = "", category: str = "governance"):
    """Build a minimal rule response dict like list_rules() returns."""
    return {
        "id": rule_id,
        "name": name or rule_id,
        "category": category,
        "status": "ACTIVE",
        "priority": "HIGH",
    }


SAMPLE_RULES = ["SESSION-EVID-01-v1", "GOV-RULE-01-v1", "TEST-GUARD-01-v1"]


# ===========================================================================
# SyncVerifier unit tests
# ===========================================================================


class TestSyncVerifierAllMatch:
    """Scenario: All 3 sources have the same rules → empty discrepancies."""

    @patch("governance.services.rules_sync.list_rules")
    def test_all_sources_match_empty_discrepancies(self, mock_list, tmp_path):
        from governance.services.rules_sync import SyncVerifier

        # TypeDB returns 3 rules
        mock_list.return_value = {
            "items": [_make_rule_dict(r) for r in SAMPLE_RULES]
        }

        # Create matching leaf files
        leaf_dir = tmp_path / "docs" / "rules" / "leaf"
        leaf_dir.mkdir(parents=True)
        for r in SAMPLE_RULES:
            (leaf_dir / f"{r}.md").write_text(f"# {r}\nDirective text.")

        # Create matching index file
        index_dir = tmp_path / "docs" / "rules"
        index_content = "\n".join(
            f"| **{r}** | Name | HIGH |" for r in SAMPLE_RULES
        )
        (index_dir / "RULES-TEST.md").write_text(
            f"# Test Index\n\n{index_content}\n"
        )

        verifier = SyncVerifier(workspace_root=str(tmp_path))
        report = verifier.verify()

        assert report.typedb_only == []
        assert report.leaf_only == []
        assert report.index_gaps == []
        assert report.all_synced_count == 3


class TestSyncVerifierTypeDBOnly:
    """Scenario: Rules in TypeDB but no leaf file."""

    @patch("governance.services.rules_sync.list_rules")
    def test_typedb_only_rules_detected(self, mock_list, tmp_path):
        from governance.services.rules_sync import SyncVerifier

        mock_list.return_value = {
            "items": [
                _make_rule_dict("SESSION-EVID-01-v1"),
                _make_rule_dict("GHOST-RULE-01-v1"),  # no leaf
            ]
        }

        leaf_dir = tmp_path / "docs" / "rules" / "leaf"
        leaf_dir.mkdir(parents=True)
        (leaf_dir / "SESSION-EVID-01-v1.md").write_text("# Rule")

        # Index references both
        index_dir = tmp_path / "docs" / "rules"
        (index_dir / "RULES-TEST.md").write_text(
            "| **SESSION-EVID-01-v1** | x | HIGH |\n"
            "| **GHOST-RULE-01-v1** | x | HIGH |\n"
        )

        verifier = SyncVerifier(workspace_root=str(tmp_path))
        report = verifier.verify()

        assert "GHOST-RULE-01-v1" in report.typedb_only
        assert "SESSION-EVID-01-v1" not in report.typedb_only


class TestSyncVerifierLeafOnly:
    """Scenario: Leaf files with no corresponding TypeDB entry."""

    @patch("governance.services.rules_sync.list_rules")
    def test_leaf_only_files_detected(self, mock_list, tmp_path):
        from governance.services.rules_sync import SyncVerifier

        mock_list.return_value = {
            "items": [_make_rule_dict("SESSION-EVID-01-v1")]
        }

        leaf_dir = tmp_path / "docs" / "rules" / "leaf"
        leaf_dir.mkdir(parents=True)
        (leaf_dir / "SESSION-EVID-01-v1.md").write_text("# Rule")
        (leaf_dir / "ORPHAN-DOC-01-v1.md").write_text("# Orphan")

        index_dir = tmp_path / "docs" / "rules"
        (index_dir / "RULES-TEST.md").write_text(
            "| **SESSION-EVID-01-v1** | x | HIGH |\n"
            "| **ORPHAN-DOC-01-v1** | x | HIGH |\n"
        )

        verifier = SyncVerifier(workspace_root=str(tmp_path))
        report = verifier.verify()

        assert "ORPHAN-DOC-01-v1" in report.leaf_only
        assert "SESSION-EVID-01-v1" not in report.leaf_only


class TestSyncVerifierIndexGaps:
    """Scenario: Rules in TypeDB/leaf but missing from RULES-*.md indexes."""

    @patch("governance.services.rules_sync.list_rules")
    def test_index_missing_rules_detected(self, mock_list, tmp_path):
        from governance.services.rules_sync import SyncVerifier

        mock_list.return_value = {
            "items": [
                _make_rule_dict("SESSION-EVID-01-v1"),
                _make_rule_dict("UNLISTED-01-v1"),
            ]
        }

        leaf_dir = tmp_path / "docs" / "rules" / "leaf"
        leaf_dir.mkdir(parents=True)
        (leaf_dir / "SESSION-EVID-01-v1.md").write_text("# Rule")
        (leaf_dir / "UNLISTED-01-v1.md").write_text("# Unlisted")

        index_dir = tmp_path / "docs" / "rules"
        # Index only has SESSION-EVID-01-v1
        (index_dir / "RULES-TEST.md").write_text(
            "| **SESSION-EVID-01-v1** | x | HIGH |\n"
        )

        verifier = SyncVerifier(workspace_root=str(tmp_path))
        report = verifier.verify()

        assert "UNLISTED-01-v1" in report.index_gaps
        assert "SESSION-EVID-01-v1" not in report.index_gaps


class TestSyncReportStructure:
    """Verify SyncReport has correct counts and detail fields."""

    @patch("governance.services.rules_sync.list_rules")
    def test_sync_report_has_counts_and_details(self, mock_list, tmp_path):
        from governance.services.rules_sync import SyncVerifier

        mock_list.return_value = {
            "items": [
                _make_rule_dict("A-01-v1"),
                _make_rule_dict("B-01-v1"),
            ]
        }

        leaf_dir = tmp_path / "docs" / "rules" / "leaf"
        leaf_dir.mkdir(parents=True)
        (leaf_dir / "A-01-v1.md").write_text("# A")
        (leaf_dir / "C-01-v1.md").write_text("# C")

        index_dir = tmp_path / "docs" / "rules"
        (index_dir / "RULES-TEST.md").write_text("| **A-01-v1** | x | HIGH |\n")

        verifier = SyncVerifier(workspace_root=str(tmp_path))
        report = verifier.verify()
        d = report.to_dict()

        # Structure checks
        assert "typedb_only" in d
        assert "leaf_only" in d
        assert "index_gaps" in d
        assert "all_synced_count" in d
        assert "typedb_count" in d
        assert "leaf_count" in d
        assert "index_count" in d
        assert "synced" in d  # boolean: True if all discrepancies empty

        # Content checks
        assert d["typedb_count"] == 2
        assert d["leaf_count"] == 2
        assert "B-01-v1" in d["typedb_only"]
        assert "C-01-v1" in d["leaf_only"]


# ===========================================================================
# API route tests
# ===========================================================================


class TestSyncVerifyRoute:
    """Test GET /api/rules/sync/verify endpoint."""

    @patch("governance.routes.rules.sync.SyncVerifier")
    def test_api_endpoint_returns_sync_report(self, MockVerifier):
        from fastapi.testclient import TestClient
        from governance.routes.rules.sync import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router, prefix="/api")

        # Mock SyncVerifier
        mock_report = MagicMock()
        mock_report.to_dict.return_value = {
            "typedb_only": ["GHOST-01-v1"],
            "leaf_only": [],
            "index_gaps": [],
            "all_synced_count": 5,
            "typedb_count": 6,
            "leaf_count": 5,
            "index_count": 6,
            "synced": False,
        }
        MockVerifier.return_value.verify.return_value = mock_report

        client = TestClient(app)
        resp = client.get("/api/rules/sync/verify")

        assert resp.status_code == 200
        data = resp.json()
        assert data["typedb_only"] == ["GHOST-01-v1"]
        assert data["typedb_count"] == 6
        assert data["synced"] is False


# ===========================================================================
# MCP tool tests
# ===========================================================================


class TestSyncVerifyMCPTool:
    """Test rules_sync_verify MCP tool."""

    @patch("governance.services.rules_sync.SyncVerifier")
    @patch("governance.mcp_tools.rules_query.format_mcp_result", side_effect=lambda d: json.dumps(d))
    def test_mcp_tool_returns_same_report(self, mock_fmt, MockVerifier):
        from governance.mcp_tools.rules_query import register_rule_query_tools

        mock_report = MagicMock()
        mock_report.to_dict.return_value = {
            "typedb_only": [],
            "leaf_only": ["ORPHAN-01-v1"],
            "index_gaps": [],
            "all_synced_count": 10,
            "typedb_count": 10,
            "leaf_count": 11,
            "index_count": 11,
            "synced": False,
        }
        MockVerifier.return_value.verify.return_value = mock_report

        # Capture registered tools
        tools = {}

        class FakeMCP:
            def tool(self):
                def decorator(fn):
                    tools[fn.__name__] = fn
                    return fn
                return decorator

        mcp = FakeMCP()
        register_rule_query_tools(mcp)

        assert "rules_sync_verify" in tools
        result = tools["rules_sync_verify"]()
        parsed = json.loads(result)
        assert parsed["leaf_only"] == ["ORPHAN-01-v1"]
        assert parsed["synced"] is False


# ===========================================================================
# Edge cases
# ===========================================================================


class TestSyncEdgeCases:
    """Edge cases for sync verification."""

    @patch("governance.services.rules_sync.list_rules")
    def test_empty_typedb_all_leaf_only(self, mock_list, tmp_path):
        from governance.services.rules_sync import SyncVerifier

        mock_list.return_value = {"items": []}

        leaf_dir = tmp_path / "docs" / "rules" / "leaf"
        leaf_dir.mkdir(parents=True)
        (leaf_dir / "SOLO-01-v1.md").write_text("# Solo")

        index_dir = tmp_path / "docs" / "rules"
        (index_dir / "RULES-TEST.md").write_text("")

        verifier = SyncVerifier(workspace_root=str(tmp_path))
        report = verifier.verify()

        assert "SOLO-01-v1" in report.leaf_only
        assert report.all_synced_count == 0

    @patch("governance.services.rules_sync.list_rules")
    def test_no_leaf_dir_graceful(self, mock_list, tmp_path):
        """Missing leaf directory should not crash."""
        from governance.services.rules_sync import SyncVerifier

        mock_list.return_value = {"items": [_make_rule_dict("A-01-v1")]}

        # No leaf dir created — only index dir
        index_dir = tmp_path / "docs" / "rules"
        index_dir.mkdir(parents=True)
        (index_dir / "RULES-TEST.md").write_text("| **A-01-v1** | x | HIGH |\n")

        verifier = SyncVerifier(workspace_root=str(tmp_path))
        report = verifier.verify()

        assert report.leaf_only == []
        assert "A-01-v1" in report.typedb_only

    @patch("governance.services.rules_sync.list_rules")
    def test_typedb_connection_error_handled(self, mock_list, tmp_path):
        """TypeDB failure returns error in report, not crash."""
        from governance.services.rules_sync import SyncVerifier

        mock_list.side_effect = ConnectionError("TypeDB not connected")

        leaf_dir = tmp_path / "docs" / "rules" / "leaf"
        leaf_dir.mkdir(parents=True)

        index_dir = tmp_path / "docs" / "rules"
        (index_dir / "RULES-TEST.md").write_text("")

        verifier = SyncVerifier(workspace_root=str(tmp_path))
        report = verifier.verify()

        assert report.error is not None
        assert "TypeDB" in report.error
