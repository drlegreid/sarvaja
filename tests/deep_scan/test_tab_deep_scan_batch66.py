"""
Batch 66 — Deep Scan: Tasks CRUD + Projects + Rules read + Agent read escaping.

Fixes verified:
- BUG-TYPEQL-ESCAPE-TASK-001: task_id escaped in all task CRUD queries
- BUG-TYPEQL-ESCAPE-TASK-002: task_id escaped in all task read queries
- BUG-TYPEQL-ESCAPE-PROJECT-001: project_id escaped in all project CRUD queries
- BUG-TYPEQL-ESCAPE-PROJECT-002: all IDs escaped in project linking queries
- BUG-TYPEQL-ESCAPE-RULE-002: rule_id/category escaped in rule read queries
- BUG-AGENT-ESCAPE-001: agent_id escaped in get_agent read query
"""
import inspect
import re

import pytest


# ===========================================================================
# BUG-TYPEQL-ESCAPE-TASK-001: Task CRUD write queries
# ===========================================================================

class TestTaskCRUDEscaping:
    """Verify task_id escaped in all task CRUD write queries."""

    def _get_source(self):
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations
        return inspect.getsource(TaskCRUDOperations)

    def test_update_attribute_escapes_task_id(self):
        """_update_attribute must escape task_id."""
        from governance.typedb.queries.tasks.crud import _update_attribute
        src = inspect.getsource(_update_attribute)
        assert 'task_id.replace(' in src or "tid = task_id" in src

    def test_set_lifecycle_timestamps_escapes(self):
        """_set_lifecycle_timestamps must escape task_id."""
        from governance.typedb.queries.tasks.crud import _set_lifecycle_timestamps
        src = inspect.getsource(_set_lifecycle_timestamps)
        assert 'task_id.replace(' in src or "tid = task_id" in src

    def test_insert_task_escapes_task_id(self):
        """insert_task must escape task_id."""
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations
        src = inspect.getsource(TaskCRUDOperations.insert_task)
        assert "task_id_escaped" in src

    def test_insert_task_escapes_linked_rule_ids(self):
        """insert_task must escape rule_id in linked_rules loop."""
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations
        src = inspect.getsource(TaskCRUDOperations.insert_task)
        # Find the linked_rules section and verify escaping
        assert 'rule_id.replace(' in src or "rid = rule_id" in src

    def test_insert_task_escapes_linked_session_ids(self):
        """insert_task must escape session_id in linked_sessions loop."""
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations
        src = inspect.getsource(TaskCRUDOperations.insert_task)
        assert 'session_id.replace(' in src or "sid = session_id" in src

    def test_delete_task_escapes_task_id(self):
        """delete_task must escape task_id."""
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations
        src = inspect.getsource(TaskCRUDOperations.delete_task)
        assert "task_id_escaped" in src

    def test_no_raw_task_id_in_delete(self):
        """delete_task must not have raw task_id in queries."""
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations
        src = inspect.getsource(TaskCRUDOperations.delete_task)
        raw = re.findall(r'task-id "\{task_id\}"', src)
        assert len(raw) == 0, f"Found {len(raw)} unescaped task_id in delete_task"


# ===========================================================================
# BUG-TYPEQL-ESCAPE-TASK-002: Task read queries
# ===========================================================================

class TestTaskReadEscaping:
    """Verify task_id escaped in all task read queries."""

    def test_fetch_task_attr_escapes(self):
        """_fetch_task_attr must escape task_id."""
        from governance.typedb.queries.tasks.read import TaskReadQueries
        src = inspect.getsource(TaskReadQueries._fetch_task_attr)
        assert '.replace(' in src

    def test_fetch_task_relation_escapes(self):
        """_fetch_task_relation must escape task_id."""
        from governance.typedb.queries.tasks.read import TaskReadQueries
        src = inspect.getsource(TaskReadQueries._fetch_task_relation)
        assert '.replace(' in src

    def test_build_task_from_id_escapes(self):
        """_build_task_from_id must escape task_id."""
        from governance.typedb.queries.tasks.read import TaskReadQueries
        src = inspect.getsource(TaskReadQueries._build_task_from_id)
        assert '.replace(' in src

    def test_get_all_tasks_escapes_filters(self):
        """get_all_tasks must escape status/phase filter values."""
        from governance.typedb.queries.tasks.read import TaskReadQueries
        src = inspect.getsource(TaskReadQueries.get_all_tasks)
        assert 'status.replace(' in src or "status_esc" in src
        assert 'phase.replace(' in src or "phase_esc" in src

    def test_no_raw_task_id_in_build_fstring(self):
        """_build_task_from_id must not have raw task_id in f-string queries.

        Note: {task_id} in str.format() templates are safe — _fetch_task_relation escapes.
        Only check the main f-string query (has 'match $t isa task' as f-string).
        """
        from governance.typedb.queries.tasks.read import TaskReadQueries
        src = inspect.getsource(TaskReadQueries._build_task_from_id)
        # The main query uses f-string; relationship templates use .format()
        # Split on _fetch_task_relation to only check code before relationship queries
        main_section = src.split("_fetch_task_relation")[0]
        raw = re.findall(r'task-id "\{task_id\}"', main_section)
        assert len(raw) == 0, f"Found {len(raw)} unescaped task_id in f-string queries"


