"""Batch 248 — Session collector sync defense tests.

Validates fixes for:
- BUG-248-SYN-002: Missing finally block in _index_task_to_typedb
- BUG-248-SYN-003: Consistent _esc() helper for TypeQL escaping
- BUG-248-SYN-004: agent_id uses _esc() helper
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-248-SYN-002: finally block in _index_task_to_typedb ──────────

class TestIndexTaskFinallyBlock:
    """_index_task_to_typedb must have finally block to close client."""

    def test_finally_present(self):
        src = (SRC / "governance/session_collector/sync.py").read_text()
        idx = src.index("def _index_task_to_typedb")
        block = src[idx:idx + 4500]
        assert "finally:" in block

    def test_client_close_in_finally(self):
        src = (SRC / "governance/session_collector/sync.py").read_text()
        idx = src.index("def _index_task_to_typedb")
        block = src[idx:idx + 4500]
        finally_idx = block.index("finally:")
        after_finally = block[finally_idx:finally_idx + 200]
        assert "client.close()" in after_finally

    def test_client_init_none(self):
        """client must be initialized to None before try block."""
        src = (SRC / "governance/session_collector/sync.py").read_text()
        idx = src.index("def _index_task_to_typedb")
        block = src[idx:idx + 400]
        assert "client = None" in block

    def test_no_bare_client_close_in_try(self):
        """client.close() should NOT appear in try block (only in finally)."""
        src = (SRC / "governance/session_collector/sync.py").read_text()
        idx = src.index("def _index_task_to_typedb")
        block = src[idx:idx + 4500]
        try_idx = block.index("try:")
        finally_idx = block.index("finally:")
        try_block = block[try_idx:finally_idx]
        assert "client.close()" not in try_block

    def test_bug_marker_present(self):
        src = (SRC / "governance/session_collector/sync.py").read_text()
        assert "BUG-248-SYN-002" in src


# ── BUG-248-SYN-003: Consistent _esc() helper ────────────────────────

class TestIndexTaskEscHelper:
    """_index_task_to_typedb must use _esc() for all interpolated strings."""

    def test_esc_helper_defined(self):
        src = (SRC / "governance/session_collector/sync.py").read_text()
        idx = src.index("def _index_task_to_typedb")
        block = src[idx:idx + 3000]
        assert "def _esc(" in block

    def test_esc_backslash_first(self):
        """_esc must escape backslash BEFORE quotes."""
        src = (SRC / "governance/session_collector/sync.py").read_text()
        idx = src.index("def _index_task_to_typedb")
        block = src[idx:idx + 3000]
        esc_idx = block.index("def _esc(")
        esc_block = block[esc_idx:esc_idx + 200]
        assert "replace('\\\\'" in esc_block

    def test_session_id_uses_esc(self):
        src = (SRC / "governance/session_collector/sync.py").read_text()
        idx = src.index("def _index_task_to_typedb")
        block = src[idx:idx + 3000]
        assert "_esc(self.session_id)" in block

    def test_topic_uses_esc(self):
        src = (SRC / "governance/session_collector/sync.py").read_text()
        idx = src.index("def _index_task_to_typedb")
        block = src[idx:idx + 3000]
        assert "_esc(self.topic)" in block

    def test_session_type_uses_esc(self):
        src = (SRC / "governance/session_collector/sync.py").read_text()
        idx = src.index("def _index_task_to_typedb")
        block = src[idx:idx + 3000]
        assert "_esc(self.session_type)" in block

    def test_task_name_uses_esc(self):
        src = (SRC / "governance/session_collector/sync.py").read_text()
        idx = src.index("def _index_task_to_typedb")
        block = src[idx:idx + 3000]
        assert "_esc(task.name)" in block

    def test_task_id_uses_esc(self):
        src = (SRC / "governance/session_collector/sync.py").read_text()
        idx = src.index("def _index_task_to_typedb")
        block = src[idx:idx + 3000]
        assert "_esc(task.id)" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/session_collector/sync.py").read_text()
        assert "BUG-248-SYN-003" in src


# ── BUG-248-SYN-004: agent_id uses _esc() ────────────────────────────

class TestAgentIdEscaping:
    """agent_id must use _esc() helper, not bare .replace()."""

    def test_agent_uses_esc(self):
        src = (SRC / "governance/session_collector/sync.py").read_text()
        idx = src.index("def _index_task_to_typedb")
        block = src[idx:idx + 3000]
        assert "_esc(self.agent_id)" in block

    def test_no_bare_replace_agent(self):
        """agent_id should NOT use bare .replace() in task indexer."""
        src = (SRC / "governance/session_collector/sync.py").read_text()
        idx = src.index("def _index_task_to_typedb")
        block = src[idx:idx + 3000]
        assert 'self.agent_id.replace(' not in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/session_collector/sync.py").read_text()
        assert "BUG-248-SYN-004" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch248Imports:
    def test_sync_importable(self):
        import governance.session_collector.sync
        assert governance.session_collector.sync is not None

    def test_models_importable(self):
        import governance.session_collector.models
        assert governance.session_collector.models is not None

    def test_registry_importable(self):
        import governance.session_collector.registry
        assert governance.session_collector.registry is not None

    def test_capture_importable(self):
        import governance.session_collector.capture
        assert governance.session_collector.capture is not None

    def test_render_importable(self):
        import governance.session_collector.render
        assert governance.session_collector.render is not None
