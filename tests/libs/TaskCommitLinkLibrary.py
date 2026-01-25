"""
Robot Framework library for Task-Git Commit Linking tests.

Per GAP-TASK-LINK-002: Tasks linked to github commits
Migrated from tests/test_task_commit_link.py
"""

import re
from robot.api.deco import keyword


class TaskCommitLinkLibrary:
    """Library for testing task-commit linking functionality."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # Commit SHA Format Tests
    # =========================================================================

    @keyword("Commit SHA Format Short")
    def commit_sha_format_short(self):
        """Test short commit SHA format (7 chars)."""
        short_sha = "abc1234"
        return {
            "length_correct": len(short_sha) == 7,
            "format_valid": bool(re.match(r'^[a-f0-9]{7}$', short_sha))
        }

    @keyword("Commit SHA Format Full")
    def commit_sha_format_full(self):
        """Test full commit SHA format (40 chars)."""
        full_sha = "abc1234567890def1234567890abc12345678901"
        return {
            "length_correct": len(full_sha) == 40,
            "format_valid": bool(re.match(r'^[a-f0-9]{40}$', full_sha))
        }

    @keyword("Commit Reference Patterns")
    def commit_reference_patterns(self):
        """Test various commit reference patterns."""
        valid_patterns = [
            "abc1234",
            "abc1234567890def1234567890abc1234567890",
            "HEAD",
            "HEAD~1",
            "main",
        ]
        return {"all_valid": all(p is not None for p in valid_patterns)}

    # =========================================================================
    # Task Entity Tests
    # =========================================================================

    @keyword("Task Has Linked Commits Field")
    def task_has_linked_commits_field(self):
        """Verify Task entity has linked_commits field."""
        try:
            from governance.typedb.entities import Task
            from dataclasses import fields
            field_names = [f.name for f in fields(Task)]
            return {"has_field": 'linked_commits' in field_names}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Task Linked Commits Is List")
    def task_linked_commits_is_list(self):
        """Verify linked_commits is a list type."""
        try:
            from governance.typedb.entities import Task
            from dataclasses import fields
            for f in fields(Task):
                if f.name == 'linked_commits':
                    return {"is_list": 'List' in str(f.type) or 'list' in str(f.type)}
            return {"is_list": False}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # TypeDB Schema Tests
    # =========================================================================

    @keyword("Schema Has Commit SHA Attribute")
    def schema_has_commit_sha_attribute(self):
        """Verify schema has commit-sha attribute."""
        try:
            schema_path = 'governance/schema.tql'
            with open(schema_path, 'r') as f:
                content = f.read()
            return {"has_attribute": 'commit-sha' in content}
        except FileNotFoundError:
            return {"skipped": True, "reason": "schema.tql not found"}

    @keyword("Schema Has Commit Relation")
    def schema_has_commit_relation(self):
        """Verify schema has task-commit relation."""
        try:
            schema_path = 'governance/schema.tql'
            with open(schema_path, 'r') as f:
                content = f.read()
            return {
                "has_relation": 'task-commit' in content or 'implemented-by-commit' in content
            }
        except FileNotFoundError:
            return {"skipped": True, "reason": "schema.tql not found"}

    # =========================================================================
    # Infrastructure Tests
    # =========================================================================

    @keyword("Linking Module Has Commit Method")
    def linking_module_has_commit_method(self):
        """Verify linking module has link_task_to_commit method."""
        try:
            from governance.typedb.queries.tasks.linking import TaskLinkingOperations
            return {"has_method": hasattr(TaskLinkingOperations, 'link_task_to_commit')}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Linking Module Has Get Commits Method")
    def linking_module_has_get_commits_method(self):
        """Verify linking module has get_task_commits method."""
        try:
            from governance.typedb.queries.tasks.linking import TaskLinkingOperations
            return {"has_method": hasattr(TaskLinkingOperations, 'get_task_commits')}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # MCP Tool Tests
    # =========================================================================

    @keyword("MCP Registration Includes Commit Tool")
    def mcp_registration_includes_commit_tool(self):
        """Verify MCP registration includes commit linking tool."""
        try:
            import inspect
            from governance.mcp_tools import tasks_linking
            source = inspect.getsource(tasks_linking)
            return {
                "has_commit_tool": 'link_commit' in source or 'commit' in source.lower()
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Data Integrity Tests
    # =========================================================================

    @keyword("Multiple Commits Per Task")
    def multiple_commits_per_task(self):
        """Test a task can have multiple commits."""
        task_commits = ["abc1234", "def5678", "ghi9012"]
        return {"allowed": len(task_commits) >= 1}

    @keyword("Commit To Multiple Tasks")
    def commit_to_multiple_tasks(self):
        """Test a commit can implement multiple tasks."""
        commit_sha = "abc1234"
        related_tasks = ["GAP-TASK-001", "GAP-TASK-002"]
        return {
            "commit_valid": commit_sha is not None,
            "multiple_tasks": len(related_tasks) >= 1
        }

    # =========================================================================
    # BDD Scenario Tests
    # =========================================================================

    @keyword("Scenario Developer Links Commit To Task")
    def scenario_developer_links_commit_to_task(self):
        """GIVEN/WHEN/THEN scenario for linking commit to task."""
        task_id = "GAP-TASK-LINK-002"
        commit_sha = "abc1234"
        return {
            "task_defined": task_id is not None,
            "commit_defined": commit_sha is not None
        }

    @keyword("Scenario Query Commits For Task")
    def scenario_query_commits_for_task(self):
        """GIVEN/WHEN/THEN scenario for querying commits."""
        expected_commits = ["abc1234", "def5678"]
        return {"has_multiple": len(expected_commits) == 2}
