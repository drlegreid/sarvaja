"""
Deep Scan Batch 314-317: Defense tests for security fixes.

Tests for:
  BUG-314-AGT-001: agents.py backslash-first escape (6 sites)
  BUG-314-DET-001: tasks/details.py backslash-first escape (1 site)
"""

import re
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-314-AGT-001: agents.py backslash-first escape ──────────────────


class TestAgentQueriesEscapeOrder:
    """Verify agents.py uses backslash-first escape on all string fields."""

    def _read_src(self):
        return (SRC / "governance/typedb/queries/agents.py").read_text()

    def test_get_agent_escape(self):
        src = self._read_src()
        idx = src.find("def get_agent")
        assert idx != -1
        block = src[idx:idx + 400]
        assert "BUG-314-AGT-001" in block
        assert ".replace('\\\\', '\\\\\\\\')" in block

    def test_insert_agent_escape(self):
        src = self._read_src()
        idx = src.find("def insert_agent")
        end_idx = src.find("def delete_agent")
        assert idx != -1
        block = src[idx:end_idx]
        assert "BUG-314-AGT-001" in block
        # Should have 3 backslash-first escapes: agent_id, name, agent_type
        pattern = r"\.replace\('\\\\', '\\\\\\\\'\)"
        matches = re.findall(pattern, block)
        assert len(matches) >= 3, f"Expected >=3 backslash-first in insert_agent, got {len(matches)}"

    def test_delete_agent_escape(self):
        src = self._read_src()
        idx = src.find("def delete_agent")
        assert idx != -1
        block = src[idx:idx + 400]
        assert "BUG-314-AGT-001" in block
        assert ".replace('\\\\', '\\\\\\\\')" in block

    def test_update_agent_trust_escape(self):
        src = self._read_src()
        idx = src.find("def update_agent_trust")
        assert idx != -1
        block = src[idx:idx + 600]
        assert "BUG-314-AGT-001" in block
        assert ".replace('\\\\', '\\\\\\\\')" in block

    def test_no_quote_only_escapes_remain(self):
        """Ensure no .replace('"', '\\"') without preceding backslash escape."""
        src = self._read_src()
        pattern = r"\.replace\('\\\\', '\\\\\\\\'\)\.replace\('\"', '\\\\\"'\)"
        correct = len(re.findall(pattern, src))
        quote_only = src.count('.replace(\'"\', \'\\\\"\')') - correct
        assert quote_only == 0, f"Found {quote_only} quote-only escapes in agents.py"

    def test_total_backslash_first_count(self):
        """Verify total count of backslash-first escapes matches expected."""
        src = self._read_src()
        pattern = r"\.replace\('\\\\', '\\\\\\\\'\)\.replace\('\"', '\\\\\"'\)"
        count = len(re.findall(pattern, src))
        # 6 escapes: get_agent(1), insert_agent(3), delete_agent(1), update_agent_trust(1)
        assert count >= 6, f"Expected >=6 backslash-first escapes in agents.py, got {count}"


# ── BUG-314-DET-001: tasks/details.py backslash-first escape ───────────


class TestTaskDetailsEscapeOrder:
    """Verify tasks/details.py uses backslash-first escape on task_id."""

    def test_task_id_escape(self):
        src = (SRC / "governance/typedb/queries/tasks/details.py").read_text()
        assert "BUG-314-DET-001" in src
        assert ".replace('\\\\', '\\\\\\\\')" in src

    def test_no_quote_only_on_task_id(self):
        """Ensure task_id_escaped uses backslash-first."""
        src = (SRC / "governance/typedb/queries/tasks/details.py").read_text()
        idx = src.find("task_id_escaped")
        assert idx != -1
        line = src[idx:idx + 100]
        assert ".replace('\\\\', '\\\\\\\\')" in line


# ── Systemic verification: no quote-only escapes in TypeDB queries ─────


class TestSystemicEscapeCompleteness:
    """Verify ALL TypeDB query files use backslash-first escapes."""

    def _check_file(self, rel_path: str):
        """Check that a file has no quote-only escapes remaining."""
        src = (SRC / rel_path).read_text()
        pattern = r"\.replace\('\\\\', '\\\\\\\\'\)\.replace\('\"', '\\\\\"'\)"
        correct = len(re.findall(pattern, src))
        quote_only = src.count('.replace(\'"\', \'\\\\"\')') - correct
        return quote_only

    def test_sessions_crud_clean(self):
        assert self._check_file("governance/typedb/queries/sessions/crud.py") == 0

    def test_sessions_mutations_clean(self):
        assert self._check_file("governance/typedb/queries/sessions/crud_mutations.py") == 0

    def test_sessions_read_clean(self):
        assert self._check_file("governance/typedb/queries/sessions/read.py") == 0

    def test_sessions_linking_clean(self):
        assert self._check_file("governance/typedb/queries/sessions/linking.py") == 0

    def test_agents_clean(self):
        assert self._check_file("governance/typedb/queries/agents.py") == 0

    def test_tasks_crud_clean(self):
        assert self._check_file("governance/typedb/queries/tasks/crud.py") == 0

    def test_tasks_linking_clean(self):
        assert self._check_file("governance/typedb/queries/tasks/linking.py") == 0

    def test_tasks_details_clean(self):
        assert self._check_file("governance/typedb/queries/tasks/details.py") == 0

    def test_tasks_status_clean(self):
        assert self._check_file("governance/typedb/queries/tasks/status.py") == 0

    def test_tasks_relationships_clean(self):
        assert self._check_file("governance/typedb/queries/tasks/relationships.py") == 0

    def test_rules_crud_clean(self):
        assert self._check_file("governance/typedb/queries/rules/crud.py") == 0

    def test_rules_inference_clean(self):
        assert self._check_file("governance/typedb/queries/rules/inference.py") == 0


# ── Import verification ─────────────────────────────────────────────


class TestBatch314Imports:
    """Verify all fixed modules import cleanly."""

    def test_import_agents_queries(self):
        from governance.typedb.queries import agents  # noqa: F401

    def test_import_task_details(self):
        from governance.typedb.queries.tasks import details  # noqa: F401