# ===========================================================================
# BUG-TYPEQL-ESCAPE-PROJECT-001: Project CRUD queries
# ===========================================================================

class TestProjectCRUDEscaping:
    """Verify project_id escaped in all project CRUD queries."""

    def test_insert_project_escapes(self):
        """insert_project must escape project_id."""
        from governance.typedb.queries.projects.crud import ProjectCRUDOperations
        src = inspect.getsource(ProjectCRUDOperations.insert_project)
        assert "project_id_escaped" in src

    def test_get_project_escapes(self):
        """get_project must escape project_id."""
        from governance.typedb.queries.projects.crud import ProjectCRUDOperations
        src = inspect.getsource(ProjectCRUDOperations.get_project)
        assert '.replace(' in src

    def test_delete_project_escapes(self):
        """delete_project must escape project_id."""
        from governance.typedb.queries.projects.crud import ProjectCRUDOperations
        src = inspect.getsource(ProjectCRUDOperations.delete_project)
        assert '.replace(' in src

    def test_no_raw_project_id_in_get(self):
        """get_project must not have raw project_id in queries."""
        from governance.typedb.queries.projects.crud import ProjectCRUDOperations
        src = inspect.getsource(ProjectCRUDOperations.get_project)
        raw = re.findall(r'project-id "\{project_id\}"', src)
        assert len(raw) == 0, f"Found {len(raw)} unescaped project_id"

    def test_no_raw_project_id_in_delete(self):
        """delete_project must not have raw project_id in queries."""
        from governance.typedb.queries.projects.crud import ProjectCRUDOperations
        src = inspect.getsource(ProjectCRUDOperations.delete_project)
        raw = re.findall(r'project-id "\{project_id\}"', src)
        assert len(raw) == 0, f"Found {len(raw)} unescaped project_id"


# ===========================================================================
# BUG-TYPEQL-ESCAPE-PROJECT-002: Project linking queries
# ===========================================================================

class TestProjectLinkingEscaping:
    """Verify all IDs escaped in project linking queries."""

    def test_link_project_to_plan_escapes_both(self):
        """link_project_to_plan must escape both project_id and plan_id."""
        from governance.typedb.queries.projects.linking import ProjectLinkingOperations
        src = inspect.getsource(ProjectLinkingOperations.link_project_to_plan)
        assert "project_id.replace" in src or "pid = project_id" in src
        assert "plan_id.replace" in src or "plid = plan_id" in src

    def test_link_plan_to_epic_escapes_both(self):
        """link_plan_to_epic must escape both plan_id and epic_id."""
        from governance.typedb.queries.projects.linking import ProjectLinkingOperations
        src = inspect.getsource(ProjectLinkingOperations.link_plan_to_epic)
        assert "plan_id.replace" in src or "plid = plan_id" in src
        assert "epic_id.replace" in src or "eid = epic_id" in src

    def test_link_epic_to_task_escapes_both(self):
        """link_epic_to_task must escape both epic_id and task_id."""
        from governance.typedb.queries.projects.linking import ProjectLinkingOperations
        src = inspect.getsource(ProjectLinkingOperations.link_epic_to_task)
        assert "epic_id.replace" in src or "eid = epic_id" in src
        assert "task_id.replace" in src or "tid = task_id" in src

    def test_link_project_to_session_escapes_both(self):
        """link_project_to_session must escape both project_id and session_id."""
        from governance.typedb.queries.projects.linking import ProjectLinkingOperations
        src = inspect.getsource(ProjectLinkingOperations.link_project_to_session)
        assert "project_id.replace" in src or "pid = project_id" in src
        assert "session_id.replace" in src or "sid = session_id" in src

    def test_get_project_sessions_escapes(self):
        """get_project_sessions must escape project_id."""
        from governance.typedb.queries.projects.linking import ProjectLinkingOperations
        src = inspect.getsource(ProjectLinkingOperations.get_project_sessions)
        assert '.replace(' in src

    def test_get_project_plans_escapes(self):
        """get_project_plans must escape project_id."""
        from governance.typedb.queries.projects.linking import ProjectLinkingOperations
        src = inspect.getsource(ProjectLinkingOperations.get_project_plans)
        assert '.replace(' in src

    def test_no_raw_ids_in_link_project_to_plan(self):
        """link_project_to_plan must not have raw IDs."""
        from governance.typedb.queries.projects.linking import ProjectLinkingOperations
        src = inspect.getsource(ProjectLinkingOperations.link_project_to_plan)
        assert len(re.findall(r'project-id "\{project_id\}"', src)) == 0
        assert len(re.findall(r'plan-id "\{plan_id\}"', src)) == 0

    def test_no_raw_ids_in_link_project_to_session(self):
        """link_project_to_session must not have raw IDs."""
        from governance.typedb.queries.projects.linking import ProjectLinkingOperations
        src = inspect.getsource(ProjectLinkingOperations.link_project_to_session)
        assert len(re.findall(r'project-id "\{project_id\}"', src)) == 0
        assert len(re.findall(r'session-id "\{session_id\}"', src)) == 0


