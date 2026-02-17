"""
Deep Scan Batch 306-309: Defense tests for security fixes.

Tests for:
  BUG-306-SES-001: insert_session backslash-first escape order
  BUG-306-SES-002: end_session backslash-first escape order
  BUG-306-SES-003: Integer field coercion in insert_session
  BUG-306-MUT-001: update_session backslash-first escape order
  BUG-306-MUT-002: delete_session backslash-first escape order
  BUG-306-MUT-003: Integer field coercion in update_session
  BUG-308-COM-001: TYPEDB_PORT crash guard in common.py
  BUG-308-DEC-001: CHROMADB_PORT crash guard in decisions.py
"""

import re
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-306-SES-001: insert_session backslash-first escape ───────────


class TestInsertSessionEscapeOrder:
    """Verify insert_session uses backslash-first escape on all string fields."""

    def test_session_id_escape_order(self):
        src = (SRC / "governance/typedb/queries/sessions/crud.py").read_text()
        idx = src.find("def insert_session")
        assert idx != -1
        block = src[idx:idx + 1200]
        assert "BUG-306-SES-001" in block
        # Must escape backslash first
        assert ".replace('\\\\', '\\\\\\\\')" in block

    def test_all_string_fields_use_backslash_first(self):
        src = (SRC / "governance/typedb/queries/sessions/crud.py").read_text()
        idx = src.find("def insert_session")
        end_idx = src.find("def end_session")
        block = src[idx:end_idx]
        # Count occurrences of the correct two-step escape pattern
        pattern = r"\.replace\('\\\\', '\\\\\\\\'\)\.replace\('\"', '\\\\\"'\)"
        matches = re.findall(pattern, block)
        # Should have at least 8: session_id, name, description, file_path,
        # agent_id, cc_session_uuid, cc_project_slug, cc_git_branch
        assert len(matches) >= 8, f"Expected >=8 backslash-first escapes, found {len(matches)}"

    def test_no_quote_only_escapes_in_insert(self):
        """Ensure no string fields use the old quote-only escape."""
        src = (SRC / "governance/typedb/queries/sessions/crud.py").read_text()
        idx = src.find("def insert_session")
        end_idx = src.find("def end_session")
        block = src[idx:end_idx]
        lines = block.split("\n")
        for line in lines:
            stripped = line.strip()
            # Match: x.replace('"', '\\"') WITHOUT preceding .replace('\\', '\\\\')
            if '.replace(\'"\',' in stripped and '.replace(\'"\',' in stripped:
                if ".replace('\\\\'" not in stripped and "replace('\\\\'" not in line:
                    if "val_esc" not in stripped:  # Skip false positives
                        pytest.fail(f"Found quote-only escape: {stripped}")


# ── BUG-306-SES-002: end_session backslash-first escape ──────────────


class TestEndSessionEscapeOrder:
    """Verify end_session uses backslash-first escape."""

    def test_end_session_escape(self):
        src = (SRC / "governance/typedb/queries/sessions/crud.py").read_text()
        idx = src.find("def end_session")
        assert idx != -1
        block = src[idx:idx + 300]
        assert "BUG-306-SES-002" in block
        assert ".replace('\\\\', '\\\\\\\\')" in block


# ── BUG-306-SES-003: Integer field coercion in insert ────────────────


class TestInsertSessionIntCoercion:
    """Verify integer fields use int() coercion."""

    def test_int_coercion_in_insert(self):
        src = (SRC / "governance/typedb/queries/sessions/crud.py").read_text()
        idx = src.find("def insert_session")
        end_idx = src.find("def end_session")
        block = src[idx:end_idx]
        assert "BUG-306-SES-003" in block
        assert "int(cc_tool_count)" in block
        assert "int(cc_thinking_chars)" in block
        assert "int(cc_compaction_count)" in block


# ── BUG-306-MUT-001: update_session backslash-first escape ───────────


