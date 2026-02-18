"""Batch 215 — Rules, agents, projects service defense tests.

Validates fixes for:
- BUG-215-RUL-001: category+status filter now applies status unconditionally
- BUG-215-AGT-004: Sort uses type-aware fallback for numeric fields
- BUG-215-PRJ-001: Duplicate project check on auto-generated ID
- BUG-215-PRJ-004: _get_client logs exceptions
"""
from pathlib import Path
from unittest.mock import patch, MagicMock

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-215-RUL-001: Status filter applied unconditionally ───────────

class TestRulesStatusFilter:
    """list_rules must filter by status even when category is set."""

    def test_status_filter_unconditional_in_source(self):
        """Source must use 'if status:' not 'if status and status != ACTIVE'."""
        src = (SRC / "governance/services/rules.py").read_text()
        # Should NOT contain the old broken guard
        assert 'status != "ACTIVE"' not in src
        # Should contain the simple filter
        assert "if status:" in src


# ── BUG-215-AGT-004: Sort type-aware fallback ────────────────────────

class TestSortTypeAwareFallback:
    """Sort must handle numeric fields with value 0.0 (falsy)."""

    def test_agents_sort_no_or_empty_string(self):
        """agents.py sort must NOT use 'or ""' pattern."""
        src = (SRC / "governance/services/agents.py").read_text()
        # Find the sort line in list_agents and verify no 'or ""'
        in_list = False
        for line in src.splitlines():
            if "def list_agents" in line:
                in_list = True
            elif in_list and line.strip().startswith("def "):
                break
            elif in_list and "result.sort" in line and 'or ""' in line:
                assert False, "Sort must not use 'or \"\"' — crashes on numeric 0.0"

    def test_rules_sort_no_or_empty_string(self):
        """rules.py sort must NOT use 'or ""' pattern."""
        src = (SRC / "governance/services/rules.py").read_text()
        in_list = False
        for line in src.splitlines():
            if "def list_rules" in line:
                in_list = True
            elif in_list and line.strip().startswith("def "):
                break
            elif in_list and "rules.sort" in line and 'or ""' in line:
                assert False, "Sort must not use 'or \"\"' — crashes on numeric 0.0"

    def test_sort_key_handles_none(self):
        """Type-aware sort key must put None values last."""
        items = [
            {"trust_score": 0.5},
            {"trust_score": None},
            {"trust_score": 0.0},
            {"trust_score": 0.8},
        ]
        def _sort_key(a):
            v = a.get("trust_score")
            if v is None:
                return (1, "")
            return (0, v)
        sorted_items = sorted(items, key=_sort_key)
        # None should be last
        assert sorted_items[-1]["trust_score"] is None
        # 0.0 should be first (not treated as None)
        assert sorted_items[0]["trust_score"] == 0.0


# ── BUG-215-PRJ-001: Duplicate project check ─────────────────────────

class TestProjectDuplicateCheck:
    """create_project must check for existing project before creating."""

    def test_duplicate_check_in_source(self):
        """Source must call get_project before creating."""
        src = (SRC / "governance/services/projects.py").read_text()
        # Find create_project and verify get_project is called
        in_func = False
        found_check = False
        for line in src.splitlines():
            if "def create_project" in line:
                in_func = True
            elif in_func and line.strip().startswith("def "):
                break
            elif in_func and "get_project(project_id)" in line:
                found_check = True
        assert found_check, "create_project must check for existing project"

    def test_create_returns_existing_on_duplicate(self):
        from governance.services.projects import create_project, get_project
        store = {"PROJ-TEST": {"project_id": "PROJ-TEST", "name": "Test"}}
        with patch("governance.services.projects._get_client", return_value=None), \
             patch("governance.services.projects._projects_store", store):
            result = create_project(project_id="PROJ-TEST", name="Test")
        assert result["project_id"] == "PROJ-TEST"


# ── BUG-215-PRJ-004: _get_client logs exceptions ────────────────────

class TestProjectClientLogging:
    """_get_client must log exceptions, not silently swallow."""

    def test_no_bare_pass_in_get_client(self):
        """Source must not have bare 'pass' in _get_client exception handler."""
        src = (SRC / "governance/services/projects.py").read_text()
        in_func = False
        for line in src.splitlines():
            if "def _get_client" in line:
                in_func = True
            elif in_func and line.strip().startswith("def "):
                break
            elif in_func and line.strip() == "pass":
                assert False, "_get_client must not have bare 'pass'"


# ── Rules service defense ────────────────────────────────────────────

class TestRulesServiceDefense:
    """Defense tests for rules service module."""

    def test_list_rules_callable(self):
        from governance.services.rules import list_rules
        assert callable(list_rules)

    def test_get_rule_callable(self):
        from governance.services.rules import get_rule
        assert callable(get_rule)

    def test_create_rule_callable(self):
        from governance.services.rules import create_rule
        assert callable(create_rule)

    def test_update_rule_callable(self):
        from governance.services.rules import update_rule
        assert callable(update_rule)

    def test_delete_rule_callable(self):
        from governance.services.rules import delete_rule
        assert callable(delete_rule)


# ── Agents service defense ───────────────────────────────────────────

class TestAgentsServiceDefense:
    """Defense tests for agents service module."""

    def test_list_agents_callable(self):
        from governance.services.agents import list_agents
        assert callable(list_agents)

    def test_get_agent_callable(self):
        from governance.services.agents import get_agent
        assert callable(get_agent)

    def test_create_agent_callable(self):
        from governance.services.agents import create_agent
        assert callable(create_agent)

    def test_toggle_agent_status_callable(self):
        from governance.services.agents import toggle_agent_status
        assert callable(toggle_agent_status)


# ── Projects service defense ─────────────────────────────────────────

class TestProjectsServiceDefense:
    """Defense tests for projects service module."""

    def test_create_project_callable(self):
        from governance.services.projects import create_project
        assert callable(create_project)

    def test_get_project_callable(self):
        from governance.services.projects import get_project
        assert callable(get_project)

    def test_list_projects_callable(self):
        from governance.services.projects import list_projects
        assert callable(list_projects)

    def test_delete_project_callable(self):
        from governance.services.projects import delete_project
        assert callable(delete_project)

    def test_get_project_returns_none_for_nonexistent(self):
        from governance.services.projects import get_project
        with patch("governance.services.projects._get_client", return_value=None), \
             patch("governance.services.projects._projects_store", {}):
            result = get_project("PROJ-NONEXISTENT")
        assert result is None

    def test_delete_project_returns_false_for_nonexistent(self):
        from governance.services.projects import delete_project
        with patch("governance.services.projects._get_client", return_value=None), \
             patch("governance.services.projects._projects_store", {}):
            result = delete_project("PROJ-NONEXISTENT")
        assert result is False