# ===========================================================================
# BUG-TYPEQL-ESCAPE-RULE-002: Rule read queries
# ===========================================================================

class TestRuleReadEscaping:
    """Verify rule_id/category escaped in rule read queries."""

    def test_fetch_optional_attrs_escapes(self):
        """_fetch_optional_rule_attrs must escape rule_id."""
        from governance.typedb.queries.rules.read import RuleReadQueries
        src = inspect.getsource(RuleReadQueries._fetch_optional_rule_attrs)
        assert '.replace(' in src

    def test_get_rule_by_id_escapes(self):
        """get_rule_by_id must escape rule_id."""
        from governance.typedb.queries.rules.read import RuleReadQueries
        src = inspect.getsource(RuleReadQueries.get_rule_by_id)
        assert '.replace(' in src

    def test_get_rules_by_category_escapes(self):
        """get_rules_by_category must escape category."""
        from governance.typedb.queries.rules.read import RuleReadQueries
        src = inspect.getsource(RuleReadQueries.get_rules_by_category)
        assert '.replace(' in src

    def test_get_tasks_for_rule_escapes(self):
        """get_tasks_for_rule must escape rule_id."""
        from governance.typedb.queries.rules.read import RuleReadQueries
        src = inspect.getsource(RuleReadQueries.get_tasks_for_rule)
        assert '.replace(' in src

    def test_no_raw_rule_id_in_get_by_id(self):
        """get_rule_by_id must not have raw rule_id in query."""
        from governance.typedb.queries.rules.read import RuleReadQueries
        src = inspect.getsource(RuleReadQueries.get_rule_by_id)
        raw = re.findall(r'rule-id "\{rule_id\}"', src)
        assert len(raw) == 0, f"Found {len(raw)} unescaped rule_id"


# ===========================================================================
# BUG-AGENT-ESCAPE-001: Agent read query
# ===========================================================================

class TestAgentReadEscaping:
    """Verify agent_id escaped in agent read queries."""

    def test_get_agent_escapes(self):
        """get_agent must escape agent_id."""
        from governance.typedb.queries.agents import AgentQueries
        src = inspect.getsource(AgentQueries.get_agent)
        assert '.replace(' in src

    def test_no_raw_agent_id_in_get(self):
        """get_agent must not have raw agent_id in query."""
        from governance.typedb.queries.agents import AgentQueries
        src = inspect.getsource(AgentQueries.get_agent)
        raw = re.findall(r'agent-id "\{agent_id\}"', src)
        assert len(raw) == 0, f"Found {len(raw)} unescaped agent_id"


# ===========================================================================
# Cross-file: Escaping completeness audit
# ===========================================================================

class TestBatch66EscapingCompleteness:
    """Cross-file audit of TypeQL escaping completeness."""

    def test_task_crud_total_escapes(self):
        """TaskCRUDOperations + helpers must have comprehensive escaping."""
        from governance.typedb.queries.tasks.crud import TaskCRUDOperations
        src = inspect.getsource(TaskCRUDOperations)
        from governance.typedb.queries.tasks.crud import _update_attribute, _set_lifecycle_timestamps
        src += inspect.getsource(_update_attribute)
        src += inspect.getsource(_set_lifecycle_timestamps)
        escape_count = src.count('.replace(')
        assert escape_count >= 15, f"Expected 15+ escape calls, found {escape_count}"

    def test_project_crud_total_escapes(self):
        """ProjectCRUDOperations must have comprehensive escaping."""
        from governance.typedb.queries.projects.crud import ProjectCRUDOperations
        src = inspect.getsource(ProjectCRUDOperations)
        escape_count = src.count('.replace(')
        assert escape_count >= 5, f"Expected 5+ escape calls, found {escape_count}"

    def test_project_linking_total_escapes(self):
        """ProjectLinkingOperations must have comprehensive escaping."""
        from governance.typedb.queries.projects.linking import ProjectLinkingOperations
        src = inspect.getsource(ProjectLinkingOperations)
        escape_count = src.count('.replace(')
        assert escape_count >= 10, f"Expected 10+ escape calls, found {escape_count}"

    def test_rule_read_total_escapes(self):
        """RuleReadQueries must have comprehensive escaping."""
        from governance.typedb.queries.rules.read import RuleReadQueries
        src = inspect.getsource(RuleReadQueries)
        escape_count = src.count('.replace(')
        assert escape_count >= 5, f"Expected 5+ escape calls, found {escape_count}"

    def test_task_read_total_escapes(self):
        """TaskReadQueries must have comprehensive escaping."""
        from governance.typedb.queries.tasks.read import TaskReadQueries
        src = inspect.getsource(TaskReadQueries)
        escape_count = src.count('.replace(')
        assert escape_count >= 4, f"Expected 4+ escape calls, found {escape_count}"