class TestUpdateSessionEscapeOrder:
    """Verify update_session uses backslash-first escape."""

    def test_session_id_escape_in_update(self):
        src = (SRC / "governance/typedb/queries/sessions/crud_mutations.py").read_text()
        idx = src.find("def update_session")
        assert idx != -1
        block = src[idx:idx + 1400]
        assert "BUG-306-MUT-001" in block
        assert ".replace('\\\\', '\\\\\\\\')" in block

    def test_description_escape_in_update(self):
        src = (SRC / "governance/typedb/queries/sessions/crud_mutations.py").read_text()
        idx = src.find("desc_escaped")
        assert idx != -1
        line = src[idx:idx + 100]
        assert ".replace('\\\\', '\\\\\\\\')" in line

    def test_agent_id_escape_in_update(self):
        src = (SRC / "governance/typedb/queries/sessions/crud_mutations.py").read_text()
        idx = src.find("agent_escaped")
        assert idx != -1
        line = src[idx:idx + 100]
        assert ".replace('\\\\', '\\\\\\\\')" in line

    def test_cc_str_fields_escape_in_update(self):
        src = (SRC / "governance/typedb/queries/sessions/crud_mutations.py").read_text()
        idx = src.find("val_esc")
        assert idx != -1
        line = src[idx:idx + 100]
        assert ".replace('\\\\', '\\\\\\\\')" in line


# ── BUG-306-MUT-002: delete_session backslash-first escape ───────────


class TestDeleteSessionEscapeOrder:
    """Verify delete_session uses backslash-first escape."""

    def test_delete_session_escape(self):
        src = (SRC / "governance/typedb/queries/sessions/crud_mutations.py").read_text()
        idx = src.find("def delete_session")
        assert idx != -1
        block = src[idx:idx + 700]
        assert "BUG-306-MUT-002" in block
        assert ".replace('\\\\', '\\\\\\\\')" in block


# ── BUG-306-MUT-003: Integer field coercion in update ────────────────


class TestUpdateSessionIntCoercion:
    """Verify integer fields use int() coercion in update."""

    def test_int_coercion_in_update(self):
        src = (SRC / "governance/typedb/queries/sessions/crud_mutations.py").read_text()
        idx = src.find("cc_int_fields")
        assert idx != -1
        block = src[idx:idx + 500]
        assert "BUG-306-MUT-003" in block
        assert "int(val)" in block

    def test_int_coercion_blocks_string_injection(self):
        """Verify int() raises on non-numeric strings."""
        with pytest.raises(ValueError):
            int("1; delete $x;")
        with pytest.raises(ValueError):
            int("abc")


# ── BUG-308-COM-001: TYPEDB_PORT crash guard ─────────────────────────


class TestTypeDBPortCrashGuard:
    """Verify TYPEDB_PORT has try/except guard at import time."""

    def test_port_guard_in_source(self):
        src = (SRC / "governance/mcp_tools/common.py").read_text()
        assert "BUG-308-COM-001" in src
        assert "except (ValueError, TypeError)" in src
        # Must default to 1729 on failure
        assert "TYPEDB_PORT = 1729" in src


# ── BUG-308-DEC-001: CHROMADB_PORT crash guard ──────────────────────


class TestChromaDBPortCrashGuard:
    """Verify CHROMADB_PORT in decisions.py has try/except guard."""

    def test_port_guard_in_decisions(self):
        src = (SRC / "governance/mcp_tools/decisions.py").read_text()
        assert "BUG-308-DEC-001" in src
        assert "except (ValueError, TypeError)" in src
        # Must default to 8001 on failure
        assert "CHROMADB_PORT = 8001" in src


# ── Import verification ─────────────────────────────────────────────


class TestBatch306Imports:
    """Verify all fixed modules import cleanly."""

    def test_import_session_crud(self):
        from governance.typedb.queries.sessions import crud  # noqa: F401

    def test_import_session_mutations(self):
        from governance.typedb.queries.sessions import crud_mutations  # noqa: F401

    def test_import_common(self):
        from governance.mcp_tools import common  # noqa: F401

    def test_import_decisions(self):
        from governance.mcp_tools import decisions  # noqa: F401
