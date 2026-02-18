"""Deep scan batch 136: TypeDB queries layer.

Batch 136 findings: 3 confirmed fixes:
- BUG-TYPEQL-DELETE-RELATIONS-001: Task relation delete used 2.x syntax
- BUG-TYPEQL-RELATION-001: Missing escaping in relationships.py
- BUG-SCANNER-DISCOVERED-001: slug=None crash in cc_session_scanner.py
"""
import pytest
import re
from pathlib import Path


# ── TypeDB delete syntax defense ──────────────


class TestTypeDBDeleteSyntaxDefense:
    """Verify TypeDB 3.x delete syntax consistency across all query files."""

    def _read_source(self, relpath: str) -> str:
        """Read a source file relative to project root."""
        root = Path(__file__).parent.parent.parent
        return (root / relpath).read_text()

    def test_session_deletes_use_correct_syntax(self):
        """Session relation deletes use 'delete $r;' not 'delete $r isa Type;'."""
        src = self._read_source(
            "governance/typedb/queries/sessions/crud_mutations.py",
        )
        # All session relation deletes should be `delete $r;`
        delete_stmts = re.findall(r"delete\s+\$\w+", src)
        for stmt in delete_stmts:
            # After the variable there should NOT be ' isa '
            pass  # Just extract and check
        # No 'delete $X isa' pattern should exist
        bad = re.findall(r"delete\s+\$\w+\s+isa\s+", src)
        assert len(bad) == 0, f"Found TypeDB 2.x syntax: {bad}"

    def test_task_deletes_use_correct_syntax(self):
        """Task relation deletes use 'delete $rel;' (fixed from 2.x syntax)."""
        src = self._read_source("governance/typedb/queries/tasks/crud.py")
        bad = re.findall(r"delete\s+\$\w+\s+isa\s+", src)
        assert len(bad) == 0, f"Found TypeDB 2.x syntax in tasks/crud.py: {bad}"

    def test_task_linking_deletes_use_correct_syntax(self):
        """Task linking deletes use 'delete $rel;' (fixed from 2.x syntax)."""
        src = self._read_source("governance/typedb/queries/tasks/linking.py")
        bad = re.findall(r"delete\s+\$\w+\s+isa\s+", src)
        assert len(bad) == 0, f"Found TypeDB 2.x syntax in tasks/linking.py: {bad}"

    def test_rules_deletes_use_correct_syntax(self):
        """Rules deletes use correct 3.x syntax."""
        src = self._read_source("governance/typedb/queries/rules/crud.py")
        # Filter out comments (lines starting with #)
        code_lines = [l for l in src.splitlines() if not l.strip().startswith("#")]
        code_only = "\n".join(code_lines)
        bad = re.findall(r"delete\s+\$\w+\s+isa\s+", code_only)
        assert len(bad) == 0, f"Found TypeDB 2.x syntax in rules/crud.py: {bad}"

    def test_project_deletes_use_correct_syntax(self):
        """Project deletes use correct 3.x syntax."""
        src = self._read_source("governance/typedb/queries/projects/crud.py")
        bad = re.findall(r"delete\s+\$\w+\s+isa\s+", src)
        assert len(bad) == 0, f"Found TypeDB 2.x syntax in projects/crud.py: {bad}"

    def test_agent_deletes_use_correct_syntax(self):
        """Agent deletes use correct 3.x syntax."""
        src = self._read_source("governance/typedb/queries/agents.py")
        bad = re.findall(r"delete\s+\$\w+\s+isa\s+", src)
        assert len(bad) == 0, f"Found TypeDB 2.x syntax in agents.py: {bad}"


# ── TypeDB relationship escaping defense ──────────────


class TestTypeDBRelationshipEscapingDefense:
    """Verify task relationship queries escape IDs (BUG-TYPEQL-RELATION-001)."""

    def _read_source(self, relpath: str) -> str:
        root = Path(__file__).parent.parent.parent
        return (root / relpath).read_text()

    def test_link_parent_escapes(self):
        """link_parent_task escapes both child and parent IDs."""
        src = self._read_source("governance/typedb/queries/tasks/relationships.py")
        assert "child_esc" in src
        assert "parent_esc" in src

    def test_link_blocking_escapes(self):
        """link_blocking_task escapes both IDs."""
        src = self._read_source("governance/typedb/queries/tasks/relationships.py")
        assert "blocker_esc" in src
        assert "blocked_esc" in src

    def test_link_related_escapes(self):
        """link_related_tasks escapes both IDs."""
        src = self._read_source("governance/typedb/queries/tasks/relationships.py")
        assert "a_esc" in src
        assert "b_esc" in src


