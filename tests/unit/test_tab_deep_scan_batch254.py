"""Batch 254 — TypeQL escaping consistency tests.

Validates fixes for:
- BUG-254-ESC-001: Backslash+quote escaping in rules/crud.py update/delete
- BUG-254-ESC-002: Backslash+quote escaping in tasks/linking.py
- BUG-254-ESC-003: Backslash+quote escaping in tasks/relationships.py
- BUG-254-VER-001: verified=False when TypeDB update fails
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-254-ESC-001: rules/crud.py escaping ──────────────────────────

class TestRulesCrudEscaping:
    """update_rule and delete_rule must escape backslash before quotes."""

    def test_update_rule_uses_esc_helper(self):
        src = (SRC / "governance/typedb/queries/rules/crud.py").read_text()
        idx = src.index("def update_rule")
        block = src[idx:idx + 4500]
        # Should use _esc(rule_id) instead of bare .replace
        assert "_esc(rule_id)" in block

    def test_delete_rule_backslash_escape(self):
        src = (SRC / "governance/typedb/queries/rules/crud.py").read_text()
        idx = src.index("def delete_rule")
        block = src[idx:idx + 1500]
        assert "replace('\\\\', '\\\\\\\\')" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/typedb/queries/rules/crud.py").read_text()
        assert "BUG-254-ESC-001" in src


# ── BUG-254-ESC-002: tasks/linking.py escaping ───────────────────────

class TestTasksLinkingEscaping:
    """All escape calls in linking.py must include backslash step."""

    def test_link_evidence_backslash_escape(self):
        src = (SRC / "governance/typedb/queries/tasks/linking.py").read_text()
        idx = src.index("def link_evidence_to_task")
        block = src[idx:idx + 1200]
        assert "replace('\\\\', '\\\\\\\\')" in block

    def test_link_task_to_session_backslash_escape(self):
        src = (SRC / "governance/typedb/queries/tasks/linking.py").read_text()
        idx = src.index("def link_task_to_session")
        block = src[idx:idx + 1000]
        assert "replace('\\\\', '\\\\\\\\')" in block

    def test_link_task_to_commit_backslash_escape(self):
        src = (SRC / "governance/typedb/queries/tasks/linking.py").read_text()
        idx = src.index("def link_task_to_commit")
        block = src[idx:idx + 1500]
        assert "replace('\\\\', '\\\\\\\\')" in block

    def test_no_bare_quote_only_escape(self):
        """No .replace('"', '\\"') without preceding backslash escape."""
        src = (SRC / "governance/typedb/queries/tasks/linking.py").read_text()
        import re
        # Find .replace('"', '\\"') NOT preceded by .replace('\\', '\\\\')
        lines = src.split("\n")
        bare_escapes = []
        for i, line in enumerate(lines):
            if '.replace(\'"\', \'\\\\"\')' in line:
                # Check if previous non-blank line has backslash escape
                prev = lines[i - 1].strip() if i > 0 else ""
                if "replace('\\\\'," not in prev and "replace('\\\\'," not in line:
                    bare_escapes.append(i + 1)
        assert not bare_escapes, f"Bare quote-only escapes at lines: {bare_escapes}"

    def test_bug_marker_present(self):
        src = (SRC / "governance/typedb/queries/tasks/linking.py").read_text()
        assert "BUG-254-ESC-002" in src


# ── BUG-254-ESC-003: tasks/relationships.py escaping ─────────────────

class TestTasksRelationshipsEscaping:
    """All escape calls in relationships.py write methods must include backslash step."""

    def test_link_parent_backslash_escape(self):
        src = (SRC / "governance/typedb/queries/tasks/relationships.py").read_text()
        idx = src.index("def link_parent_task")
        block = src[idx:idx + 1000]
        assert "replace('\\\\', '\\\\\\\\')" in block

    def test_link_blocking_backslash_escape(self):
        src = (SRC / "governance/typedb/queries/tasks/relationships.py").read_text()
        idx = src.index("def link_blocking_task")
        block = src[idx:idx + 1000]
        assert "replace('\\\\', '\\\\\\\\')" in block

    def test_link_related_backslash_escape(self):
        src = (SRC / "governance/typedb/queries/tasks/relationships.py").read_text()
        idx = src.index("def link_related_tasks")
        block = src[idx:idx + 1000]
        assert "replace('\\\\', '\\\\\\\\')" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/typedb/queries/tasks/relationships.py").read_text()
        assert "BUG-254-ESC-003" in src


# ── BUG-254-VER-001: verified=False on TypeDB failure ────────────────

class TestVerifyFalseOnFailure:
    """task_verify must return verified=False when TypeDB update fails."""

    def test_verified_false_in_fallback_path(self):
        src = (SRC / "governance/mcp_tools/tasks_crud_verify.py").read_text()
        idx = src.index("def task_verify")
        block = src[idx:idx + 3200]
        assert '"verified": False' in block

    def test_no_verified_true_in_fallback(self):
        """The fallback path must NOT say verified=True."""
        src = (SRC / "governance/mcp_tools/tasks_crud_verify.py").read_text()
        idx = src.index("def task_verify")
        block = src[idx:idx + 3200]
        # Count occurrences of verified: True — should be exactly 1 (success path)
        count = block.count('"verified": True')
        assert count == 1, f"Expected 1 verified=True (success), found {count}"

    def test_bug_marker_present(self):
        src = (SRC / "governance/mcp_tools/tasks_crud_verify.py").read_text()
        assert "BUG-254-VER-001" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch254Imports:
    def test_rules_crud_importable(self):
        import governance.typedb.queries.rules.crud
        assert governance.typedb.queries.rules.crud is not None

    def test_rules_inference_importable(self):
        import governance.typedb.queries.rules.inference
        assert governance.typedb.queries.rules.inference is not None

    def test_tasks_linking_importable(self):
        import governance.typedb.queries.tasks.linking
        assert governance.typedb.queries.tasks.linking is not None

    def test_tasks_relationships_importable(self):
        import governance.typedb.queries.tasks.relationships
        assert governance.typedb.queries.tasks.relationships is not None

    def test_tasks_crud_verify_importable(self):
        import governance.mcp_tools.tasks_crud_verify
        assert governance.mcp_tools.tasks_crud_verify is not None
