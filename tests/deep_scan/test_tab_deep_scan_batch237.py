"""Batch 237 — REST API route defense tests.

Validates fixes for:
- BUG-237-SORT-001: sort_by whitelist validation across all CRUD routes
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-237-SORT-001: sort_by whitelist in agents route ──────────────

class TestAgentsSortByWhitelist:
    """Agents list_agents must validate sort_by."""

    def test_agents_has_valid_sort_set(self):
        src = (SRC / "governance/routes/agents/crud.py").read_text()
        assert "_valid_sort" in src

    def test_agents_rejects_invalid_sort(self):
        src = (SRC / "governance/routes/agents/crud.py").read_text()
        assert "Invalid sort_by" in src

    def test_agents_sort_includes_trust_score(self):
        src = (SRC / "governance/routes/agents/crud.py").read_text()
        assert '"trust_score"' in src

    def test_agents_bug_marker(self):
        src = (SRC / "governance/routes/agents/crud.py").read_text()
        assert "BUG-237-SORT-001" in src


# ── BUG-237-SORT-001: sort_by whitelist in rules route ───────────────

class TestRulesSortByWhitelist:
    """Rules list_rules must validate sort_by."""

    def test_rules_has_valid_sort_set(self):
        src = (SRC / "governance/routes/rules/crud.py").read_text()
        assert "_valid_sort" in src

    def test_rules_rejects_invalid_sort(self):
        src = (SRC / "governance/routes/rules/crud.py").read_text()
        assert "Invalid sort_by" in src

    def test_rules_sort_includes_category(self):
        src = (SRC / "governance/routes/rules/crud.py").read_text()
        assert '"category"' in src

    def test_rules_bug_marker(self):
        src = (SRC / "governance/routes/rules/crud.py").read_text()
        assert "BUG-237-SORT-001" in src


# ── BUG-237-SORT-001: sort_by whitelist in sessions route ────────────

class TestSessionsSortByWhitelist:
    """Sessions list_sessions must validate sort_by."""

    def test_sessions_has_valid_sort_set(self):
        src = (SRC / "governance/routes/sessions/crud.py").read_text()
        assert "_valid_sort" in src

    def test_sessions_rejects_invalid_sort(self):
        src = (SRC / "governance/routes/sessions/crud.py").read_text()
        assert "Invalid sort_by" in src

    def test_sessions_sort_includes_started_at(self):
        src = (SRC / "governance/routes/sessions/crud.py").read_text()
        assert '"started_at"' in src

    def test_sessions_bug_marker(self):
        src = (SRC / "governance/routes/sessions/crud.py").read_text()
        assert "BUG-237-SORT-001" in src


# ── BUG-237-SORT-001: sort_by whitelist in tasks route ───────────────

class TestTasksSortByWhitelist:
    """Tasks list_tasks must validate sort_by."""

    def test_tasks_has_valid_sort_set(self):
        src = (SRC / "governance/routes/tasks/crud.py").read_text()
        assert "_valid_sort" in src

    def test_tasks_rejects_invalid_sort(self):
        src = (SRC / "governance/routes/tasks/crud.py").read_text()
        assert "Invalid sort_by" in src

    def test_tasks_sort_includes_phase(self):
        src = (SRC / "governance/routes/tasks/crud.py").read_text()
        assert '"phase"' in src

    def test_tasks_bug_marker(self):
        src = (SRC / "governance/routes/tasks/crud.py").read_text()
        assert "BUG-237-SORT-001" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch237Imports:
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

    def test_agents_observability_importable(self):
        import governance.routes.agents.observability
        assert governance.routes.agents.observability is not None

    def test_sessions_detail_importable(self):
        import governance.routes.sessions.detail
        assert governance.routes.sessions.detail is not None

    def test_sessions_relations_importable(self):
        import governance.routes.sessions.relations
        assert governance.routes.sessions.relations is not None
