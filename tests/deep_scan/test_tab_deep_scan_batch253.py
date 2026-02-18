"""Batch 253 — Routes layer defense tests.

Validates fixes for:
- BUG-253-INJ-001: Order parameter whitelist across all CRUD endpoints
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-253-INJ-001: order parameter whitelist ───────────────────────

class TestAgentsOrderWhitelist:
    """agents/crud.py must validate order param."""

    def test_order_whitelist_present(self):
        src = (SRC / "governance/routes/agents/crud.py").read_text()
        idx = src.index("def list_agents")
        block = src[idx:idx + 1200]
        assert 'order not in {"asc", "desc"}' in block or "order not in {" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/routes/agents/crud.py").read_text()
        assert "BUG-253-INJ-001" in src


class TestRulesOrderWhitelist:
    """rules/crud.py must validate order param."""

    def test_order_whitelist_present(self):
        src = (SRC / "governance/routes/rules/crud.py").read_text()
        idx = src.index("def list_rules")
        block = src[idx:idx + 1200]
        assert 'order not in {"asc", "desc"}' in block or "order not in {" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/routes/rules/crud.py").read_text()
        assert "BUG-253-INJ-001" in src


class TestSessionsOrderWhitelist:
    """sessions/crud.py must validate order param."""

    def test_order_whitelist_present(self):
        src = (SRC / "governance/routes/sessions/crud.py").read_text()
        idx = src.index("def list_sessions")
        block = src[idx:idx + 1800]
        assert 'order not in {"asc", "desc"}' in block or "order not in {" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/routes/sessions/crud.py").read_text()
        assert "BUG-253-INJ-001" in src


class TestTasksOrderWhitelist:
    """tasks/crud.py must validate order param."""

    def test_order_whitelist_present(self):
        src = (SRC / "governance/routes/tasks/crud.py").read_text()
        idx = src.index("def list_tasks")
        block = src[idx:idx + 1200]
        assert 'order not in {"asc", "desc"}' in block or "order not in {" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/routes/tasks/crud.py").read_text()
        assert "BUG-253-INJ-001" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch253Imports:
    def test_agents_crud_importable(self):
        import governance.routes.agents.crud
        assert governance.routes.agents.crud is not None

    def test_rules_crud_importable(self):
        import governance.routes.rules.crud
        assert governance.routes.rules.crud is not None

    def test_sessions_crud_importable(self):
        import governance.routes.sessions.crud
        assert governance.routes.sessions.crud is not None

    def test_tasks_crud_importable(self):
        import governance.routes.tasks.crud
        assert governance.routes.tasks.crud is not None

    def test_sessions_detail_importable(self):
        import governance.routes.sessions.detail
        assert governance.routes.sessions.detail is not None

    def test_sessions_relations_importable(self):
        import governance.routes.sessions.relations
        assert governance.routes.sessions.relations is not None

    def test_chat_commands_importable(self):
        import governance.routes.chat.commands
        assert governance.routes.chat.commands is not None

    def test_chat_endpoints_importable(self):
        import governance.routes.chat.endpoints
        assert governance.routes.chat.endpoints is not None

    def test_chat_session_bridge_importable(self):
        import governance.routes.chat.session_bridge
        assert governance.routes.chat.session_bridge is not None