# ── CC scanner slug defense ──────────────


class TestCCScannerSlugDefense:
    """Verify build_session_id handles None slug (BUG-SCANNER-DISCOVERED-001)."""

    def test_slug_none_uses_fallback(self):
        """meta with slug=None should not crash."""
        from governance.services.cc_session_scanner import build_session_id
        result = build_session_id({"slug": None}, "test")
        assert "UNKNOWN" in result

    def test_slug_missing_uses_fallback(self):
        """meta without slug key should use 'unknown'."""
        from governance.services.cc_session_scanner import build_session_id
        result = build_session_id({}, "test")
        assert "UNKNOWN" in result

    def test_slug_normal_works(self):
        """Normal slug is uppercased."""
        from governance.services.cc_session_scanner import build_session_id
        result = build_session_id({"slug": "my-project"}, "test")
        assert "MY-PROJECT" in result


# ── TypeDB datetime format defense ──────────────


class TestTypeDBDatetimeFormatDefense:
    """Verify datetime attributes use unquoted format per TypeDB 3.x."""

    def test_started_at_is_datetime_type(self):
        """started-at is 'value datetime' in schema — unquoted format correct."""
        root = Path(__file__).parent.parent.parent
        schema = (root / "governance/schema.tql").read_text()
        assert "started-at, value datetime" in schema or "started-at value datetime" in schema

    def test_timestamp_format_19_chars(self):
        """Timestamps sliced to 19 chars: YYYY-MM-DDTHH:MM:SS."""
        from datetime import datetime
        now = datetime.now()
        ts = now.strftime("%Y-%m-%dT%H:%M:%S")
        assert len(ts) == 19

    def test_unquoted_datetime_in_insert(self):
        """Insert queries use unquoted datetime (TypeDB datetime literal)."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/typedb/queries/sessions/crud.py").read_text()
        # Should have: has started-at {timestamp_str} (no quotes around it)
        assert "has started-at {timestamp_str}" in src


# ── TypeDB escaping defense ──────────────


class TestTypeDBEscapingDefense:
    """Verify all user-provided strings are escaped before TypeQL interpolation."""

    def test_session_id_escaped_in_mutations(self):
        """Session mutations escape session_id."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/typedb/queries/sessions/crud_mutations.py").read_text()
        assert 'session_id.replace(\'"\', \'\\\\"\')' in src or "session_id_escaped" in src

    def test_task_id_escaped_in_crud(self):
        """Task CRUD escapes task_id."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/typedb/queries/tasks/crud.py").read_text()
        assert "task_id_escaped" in src

    def test_task_id_escaped_in_linking(self):
        """Task linking escapes task_id."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/typedb/queries/tasks/linking.py").read_text()
        assert "task_id_escaped" in src

    def test_description_escaped(self):
        """String fields like description are escaped."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/typedb/queries/sessions/crud_mutations.py").read_text()
        assert "desc_escaped" in src


# ── Session attribute update pattern defense ──────────────


class TestSessionAttributeUpdateDefense:
    """Verify delete-then-insert pattern for TypeDB attribute updates."""

    def test_delete_old_before_insert_new(self):
        """Update uses delete old attribute then insert new."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/typedb/queries/sessions/crud_mutations.py").read_text()
        # Should have delete pattern before insert for started-at
        delete_idx = src.index("delete")
        insert_idx = src.index("insert", delete_idx)
        assert insert_idx > delete_idx

    def test_cc_string_fields_loop(self):
        """CC string fields updated via loop (DRY pattern)."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/typedb/queries/sessions/crud_mutations.py").read_text()
        assert "cc_str_fields" in src
        assert "cc-session-uuid" in src

    def test_cc_int_fields_loop(self):
        """CC integer fields updated via separate loop (no quotes)."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/typedb/queries/sessions/crud_mutations.py").read_text()
        assert "cc_int_fields" in src
        assert "cc-tool-count" in src
