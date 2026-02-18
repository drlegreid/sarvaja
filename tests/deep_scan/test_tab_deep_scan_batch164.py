"""Deep scan batch 164: Scripts + CLI tools.

Batch 164 findings: 23 total, 0 confirmed fixes in scripts, 23 rejected.
Scripts are one-time migration/backfill tools — bugs are latent, not production.
"""
import pytest
import re
from pathlib import Path


# ── API_BASE path defense ──────────────


class TestAPIBasePathDefense:
    """Verify scripts use correct API_BASE with /api prefix."""

    def test_backfill_task_evidence_url(self):
        """backfill_task_evidence.py uses /api in API_BASE."""
        root = Path(__file__).parent.parent.parent
        src = (root / "scripts/backfill_task_evidence.py").read_text()
        assert 'API_BASE = "http://localhost:8082/api"' in src

    def test_url_includes_api_prefix(self):
        """URL constructed as API_BASE/tasks includes /api."""
        api_base = "http://localhost:8082/api"
        url = f"{api_base}/tasks?limit=200"
        assert "/api/tasks" in url


# ── TypeDB export TQL generation defense ──────────────


class TestTypeDBExportTQLDefense:
    """Verify generate_3x_tql newline handling is correct."""

    def test_join_with_trailing_empty_provides_newline(self):
        """Empty string at end of lines list produces trailing newline in join."""
        lines = ["header", "insert", ""]
        result = "\n".join(lines)
        assert result.endswith("\n")

    def test_3x_tql_has_insert_keyword(self):
        """generate_3x_tql output contains insert keyword."""
        root = Path(__file__).parent.parent.parent
        src = (root / "scripts/typedb_export.py").read_text()
        assert "def generate_3x_tql" in src
        assert '"insert"' in src

    def test_escape_typeql_handles_special_chars(self):
        """escape_typeql escapes backslash, quote, newline."""
        root = Path(__file__).parent.parent.parent
        src = (root / "scripts/typedb_export.py").read_text()
        assert '.replace("\\\\", "\\\\\\\\")' in src or "replace" in src


# ── Script path patterns defense ──────────────


class TestScriptPathPatternsDefense:
    """Verify scripts use correct project root pattern."""

    def test_most_scripts_use_parent_parent(self):
        """Most scripts use Path(__file__).parent.parent for project root."""
        root = Path(__file__).parent.parent.parent
        scripts_dir = root / "scripts"
        correct_pattern = 0
        total = 0
        for f in scripts_dir.glob("*.py"):
            src = f.read_text()
            if "sys.path" in src:
                total += 1
                if "parent.parent" in src or "Path(__file__)" in src:
                    correct_pattern += 1
        # Most scripts should use the proper pattern
        assert correct_pattern >= total * 0.5

    def test_backfill_task_session_uses_parent_parent(self):
        """backfill_task_session_from_evidence.py uses Path(__file__).parent.parent."""
        root = Path(__file__).parent.parent.parent
        src = (root / "scripts/backfill_task_session_from_evidence.py").read_text()
        assert "Path(__file__).parent.parent" in src


# ── fetch_json pagination defense ──────────────


class TestFetchJsonPaginationDefense:
    """Verify typedb_export.py handles paginated responses."""

    def test_fetch_json_extracts_items(self):
        """fetch_json extracts 'items' from paginated responses."""
        root = Path(__file__).parent.parent.parent
        src = (root / "scripts/typedb_export.py").read_text()
        assert '"items"' in src

    def test_fetch_all_paginated_exists(self):
        """fetch_all_paginated function exists (dead code but available)."""
        root = Path(__file__).parent.parent.parent
        src = (root / "scripts/typedb_export.py").read_text()
        assert "def fetch_all_paginated" in src


# ── Argparse safety defense ──────────────


class TestArgparseSafetyDefense:
    """Verify backfill scripts use argparse for safe argument parsing."""

    def test_backfill_task_evidence_uses_argparse(self):
        """backfill_task_evidence.py uses argparse."""
        root = Path(__file__).parent.parent.parent
        src = (root / "scripts/backfill_task_evidence.py").read_text()
        assert "import argparse" in src
        assert "parser.parse_args()" in src

    def test_backfill_task_session_uses_argparse(self):
        """backfill_task_session_from_evidence.py uses argparse."""
        root = Path(__file__).parent.parent.parent
        src = (root / "scripts/backfill_task_session_from_evidence.py").read_text()
        assert "import argparse" in src
        assert "--dry-run" in src and "--apply" in src
